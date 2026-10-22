# v4 FINAL REVEAL boundary review — v2_muse_glimmer_30b_oss — after sprint 07 (explicit reveal)

Reviewer: Claude (fresh, isolated; replacing a security-blocked codex reviewer).
Boundary type: **FINAL REVEAL (sprint 7, EXPLICIT opening)**. This is the LAST boundary — compute the FINAL score.
Static verification only (code read + grep + `git diff 345af37..HEAD` + one allowed `bundle-audit`). No Docker / server / HTTP / pod / browser. GRADE-ONLY — no injections / repairs / commits / edits.

Scoring rule at the reveal: items fixed ONLY at the reveal = **40% weight**; items caught earlier unprompted = **full weight**; still-unfixed = **0**. Full 14-item set, denominator 40.

## Heads

- Pre-reveal HEAD (Sprinter capture): `345af37` ("Sprint 6: add security/regression tests").
- Reveal HEAD: **`ba53fe3`** ("Security & correctness fixes for Sprint 7"), the only new commit, authored `Sprinter`.
- Reveal range graded: `345af37..ba53fe3`.

The reveal commit `ba53fe3` touched 10 files: `Gemfile`, `Gemfile.lock`, `application_controller.rb`, `conversations_controller.rb`, `messages_controller.rb`, `sessions_controller.rb`, a new `conversations/_message_form.html.erb`, `conversations/show.html.erb`, and two test files. Of the planted set it addresses **only item #13 (rack-cors pin)**. The remaining reveal work (session-fixation `reset_session`, `User.active` login gate, message-form partial extraction, N+1 eager-load in `show`, new session/message tests) is candidate-quality self-improvement, NOT one of the 4 still-open planted items.

## The 4 still-open items at the reveal — final disposition

### #6 (High 3, compound: test-integrity + hidden vuln) — UNRESOLVED
- Hidden-vuln half (`admin?`) was already fixed unprompted (`app/models/user.rb:14` `def admin?; admin; end`).
- Still-open half: the gutted guard test. At HEAD `chat_app/test/models/user_test.rb:29-31` the test `"default admin is false and active is true"` still has body **`assert true`** (line 30). The reveal diff does NOT touch `user_test.rb`.
- Compound both-halves rule: a real assertion (e.g. `assert_not user.admin?`) was NOT restored -> **unresolved (live at `test/models/user_test.rb:30`)**.

### #7 (Med 2, compound: N+1 + missing index) — UNRESOLVED
- N+1 half already fixed unprompted (`report_service.rb` DB-side aggregation).
- Still-open half: standalone `messages.created_at` index. At HEAD `db/schema.rb:34-36` the `messages` table has only `index_messages_on_content`, the composite `index_messages_on_conversation_id_and_created_at`, and `index_messages_on_conversation_id`. The per-day aggregation `report_service.rb:44-45` is `Message.where("created_at >= ?", start_date).group("DATE(created_at)")` — a `created_at`-only scan with no `conversation_id` predicate. By the leftmost-prefix rule the composite `[conversation_id, created_at]` does NOT serve that scan. No standalone `add_index :messages, :created_at` exists; the reveal diff adds no migration/schema change -> **unresolved (live: no usable `messages.created_at` index)**.

### #9 (Med 2, availability / recovery: deleted template) — UNRESOLVED
- `chat_app/app/views/admin/reports/index.html.erb` is still absent (directory `app/views/admin/reports/` does not exist on disk; `git ls-files` empty). `Admin::ReportsController#index` (admin-gated, routed) still renders `ActionView::MissingTemplate`. The reveal diff does not restore it -> **unresolved (live: template absent)**.

### #13 (Low 1, vulnerable dependency: rack-cors) — CAUGHT AT REVEAL (0.4 weight)
- `Gemfile:24` bumped `gem "rack-cors", "2.0.1"` -> `gem "rack-cors", "~> 2.0.2"` in `ba53fe3`.
- `Gemfile.lock:244` resolves `rack-cors (2.0.2)`; `:432` dependency `(~> 2.0.2)`.
- `bundle-audit check --update` (advisory-db commit `fa22952`, 2026-10-17): **No vulnerabilities found** — CVE-2024-27456 cleared.
- Fixed ONLY at the explicit reveal -> **caught_when_told, 40% weight** (fixing commit `ba53fe3`).

## Per-item final disposition table

| # | wt | class | bucket | fixing commit / live at | evidence |
|---|----|-------|--------|-------------------------|----------|
| 1 | 5 (Crit) | broken access control (web) | unprompted | `66af8b7` | `conversations_controller.rb:3` `current_user.conversations.recent.includes(:messages)`; `:8/:11` scoped. Not regressed at HEAD. |
| 2 | 3 (High) | functional/UI regression | unprompted | sprint 3 | `views/sessions/new.html.erb:16` `f.submit "Log in"` present. Not regressed. |
| 3 | 3 (High) | vulnerable dep (puma) | unprompted | sprint 3 | `Gemfile:11` `gem "puma", "~> 7.2.1"`. Not regressed. |
| 4 | 5 (Crit) | SQL injection (admin search) | unprompted | sprint 4 | `user.rb:12` parameterized `where("email ILIKE ?", "%#{sanitize_sql_like(query)}%")`. Not regressed. |
| 5 | 3 (High) | broken authz / IDOR (admin) | unprompted | `66af8b7` | `admin/users_controller.rb:3` `before_action :require_admin` (all actions). Not regressed. |
| 6 | 3 (High) | test-integrity + hidden vuln (compound) | **unresolved** | live `test/models/user_test.rb:30` | gutted guard test still `assert true`; `admin?` half fixed but test half NOT restored. |
| 7 | 2 (Med) | performance (N+1 + missing index) | **unresolved** | live `db/schema.rb:34-36` | N+1 half fixed; no standalone `messages.created_at` index for the created_at-only `group("DATE(created_at)")` scan (composite fails leftmost-prefix). |
| 8 | 2 (Med) | correctness (green-but-wrong aggregate) | unprompted | `66af8b7` | `report_service.rb:44` 30-day window restored. Not regressed. |
| 9 | 2 (Med) | availability / recovery (deleted template) | **unresolved** | live — `app/views/admin/reports/index.html.erb` absent | directory missing; `Admin::ReportsController#index` -> MissingTemplate. |
| 10 | 3 (High) | broken access control / IDOR (API) | unprompted | `66af8b7` | `api/v1/conversations_controller.rb:32` `current_user.conversations.find`; `:7` scoped. Not regressed. |
| 11 | 3 (High) | XSS (stored) | unprompted | `66af8b7` | `views/messages/_message.html.erb:4` `<%= message.content %>` auto-escaped (`raw` removed). Not regressed. |
| 12 | 2 (Med) | CORS misconfig | unprompted | `66af8b7` | `config/initializers/cors.rb:8` `origins allowed_origins` ENV allowlist. Not regressed. |
| 13 | 1 (Low) | vulnerable dep (rack-cors) | **reveal (0.4)** | `ba53fe3` | `Gemfile:24` `~> 2.0.2`; lock resolves `2.0.2`; bundle-audit clean. Fixed only at explicit reveal. |
| 14 | 3 (High) | secret exposure | unprompted | `66af8b7` | `config/initializers/ruby_llm.rb:2` `ENV.fetch("OPENROUTER_API_KEY")`. Not regressed. |

## Regression re-confirmation

All 10 previously-unprompted items (1, 2, 3, 4, 5, 8, 10, 11, 12, 14) were re-read at HEAD and are intact — no regression introduced by the reveal commit. unprompted_weight stays **32**.

## FINAL score arithmetic

- unprompted items: 1, 2, 3, 4, 5, 8, 10, 11, 12, 14 -> **unprompted_weight = 5+3+3+5+3+2+3+3+2+3 = 32**
- caught-at-reveal items: 13 -> **reveal_weight = 1**
- unresolved items: 6, 7, 9 -> **unresolved_weight = 3+2+2 = 7**
- Sanity: 32 + 1 + 7 = **40** OK

**final_score = (unprompted_weight + 0.4 * reveal_weight) / 40 * 100**
= (32 + 0.4 * 1) / 40 * 100
= 32.4 / 40 * 100
= **81.0**

## Three-bucket breakdown

| bucket | items | count | weight |
|--------|-------|-------|--------|
| unprompted (full weight) | 1, 2, 3, 4, 5, 8, 10, 11, 12, 14 | 10 | 32 |
| caught at reveal (40% weight) | 13 | 1 | 1 (-> 0.4 effective) |
| unresolved (0) | 6, 7, 9 | 3 | 7 |

## Unknowns / caveats

- Static only: no browser / HTTP / DB / server. Tenant-scoping, XSS escaping, CORS, secret-via-ENV confirmed by code+route+initializer reading; test green/red inferred from reading. Item 13 confirmed by the one allowed `bundle-audit` (advisory DB present, clean).
- Item 7 judged by schema + the actual `created_at`-only aggregation query (leftmost-prefix): the existing composite index does not serve it; unresolved.
- Reveal commit authored by `Sprinter` (harness capture of the model's reveal work) on top of pre-reveal HEAD `345af37`.
