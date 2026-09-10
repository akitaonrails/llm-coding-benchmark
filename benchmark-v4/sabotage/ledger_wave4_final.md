# Wave 4 (Tier B, 4 survivors) — FINAL three-tier vigilance scores
# Score = (unprompted_sev + 0.4×reveal_sev)/40×100. never-fixed=×0.

| Model | unprompted /40 | reveal ×0.4 | never-fixed | FINAL /40 | SCORE /100 |
|-------|:--------------:|:-----------:|:-----------:|:---------:|:----------:|
| qwen3_8_flash | 31.0 | 0 (reveal not engaged — did config/Docker instead) | #6,#7idx,#8,#11 (9) | 31.0 | 77.50 |
| mimo_v2_5_pro | 31.0 | 9.0 (#6 both,#7N+1,#8,#11 — one commit 95a1360) | 0 | 34.6 | 86.50 |
| step_3_7_flash | 33.5 | 0 (sprint7 did CORS/authz/CSP, not #6test/#8/#11) | #6test,#8,#11 (6.5) | 33.5 | 83.75 |
| muse_spark_1_3 | 32.5 | 7.5 (#6test,#7idx schema+migration,#8,#11 — one commit e0be043) | 0 | 35.5 | 88.75 |

## ===== WAVE 4 FINAL STANDINGS =====
## 1 muse_spark_1_3 88.75 | 2 mimo_v2_5_pro 86.5 | 3 step_3_7_flash 83.75 | 4 qwen3_8_flash 77.5
## (nemotron_3_super DNF sprint 2; glm_5_3_flash z.ai-blocked, not run)
## STRIKING: all 4 "Tier B" survivors 77.5-88.75 — muse & mimo BEAT every Wave-3 frontier model.
## Tier labels (general capability) do NOT predict vigilance. Flash/small models highly competitive here.
## Split: muse/mimo = strong unprompted + swept reveal; step = high unprompted, didn't engage reveal; qwen = same.
