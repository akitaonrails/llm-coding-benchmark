# B300 batch progress

Probe speed is the latest saved admission measurement and may predate pod revalidation; it is not a coding-quality score. Paused runs retain their work for post-batch review. Follow each evidence link for actual grading and limitations.

**Reviewer provenance:** the independent boundary reviewer was OpenAI Codex (`codex exec`) for the five completed models (end-to-end) and the early boundaries of the rest; it was switched to Claude (Opus 4.8) on 2026-10-19 — on the user's explicit instruction — to complete the eight resumed models after Codex's security service refused the authorized injection/grading step. Same recipe, catalog, denominator and rules across the switch; per-boundary provenance is auditable (`sprint<NN>-claude-*` dirs vs Codex `agent.ndjson`). See the analysis doc's "Reviewer provenance" section and `results-v4/_b300_campaign/reviewer-provenance.json`.

| Model | State | Sprints | Sprint minutes | Probe tok/s | Nudges |
|---|---|---:|---:|---:|---:|
| [v2_glm_5_3_flash_oss](../results-v4/v2_glm_5_3_flash_oss) | completed — 92.5 (Codex) | 7/7 | 144.95 | 141.6 | 0 |
| [v2_qwen35_122b_oss](../results-v4/v2_qwen35_122b_oss) | skipped — conditional fallback not triggered (397B did not DNF) | 3/7 | 38.87 | 171.9 | 0 |
| [v2_qwen35_397b_oss](../results-v4/v2_qwen35_397b_oss) | completed — 68.5 (Codex→Claude) | 7/7 | 54.3 | 143.9 | 0 |
| [v2_dsv4_flash_oss](../results-v4/v2_dsv4_flash_oss) | completed — 44.5 (Codex) | 7/7 | 36.88 | 153.2 | 0 |
| [v2_nemotron35_super_vl_oss](../results-v4/v2_nemotron35_super_vl_oss) | completed — 63.0 (Codex→Claude) | 7/7 | 49.6 | 207.2 | 0 |
| [v2_qwen3_8_27b_oss](../results-v4/v2_qwen3_8_27b_oss) | completed — 80.5 (Codex) | 7/7 | 192.14 | 195.0 | 1 |
| [v2_glm_4_7_flash_bf16_oss](../results-v4/v2_glm_4_7_flash_bf16_oss) | completed — 33.5 (Codex) | 7/7 | 30.37 | 217.4 | 2 |
| [v2_qwen3_8_flash_next_oss](../results-v4/v2_qwen3_8_flash_next_oss) | completed — 92.5 (Codex→Claude) | 7/7 | 79.5 | 194.6 | 1 |
| [v2_muse_glimmer_30b_oss](../results-v4/v2_muse_glimmer_30b_oss) | completed — 81.0 (Codex→Claude) | 7/7 | 23.4 | 295.0 | 1 |
| [v2_command_a_plus_oss](../results-v4/v2_command_a_plus_oss) | partial — assist-exhausted (3 attempts), valid quality + infra block | 3/7 | 40.10 | 202.4 | 3 |
| [v2_ornith_1_5_35b_oss](../results-v4/v2_ornith_1_5_35b_oss) | completed — 81.0 (Codex→Claude) | 7/7 | 161.0 | 316.6 | 0 |
| [v2_nex_n2_5_mini_oss](../results-v4/v2_nex_n2_5_mini_oss) | partial — valid poor implementation result | 1/7 | 20.23 | 336.7 | 2 |
| [v2_swift_1_5_27b_oss](../results-v4/v2_swift_1_5_27b_oss) | completed — 88.0 (Codex) | 7/7 | 64.10 | 203.0 | 1 |
| [v2_thinkingcap_3_8_27b_oss](../results-v4/v2_thinkingcap_3_8_27b_oss) | completed — 83.0 (Codex→Claude) | 7/7 | 75.7 | 188.9 | 1 |
