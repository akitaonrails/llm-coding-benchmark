# Cost Analysis: Pricing Audit & the Productivity Floor

**Verified: 2026-07-09.** Per-M rates checked against the OpenRouter live API (`/api/v1/models`) on that date, and vendor pages for non-OpenRouter providers. Per-run costs are recomputed from each run's recorded token logs (`opencode-output.ndjson` + follow-up logs) at these verified rates — not from memory or marketing pages. Where a run's logs are no longer on disk, the original estimate is retained and marked "(hist.)".

This document answers three questions:
1. What does each model actually cost, today?
2. Which models are worth the money (quality × time × cost)?
3. Where is the floor below which "cheap" becomes a false economy for programming work?

---

## 1. Verified pricing (2026-07-09)

### OpenRouter pay-per-token (what the benchmark actually pays)

| Model | ID | In $/M | Out $/M | Notes |
|---|---|---:|---:|---|
| Claude Opus 4.7 / 4.8 | `anthropic/claude-opus-4.*` | 5.00 | 25.00 | |
| Claude Fable 5 (both runs) | `anthropic/claude-fable-5` | 10.00 | 50.00 | |
| Claude Sonnet 5 | `anthropic/claude-sonnet-5` | 2.00 | 10.00 | |
| Claude Sonnet 4.6 | `anthropic/claude-sonnet-4.6` | 3.00 | 15.00 | |
| Claude Opus 4.6 | `anthropic/claude-opus-4.6` | 5.00 | 25.00 | |
| Gemini 3.5 Flash | `google/gemini-3.5-flash` | 1.50 | 9.00 | |
| Gemini 3.1 Pro | `google/gemini-3.1-pro-preview` | 2.00 | 12.00 | |
| Kimi K2.5 | `moonshotai/kimi-k2.5` | 0.38 | 2.02 | |
| Kimi K2.6 | `moonshotai/kimi-k2.6` | 0.65 | 3.41 | **↑ ~30% since its 2026-05 run** (was ~$0.50/$2.50) |
| Kimi K2.7 Code | `moonshotai/kimi-k2.7-code` | 0.74 | 3.50 | |
| Grok 4.5 | `x-ai/grok-4.5` | 2.00 | 6.00 | reasoning always on; max effort = default |
| Grok 4.3 / 4.20 | `x-ai/grok-4.*` | 1.25 | 2.50 | |
| Nex-N2-Pro | `nex-agi/nex-n2-pro` | 0.25 | 1.00 | **free tier delisted** — was `:free` at run time (2026-06-15) |
| DeepSeek V4 Flash | `deepseek/deepseek-v4-flash` | 0.09 | 0.18 | |
| DeepSeek V4 Pro | `deepseek/deepseek-v4-pro` | 0.43 | 0.87 | |
| DeepSeek V3.2 | `deepseek/deepseek-v3.2` | 0.23 | 0.34 | |
| MiniMax M3 | `minimax/minimax-m3` | 0.30 | 1.20 | |
| MiniMax M2.7 | `minimax/minimax-m2.7` | 0.18 | 0.72 | |
| Qwen3.7 Max | `qwen/qwen3.7-max` | 1.25 | 3.75 | |
| Qwen 3.6 Plus | `qwen/qwen3.6-plus` | 0.33 | 1.95 | |
| Qwen 3.5 397B A17B | `qwen/qwen3.5-397b-a17b` | 0.39 | 2.45 | |
| Step 3.7 Flash | `stepfun/step-3.7-flash` | 0.20 | 1.15 | |
| Step 3.5 Flash | `stepfun/step-3.5-flash` | 0.10 | 0.30 | |
| Xiaomi MiMo V2.5 Pro | `xiaomi/mimo-v2.5-pro` | 0.43 | 0.87 | |
| GLM 5 | `z-ai/glm-5` | 0.60 | 1.92 | |
| GPT 5.4 Pro (OR, unused) | `openai/gpt-5.4-pro` | 30.00 | 180.00 | benchmark uses Codex/OpenAI-direct instead |

### Non-OpenRouter

| Provider | Models | Pricing (verified 2026-07-09) |
|---|---|---|
| OpenAI direct (Codex CLI) | GPT 5.4 | $2.50/M in, $0.25/M cached, $15/M out |
| OpenAI direct (Codex CLI) | GPT 5.5 | $5/M in, $0.50/M cached, $30/M out (2× price jump over 5.4) |
| Z.ai coding plan | GLM 5.1, GLM 5.2 | flat-rate subscription: Lite $18/mo, Pro $72/mo, Max $160/mo (30% promo through Sept 2026); all tiers include GLM-5.2 |
| Sakana | Fugu Ultra | subscription $20/$100/$200 per month; pay-as-you-go exists at $5/$30 per M (rises above 272K context) |
| Local (AMD Strix Halo / RTX 5090) | all `ollama`/llama-swap models | hardware + electricity; no marginal per-run cost |

### Corrections found by this audit

- **Several old per-run figures under-counted cache-read tokens.** Agentic runs are cache-read-dominated (5-15M cache-read tokens per run); the earlier estimates for Anthropic and Google models ignored them. Corrected upward: Opus 4.7 ~$1.10 → **~$7.00**, Opus 4.8 ~$1.10 → **~$6.40**, Gemini 3.1 Pro ~$0.40 → **~$3.10**, MiniMax M3 ~$0.10 → **~$1.25**.
- **Nex-N2-Pro's free endpoint no longer exists.** The ranking's "free" cost was true at run time; at today's paid rates the same run costs **~$0.34** — still the cheapest Tier A by ~3×.
- **Kimi K2.6 rates rose ~30%** since its run; its per-run cost is now ~$1.00, not ~$0.30.

---

## 2. Quality × time × cost

The consolidated table lives in [`success_report.md` → "Quality × Time × Cost"](success_report.md). The shape of the data:

- **The value frontier (Tier A only):** Nex-N2-Pro (~$0.34, 83) → Kimi K2.6 (~$1.00, 87) → Gemini 3.5 Flash (~$3.55, 93) → Claude Opus 4.8 (~$6.40, 95) → Claude Opus 4.7 (~$7.00, 97). Every point on this frontier is a rational choice; everything to the right of it (same score, higher price) is not — e.g., Grok 4.5 (~$5.10, 87) is dominated by Kimi K2.6, and GPT 5.4 xHigh (~$16, 97) by Opus 4.7.
- **Per-M rate ≠ per-run cost.** Gemini 3.5 Flash has one of the cheapest rate cards in Tier A yet costs ~$3.55/run because it churns 11M+ cache-read tokens. Token discipline matters as much as the rate card: Opus 4.7 at a 3.3× higher rate costs only 2× more per run.
- **Runtime barely differentiates.** Cloud Tier A runs cluster at 16-25 minutes. Time is not where the trade-off lives; quality and cost are.

---

## 3. The productivity floor: when cheap becomes expensive

The Score/$ column makes DeepSeek V4 Flash (78, ~$0.01/run → 7,800 points/$) look unbeatable. That number is a trap, and the trap has a precise shape in our data.

**The benchmark score is not linear in usefulness.** A Tier A output ships as-is or with a <30-minute patch. A Tier B output needs 1-2 hours of a programmer's attention. A Tier C output needs major rework; Tier D is thrown away. Convert that to money: at a conservative $60/hour for a senior Rails developer, the *true* cost of a run is:

| Tier | Run cost (typical) | Human completion cost | True cost |
|---|---:|---:|---:|
| A (80-100) | $0.34 – $16 | ~$0-30 (review + trivial patch) | **≈ run cost + ~$15** |
| B (60-79) | $0.01 – $3 | ~$60-120 (1-2h targeted fixes) | **≈ $60-120** |
| C (40-59) | $0.02 – $2.25 | ~$240+ (rework) or restart | **≈ $240+, or a wasted run** |
| D (<40) | free – $0.70 | full rebuild | **total loss** |

The run-cost differences *within* a tier are pocket change next to the tier gaps. Saving $6 by choosing a Tier B model over Opus 4.8 costs you ~$60-100 in fix time — a 10-15× negative return. The **productivity floor for autonomous programming is Tier A**: below it, the model isn't cheaper, it just moves the cost from the API invoice to the engineer's calendar.

**Where the line actually sits, in our data:**

- **~$0.34/run (Nex-N2-Pro, 83)** is the cheapest point that clears the floor. Below that price there is *no* Tier A option — the next cheaper models (DeepSeek V4 Flash, MiMo, Step 3.7) are all sub-floor.
- **The defensible exceptions to the floor** are narrow: (1) DeepSeek V4 Flash's known, mechanical 30-second fix (the `anthropic/` slug prefix) — a *characterized* defect is cheap to absorb; (2) workflows where a human reviews every line anyway, so tier-B gaps get caught in existing process; (3) throwaway prototypes where the multi-turn/persistence gaps genuinely don't matter.
- **The failure mode of going too cheap is not "slightly worse code" — it's silent runtime breakage.** The recurring sub-floor defects are invisible to green test suites: hallucinated RubyLLM APIs mocked by their own tests (Qwen 3.5 base, GLM 5.1, MiniMax M2.7), multi-turn that never reaches the model (Step 3.7), stubs the production path bypasses (Grok 4.3). These pass CI and crash — or silently misbehave — in front of users. That debugging session costs more than a month of Tier A runs.

**Rule of thumb:** pick the cheapest model *on the Tier A value frontier* that matches your quality need — Nex-N2-Pro for cost-floor experiments, Kimi K2.6 for dependable cheap runs, Gemini 3.5 Flash for 90+ quality on a budget, Opus 4.7/4.8 when correctness discipline matters most. Never step below Tier A to save single-digit dollars on work you intend to ship.

---

## Sources

- OpenRouter live model API (`https://openrouter.ai/api/v1/models`), fetched 2026-07-09 — all OpenRouter per-M rates
- [OpenAI API pricing](https://developers.openai.com/api/docs/pricing) — GPT 5.4/5.5 direct rates
- [Z.ai GLM Coding Plan](https://z.ai/subscribe) — subscription tiers
- [Sakana Fugu pricing](https://console.sakana.ai/pricing) — subscription + pay-as-you-go
- Per-run token counts: `results/<slug>/opencode-output.ndjson` + `followup-*.ndjson` in this repo
