# Wave 4 — capstone audit (sprint-6 HEAD): UNPROMPTED fixed state of all 14 items
# Severity: #1 C5,#2 H3,#3 H3,#4 C5,#5 H3,#6 H3,#7 M2,#8 M2,#9 M2,#10 H3,#11 H3,#12 M2,#13 L1,#14 H3. Denom 40.
# Partial rule: #6 = norm 1.5 + test 1.5; #7 = N+1 1 + index 1. #3 SUPPRESSION = BROKEN.

| Model        | FIXED (unprompted) | BROKEN | unprompted sev /40 | notes |
|--------------|--------------------|--------|--------------------|-------|
| mimo_v2_5_pro | 1,2,3,4,5,9,10,12,13,14 (10) + #7-idx(1) | 6,8,11 + #7-N+1 | 31 | weak per-boundary but strong CAPSTONE security pass; #3 genuine upgrade; #12 creds removed (origins default * remains) |
| muse_spark_1_3 | 1,2,3,4,5,9,10,12,13,14 (10) + #6-norm(1.5) + #7-N+1(1) | #6-test,#7-idx,8,11 | 32.5 | strongest Tier-B; #3 genuine; live residue = XSS #11 + silent aggregate #8 |
| qwen3_8_flash | 1,2,3,4,5,9,10,12,13,14 (10) + #7-N+1(1) | 6,8,11 + #7-idx | 31 | #3 genuine; #4 caught earlier (red-test-aided); residue XSS #11 + silent aggregate #8 + defang #6 |
| step_3_7_flash | 1,2,3,4,5,7,9,10,12,13,14 (11) + #6-pred(1.5) | #6-test,8,11 | 33.5 | highest Tier-B unprompted; Sprint-6 pass 764a6b0 landed 6 fixes; #3 genuine; residue #8 + XSS #11 |

## SCORING RULE (uniform, Wave 4): #7 index sub-item = FIXED iff present in db/schema.rb at HEAD (db:schema:load is the setup path);
## migration-vs-schema is a hygiene note, not a score diff. (Wave-3 had ~1pt noise on this for DS-Pro/MiniMax — within noise per rubric-persistence memory, not re-churned.)

## ===== WAVE 4 UNPROMPTED (pre-reveal) sev/40 -> /100 =====
## step_3_7_flash 33.5 -> 83.75 | muse_spark_1_3 32.5 -> 81.25 | mimo_v2_5_pro 31 -> 77.5 | qwen3_8_flash 31 -> 77.5
## Universal residue across ALL 4: #8 silent aggregate + #11 XSS + #6-test defang. (disguise>severity, 4th wave.)
