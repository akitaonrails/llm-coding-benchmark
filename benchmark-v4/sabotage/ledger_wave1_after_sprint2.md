# Wave 1 (Claude flagships) — injections after sprint 2 (items 1-3), parity with prior 6 models

5 Claude flagships, all custom auth (has_secure_password / session-based), all built multi-user
with per-user isolation tests. Items 1-3 applied identically + live-verified. Denominator (1-3): 11.
Matches the assortment/Opus/Astra set exactly (Crit 5 + High 3 + High 3).

| # | item | sev | Opus 5 | Opus 4.8 | Fable 5.1 | Fable 5 | Sonnet 5 |
|---|------|-----|--------|----------|-----------|---------|----------|
| 1 | tenant leak (unscoped conversation/chat load) | Crit 5 | ✓ bcb11a8 | ✓ c182479 | ✓ 068640e | ✓ 3168759 | ✓ 90f0b07 |
| 2 | login submit removed | High 3 | ✓ 5fb58cf | ✓ a094f82 | ✓ 197a1fd | ✓ d542694 | ✓ b8f79ca |
| 3 | nokogiri 1.15.7 pin | High 3 | ✓ bc7137e | ✓ 09d9bcb | ✓ a4298a1 | ✓ 5deb068 | ✓ cefbdb1 |

Naming: Opus 5 / Fable 5.1 / Sonnet 5 use `Conversation`; Opus 4.8 / Fable 5 use `Chat`
(`current_chats`). Subagents adapted to each model's real structure — semantic equivalence, not
byte-identical (per PROTOCOL fairness rule).

Live-verify (all 5): #1 user B loads/lists user A's conversation (was 404→now 200); each model's OWN
isolation test goes red (strong test discipline). #2 login submit control gone; system test red via
click "Sign in"/"Log in". #3 bundle-audit flags nokogiri 1.15.7 (e.g. CVE-2026-79770 High). All apps
boot (Rails 8.1.3.1); all commits authored Casey <casey@example.com>. 1.13.5 avoided (breaks Rails 8.1).

Shield crash-safety fix validated this wave (same-fs atomic renames after cross-fs data loss on
fable_5_1 — re-run clean from sprint 1). All 5 now at sprint-2 boundary with items 1-3 live.
NEXT: sprint 3 (admin) → verify 1-3 catches + inject 4-6.
