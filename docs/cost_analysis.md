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
| Kimi K3 | `moonshotai/kimi-k3` | 3.00 | 15.00 | harness-incompatible with opencode (see Failed Models) |
| Kimi K2.5 | `moonshotai/kimi-k2.5` | 0.57 | 2.85 | ↑ again (Jul 9: $0.38/$2.02) |
| Kimi K2.6 | `moonshotai/kimi-k2.6` | 0.95 | 4.00 | **↑ again 2026-07-16** (Jul 9: $0.65/$3.41; run-era ~$0.50/$2.50 — ≈2× total) |
| Kimi K2.7 Code | `moonshotai/kimi-k2.7-code` | 0.75 | 3.50 | |
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
| ChatGPT subscription (Codex CLI) | GPT 5.6 Sol | billed as plan credits; API-equiv $5/$30 per M — the benchmark run ≈$8.70 equivalent |
| Z.ai coding plan | GLM 5.1, GLM 5.2 | flat-rate subscription: Lite $18/mo, Pro $72/mo, Max $160/mo (30% promo through Sept 2026); all tiers include GLM-5.2 |
| Sakana | Fugu Ultra | subscription $20/$100/$200 per month; pay-as-you-go exists at $5/$30 per M (rises above 272K context) |
| Kimi subscription (Kimi Code CLI) | Kimi K3, K2.7-Coding | Moderato $19/mo (K3 @256K); benchmark K3 run ≈$2.10 API-equivalent; 5h-window quota — see §4 empirical verdict |
| Local (AMD Strix Halo / RTX 5090) | all `ollama`/llama-swap models | hardware + electricity; no marginal per-run cost |

### Corrections found by this audit

- **Several old per-run figures under-counted cache-read tokens.** Agentic runs are cache-read-dominated (5-15M cache-read tokens per run); the earlier estimates for Anthropic and Google models ignored them. Corrected upward: Opus 4.7 ~$1.10 → **~$7.00**, Opus 4.8 ~$1.10 → **~$6.40**, Gemini 3.1 Pro ~$0.40 → **~$3.10**, MiniMax M3 ~$0.10 → **~$1.25**.
- **Nex-N2-Pro's free endpoint no longer exists.** The ranking's "free" cost was true at run time; at today's paid rates the same run costs **~$0.34** — still the cheapest Tier A by ~3×.
- **Kimi rates keep climbing**: K2.6 has roughly doubled since its run (run cost now ~$1.19 at 2026-07-16 rates; ~$1.00 at Jul 9; ~$0.30 originally). K2.7 ~$1.23. Moonshot exited the value niche entirely with K3 at $3/$15.

---

## 2. Quality × time × cost

The consolidated table lives in [`success_report.md` → "Quality × Time × Cost"](success_report.md). The shape of the data:

- **The value frontier (Tier A only):** Nex-N2-Pro (~$0.34, 83) → Kimi K2.6 (~$1.19, 87) → Gemini 3.5 Flash (~$3.55, 93) → Claude Opus 4.8 (~$6.40, 95) → Claude Opus 4.7 (~$7.00, 97). Every point on this frontier is a rational choice; everything to the right of it (same score, higher price) is not — e.g., Grok 4.5 (~$5.10, 87) is dominated by Kimi K2.6, and GPT 5.4 xHigh (~$16, 97) by Opus 4.7.
- **Per-M rate ≠ per-run cost.** Gemini 3.5 Flash has one of the cheapest rate cards in Tier A yet costs ~$3.55/run because it churns 11M+ cache-read tokens. Token discipline matters as much as the rate card: Opus 4.7 at a 3.3× higher rate costs only 2× more per run.
- **Subscription billing is now on the board**: GPT 5.6 Sol (92) ran on ChatGPT plan credits at ≈$8.70 API-equivalent. At API rates it is dominated by Opus 4.8 (95 at ~$6.40); on an already-paid ChatGPT plan its marginal cost is ≈$0, making it the rational frontier pick for Pro subscribers (see §4).
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

## 4. Subscriptions change the math — but only for individuals, and only up to the caps

Everything above prices runs at raw API rates, which is how *this benchmark* pays (OpenRouter BYO key; Codex runs billed via `OPENAI_API_KEY`). But Anthropic and OpenAI consumer plans (verified 2026-07-09, see [`pricing.md`](pricing.md)) change the calculus for an individual developer who already owns one:

**Break-even against our measured per-run costs:**

| Plan | $/mo | Covers | Break-even vs API |
|---|---:|---|---|
| Claude Pro | $20 | Claude Code incl. Opus-class usage within capped windows | ~3 Opus 4.7/4.8-scale runs/month |
| Claude Max 5x | $100 | 5× Pro limits | ~14-16 Opus runs/month |
| Claude Max 20x | $200 | 20× Pro limits | ~29-31 Opus runs (~$6.40-7.00 each) or ~18 Fable 5 runs (~$11.20) /month |
| ChatGPT Plus | $20 | Codex, credit-metered | ~1-2 GPT 5.4 xHigh-scale runs/month |
| ChatGPT Pro 20x | $200 | 20× Plus credits | ~13 GPT 5.4 xHigh runs (~$16) or ~20 GPT 5.5 runs (~$10) /month |

Three consequences, and three caveats that keep the API analysis primary:

- **For an individual on Max/Pro, the marginal cost of a frontier run is ≈ $0 within caps.** That collapses the price axis of the value frontier: if the subscription is already paid for, "use the best model your plan gives you" beats every per-token optimization — a Max 20x holder gains nothing choosing Kimi K2.6 over Opus 4.7 to save $6 they aren't spending. The frontier logic (§2) then only governs *overflow* usage beyond the caps and models outside the plan.
- **The productivity-floor conclusion (§3) is unchanged and gets stronger.** Subscriptions make Tier A frontier models *cheaper* relative to sub-floor models, not pricier — there is even less reason to step below Tier A when Opus-class runs are effectively prepaid.
- **At ~30 benchmark-scale agentic runs/month, subscription and API costs converge** (~$200 either way for Opus-class). Below that volume the subscription wins; far above it you exhaust caps and are back to API rates anyway.

**Empirical: the $19 Kimi Moderato plan under benchmark-scale load (2026-07-16/17).** We ran the Kimi K3/K2.7 pipeline entirely on the cheapest Kimi plan and logged every quota event. Results: the 5-hour rolling window absorbed roughly **two benchmark-scale agentic runs (~9M tokens) before hard-403ing mid-way through a third**; the mid-run death wasted the partial build. The subsequent wait for quota release was **4h16m** (7 blocked 20-minute probes). After release, a fresh window absorbed **two full back-to-back runs (K3 4.8M + K2.7 9.2M ≈ 14M tokens) without blocking**. Verdict: Moderato comfortably supports an individual's *interactive* pace (~2-3 heavy agentic sessions per window, ~8-12/day if you ride the windows) and delivered ~$6-7 of API-equivalent tokens in one day — but it is **hostile to batch/unattended work**: one mis-timed run costs a 4+ hour stall, and a mid-run 403 burns quota on an unusable partial. For anything scripted, either the API key path or a higher tier; for solo interactive coding, Moderato is genuinely the cheapest frontier-model seat on the market.

Caveats: (1) **"included" is not "unlimited"** — Codex has been credit-metered since 2026-04-02 (GPT-5.5 at 125/750 credits per 1M tokens; heavy real-world use runs $100-200/dev/month), and Claude plans meter by session/weekly windows; a cache-read-heavy agentic session consumes limits fast. (2) **Automation and CI cannot ride consumer plans** — unattended pipelines, this benchmark included, pay API rates, so the §2 frontier is the right lens for anything scripted. (3) **OpenRouter-served models never see these subscriptions** — Kimi, GLM, DeepSeek, Nex, Gemini et al. are API-priced regardless, so cross-vendor comparisons must hold the billing mode constant or say which one they assume.

---

## Sources

- OpenRouter live model API (`https://openrouter.ai/api/v1/models`), fetched 2026-07-09 — all OpenRouter per-M rates
- [OpenAI API pricing](https://developers.openai.com/api/docs/pricing) — GPT 5.4/5.5 direct rates
- [Z.ai GLM Coding Plan](https://z.ai/subscribe) — subscription tiers
- [Sakana Fugu pricing](https://console.sakana.ai/pricing) — subscription + pay-as-you-go
- [Claude plans](https://claude.com/pricing) + [Max plan help page](https://support.claude.com/en/articles/11049741-what-is-the-max-plan) — Pro/Max pricing and limits
- [Codex pricing](https://developers.openai.com/codex/pricing) + [Codex rate card](https://help.openai.com/en/articles/20001106-codex-rate-card) — ChatGPT plan inclusion and credit metering
- Per-run token counts: `results/<slug>/opencode-output.ndjson` + `followup-*.ndjson` in this repo
