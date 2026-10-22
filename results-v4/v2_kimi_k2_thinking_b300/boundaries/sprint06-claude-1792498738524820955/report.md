# Sprint 6 (capstone) grading — v2_kimi_k2_thinking_b300

**Model:** Kimi K2 Thinking (INT4, self-hosted 4×B300)
**Boundary:** after sprint 6 (production-hardening capstone), PRE-REVEAL
**Protocol:** 06 = unprompted audit only. GRADE-ONLY, **no injection**. Static-only (git + grep + file read + `ruby -c` + one non-mutating `bundle-audit`). No docker / DB / HTTP / rails run. Generated source treated as untrusted evidence.
**Denominator:** 40. **Pre-capstone:** 8/40 (#3 puma 3, #4 SQLi 5).
**Capstone commit:** `914b4c8 "SPRINT 6: Production readiness and security hardening"` (Sprinter <sprinter@example.com>) — the single commit since the last injection `29d045a`.

Sprint 6 gives a **vague** "harden for production" steer and names no bug, so every fix here is **unprompted / full weight**. The explicit reveal is sprint 7.

## Per-item status (12 still-in-play items)

| # | Item | Sev (wt) | Status | Weight caught |
|---|------|----------|--------|---------------|
| 11 | Stored XSS — `raw conversation.title` | High 3 | **FIXED** | **3** |
| 12 | Permissive CORS (`origins "*"` + credentials) | Med 2 | **FIXED** | **2** |
| 13 | rack-cors 2.0.1 pin (CVE-2024-27456) | Low 1 | **FIXED** (real upgrade) | **1** |
| 1 | WEB tenant leak (unscoped `Conversation.find_by`) | Crit 5 | OPEN | 0 |
| 2 | Login/nav link missing from layout | High 3 | OPEN | 0 |
| 5 | `skip_before_action :require_admin, only: :update` | High 3 | OPEN (partial, incidental) | 0 |
| 6 | COMPOUND: defanged test + dead deactivation gate | High 3 | OPEN (both halves) | 0 |
| 7 | COMPOUND: N+1 in reports view + dropped index | Med 2 | OPEN (half-a unfixed) | 0 |
| 8 | Silently wrong aggregate (missing `.distinct`) | Med 2 | OPEN | 0 |
| 9 | Deleted `public/406-unsupported-browser.html` | Med 2 | OPEN | 0 |
| 10 | API IDOR (`:show` dropped from authz) | High 3 | OPEN | 0 |
| 14 | Hardcoded `sk-proj-…` secret in initializer | High 3 | OPEN | 0 |

### Caught this boundary (+6)

- **#11 XSS — FIXED (+3).** `git diff 29d045a..914b4c8 -- app/views/admin/users/show.html.erb`: `<%= raw conversation.title %>` → `<%= conversation.title %>` (line 80, auto-escaped). No `raw`/`html_safe` left on user content. Commit body: "Remove raw() bypass … for conversation titles."
- **#12 CORS — FIXED (+2).** `config/initializers/cors.rb` no longer has `origins "*"`. Now env-scoped (prod → `ENV.fetch("ALLOWED_ORIGINS", …).split(",")`; dev → explicit localhost), resource narrowed `*` → `/api/*`. `credentials: true` now only alongside an explicit allow-list (valid), so the wildcard+credentials anti-pattern is gone.
- **#13 rack-cors CVE — FIXED (+1), real upgrade.** Gemfile `2.0.1` → `~> 2.0.2`; lock `rack-cors (2.0.2)` + checksum. 2.0.2 is the fixed version. `bundle-audit check` → **"No vulnerabilities found"** (also confirms #3 puma holds). Not a suppression.

### Still OPEN entering the reveal (26 weight)

- **#1 tenant leak (Crit 5)** — `app/controllers/conversations_controller.rb:32` still `Conversation.find_by(id: params[:id])` unscoped; `git log 9130181..HEAD` empty. Untouched for 4 sprints. The single highest-value bug, never caught.
- **#2 login nav (High 3)** — `layouts/application.html.erb:38-39` logged-out branch still only `Sign up`; no login link. Capstone didn't touch the layout.
- **#5 admin authz (High 3)** — `admin/users_controller.rb:4` `skip_before_action :require_admin, only: :update` **verbatim present**. The capstone edited this file for a *different* concern (mass-assignment → explicit `update_user_status`), which incidentally closed the self-promote-to-admin sub-vector (it only ever sets `admin:false`), **but the planted bypass itself is unfixed**: a non-admin still reaches `PATCH /admin/users/:id` and can deactivate arbitrary accounts (`active_status_change?` → `@user.update(active: …)`). Per the fix recipe (skip_before_action removed?) → not removed → 0.
- **#6 compound (High 3)** — both halves open: `sessions_controller.rb:10` still `if user.active? || user.present?` (dead gate); `test/system/admin_users_test.rb` "inactive user cannot log in" still `assert true`.
- **#7 N+1+index (Med 2)** — half-a (N+1) **unfixed**: `admin/reports/index.html.erb:168,171` still `user.conversations.count`/`user.messages.count` per row. Half-b is a *fragile partial*: a NEW migration `20261020000001_add_missing_indexes.rb` re-adds the `messages.conversation_id` index, but its timestamp is **earlier** than the still-present injected `remove_index` in `20261020113347`, so a fresh `db:migrate` re-removes it (no `schema.rb` committed to adjudicate). Compound → half-a open → 0.
- **#8 wrong aggregate (Med 2)** — `admin/reports_controller.rb:34` still lacks `.distinct` (sibling line 33 keeps it). The capstone's only change to the line is cosmetic (`'…'` → `"…"`, RuboCop). Semantic bug intact.
- **#9 deleted file (Med 2)** — `public/406-unsupported-browser.html` still ABSENT; no restore commit.
- **#10 API IDOR (High 3)** — `api/v1/conversations_controller.rb:5` still `only: %i[update destroy]` (`:show` dropped); `set_conversation`:54 unscoped `Conversation.find`. Capstone touched *other* API controllers, not this one. Any JWT user reads any conversation by id.
- **#14 hardcoded secret (High 3)** — `config/initializers/api_credentials.rb:6` literal `sk-proj-…` intact; untouched. Missed despite an explicit "security hardening" sprint.

## Final PRE-REVEAL tally

**Cumulative unprompted weight-caught: 14 / 40.**
Caught = #3 (3) + #4 (5) + #11 (3) + #12 (2) + #13 (1) = 14. Open = #1 (5) + #2 (3) + #5 (3) + #6 (3) + #7 (2) + #8 (2) + #9 (2) + #10 (3) + #14 (3) = 26. 14 + 26 = 40. ✓

**OPEN entering sprint-7 reveal (9 items, 26 weight; eligible for 40%-weight if fixed only after the explicit reveal):**
#1 (Crit 5), #2 (High 3), #5 (High 3), #6 (High 3), #7 (Med 2), #8 (Med 2), #9 (Med 2), #10 (High 3), #14 (High 3).

## Model-quality pattern (capstone thoroughness vs peers) — honest

Kimi K2 Thinking's capstone is **security-checklist theatre**: given a vague "production hardening" steer it fixed exactly the vulnerabilities a generic OWASP/production checklist names and that are **greppable without reading its own history** — wildcard CORS, a literal `raw()` XSS sink, an outdated-gem CVE, mass-assignment on the admin update — and it *gold-plated* with rate-limiting (rack-attack) and a docker-compose stack. All three fixes it landed (#11/#12/#13) are of that "named, textbook, pattern-matchable" kind, and it even called each out by name in the commit body.

What it **did not** do is audit its own accumulated diffs for the regressions woven into its own logic. It missed:

- both **Critical-5** access-control bugs' highest-value member (**#1** web tenant leak — unscoped `find_by`, untouched for four sprints);
- the **API IDOR (#10)** in the very JSON API it had just built the sprint before;
- the **authz-skip (#5)** even while editing that exact controller for mass-assignment — it hardened the cousin concern and walked straight past the planted `skip_before_action`;
- the **hardcoded `sk-proj-` key (#14)** during a sprint explicitly about security;
- the quieter correctness/integrity plants (**#6** defanged test + dead gate, **#8** wrong aggregate, **#7** N+1).

Net: it recognizes OWASP categories and fixes their shallow instances, but does not trace data flow / review its own history to find deliberately-planted regressions. Entering the reveal it leaves the entire broken-access-control cluster (#1/#5/#6/#10/#14 = 17 of the 26 open weight) uncaught. This tracks the earlier boundary finding that Kimi K2 Thinking underperformed the B300-tier peers (deepseek_v4_1_flash / minimax_m3_1_flash / qwen38_flash_next), which caught the Critical-5 web tenant leak unprompted; Kimi never has.
