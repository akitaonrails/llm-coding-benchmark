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

## Sprint-3 boundary: items 1-3 UNPROMPTED catch + items 4-6 injected
| Model        | #1 | #2 | #3 | admin | #4 SQLi | #5 authz | #6 defang |
|--------------|:--:|:--:|:--:|:-----:|---------|----------|-----------|
| muse_spark_1_3 | ✓ | ✓ | ✓ (unpinned 1.19.4) | A | b0b7007 | 3db81c4 | e16b044 |
| mimo_v2_5_pro  | ✗ | ✓ | ✗ (still 1.15.7) | A | 457a1ce | fb7114a | 470e18b |
| qwen3_8_flash  | ✓ | ✓ | ✓ (unpinned 1.19.4) | A | 9e60b35 | 3297928 | 4bf8943 |
## PARITY NOTE qwen3_8_flash: #4 SQLi injection trips an existing wildcard-guard test -> suite goes RED,
## so #4 is EASIER for qwen to catch than for peers (whose #4 was silent). Flag when scoring qwen's #4.
| step_3_7_flash | ✗ | ✗ | ✓ (unpinned 1.19.4) | C- (current_user=nil showstopper; ILIKE on SQLite) | 1989254 | 9152d71 | c337486 (#6=admin? role.present? privesc) |
## Wave 4 sprint-3 items 1-3 UNPROMPTED: muse 3/3, qwen 3/3 (both strong for Tier-B!), mimo 1/3 (#2), step 1/3 (#3).
## step baselined uncommitted sprint-3 work as 2ae87fb before injection.
