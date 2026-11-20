"""Normalized 5-bucket token, cache, and cost extraction for Benchmark v5."""
from __future__ import annotations

import json
from typing import Any

from benchmark.runner import (
    collect_kimi_session_tokens,
    extract_codex_metrics,
    extract_kimi_metrics,
    extract_metrics as extract_opencode_metrics,
)


def empty_tokens() -> dict[str, Any]:
    return {
        "input_uncached": 0,
        "cache_read": 0,
        "cache_write": 0,
        "cache_write_5m": 0,
        "cache_write_1h": 0,
        "output": 0,
        "reasoning": 0,
        "billable_output": 0,
        "total_prompt": 0,
        "total": 0,
        "cache_hit_ratio": 0.0,
    }


def finalize_tokens(t: dict[str, Any], output_includes_reasoning: bool = True) -> dict[str, Any]:
    """Compute derived totals consistently across all harnesses."""
    in_uncached = int(t.get("input_uncached") or 0)
    cr = int(t.get("cache_read") or 0)
    cw5 = int(t.get("cache_write_5m") or 0)
    cw1 = int(t.get("cache_write_1h") or 0)
    cw = int(t.get("cache_write") or 0)
    if cw == 0 and (cw5 or cw1):
        cw = cw5 + cw1
    out = int(t.get("output") or 0)
    reas = int(t.get("reasoning") or 0)
    billable_out = out if output_includes_reasoning else (out + reas)
    total_prompt = in_uncached + cr + cw
    total = total_prompt + billable_out
    cache_hit_ratio = round(cr / total_prompt, 4) if total_prompt > 0 else 0.0
    return {
        "input_uncached": in_uncached,
        "cache_read": cr,
        "cache_write": cw,
        "cache_write_5m": cw5,
        "cache_write_1h": cw1,
        "output": out,
        "reasoning": reas,
        "billable_output": billable_out,
        "total_prompt": total_prompt,
        "total": total,
        "cache_hit_ratio": cache_hit_ratio,
    }


def extract_v5_usage(
    harness: str,
    events: list[dict[str, Any]],
    stdout_text: str,
    model_slug: str,
) -> tuple[dict[str, Any], float | None, str | None, int]:
    """Return (normalized_tokens, native_cost_usd, session_id, turns)."""
    native_cost: float | None = None
    session_id: str | None = None
    turns = 0

    if harness == "claude":
        for ev in events:
            if ev.get("type") == "result":
                native_cost = ev.get("total_cost_usd")
                session_id = ev.get("session_id")
                turns = int(ev.get("num_turns") or 0)
                usage = ev.get("usage") or {}
                cc = usage.get("cache_creation") or {}
                cw5 = int(cc.get("ephemeral_5m_input_tokens") or 0)
                cw1 = int(cc.get("ephemeral_1h_input_tokens") or 0)
                cw_total = int(usage.get("cache_creation_input_tokens") or 0)
                if cw_total and not (cw5 or cw1):
                    cw5 = cw_total
                out_details = usage.get("output_tokens_details") or {}
                tokens = finalize_tokens(
                    {
                        "input_uncached": usage.get("input_tokens", 0),
                        "cache_read": usage.get("cache_read_input_tokens", 0),
                        "cache_write": cw_total,
                        "cache_write_5m": cw5,
                        "cache_write_1h": cw1,
                        "output": usage.get("output_tokens", 0),
                        "reasoning": out_details.get("thinking_tokens", 0),
                    },
                    output_includes_reasoning=True,
                )
                return tokens, native_cost, session_id, turns
        # Fallback if grok exited with error (e.g. background-wait timeout) before `end`:
        # sum every per-step `{"type":"usage","usage":{...}}` event.
        in_u = cr = cw = out = reas = step_turns = 0
        for ev in events:
            if ev.get("type") == "usage" and isinstance(ev.get("usage"), dict):
                u = ev["usage"]
                step_turns += 1
                in_u += int(u.get("input_tokens") or u.get("prompt_tokens") or 0)
                cr += int(u.get("cache_read_input_tokens") or u.get("cached_tokens") or 0)
                cw += int(u.get("cache_creation_input_tokens") or 0)
                out += int(u.get("output_tokens") or u.get("completion_tokens") or 0)
                reas += int(u.get("reasoning_tokens") or 0)
        if step_turns:
            return finalize_tokens(
                {
                    "input_uncached": in_u,
                    "cache_read": cr,
                    "cache_write": cw,
                    "output": out,
                    "reasoning": reas,
                },
                output_includes_reasoning=True,
            ), None, session_id, step_turns
        return empty_tokens(), None, None, 0

    if harness == "codex":
        metrics = extract_codex_metrics(events)
        raw = metrics.get("tokens") or {}
        session_id = metrics.get("session_id")
        turns = sum(1 for ev in events if ev.get("type") == "turn.completed")
        # Codex turn.completed output_tokens includes reasoning_output_tokens in Responses API;
        # keep reasoning separately for diagnostics without double-billing.
        tokens = finalize_tokens(
            {
                "input_uncached": raw.get("input", 0),
                "cache_read": (raw.get("cache") or {}).get("read", 0),
                "cache_write": (raw.get("cache") or {}).get("write", 0),
                "output": raw.get("output", 0),
                "reasoning": raw.get("reasoning", 0),
            },
            output_includes_reasoning=True,
        )
        return tokens, None, session_id, turns

    if harness == "agy":
        # agy 1.5.13 --output-format stream-json emits per-step `step_update` usage
        # and a final `result` event with cumulative usage.
        # Verified on real cached step 104: input_tokens (6436) + output_tokens (4458)
        # == total_tokens (10894), with cache_read_tokens (227976) reported SEPARATELY
        # (so input_tokens is ALWAYS exclusive of cache_read_tokens, and output_tokens
        # already includes thinking_tokens).
        for ev in reversed(events):
            if ev.get("event") == "result":
                res = ev.get("result") or {}
                session_id = res.get("conversation_id")
                turns = int(res.get("num_turns") or 0)
                u = res.get("usage") or {}
                tokens = finalize_tokens(
                    {
                        "input_uncached": int(u.get("input_tokens") or 0),
                        "cache_read": int(u.get("cache_read_tokens") or 0),
                        "cache_write": 0,
                        "output": int(u.get("output_tokens") or 0),
                        "reasoning": int(u.get("thinking_tokens") or 0),
                    },
                    output_includes_reasoning=True,
                )
                return tokens, None, session_id, turns
        # Fallback if interrupted before terminal result: sum DONE step_update usages
        in_u = cr = out = think = step_turns = 0
        for ev in events:
            if ev.get("event") == "step_update":
                su = ev.get("step_update") or {}
                if not session_id:
                    session_id = su.get("conversation_id")
                u = su.get("usage")
                if su.get("state") == "DONE" and isinstance(u, dict):
                    step_turns += 1
                    in_u += int(u.get("input_tokens") or 0)
                    cr += int(u.get("cache_read_tokens") or 0)
                    out += int(u.get("output_tokens") or 0)
                    think += int(u.get("thinking_tokens") or 0)
        if step_turns:
            return finalize_tokens(
                {
                    "input_uncached": in_u,
                    "cache_read": cr,
                    "cache_write": 0,
                    "output": out,
                    "reasoning": think,
                },
                output_includes_reasoning=True,
            ), None, session_id, step_turns
        return empty_tokens(), None, session_id, 0

    if harness == "muse":
        # muse exec --json emits status event with payload_type == "run.usage"
        for ev in reversed(events):
            if ev.get("payload_type") == "run.usage":
                p = ev.get("payload") or {}
                session_id = (ev.get("stream") or {}).get("id")
                turns = int(p.get("completed_calls") or 0)
                in_raw = cr = out = reas = 0
                for m in p.get("models") or []:
                    in_raw += int(m.get("input_tokens") or 0)
                    cr += int(m.get("cached_tokens") or 0)
                    out += int(m.get("output_tokens") or 0)
                    reas += int(m.get("reasoning_tokens") or 0)
                in_uncached = max(0, in_raw - cr) if cr <= in_raw else in_raw
                tokens = finalize_tokens(
                    {
                        "input_uncached": in_uncached,
                        "cache_read": cr,
                        "cache_write": 0,
                        "output": out,
                        "reasoning": reas,
                    },
                    output_includes_reasoning=True,
                )
                return tokens, None, session_id, turns
        return empty_tokens(), None, None, 0

    if harness == "grok":
        for ev in reversed(events):
            if ev.get("type") in ("end", "result") and isinstance(ev.get("usage"), dict):
                u = ev["usage"]
                native_cost = ev.get("total_cost_usd")
                session_id = ev.get("session_id")
                turns = int(ev.get("num_turns") or ev.get("turns") or 0)
                in_raw = int(u.get("input_tokens") or u.get("prompt_tokens") or 0)
                cr = int(u.get("cache_read_input_tokens") or u.get("cached_tokens") or 0)
                cw = int(u.get("cache_creation_input_tokens") or 0)
                out = int(u.get("output_tokens") or u.get("completion_tokens") or 0)
                reas = int(u.get("reasoning_tokens") or 0)
                total = int(u.get("total_tokens") or 0)
                # Verified on grok 1.0.89: input_tokens + cache_read + output == total_tokens
                # (input_tokens is already EXCLUSIVE of cache_read_input_tokens).
                if total and (in_raw + out == total) and cr <= in_raw:
                    in_uncached = max(0, in_raw - cr)
                else:
                    in_uncached = in_raw
                tokens = finalize_tokens(
                    {
                        "input_uncached": in_uncached,
                        "cache_read": cr,
                        "cache_write": cw,
                        "output": out,
                        "reasoning": reas,
                    },
                    output_includes_reasoning=True,
                )
                return tokens, native_cost, session_id, turns
        # Fallback if grok exited with error (e.g. background-wait timeout) before `end`:
        # sum every per-step `{"type":"usage","usage":{...}}` event.
        in_u = cr = cw = out = reas = step_turns = 0
        for ev in events:
            if ev.get("type") == "usage" and isinstance(ev.get("usage"), dict):
                u = ev["usage"]
                step_turns += 1
                in_u += int(u.get("input_tokens") or u.get("prompt_tokens") or 0)
                cr += int(u.get("cache_read_input_tokens") or u.get("cached_tokens") or 0)
                cw += int(u.get("cache_creation_input_tokens") or 0)
                out += int(u.get("output_tokens") or u.get("completion_tokens") or 0)
                reas += int(u.get("reasoning_tokens") or 0)
        if step_turns:
            return finalize_tokens(
                {
                    "input_uncached": in_u,
                    "cache_read": cr,
                    "cache_write": cw,
                    "output": out,
                    "reasoning": reas,
                },
                output_includes_reasoning=True,
            ), None, session_id, step_turns
        return empty_tokens(), None, None, 0

    if harness == "zcode":
        try:
            d = json.loads(stdout_text)
            u = d.get("usage") or {}
            session_id = d.get("sessionId")
            in_raw = int(u.get("inputTokens") or 0)
            cr = int(u.get("cacheReadTokens") or 0)
            out = int(u.get("outputTokens") or 0)
            total = int(u.get("totalTokens") or 0)
            if total and (in_raw + out == total) and cr <= in_raw:
                in_uncached = max(0, in_raw - cr)
            else:
                in_uncached = in_raw
            tokens = finalize_tokens(
                {
                    "input_uncached": in_uncached,
                    "cache_read": cr,
                    "cache_write": 0,
                    "output": out,
                    "reasoning": 0,
                },
                output_includes_reasoning=True,
            )
            return tokens, None, session_id, 0
        except Exception:
            return empty_tokens(), None, None, 0

    if harness == "kimi":
        metrics = extract_kimi_metrics(events)
        session_id = metrics.get("session_id")
        raw = collect_kimi_session_tokens(session_id, model_slug) or {}
        tokens = finalize_tokens(
            {
                "input_uncached": raw.get("input", 0),
                "cache_read": (raw.get("cache") or {}).get("read", 0),
                "cache_write": (raw.get("cache") or {}).get("write", 0),
                "output": raw.get("output", 0),
                "reasoning": raw.get("reasoning", 0),
            },
            output_includes_reasoning=True,
        )
        return tokens, None, session_id, 0

    if harness == "qwen":
        for ev in reversed(events):
            if ev.get("type") == "result" and isinstance(ev.get("usage"), dict):
                u = ev["usage"]
                session_id = ev.get("session_id")
                turns = int(ev.get("num_turns") or 0)
                in_raw = int(u.get("input_tokens") or 0)
                cr = int(u.get("cache_read_input_tokens") or u.get("cached_tokens") or 0)
                cw = int(u.get("cache_creation_input_tokens") or 0)
                out = int(u.get("output_tokens") or 0)
                reas = int(u.get("reasoning_tokens") or 0)
                in_uncached = max(0, in_raw - cr) if cr <= in_raw else in_raw
                tokens = finalize_tokens(
                    {
                        "input_uncached": in_uncached,
                        "cache_read": cr,
                        "cache_write": cw,
                        "output": out,
                        "reasoning": reas,
                    },
                    output_includes_reasoning=True,
                )
                return tokens, ev.get("total_cost_usd"), session_id, turns
        return empty_tokens(), None, None, 0

    if harness == "opencode":
        metrics = extract_opencode_metrics(events)
        raw = metrics.get("tokens") or {}
        session_id = metrics.get("session_id")
        native_cost = round(metrics["cost"], 6) if metrics.get("cost") is not None else None
        turns = sum(1 for ev in events if ev.get("type") == "step_finish")
        # opencode reports output and reasoning as separate buckets
        tokens = finalize_tokens(
            {
                "input_uncached": raw.get("input", 0),
                "cache_read": (raw.get("cache") or {}).get("read", 0),
                "cache_write": (raw.get("cache") or {}).get("write", 0),
                "output": raw.get("output", 0),
                "reasoning": raw.get("reasoning", 0),
            },
            output_includes_reasoning=False,
        )
        return tokens, native_cost, session_id, turns

    return empty_tokens(), None, None, 0


def compute_cost_breakdown(
    tokens: dict[str, Any],
    rates: dict[str, Any],
) -> dict[str, Any]:
    """Compute actual API-equivalent cost, no-cache counterfactual, and cache savings."""
    r_in = float(rates.get("input") or 0.0)
    r_out = float(rates.get("output") or 0.0)
    r_cr = float(rates.get("cache_read") if rates.get("cache_read") is not None else r_in)
    r_cw5 = float(rates.get("cache_write_5m") if rates.get("cache_write_5m") is not None else (rates.get("cache_write") or r_in))
    r_cw1 = float(rates.get("cache_write_1h") if rates.get("cache_write_1h") is not None else r_cw5)

    in_u = int(tokens.get("input_uncached") or 0)
    cr = int(tokens.get("cache_read") or 0)
    cw5 = int(tokens.get("cache_write_5m") or 0)
    cw1 = int(tokens.get("cache_write_1h") or 0)
    cw = int(tokens.get("cache_write") or 0)
    if cw > (cw5 + cw1):
        cw5 += cw - (cw5 + cw1)
    out = int(tokens.get("billable_output") or tokens.get("output") or 0)

    cost_input = in_u / 1e6 * r_in
    cost_cache_read = cr / 1e6 * r_cr
    cost_cache_write = (cw5 / 1e6 * r_cw5) + (cw1 / 1e6 * r_cw1)
    cost_output = out / 1e6 * r_out
    actual_cost = cost_input + cost_cache_read + cost_cache_write + cost_output

    total_prompt = in_u + cr + cw5 + cw1
    no_cache_cost = (total_prompt / 1e6 * r_in) + cost_output
    cache_savings = no_cache_cost - actual_cost
    cache_savings_pct = (cache_savings / no_cache_cost * 100.0) if no_cache_cost > 0 else 0.0

    return {
        "actual_cost_usd": round(actual_cost, 6),
        "no_cache_cost_usd": round(no_cache_cost, 6),
        "cache_savings_usd": round(cache_savings, 6),
        "cache_savings_pct": round(cache_savings_pct, 2),
        "components_usd": {
            "input_uncached": round(cost_input, 6),
            "cache_read": round(cost_cache_read, 6),
            "cache_write": round(cost_cache_write, 6),
            "output": round(cost_output, 6),
        },
    }


def sum_token_dicts(items: list[dict[str, Any]]) -> dict[str, Any]:
    acc = {
        "input_uncached": sum(int(x.get("input_uncached") or 0) for x in items),
        "cache_read": sum(int(x.get("cache_read") or 0) for x in items),
        "cache_write": sum(int(x.get("cache_write") or 0) for x in items),
        "cache_write_5m": sum(int(x.get("cache_write_5m") or 0) for x in items),
        "cache_write_1h": sum(int(x.get("cache_write_1h") or 0) for x in items),
        "output": sum(int(x.get("output") or 0) for x in items),
        "reasoning": sum(int(x.get("reasoning") or 0) for x in items),
        "billable_output": sum(int(x.get("billable_output") or 0) for x in items),
    }
    total_prompt = acc["input_uncached"] + acc["cache_read"] + acc["cache_write"]
    acc["total_prompt"] = total_prompt
    acc["total"] = total_prompt + acc["billable_output"]
    acc["cache_hit_ratio"] = round(acc["cache_read"] / total_prompt, 4) if total_prompt > 0 else 0.0
    return acc
