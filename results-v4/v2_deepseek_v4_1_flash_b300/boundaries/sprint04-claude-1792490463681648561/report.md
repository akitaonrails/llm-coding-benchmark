# Sprint-4 boundary review — v2_deepseek_v4_1_flash_b300

**Model:** DeepSeek V4.1 Flash (self-hosted 4xB300)
**Boundary:** after sprint 4 (admin reporting dashboard + per-user activity). Grade #4–#6
(injected after sprint 3), inject #7–#9.
**Reviewer:** fresh, isolated v4 boundary reviewer. **Method:** STATIC-ONLY — git log/diff,
grep, file read, `ruby -c`. No docker/db/server/rails/bundle/test execution; tree not reset.
**Author on all injections:** Casey <casey@example.com>.
**Set:** full 14-item / denominator 40 (Tier A; parity with minimax_m3_1_flash + qwen38_flash_next).

---

## Part A — grading #4–#6 (fixes on the model's own initiative in any pre-reveal sprint = full weight)

Sprint 4 produced two Sprinter commits: `32b2d83` (reporting dashboard) and
`d0c6a90` "Harden admin mutations and parameterize user search". The latter addressed ALL
THREE sprint-3 admin injections in a single **unprompted** commit — no sprint prompt disclosed
the injections.

| # | Class | Sev/Wt | Status | Caught | Evidence |
|---|-------|--------|--------|--------|----------|
| 4 | SQL injection (admin user search) | Crit 5 | **UNPROMPTED FIXED** | **5** | `app/models/user.rb:33` now `where("email_address LIKE ? ESCAPE '\\'", "%#{sanitize_sql_like(term)}%")` — injected interpolated literal replaced by a bound `?`. Commit names the Brakeman SQLi. Routed `/admin/users?filters[q]=` intact. |
| 5 | broken authz / IDOR (promote) | High 3 | **UNPROMPTED FIXED** | **3** | injected `skip_before_action :require_admin, only: %i[promote]` removed (grep → none); inherited `Admin::BaseController#require_admin` restored. Added `users_controller_test.rb:28-32` non-admin-promote coverage. Commit: "Restore the admin gate on promotions". |
| 6 | test-integrity + hidden vuln (compound) | High 3 | **UNPROMPTED FIXED (both halves)** | **3** | (a) `admin/users_controller.rb:27` dead-branch `@user.id == params[:id]` → correct `@user == current_user`; (b) `users_controller_test.rb:153-162` gutted `assert true` → real `assert_no_changes active? + redirect + flash` assertion. Compound rule satisfied (both halves). |

**Sprint-4 caught = 11.** **Cumulative after s4 = 8 (prior) + 11 = 19/40.**
Prior boundary (after s3): #1 Crit-5 tenant-leak fixed (5), #2 High-3 login-link OPEN (0),
#3 High-3 puma CVE fixed via real upgrade (3) = 8. Open carry-over: **#2** (login-link nav
regression) remained open through s3.

### Parity note (outcome, not injected-set, differs)
The injected set is identical to the minimax_m3_1_flash and qwen38_flash_next precedents.
Those two peers fixed #4+#5 unprompted but **left the disguised compound #6 at 0** (scoring 8
at this boundary). DeepSeek V4.1 Flash additionally caught #6 (both halves) → **11 here**. That
is a genuine model-quality difference (it even restored the defanged test), not a parity drift.

---

## Part B — injected #7–#9 (after sprint 4; Med 2 each; full 14-item set)

All woven into the model's real sprint-4 code, live-verified statically, disjoint from #1–#6,
suite-green-preserving, no boot break, committed as Casey.

### #7 — N+1 + missing index (Med 2, two halves) — `ca0c05b` + `c0da82e`
- **7a N+1** `app/views/conversations/_conversation.html.erb:9`: `conversation.messages_count`
  (counter_cache column, 0 queries) → `conversation.messages.count` (1 COUNT per row). Live on
  `GET /` and `/conversations` where the sidebar/mobile list renders the partial as a collection
  over `current_user.conversations.recent.limit(100)` → 1+N. The suite's only query-count guard
  (`admin_report_test.rb:163`) is on the AdminReport service, not this view → stays green.
- **7b missing index** new migration `20261020120001_retune_message_indexes.rb`
  (`remove_index :messages, :created_at` + `add_index :messages, [:role, :created_at]`) + synced
  `db/schema.rb` (version `…120001`, `index_messages_on_created_at` → `index_messages_on_role_and_created_at`).
  The dropped bare-created_at index backed `AdminReport#activity` (`admin_report.rb:111`,
  grouped `DATE(created_at)`, no role predicate); a `[role, created_at]` composite cannot serve
  it. `grep -c index_messages_on_created_at db/schema.rb` → 0; control conversation/user
  created_at indexes untouched.

### #8 — silently wrong aggregate (Med 2) — `5519c77`
`app/services/admin_report.rb:11` TOTALS_SQL `admins_count`:
`SUM(CASE WHEN admin THEN 1 ELSE 0 END)` → `SUM(CASE WHEN admin AND active THEN 1 ELSE 0 END)`.
The dashboard Admins card (`admin/dashboard/index.html.erb:31 #total-admins`, GET /admin,
/admin/dashboard, /admin/reports) now under-reports any **deactivated** admin (deactivate! keeps
the role, clears active). Green-but-wrong: the only pins (`admin_report_test.rb:25`,
`dashboard_controller_test.rb:51`) use an ACTIVE admin so the figure stays 1; no test deactivates
an admin and re-checks the total.

### #9 — delete a needed file (Med 2) — `979840f`
Deleted `app/javascript/controllers/chat_controller.js`, still wired by
`conversations/show.html.erb` (`data-controller="chat"`, `chat#usePrompt`) and
`messages/_composer.html.erb` (`chat#submitting/submitted/autogrow/keydown`, `chat_target`).
Eager-loaded by glob (`pin_all_from app/javascript/controllers`) → missing file raises no boot
error; it simply never registers. Silently dead: **Enter-to-send** (advertised in the composer
footer), submit busy-state, textarea autogrow, auto-scroll, and prompt-suggestion fill. Suite
stays green — `chat_flow_test` submits via `click_button "Send"` (never Enter/suggestions), and
every assertion (including the cleared input, `create.turbo_stream.erb:23` re-renders #composer
with `Message.new` server-side) is Turbo/server-driven. Fix = `git restore` (not recreate).

**Running total injected after sprint 4 = 28/40 (#1–#6 = 22, #7–#9 = 6).**

---

## Acceptance gate — all five hold
1. Right path, real code — ✔ (conversation list / activity index / admins card / wired chat controller).
2. Minimal & realistic — ✔ (one ERB line, one migration+schema line, one SQL predicate, one file delete).
3. Boots + happy-path green — ✔ (`ruby -c` clean; value-preserving #7a/#8; no index-presence or
   Enter/busy/scroll assertions in the suite; input clears server-side).
4. Exploit live — ✔ (N+1 fires; index gone from schema; admin undercount; chat JS dead).
5. Severity-matched parity — ✔ (Med2×3 = 6; denominator 40; disjoint; matches both peers).

## Eligibility
`eligible = true`. Parity holds; static-only discipline observed; no candidate-defect repair,
no weight changes, no reset.
