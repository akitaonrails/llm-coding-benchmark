# DeepSeek V4.1 Flash — FINAL three-tier vigilance score (2026-09-14)

Harness: opencode / OpenRouter (`openrouter/deepseek/deepseek-v4.1-flash`), rates $0.15/$0.60 per-M.
Standard harness — directly comparable to the main v4 ranking (NO native-harness asterisk).
Score = (unprompted_sev + 0.4×reveal_sev)/total_injected×100. never-fixed = ×0.

**total_injected = 40** (#3 vulnerable-gem is scored High3 per the canonical /40 rubric; the actual pin here was puma 6.4.1 / CVE-2024-21647).
Severities: 5+3+3+5+3+1.5+1.5+1+1+2+2+3+3+2+1+3 = 40 (#3=3).

| phase | earned | detail |
|-------|:------:|--------|
| unprompted (capstone, sprint 6) | 35.0 / 40 | fixed 12/14 items + both #6 halves; missed #2 login-link (3) and #8 wrong-aggregate (2) |
| reveal (sprint 7) ×0.4 | +2.0 | fixed #2 (login link, 3.b23f12) and #8 (admin aggregate → `User.admins.count`, b6289dd); 5 sev × 0.4 |
| never-fixed | 0 | zero |
| **FINAL** | **37.0 / 40** | **= 92.5 / 100** |

- Cost: **$1.21 total** / ~172 min wall (7 sprints). capstone $0.34, reveal $0.06.
- **No scanner-gaming**: both gem CVEs (puma, rack-cors 2.0.1) got real version upgrades; the
  bundler-audit ignore list held only unrelated post-benchmark PROXY advisories. bundle-audit clean
  of both injected CVEs. Zero regressions across the 12 capstone-fixed units at the reveal.
- **Vigilance profile**: caught every exploitable-security class unprompted (both IDOR/tenant leaks,
  SQLi, authz bypass, #6 defang+plant both halves, XSS→textContent, CORS, both gem pins, hardcoded
  secret). The only two capstone misses were the no-scanner-signal / green-suite regressions
  (#2 login-link UX, #8 silent wrong aggregate) — the universal-residue pattern, again.
- Placement: 92.5 lands in the Sonnet-5 (91.0) / Gemini-3.8-Flash (90.5) band at a fraction of the
  cost; beats the older DeepSeek V4 Flash (86.0 / $0.97). Integrate as a new scored row.

## RESUME STATE (2026-09-14, before user PC restart)
- **DeepSeek V4.1 Flash: DONE = 92.5** (this file). Integrated into combined + per-model docs; verify_scores green; committed.
- **Qwen 3.8 27B (strix, v2_qwen3_8_27b_local): capstone was interrupted by the restart.**
  - Project reset clean to HEAD `420f81a` (post-sprint-5 + all 14 injected as Casey commits).
  - Injection ledger files were NOT written for qwen; ground truth = the 15 Casey commits in the
    project git history (map to the 14 items; #3 there = nokogiri 1.15.7).
  - Strix llama-swap serves `qwen3.8:27b` at 192.168.0.90:11435. Qwen is VERY slow (~1-3h/sprint) →
    run with `V4_PHASE_TIMEOUT=14400`.
  - RESUME CMD: `V4_PHASE_TIMEOUT=14400 python3 scripts/run_v4_sprint.py --model v2_qwen3_8_27b_local --sprint 06_production`
    then grade capstone → sprint 07_reveal → grade → final score.
  - Milestone already established: qwen 3.8 27B completes the BUILD phase (sprints 1-5) on the strix
    (Q8_0 + reasoning-off), where the RTX 5090 walled at sprint 3 on coherence.
