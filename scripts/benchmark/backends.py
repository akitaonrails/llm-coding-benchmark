"""Local model backend abstraction (Ollama, llama-swap)."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

from benchmark.util import print_line


PREFLIGHT_TIMEOUT_SECONDS = 45.0
PREFLIGHT_FALLBACK_CONTEXTS = [131072, 98304, 65536, 32768]


def _api_url(api_base: str, path: str) -> str:
    return urllib.parse.urljoin(api_base.rstrip("/") + "/", path.lstrip("/"))


def _post_json(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any] | None:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        try:
            return json.loads(error.read().decode("utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"error": f"http_error:{error.code}"}
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError):
        return None


def _get_json(url: str, timeout: float) -> dict[str, Any] | None:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError):
        return None


class LocalModelBackend(ABC):
    """Interface for a local model serving backend."""

    def __init__(self, api_base: str) -> None:
        self.api_base = api_base

    @abstractmethod
    def list_active(self) -> list[str] | None:
        """Return names of currently loaded models, or None if the server is unreachable."""

    @abstractmethod
    def unload(self, model: str) -> bool:
        """Unload a specific model. Return True on success."""

    @abstractmethod
    def preload(self, model: str, context: int | None = None) -> tuple[bool, str]:
        """Load a model (optionally at a given context size). Return (ok, message)."""

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the backend is reachable."""

    def fetch_status_string(self) -> str | None:
        """Return a short human-readable status string, or None if unreachable."""
        models = self.list_active()
        if models is None:
            return None
        if not models:
            return f"{self.backend_name}=idle"
        return f"{self.backend_name}={','.join(models)}"

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Short identifier for log messages."""

    def unload_all(self) -> None:
        current = self.list_active()
        if not current:
            return
        print_line(f"Unloading: {', '.join(current)}")
        for model in current:
            self.unload(model)

    def preflight_context_candidates(self, context_limit: int | None) -> list[int | None]:
        if context_limit is None:
            return [None]
        ordered: list[int | None] = [context_limit]
        for candidate in PREFLIGHT_FALLBACK_CONTEXTS:
            if candidate >= context_limit:
                continue
            if candidate not in ordered:
                ordered.append(candidate)
        return ordered

    def ensure_model_ready(
        self,
        model_name: str,
        model_slug: str,
        context_limit: int | None = None,
    ) -> tuple[bool, str]:
        """Unload other models, then try to preload the target at available context sizes."""
        current = self.list_active()
        if current is None:
            print_line(f"[{model_slug}] preflight skipped: unable to reach {self.backend_name}")
            return True, f"preflight skipped: unable to reach {self.backend_name}"

        if current:
            print_line(f"[{model_slug}] unloading: {', '.join(current)}")
            for name in current:
                if self.unload(name):
                    print_line(f"[{model_slug}] unloaded {name}")
                else:
                    print_line(f"[{model_slug}] unload may have failed for {name}")

        last_message = "unknown preflight failure"
        for candidate_context in self.preflight_context_candidates(context_limit):
            ctx_str = f" ctx={candidate_context}" if candidate_context else ""
            print_line(f"[{model_slug}] preloading: {model_name}{ctx_str}")
            ok, message = self.preload(model_name, candidate_context)
            if ok:
                print_line(f"[{model_slug}] preload ok: {model_name}{ctx_str}")
                return True, message
            last_message = message
            print_line(f"[{model_slug}] preload failed: {model_name}{ctx_str}: {message}")

        return False, last_message


class OllamaBackend(LocalModelBackend):
    """Ollama-specific backend using /api/* endpoints."""

    @property
    def backend_name(self) -> str:
        return "ollama"

    def list_active(self) -> list[str] | None:
        payload = _get_json(_api_url(self.api_base, "/api/ps"), timeout=1.5)
        if not payload:
            return None
        models = payload.get("models")
        if not isinstance(models, list):
            return None
        names: list[str] = []
        for item in models:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("model")
            if isinstance(name, str) and name:
                names.append(name)
        return names

    def unload(self, model: str) -> bool:
        response = _post_json(
            _api_url(self.api_base, "/api/generate"),
            {"model": model, "prompt": "", "keep_alive": 0, "stream": False},
            timeout=30.0,
        )
        return bool(response and response.get("done_reason") == "unload")

    def preload(self, model: str, context: int | None = None) -> tuple[bool, str]:
        payload: dict[str, Any] = {
            "model": model,
            "prompt": "ping",
            "keep_alive": "2h",
            "stream": False,
            "options": {"num_predict": 8},
        }
        if context:
            payload["options"]["num_ctx"] = context
        response = _post_json(
            _api_url(self.api_base, "/api/generate"),
            payload,
            timeout=PREFLIGHT_TIMEOUT_SECONDS,
        )
        if not response:
            return False, "no response from ollama"
        if response.get("error"):
            return False, str(response["error"])
        if response.get("done") is True:
            return True, "preload ok"
        return False, "unexpected preload response"

    def health_check(self) -> bool:
        return self.list_active() is not None


class LlamaSwapBackend(LocalModelBackend):
    """llama-swap backend using OpenAI-compatible /v1/* endpoints."""

    @property
    def backend_name(self) -> str:
        return "llama-swap"

    def list_active(self) -> list[str] | None:
        payload = _get_json(_api_url(self.api_base, "/v1/models"), timeout=3.0)
        if not payload:
            return None
        data = payload.get("data")
        if not isinstance(data, list):
            return []
        return [item["id"] for item in data if isinstance(item, dict) and isinstance(item.get("id"), str)]

    def unload(self, model: str) -> bool:
        # llama-swap manages model lifecycle automatically.
        # Requesting a different model unloads the current one.
        # An explicit unload can be done via the upstream endpoint if available,
        # but for most setups this is a no-op.
        response = _post_json(
            _api_url(self.api_base, "/unload"),
            {"model": model},
            timeout=30.0,
        )
        # If the endpoint doesn't exist, that's fine — llama-swap handles it.
        return True if response is None else bool(response)

    def preload(self, model: str, context: int | None = None) -> tuple[bool, str]:
        # llama-swap context is configured server-side, not per-request.
        # We just send a small completion to trigger model loading.
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 8,
        }
        response = _post_json(
            _api_url(self.api_base, "/v1/chat/completions"),
            payload,
            timeout=PREFLIGHT_TIMEOUT_SECONDS,
        )
        if not response:
            return False, "no response from llama-swap"
        if response.get("error"):
            error = response["error"]
            message = error.get("message", str(error)) if isinstance(error, dict) else str(error)
            return False, message
        if response.get("choices"):
            return True, "preload ok"
        return False, "unexpected preload response"

    def health_check(self) -> bool:
        return _get_json(_api_url(self.api_base, "/v1/models"), timeout=3.0) is not None


BACKEND_TYPES: dict[str, type[LocalModelBackend]] = {
    "ollama": OllamaBackend,
    "llama-swap": LlamaSwapBackend,
}


def create_backend(backend_type: str, api_base: str) -> LocalModelBackend:
    cls = BACKEND_TYPES.get(backend_type)
    if cls is None:
        raise ValueError(f"Unknown backend type: {backend_type!r}. Available: {', '.join(BACKEND_TYPES)}")
    return cls(api_base)
