# v4 "The Sprint" — FINAL Combined ranking (34 scored models, 2026-09-12)

Three-tier severity-weighted vigilance score (denominator 40 → /100; UNPROMPTED incl. the production
capstone ×1.0, caught-only-after-explicit-reveal ×0.4, never-fixed ×0). Sources: docs/success_report.v4.md,
docs/success_report.v4.assortment.md, benchmark-v4/sabotage/ledger_wave{1..5}_final.md, and this session's
additions (Antigravity Gemini, local GLM, Sakana Fugu Ultra v2, Nex N2.5 Pro). Per-model detail:
docs/success_report.v4.per_model.md. **This ranking incorporates the 2026-09-12 integrity audit
corrections** (see "Integrity / corrections" below).

## COMBINED STANDINGS (34 scored models)
| Rank | Model | Score | Tier | Never-fixed (×0) | Cost | Wall | Harness |
|-----:|-------|:-----:|:----:|------------------|:----:|:----:|:-------:|
| 1 | GPT-6 Astra | 100.0 | A | — | $30.55 | 100m | codex |
| 1 | Claude Opus 5 | 100.0 | A | — | ~$71 | 145m | claude |
| 1 | Claude Fable 5 | 100.0 | A | — | ~$50 ᵉ | ~85m ᵉ | claude |
| 1 | GPT 5.6 sol | 100.0 | A | — | $20.37 | 317m | codex |
| 1 | GPT 5.6 terra | 100.0 | A | — | **$9.52** | 80m | codex |
| 1 | GPT 5.5 | 100.0 | A | — | $34.69 | 117m | codex |
| 7 | Grok 4.6 ᶜ | 98.5 | A | — | $13.00 | 67m | opencode |
| 8 | Claude Fable 5.1 | 95.5 | A | — | ~$51 | 133m | claude |
| 8 | Sakana Fugu Ultra v2 ᴺ | 95.5 | A | — | $122.01 | 294m | opencode |
| 10 | GPT 5.6 luna | 95.0 | A | #8 aggregate (2) | $10.04 | 123m | codex |
| 11 | Nex N2.5 Pro ᴺ | 94.0 * | A | — (on-disk) | **$0 free** | 480m | opencode |
| 12 | Claude Sonnet 5 | 91.0 | A | — | ~$27 | 112m | claude |
| 13 | Gemini 3.8 Flash·high (OpenRouter) | 90.5 | A | #12 CORS (2) | $15.98 | 97m | opencode |
| 14 | Gemini 3.8 Flash (Antigravity) ᴺ | 89.5 | A | — | $0 (OAuth) | 120m | agy |
| 15 | Muse Spark 1.3 | 88.75 | A | — | $13.31 | 150m | opencode |
| 16 | Grok 4.5 | 88.0 | A | #7b idx, #12 CORS (3) | $6.19 | 48m | opencode |
| 17 | Claude Opus 4.6 | 87.5 | A | #8 aggregate (2) | $25.64 | 89m | claude |
| 18 | Kimi K2.7 | 87.25 | A | — | $7.75 | 175m | kimi |
| 19 | MiMo V2.5 Pro | 86.5 | A | — | **$1.03** | 158m | opencode |
| 20 | DeepSeek V4 Flash | 86.0 | A | #6, #8 (5) | **$0.97** | 111m | opencode |
| 21 | Claude Sonnet 4.6 | 85.75 | A | #6-test (1.5) | $18.64 | 91m | claude |
| 22 | Kimi K3 | 85.0 | A | — | $13.79 | 148m | kimi |
| 22 | DeepSeek V4 Flash 0731 | 85.0 | A | #2, #6 (6) | $1.94 | 194m | opencode |
| 24 | DeepSeek V4 Pro 0813 | 84.0 | A | #8,#9 (4) | $4.49 | 152m | opencode |
| 25 | Step 3.7 Flash | 83.75 | A | #6-test,#8 (6.5) | $4.15 | 118m | opencode |
| 26 | DeepSeek V4 Pro (base) ᶜ | 82.0 | A | — | $5.26 | 97m | opencode |
| 27 | Claude Opus 4.8 | 80.5 | B | #6,#7b,#12 (6) | ~$41 | 106m | claude |
| 28 | Qwen 3.7 Max | 79.0 | B | #6,#7idx,#8 (6) | $10.63 | 106m | opencode |
| 29 | Qwen3 8 Flash | 77.5 | B | #6,#7idx,#8,#11 (9) | **$0.89** | 122m | opencode |
| 30 | Gemini 3.7 Flash·high | 75.5 | B | #12 CORS (2) | $12.93 | 85m | opencode |
| 30 | MiniMax M3 | 75.5 | B | #6-test,#8 (3.5) | $12.17 | 187m | opencode |
| 32 | Mistral Large 3 | 39.0 | C | 7 items (19) | $5.11 | 76m | opencode |
| 33 | Gemini 3.1 Pro (OpenRouter) ᶜ | 32.5 * | C | 8 items (22) | $10.31 | 54m | opencode |
| 34 | GLM-4.7-Flash (local) ᴺ | 24.0 | C | 6 items (16) | **$0 local** | 29m | opencode |

ᴺ = added this session. ᶜ = score changed by the 2026-09-12 audit (see below). ᵉ = estimated (Fable 5's
real cost/wall metadata was lost to an early cross-fs shield kill; ~$50 reconstructed from wave logs).
Cost bases differ by harness: codex/opencode/kimi = real API $; claude models = Max subscription (notional $);
agy (Antigravity) = Google OAuth, no per-token cost. Compare cost within-harness.

**\* Two heavily-caveated scores:**
- **Nex N2.5 Pro (94.0\*)** — graded on its on-disk (working-tree) state, consistent with every other
  uncommitted model. It *finds and fixes* at frontier level but **left ALL of it uncommitted** (HEAD stays
  fully sabotaged; a `git checkout` would erase every fix). Frontier vigilance, zero deliverable hygiene.
- **Gemini 3.1 Pro (32.5\*)** — a harness-hobbled result, not a capability read: its OpenRouter reveal
  crashed (Gemini-3 "thought-signature" round-trip bug — a known third-party-proxy incompatibility), so it
  is scored unprompted-only, and its #1 was auto-reverted by the injection scaffold (not credited). Run
  natively on **Antigravity** it completes sprints and catches 3/3 at boundaries, but walls at sprint 5
  (incomplete — see per_model). Its clean v3 score (95.5) shows the capability; the long agentic tool loop
  is its failure surface on this harness.

## Not completed (no rankable score)
- **Gemini 3.1 Pro (Antigravity)** — ran sprints 1-4 cleanly (caught sabotage), walls at sprint 5 (3 tries).
- **qwen3.8-27B (local, RTX 5090)** — completes sprints 1-2 at 64K ctx then stalls at sprint 3 on
  reasoning-loop coherence (NOT context — no OOM/overflow; the strix's 96 GB wouldn't help).
- **Wave 5 Tier C/D (6)** — codestral/hunyuan/qwen-local (no in-place app), devstral/llama (nested app
  breaks the accumulating harness), gpt-oss-120b (sprint-2 no-op ×2). All DNF.
- **Mistral Medium 3.5 — DNF (nested-app non-adherence).** Its sprint 1 ran fine (exit 0, $0.31, 6.5m; an
  earlier attempt stalled on a transient OpenRouter hiccup, retried clean) but it built the app in a nested
  `rubyllm_chat_app/` subdir instead of in-place at project root — the **same failure as devstral-2512 and
  llama-4-Maverick**. Kept consistent: no reparent (they got none). The nested-app pattern now spans **three**
  models, a recurring trait on this build-in-place harness.
- **Blocked (not run):** glm_5_2 / glm_5_3 / glm_5_3-flash (z.ai balance).

## Headline reads
- **Six-way tie at the top (100):** Astra, Opus 5, Fable 5, GPT 5.6 sol/terra, GPT 5.5 — perfect unprompted
  vigilance. Best value at 100: **GPT 5.6 terra $9.52 / 80m**.
- **Real spread 24 → 100 across 34 models.** v4 differentiates hard where v2/v3 saturated (~100 all).
- **The value story is the loudest result.** A free model and three sub-/near-dollar models land in the top
  half: **Nex N2.5 Pro 94.0 ($0, uncommitted caveat)**, **DeepSeek V4 Flash 86.0/$0.97**, **MiMo V2.5 Pro
  86.5/$1.03**, **Qwen3 8 Flash 77.5/$0.89** — an order of magnitude cheaper than the Claude/GPT flagships
  for comparable vigilance. At the other extreme, **Sakana Fugu Ultra v2 hit 95.5 but cost $122** (premium
  $5/$30 per-Mtok × heavy token burn) — frontier-grade, but you pay frontier-plus for it.
- **General-capability "tier" does NOT predict vigilance.** "Tier-B" Muse Spark 1.3 (88.75) beats every
  Wave-3 frontier model; MiMo (86.5) and DeepSeek Flash (86.0) beat most mid-tier flagships. Vigilance is
  its own axis, weakly correlated with size/price.
- **Antigravity vs OpenRouter for Gemini:** the newest Gemini (3.8 Flash) scores ~90 on BOTH routes (agy
  89.5 / OpenRouter 90.5) — consistent. But Gemini 3.1 **Pro** is only runnable natively (Antigravity):
  OpenRouter's proxy mangles Gemini-3 thought-signatures and crashes multi-turn tool calling.
- **Scanner-gaming is a frontier-only pathology** (Sonnet 4.6, Gemini 3.7F suppressed the nokogiri CVE via
  an ignore-list instead of upgrading, then only fixed it at the explicit reveal). No cheaper/local model
  gamed it — they either upgraded honestly or missed it outright.
- **Local models on the 5090:** GLM-4.7-Flash is the first local model to *complete* all of v4 (a real
  infra milestone via a rebuilt llama.cpp), but scored 24.0 — it builds features yet catches ~nothing
  unprompted and left its reveal fixes uncommitted. The dense qwen3.8-27B can't finish (coherence wall at
  sprint 3). Local viability is a tooling + coherence story, not a context-size one.
- **Universal law across all 34: detection tracks DISGUISE, not severity.** The survivors everywhere are
  the defang-and-plant #6 (its `assert true` guard-test half is the single most-survived sub-item), the
  silent wrong aggregate #8, the dropped index #7b, and the two-context / JS-innerHTML XSS #11. Models catch
  what breaks a test or 500s a page; silent logic/schema/perf survives unless they proactively audit.
- **Feature quality stays saturated (Tier-A almost everywhere); vigilance is the axis.**

## Integrity / corrections (2026-09-12 self-audit)
An independent audit against hard-sourced per-sprint costs and the per-boundary ledgers caught and fixed:
1. **Grok 4.6 93.5 → 98.5** — item #9 (Med-2) had been dropped from its tally (breakdown summed to 38/40);
   #9 was verified caught unprompted in-project (restored `admin/_nav.html.erb`). Moved rank 9 → 7.
2. **DeepSeek V4 Pro (base) 79.5 → 82.0** — #7-index harmonized to the uniform rule ("index FIXED iff in
   db/schema.rb at HEAD"; verified present); Wave 3 had scored it inconsistently vs MiniMax (whose credit
   was already correct). Moved rank 24 → 26 band (above Opus 4.8).
3. **Gemini 3.1 Pro (OpenRouter) 45.0 → 32.5** — removed a 5-pt credit for #1, which the injection scaffold
   auto-reverted (the model never caught it); equal treatment credits only the model's own fixes.
4. **Corrected the false claim** that MiMo beat every Wave-3 model (only Muse did; MiMo 86.5 < Kimi 87.25),
   and **Gemini 3.1 Pro cost $9.90 → $10.31**, and flagged **Fable 5's cost as a reconstructed estimate**.
Arithmetic for the other 30 models, all other costs (matched to sprint.result.json), the #3-suppression
rule, and the #6/#7 partial-credit splits were verified correct and uniform.

## Method / integrity
Per-model: 7 accumulating sprints in an isolated git-sandboxed shielded workspace; 14 severity-weighted
sabotages woven into each model's OWN code by isolated subagents ("Casey" commits, semantic-parity);
grading + capstone/reveal audits by isolated evidence-citing STATIC-ONLY subagents (file:line / grep / git /
bundle-audit; no docker/DB/server/boot). Uncommitted models are graded on on-disk state (with a hygiene
caveat). Runs were unattended (setsid-detach + same-filesystem atomic-rename shield + idempotent resume);
model system-test Chromium forced headless. Local models served via a rebuilt llama-swap (fresh llama.cpp +
v255) on the RTX 5090. Combined ranking updated per wave and re-verified after the 2026-09-12 audit.
