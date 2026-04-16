"""Benchmark configuration loading and opencode config generation."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from benchmark.backends import LocalModelBackend
from benchmark.util import (
    clone_json,
    load_json,
    load_optional_json,
    print_line,
    save_json,
    save_json_preserve_order,
)


OPENCODE_CONFIG_PATH = Path.home() / ".config" / "opencode" / "opencode.json"

OPENCODE_YOLO_PERMISSION = {
    "bash": {"*": "allow"},
    "codesearch": {"*": "allow"},
    "doom_loop": {"*": "allow"},
    "edit": {"*": "allow"},
    "external_directory": {"*": "allow"},
    "glob": {"*": "allow"},
    "grep": {"*": "allow"},
    "list": {"*": "allow"},
    "lsp": {"*": "allow"},
    "read": {"*": "allow"},
    "skill": {"*": "allow"},
    "task": {"*": "allow"},
    "todowrite": {"*": "allow"},
    "webfetch": {"*": "allow"},
    "websearch": {"*": "allow"},
}

TERMINAL_STATUSES = {"completed", "completed_with_errors", "failed", "timeout"}


@dataclass
class BenchmarkConfig:
    """All settings needed for a benchmark run, built from CLI args and config files."""

    runner: dict[str, Any]
    config_path: Path
    results_dir: Path
    opencode_config_path: Path | None
    timeout_seconds: int
    no_progress_timeout_seconds: int
    min_preview_output_tps: float | None
    min_preview_samples: int
    auto_skip_slow_preview: bool
    force: bool
    backend: LocalModelBackend | None = None
    selected_models: list[dict[str, Any]] = field(default_factory=list)
    prompt: str = ""
    followup_prompt: str | None = None


def load_opencode_config() -> dict[str, Any] | None:
    if not OPENCODE_CONFIG_PATH.exists():
        return None
    try:
        return json.loads(OPENCODE_CONFIG_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def load_opencode_config_from_path(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return load_opencode_config()
    return load_optional_json(path)


def load_opencode_ollama_api_base() -> str | None:
    payload = load_opencode_config()
    if not payload:
        return None
    base_url = (
        payload.get("provider", {})
        .get("ollama", {})
        .get("options", {})
        .get("baseURL")
    )
    if not isinstance(base_url, str) or not base_url:
        return None
    return base_url[:-3] if base_url.endswith("/v1") else base_url


def resolve_ollama_model_name(opencode_model_id: str, config_path: Path | None = None) -> str | None:
    payload = load_opencode_config_from_path(config_path)
    if not payload:
        return None
    normalized = opencode_model_id.split("/", 1)[1] if opencode_model_id.startswith("ollama/") else opencode_model_id
    model_entry = (
        payload.get("provider", {})
        .get("ollama", {})
        .get("models", {})
        .get(normalized, {})
    )
    model_name = model_entry.get("id")
    if isinstance(model_name, str) and model_name:
        return model_name
    return None


def resolve_ollama_context_limit(opencode_model_id: str, config_path: Path | None = None) -> int | None:
    payload = load_opencode_config_from_path(config_path)
    if not payload:
        return None
    normalized = opencode_model_id.split("/", 1)[1] if opencode_model_id.startswith("ollama/") else opencode_model_id
    model_entry = (
        payload.get("provider", {})
        .get("ollama", {})
        .get("models", {})
        .get(normalized, {})
    )
    context_limit = model_entry.get("limit", {}).get("context")
    if isinstance(context_limit, int) and context_limit > 0:
        return context_limit
    return None


def provider_model_key(model: dict[str, Any]) -> str:
    provider_prefix = f"{model['provider']}/"
    if model["id"].startswith(provider_prefix):
        return model["id"][len(provider_prefix):]
    return model["id"]


def fallback_ollama_config_entry(model: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    model_name = model.get("ollama_model_name")
    if not isinstance(model_name, str) or not model_name:
        return None
    model_key = provider_model_key(model)
    entry: dict[str, Any] = {
        "id": model_name,
        "name": model.get("ollama_display_name") or f"{model['label']} (Ollama)",
        "limit": {},
    }
    context_limit = model.get("ollama_limit_context")
    output_limit = model.get("ollama_limit_output")
    if isinstance(context_limit, int) and context_limit > 0:
        entry["limit"]["context"] = context_limit
    if isinstance(output_limit, int) and output_limit > 0:
        entry["limit"]["output"] = output_limit
    if model.get("ollama_tool_call") is True:
        entry["tool_call"] = True
    if model.get("ollama_reasoning") is True:
        entry["reasoning"] = True
    return model_key, entry


def apply_ollama_model_overrides(local_entry: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    model_name = model.get("ollama_model_name")
    if isinstance(model_name, str) and model_name:
        local_entry["id"] = model_name
    display_name = model.get("ollama_display_name")
    if isinstance(display_name, str) and display_name:
        local_entry["name"] = display_name
    if model.get("ollama_tool_call") is True:
        local_entry["tool_call"] = True
    if model.get("ollama_reasoning") is True:
        local_entry["reasoning"] = True
    return local_entry


def fallback_provider_config_entry(model: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    model_key = provider_model_key(model)
    entry: dict[str, Any] = {
        "id": model_key,
        "name": model.get("label") or model_key,
    }
    return model_key, entry


def load_ollama_warmup_payload(path: Path) -> dict[str, Any] | None:
    payload = load_optional_json(path)
    if not payload:
        return None
    results = payload.get("results")
    if not isinstance(results, list):
        return None
    results_by_slug: dict[str, dict[str, Any]] = {}
    for entry in results:
        if not isinstance(entry, dict):
            continue
        slug = entry.get("slug")
        if isinstance(slug, str) and slug:
            results_by_slug[slug] = entry
    payload["results_by_slug"] = results_by_slug
    return payload


def summarize_project(project_dir: Path) -> dict[str, Any]:
    checks = {
        "gemfile": project_dir / "Gemfile",
        "routes": project_dir / "config" / "routes.rb",
        "app_dir": project_dir / "app",
        "views_dir": project_dir / "app" / "views",
        "javascript_dir": project_dir / "app" / "javascript",
        "tests_dir": project_dir / "test",
        "readme_md": project_dir / "README.md",
        "readme_lower": project_dir / "readme.md",
        "dockerfile": project_dir / "Dockerfile",
        "docker_compose_yml": project_dir / "docker-compose.yml",
        "docker_compose_yaml": project_dir / "docker-compose.yaml",
        "compose_yml": project_dir / "compose.yml",
        "compose_yaml": project_dir / "compose.yaml",
    }
    present = {name: path.exists() for name, path in checks.items()}
    files = sum(1 for item in project_dir.rglob("*") if item.is_file())
    readme_present = present["readme_md"] or present["readme_lower"]
    compose_present = any(
        present[name]
        for name in ("docker_compose_yml", "docker_compose_yaml", "compose_yml", "compose_yaml")
    )
    rails_present = present["gemfile"] and present["routes"] and present["app_dir"]
    tests_present = present["tests_dir"]
    docker_present = present["dockerfile"] and compose_present

    if rails_present and readme_present and tests_present and docker_present:
        intended = "yes"
        note = "Rails app, tests, README, and container files detected."
    elif files == 0:
        intended = "no"
        note = "Project directory is empty."
    elif rails_present or readme_present or docker_present or tests_present:
        intended = "partial"
        note = "Some expected benchmark artifacts exist, but the scaffold looks incomplete."
    else:
        intended = "no"
        note = "Generated files do not resemble the requested Rails project."

    return {
        "file_count": files,
        "present": present,
        "works_as_intended": intended,
        "works_note": note,
    }


def existing_terminal_result(result_path: Path) -> dict[str, Any] | None:
    if not result_path.exists():
        return None
    payload = load_json(result_path)
    if payload.get("status") in TERMINAL_STATUSES:
        return payload
    return None


def mark_model_skip_by_default(config_path: Path, model_slug: str, note: str) -> bool:
    payload = load_optional_json(config_path)
    if not payload:
        return False
    models = payload.get("models")
    if not isinstance(models, list):
        return False
    changed = False
    for model in models:
        if not isinstance(model, dict):
            continue
        if model.get("slug") != model_slug:
            continue
        if model.get("skip_by_default") is not True:
            model["skip_by_default"] = True
            changed = True
        reason = model.get("selection_reason")
        note_suffix = f" {note}"
        if isinstance(reason, str) and note_suffix not in reason:
            model["selection_reason"] = reason + note_suffix
            changed = True
        break
    if not changed:
        return False
    save_json_preserve_order(config_path, payload)
    return True


def model_enables_followup(model: dict[str, Any]) -> bool:
    """Whether a model should run phase 2. Opt-in via enable_followup, defaults by provider."""
    explicit = model.get("enable_followup")
    if isinstance(explicit, bool):
        return explicit
    # Default: enabled for cloud providers, disabled for local and codex
    # (codex uses --ephemeral with no session continuity)
    return model["provider"] not in ("ollama", "codex")


def prepare_local_opencode_config(
    models: list[dict[str, Any]],
    warmup_payload: dict[str, Any] | None,
    local_api_base: str | None = None,
    local_backend_type: str | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    summary: dict[str, Any] = {
        "configured": [],
        "missing_warmup": [],
        "missing_source_entry": [],
        "skipped_reason": None,
        "source": str(OPENCODE_CONFIG_PATH),
    }
    source_config = load_opencode_config()
    if not source_config:
        summary["skipped_reason"] = f"missing opencode config at {OPENCODE_CONFIG_PATH}"
        return None, summary

    source_providers = source_config.get("provider", {})
    if not isinstance(source_providers, dict):
        summary["skipped_reason"] = "opencode config has no provider map"
        return None, summary

    using_llama_swap = local_backend_type == "llama-swap"
    warmup_results = warmup_payload.get("results_by_slug", {}) if warmup_payload else {}
    local_config: dict[str, Any] = {
        "$schema": source_config.get("$schema", "https://opencode.ai/config.json"),
        "provider": {},
    }

    selected_provider_names = sorted({model["provider"] for model in models if model["provider"] != "ollama"})
    for provider_name in selected_provider_names:
        provider_entry = source_providers.get(provider_name)
        if isinstance(provider_entry, dict):
            local_config["provider"][provider_name] = clone_json(provider_entry)
        else:
            local_config["provider"][provider_name] = {}
        provider_models = local_config["provider"][provider_name].get("models")
        if not isinstance(provider_models, dict):
            local_config["provider"][provider_name]["models"] = {}

    ollama_provider = source_providers.get("ollama")
    # When using llama-swap backend, also accept a "llama-swap" provider as the
    # source for local models (the home config may wire models there directly).
    if not isinstance(ollama_provider, dict) and using_llama_swap:
        ollama_provider = source_providers.get("llama-swap")
    if isinstance(ollama_provider, dict):
        local_ollama_provider = clone_json(ollama_provider)
        source_ollama_models = ollama_provider.get("models", {})
        local_ollama_models: dict[str, Any] = {}
    else:
        local_ollama_provider = None
        source_ollama_models = {}
        local_ollama_models = {}

    # Override the ollama provider baseURL when using llama-swap
    if using_llama_swap and local_api_base and local_ollama_provider is not None:
        api_url = local_api_base.rstrip("/")
        if not api_url.endswith("/v1"):
            api_url += "/v1"
        local_ollama_provider.setdefault("options", {})["baseURL"] = api_url
        summary["baseURL_override"] = api_url

    for model in models:
        if model.get("provider") != "ollama":
            continue
        warmup_entry = warmup_results.get(model["slug"])
        verified_context = warmup_entry.get("highest_verified_context") if isinstance(warmup_entry, dict) else None
        override_context = model.get("benchmark_context_override")

        model_key = provider_model_key(model)
        config_entry = source_ollama_models.get(model_key) if isinstance(source_ollama_models, dict) else None
        fallback = fallback_ollama_config_entry(model)
        if not isinstance(config_entry, dict) and fallback is not None:
            _, config_entry = fallback
        if not isinstance(config_entry, dict):
            summary["missing_source_entry"].append(model_key)
            continue

        local_entry = clone_json(config_entry)
        local_entry = apply_ollama_model_overrides(local_entry, model)

        # When using llama-swap, override the model ID, strip context limits
        # (context is managed server-side), and only keep reasoning/tool_call
        # flags if explicitly set in the benchmark model config.
        llama_swap_name = model.get("llama_swap_model")
        if using_llama_swap and llama_swap_name:
            local_entry["id"] = llama_swap_name
            if "limit" in local_entry:
                local_entry["limit"].pop("context", None)
                local_entry["limit"].pop("output", None)
                if not local_entry["limit"]:
                    del local_entry["limit"]
            # Reset capability flags — only keep them if the benchmark
            # model config explicitly declares them for llama-swap use.
            if "reasoning" not in model:
                local_entry.pop("reasoning", None)
            if "tool_call" not in model:
                local_entry.pop("tool_call", None)

        chosen_context = None
        if not using_llama_swap:
            # Context negotiation only matters for Ollama; llama-swap manages it server-side
            if isinstance(override_context, int) and override_context > 0:
                chosen_context = override_context
            elif isinstance(verified_context, int) and verified_context > 0:
                chosen_context = verified_context

        if chosen_context is not None:
            local_entry.setdefault("limit", {})["context"] = chosen_context
            source_label = "override" if isinstance(override_context, int) and override_context > 0 else "warmup"
            summary["configured"].append(f"{model['slug']}={chosen_context} ({source_label})")
        elif not using_llama_swap:
            summary["missing_warmup"].append(model["slug"])

        local_ollama_models[model_key] = local_entry

    if local_ollama_provider is not None:
        local_ollama_provider["models"] = local_ollama_models
        local_config["provider"]["ollama"] = local_ollama_provider

    for model in models:
        if model.get("provider") == "ollama":
            continue
        provider_name = model["provider"]
        provider_entry = local_config["provider"].setdefault(provider_name, {})
        provider_models = provider_entry.get("models")
        if not isinstance(provider_models, dict):
            provider_models = {}
            provider_entry["models"] = provider_models
        model_key, fallback_entry = fallback_provider_config_entry(model)
        provider_models.setdefault(model_key, fallback_entry)

    if not local_config["provider"]:
        summary["skipped_reason"] = "no provider config available for selected models"
        return None, summary

    return local_config, summary


def write_local_opencode_config(
    path: Path,
    models: list[dict[str, Any]],
    warmup_payload: dict[str, Any] | None,
    local_api_base: str | None = None,
    local_backend_type: str | None = None,
) -> dict[str, Any]:
    local_config, summary = prepare_local_opencode_config(
        models, warmup_payload, local_api_base=local_api_base, local_backend_type=local_backend_type,
    )
    if local_config is None:
        return summary
    save_json(path, local_config)
    summary["path"] = str(path)
    return summary


def print_local_opencode_config_summary(summary: dict[str, Any]) -> None:
    skipped_reason = summary.get("skipped_reason")
    if skipped_reason:
        print_line(f"Local opencode benchmark config skipped: {skipped_reason}")
        return
    path = summary.get("path")
    configured = summary.get("configured", [])
    missing_warmup = summary.get("missing_warmup", [])
    missing_source_entry = summary.get("missing_source_entry", [])
    source = summary.get("source")
    if path:
        print_line(f"Local opencode benchmark config: {path}")
    if source:
        print_line(f"Local opencode benchmark config source: {source}")
    base_override = summary.get("baseURL_override")
    if base_override:
        print_line(f"Ollama provider baseURL override: {base_override}")
    print_line("Local opencode benchmark permissions: yolo (auto-approve enabled)")
    if configured:
        print_line(f"Ollama benchmark contexts: {', '.join(configured)}")
    else:
        print_line("Ollama benchmark contexts: none")
    if missing_warmup:
        print_line(f"Ollama benchmark config missing warmup: {', '.join(missing_warmup)}")
    if missing_source_entry:
        print_line(f"Ollama benchmark config missing source entries: {', '.join(missing_source_entry)}")
