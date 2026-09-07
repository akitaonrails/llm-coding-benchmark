# v4 FULL-LIST run procedure (adjusted after the 4-model assortment, 2026-09-07)

Extends PROTOCOL.md with the operational fixes learned running the assortment. Goal: run the
full v3 model set through v4 robustly, frontier-first, without wasting spend on models that DNF.

## Robustness fixes (baked into tooling)
1. **Self-healing shield** (`run_v4_sprint.py`): `restore_stranded_shields()` runs at startup and
   moves any stranded `~/.cache/.v4shield_*` (from a prior KILLED run) back into the repo before
   shielding — conservative (only restores a target that's currently missing; skips if another
   run_v4 is active). Plus a SIGTERM/SIGINT handler that unshields on kill. => a killed batch no
   longer strands the answer key; just re-run the wave for the same sprint.
2. **Abort-early wave runner** (`run_v4_wave.py --sprint NN --models a,b,c`): runs a sprint across
   a wave sequentially (shield forces sequential), SKIPS models already marked `results-v4/<slug>/DNF`,
   and marks DNF when a run stall_aborts / crashes with ~no tokens / produces no Rails app (sprint≥2).
   Idempotent: skips a model whose sprint dir already exists (resume after a kill). Benign exit -15
   WITH tokens (kimi lingers) is NOT a DNF.

## Subagent-grading discipline (MUST — learned from hangs/contamination)
- Grade/inject subagents verify STATICALLY: code inspection + grep + bundle-audit. **NEVER loop on
  live HTTP / rack-test / CSRF** (that hung a DeepSeek subagent ~2h). One quick test-env check max.
- **NEVER let a boundary subagent outlive its sprint.** Confirm ALL boundary subagents RETURNED
  before launching the next sprint wave. A late one operates on a moving (shielded/unshielded) target
  and corrupts state (it clobbered a Grok fix + wrote into an active shield cache). Kill stragglers.
- Grade in ISOLATED subagents, evidence-cited (file:line/grep/bundle-audit), never status-from-memory.
- Injection = real code, minimal, live-verified, committed as "Casey <casey@example.com>"; parity
  ledger per wave.

## Injection parity by TIER (user rule: same within tier; tone down for weaker tiers)
- **Tier A (frontier)** — full 14-item set (severities sum 40). Waves 1–3.
- **Tier B** — drop the 2 subtlest disguised plants (#6 defang-and-plant, and treat #7 as N+1 only,
  no dropped-index half): ~11 items. Recompute denominator from the actual injected set; score on
  that denominator (report notes the reduced set). Keep identical WITHIN the tier's wave.
- **Tier C/D** — most DNF (abort-early drops them). If one completes, inject only the LOUD set
  (#1 tenant leak, #2 login button, #4 SQLi, #5 authz, #10 API authz, #11 XSS, #14 secret) ≈ 7 items.
- Tier assignment from v2/v3 score (A≥83, B 73–82, C 51–72, D≤50). Provisional; a model that
  overperforms its tier still graded on its wave's set (parity > individual tuning).

## Per-model flow (unchanged from PROTOCOL, 7 sprints)
run sprint 1 → 2 (inject 1-3) → 3 (verify 1-3 + inject 4-6) → 4 (verify 4-6 + grade + inject 7-9)
→ 5 (verify 7-9 + grade API + inject 10-14) → 6 (capstone, grade unprompted) → 7 (reveal, final audit).
Each boundary = one grade+inject subagent per model, spawned in parallel across the wave, ALL
returned before the next sprint. Ledgers in benchmark-v4/sabotage/.

## Wave order (frontier-first; 6 already done: opus_4_6, deepseek_v4_pro_0813, gemini_3_8_flash_high,
##   gpt_6_astra, grok_4_6, kimi_k3). ~36 remaining distinct models (CLI/agy harness A/B variants deferred).
- **Wave 1 — Claude flagships (Tier A):** claude_opus_5, claude_opus_4_8, claude_fable_5_1, claude_fable_5, claude_sonnet_5
- **Wave 2 — GPT/Gemini/Grok top (Tier A):** gpt_5_6_sol, gpt_5_6_terra, gpt_5_6_luna, gpt_5_5, gemini_3_7_flash_high, grok_4_5
- **Wave 3 — strong rest (Tier A):** claude_sonnet_4_6, deepseek_v4_pro, deepseek_v4_flash_0731, deepseek_v4_flash, glm_5_3, glm_5_2, qwen3_8_max, qwen3_7_max, kimi_k2_7_coding, kimi_k2_6, mistral_large_3, minimax_m3, gemini_3_1_pro
- **Wave 4 — Tier B (tone-down set):** glm_5_3_flash, qwen3_8_flash, step_3_7_flash, mimo_v2_5_pro, muse_spark_1_3, nemotron_3_super
- **Wave 5 — Tier C/D (expect DNF, abort-early):** codestral_2508, devstral_2512, gpt_oss_120b, hunyuan_a13b, llama_4_maverick, qwen3_8_27b_local

## Cost reality (from assortment: ~$4–30/model model-cost + ~7 grade/inject subagents/model)
Full Tier-A (~30 models) ≈ $400–700 model-cost + subagent grading; Tier B/C mostly abort-early.
Frontier-first means the valuable ranking data lands first; weaker waves add breadth cheaply (DNFs).
Deliver an updated combined ranking after each wave (don't wait for all 5).
