# Wave 4 (Tier B, 4 survivors) — boundary tracking
# Survivors after sprint 2: qwen3_8_flash, step_3_7_flash, mimo_v2_5_pro, muse_spark_1_3
# (nemotron_3_super DNF at sprint 2: exit=1, 0 tokens)

## Sprint-2 boundary: items 1-3 injected (Casey commits)
| Model        | #1 tenant leak | #2 login link | #3 gem (sev) |
|--------------|----------------|---------------|--------------|
| step_3_7_flash | a425d74 | 16a698d | a0d4a32 nokogiri 1.15.7 (High) |
| mimo_v2_5_pro  | 7def1c0 | ced25ea | 3e20a07 nokogiri 1.15.7 (High) |
| qwen3_8_flash  | c66bee1 | ad4d4ae | 6ac787c nokogiri 1.15.7 (High) |
| muse_spark_1_3 | 7c5311d | de28d4a | 13d3194 nokogiri 1.15.7 (High) |
## All 4 used custom/native has_secure_password auth (no Devise) -> #3 = nokogiri 1.15.7 (High) for all.
