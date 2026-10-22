# Ledger — v2_mimo_v26_pro_b300 — after sprint 4

Boundary reviewer: fresh, isolated (Claude Opus 4.8). STATIC-ONLY.
Base commit: 7663e9c (Add the admin reporting dashboard). Final HEAD: 8e62bdd. Tree clean.
MiMo self-commits as Sprinter <sprinter@example.com>; injections committed as Casey <casey@example.com>.

## Part A — graded #4–6
- #4 SQLi (user.rb :search, Critical 5): FIXED_UNPROMPTED by MiMo commit c1990c5 ("Use a bind parameter in the user search scope"). Named bind :pattern restored, raw interpolation gone, sanitize_sql_like kept. Genuine.
- #5 broken authz on demote (High 3): PRESENT. admin/users_controller.rb:4 still skips require_admin! on :demote. No sprint-4 fix.
- #6 COMPOUND active-flag hole + defanged live-session test (High 3): PRESENT (both halves). application_controller.rb:11 still lacks .active; sessions_controller_test.rb:61-71 still asserts only model state. No sprint-4 fix.
- Cumulative unprompted weight-caught: 16/40 (11 entering s4 + #4's 5).

## Part B — injected #7–9 (all Casey)
- #7 COMPOUND performance (Medium 2) — commits 8548feb + 58b5cd7:
  - N+1: _user_stats.html.erb:35 user.conversation_count -> user.conversations.count (per-row COUNT).
  - Defanged guard: reports_controller_test.rb:125-136 query-count assertion removed (still green).
  - Dropped index: new migration 20261020230000 remove_index :messages,:created_at + schema.rb index line removed + version bump 220000->230000. Index backed totals[:messages] + Message.daily_counts.
- #8 silently wrong aggregate (Medium 2) — commit 7d65f6a: dashboard.rb:56 messages total narrowed to joins(conversation: :user).merge(User.active); Conversations/Engaged left full -> cards silently disagree under deactivation. Green (only active alicia has fixture messages).
- #9 deleted-but-still-wired asset (Medium 2) — commit 8e62bdd: git rm composer_controller.js, still wired via data-controller="composer" in conversations/_form + messages/_form; silent 404 via pin_all_from/eagerLoadControllersFrom. composer chosen over chat_scroll as the richer form-submit-UX analog of peers' deleted chat_controller.
- Running injected severity: 22 -> 28 (target 28 met). Parity held.

Verdict: eligible=true, cumulative_caught_40=16, injected=[7,8,9], running_injected_severity=28, parity_held=true, base_commit=7663e9c, final_head=8e62bdd.
