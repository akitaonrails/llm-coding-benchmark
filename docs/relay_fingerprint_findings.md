# Claude-relay fingerprinting — findings (2026-09-12)

**Question (user, prompted by a 2026-09-10 Bloomberg report that Anthropic alleges Moonshot secretly
routed user requests through Claude):** can our tests detect whether **Kimi** (Moonshot) or **DeepSeek**
covertly relay requests to Claude?

**Verdict: No detectable evidence of live Claude routing on either Kimi or DeepSeek.** The one alarming
signal, when investigated, dissolved into OpenRouter's multi-provider load-balancing + likely training-data
distillation — not a live relay. This is **suggestive, not conclusive** (see Limitations).

## Method
The rigorous discriminator (top-k logprob KL-divergence, native-vs-OpenRouter vs a known-Claude reference)
was **impossible**: no route exposes token logprobs for these models, and **Anthropic never exposes logprobs
on any route**, so there is no Claude logprob distribution to compare against. Fallback: a **behavioral
tripwire battery** at temperature 0 — identity-leaking prompts (who made you / your name / knowledge cutoff /
"repeat your system prompt" refusal phrasing) run across every available route, looking for **route-dependent
Claude-identity leakage**. Live routing is route-consistent; distillation affects all routes equally.

## Routes available (and blocked)
| Route | Status |
|-------|--------|
| Kimi native — Moonshot direct API (`api.moonshot.ai`) | **suspended** (account org suspended) — blocked |
| Kimi native — `kimi` CLI | works (separate auth) → self-IDs **"Moonshot AI"**, non-Claude reasoning style |
| Kimi — OpenRouter (`moonshotai/kimi-k2.7-code`, `kimi-k3`) | works; **load-balanced across ~15 providers** |
| DeepSeek native (`api.deepseek.com`) | **no key** (401) — blocked |
| DeepSeek — OpenRouter (`deepseek/deepseek-v4-pro`) | works |
| Claude reference — Anthropic native (`claude-opus-4-6`) | works (used as signature reference) |

Claude reference signatures (temp 0): company=**Anthropic**, name=**Claude**, cutoff=**April 2024**,
refusal=*"I don't have access to my system prompt to repeat it verbatim…"*

## What happened
1. **First pass turned up an alarming hit:** `moonshotai/kimi-k2.7-code` via OpenRouter answered company →
   **"Anthropic"** and refused with *"I don't have access to my system prompt, so I can't repeat it
   verbatim"* — almost verbatim Claude. That looked like a relay.
2. **It did not reproduce.** OpenRouter load-balances that model across **~15 upstream providers** (DeepInfra,
   CoreWeave, Fireworks, Alibaba, SiliconFlow, Cloudflare, Moonshot AI, …), and each request hit a different
   one. Re-runs all returned **"Moonshot AI" / "Kimi"**.
3. **Per-provider pinned sweep (the decisive test):** pinning each of the 14 providers individually and asking
   identity → **every single one answered "Moonshot AI". Zero said Anthropic/Claude.** A live relay would be
   100% consistent for the relaying provider; it was 0/14 on pinned re-runs.
4. **Cross-route for Kimi:** native CLI (`kimi-k2.7-code`, same weights) → "Moonshot AI"; newer `kimi-k3` on
   OpenRouter → "Moonshot AI". Only the one non-reproducible k2.7-code response ever said otherwise.
5. **DeepSeek:** `deepseek-v4-pro` via OpenRouter → "DeepSeek", cutoff Oct 2023, and it leaked a plain *"You
   are a helpful assistant."* system prompt — **no Claude signal**.

## Interpretation
- The single "Anthropic" + Claude-style refusal is best explained by **distillation** (Kimi k2.7-code trained
  partly on Claude outputs, so a Claude-ism surfaces occasionally when no identity system prompt overrides
  it) plus **provider variance** (different quantizations/templates across OpenRouter's 15 hosts). It is
  **not** live routing: routing would be consistent per-route/provider, and it was not.
- Corroborating, independent evidence from the v4 benchmark itself: **Kimi's disguise-detection fingerprint
  (which sabotages it catches vs misses) matches no Claude model's** — a distinctly non-Claude behavioral
  shape. If Kimi were Claude under the hood, its v4 vigilance profile would track a Claude sibling; it does
  not (Kimi K2.7 = 87.25, K3 = 85.0; neither aligns with any Claude row).

## Limitations (why this is suggestive, not proof)
- **No logprobs** on any route, and **Claude exposes none anywhere** — the strongest cross-route discriminator
  is unavailable in principle.
- **Kimi native direct API suspended** and **no DeepSeek native key**, so the clean native-vs-OpenRouter
  weight comparison (the distillation control) could only be done partially (via the CLI, which forces its
  own system prompt).
- Behavioral tripwires can be masked; absence of a leak is not proof of absence of routing. But the specific
  positive signal that appeared was falsified on investigation, and everything else points away from routing.

**Bottom line:** on the evidence obtainable here, neither Kimi nor DeepSeek shows a detectable live Claude
relay; the scary-looking hit was a reproducibility artifact of OpenRouter's provider fan-out, not a route to
Claude.
