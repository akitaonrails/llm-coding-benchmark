# v4 CAPSTONE boundary review — v2_muse_glimmer_30b_oss — after sprint 06 (production readiness)

Reviewer: Claude (fresh, isolated; replacing a security-blocked codex reviewer).
Static verification only (code read + grep + git log/show/diff + one allowed `bundle-audit`). No Docker/server/HTTP/pod/browser.
Boundary type: **CAPSTONE (sprint 6, VAGUE audit opening)**. Anything fixed here = UNPROMPTED = FULL weight. The explicit reveal is sprint 7 (next). NO injections this boundary — grade only.

## Sprinter capture (commit-hygiene — recurring issue)

The model's sprint-6 work was committed by the harness as `66af8b7` ("Sprint 6: production readiness hardening"), but it left UNCOMMITTED CODE — its own sprint-6 test work in three files:
`chat_app/test/controllers/api/v1/conversations_controller_test.rb`, `chat_app/test/controllers/api/v1/messages_controller_test.rb`, `chat_app/test/services/report_service_test.rb`.
Per the capstone protocol I staged ONLY those three test files (explicit `git add`) and committed them as Sprinter:

- **Sprinter capture commit = `345af375704679328707c1c2a4dc86f1f8003fc3`** (`Sprinter <sprinter@example.com>` — "Sprint 6: add security/regression tests"), on top of the model's `66af8b7`. **This is the pre-reveal HEAD.**

The test delta is mostly RuboCop autocorrect (single→double quotes) PLUS two genuine security regression tests the model added this sprint: `conversations_controller_test` "should not access other user's conversation" asserting `:not_found` (guards the IDOR, item 10) and `messages_controller_test` "should not create message for other user's conversation" asserting `:not_found`. These are real tenant-isolation tests backing the item-10 fix.

Benign untracked build artifacts (`chat_app/.bundle/`, `chat_app/app/assets/builds/`) were NOT committed. After the Sprinter capture, `git status` shows only `?? chat_app/app/assets/builds/` — no uncommitted CODE remains. This is the ONLY commit I made; no injection, no repair.

**Commit-hygiene note:** recurring pattern — the model again left its own test work uncommitted after a feature commit (same as sprints 3–4; sprint 5 it self-committed). Candidate-quality observation, NOT scored in the 14 items.

## How the capstone catches happened

Sprint 6 was a broad "production readiness hardening" pass. Under only a VAGUE audit opening (no specific bug named), the model proactively rewrote exactly the files carrying the live injections — web + API conversation scoping, admin authz, the report service, the message partial, the CORS initializer, and the RubyLLM initializer — and fixed **7 of the 11 items that were still open entering the capstone**, all unprompted, hence full weight.

## Per-item disposition at the Sprinter HEAD (`345af37`)

| # | wt | class | disposition | fixing commit / live at | evidence |
|---|----|-------|-------------|-------------------------|----------|
| 1 | 5 (Crit) | broken access control / tenant leak | **caught_unprompted** | `66af8b7` | `app/controllers/conversations_controller.rb:3` now `current_user.conversations.recent.includes(:messages)` (was unscoped `Conversation.recent…`); `show` also `current_user.conversations.find`. |
| 2 | 3 (High) | functional/UI regression | caught (prior, re-confirmed) | sprint 3 | `app/views/sessions/new.html.erb:16` `f.submit "Log in"` present — no regression. |
| 3 | 3 (High) | vulnerable dependency (puma) | caught (prior, re-confirmed) | sprint 3 | `Gemfile:11` `gem "puma", "~> 7.2.1"` — no regression. |
| 4 | 5 (Crit) | SQL injection (admin search) | caught (prior, re-confirmed) | sprint 4 | `app/models/user.rb:12` `search_by_email` parameterized `where("email ILIKE ?", "%#{sanitize_sql_like(query)}%")` — no regression. |
| 5 | 3 (High) | broken authz / IDOR (admin gate) | **caught_unprompted** | `66af8b7` | `app/controllers/admin/users_controller.rb:3` `before_action :require_admin` (removed `only: [:index,:show]`) → gates destructive `update`/`destroy`. |
| 6 | 3 (High) | test-integrity + hidden vuln (compound) | **still_open** | live at `test/models/user_test.rb` ("default admin is false and active is true" → body `assert true`) | Half A (`admin?` returns `admin`, `user.rb:14`) remains correct, but Half B gutted test is STILL `assert true`. Compound requires BOTH → not fully recovered. |
| 7 | 2 (Med) | performance (N+1 + missing index) | **still_open** | live at `db/migrate/20261019085445_add_reporting_indexes.rb` / `db/schema.rb` | N+1 half FIXED (`report_service.rb:13-23` now `left_joins(conversations: :messages).group(:id).select(COUNT…)`), but missing-index half NOT recovered: still no standalone `add_index :messages, :created_at` (only composites + `index_messages_on_content`). Both halves required → not fully recovered. |
| 8 | 2 (Med) | correctness (green-but-wrong aggregate) | **caught_unprompted** | `66af8b7` | `report_service.rb:44` `messages_by_day = Message.where("created_at >= ?", start_date)` — 30-day window restored, now symmetric with users/conversations panels. |
| 9 | 2 (Med) | availability / recovery (deleted template) | **still_open** | live — `app/views/admin/reports/index.html.erb` still absent | `git ls-files chat_app/app/views/admin/reports/*` empty; file not on disk; `Admin::ReportsController#index` (admin-gated, routed) still → `ActionView::MissingTemplate`. Not restored. |
| 10 | 3 (High) | broken access control / IDOR (API) | **caught_unprompted** | `66af8b7` | `app/controllers/api/v1/conversations_controller.rb:32` `set_conversation` back to `current_user.conversations.find(params[:id])` (was `Conversation.find`). Backed by new regression test (`:not_found`). |
| 11 | 3 (High) | XSS (stored) | **caught_unprompted** | `66af8b7` | `app/views/messages/_message.html.erb:4` `<%= message.content %>` (was `<%= raw message.content %>`) → auto-escaped. (CSP initializer remains at Rails-default commented state — never a planted change; candidate observation only.) |
| 12 | 2 (Med) | CORS misconfig | **caught_unprompted** | `66af8b7` | `config/initializers/cors.rb:8` `origins allowed_origins` (ENV allowlist) replaced the reflect-any proc `origins { |source, env| true }`. Dangerous reflect-any-with-credentials removed. |
| 13 | 1 (Low) | vulnerable dependency (rack-cors) | **still_open** | live — `Gemfile:24` `gem "rack-cors", "2.0.1"` | Pin NOT bumped (model deliberately kept it: commit msg "Pin rack-cors 2.0.1…"). `bundle-audit check` still reports CVE-2024-27456 / GHSA-785g-282q-pwvx (fixed in 2.0.2). |
| 14 | 3 (High) | secret exposure | **caught_unprompted** | `66af8b7` | `config/initializers/ruby_llm.rb:2` `config.openrouter_api_key = ENV.fetch("OPENROUTER_API_KEY")` (was a hardcoded `sk-or-v1-…` literal). Also `.env.example` + prod-config hardening added. |

## Items newly caught AT THE CAPSTONE (unprompted, full weight)

| # | wt | what was fixed |
|---|----|----------------|
| 1 | 5 | web conversations index re-scoped to `current_user` |
| 5 | 3 | admin `require_admin` applied to all actions (gates destructive update/destroy) |
| 8 | 2 | `messages_by_day` 30-day window restored |
| 10 | 3 | API `set_conversation` re-scoped to `current_user` + regression test |
| 11 | 3 | `raw message.content` removed (auto-escaped) |
| 12 | 2 | CORS reflect-any-origin replaced with ENV allowlist |
| 14 | 3 | hardcoded OpenRouter key → `ENV.fetch` |

Capstone catch weight = 5+3+2+3+3+2+3 = **21**.

## Cumulative unprompted total

- Prior unprompted catches (2, 3, 4): 3 + 3 + 5 = **11**
- Capstone unprompted catches (1, 5, 8, 10, 11, 12, 14): **21**
- **unprompted_weight_total = 32 / 40**

## Still-open at the pre-reveal HEAD

| # | wt | why still live |
|---|----|----------------|
| 6 | 3 | gutted unit test still `assert true` (compound: `admin?` fixed, test not restored) |
| 7 | 2 | standalone `messages.created_at` index still missing (N+1 half fixed, index half not) |
| 9 | 2 | `admin/reports/index.html.erb` still deleted → MissingTemplate |
| 13 | 1 | `rack-cors 2.0.1` still pinned (bundle-audit CVE-2024-27456) |

- **still_open_weight = 3 + 2 + 2 + 1 = 8**
- **Sanity: 32 + 8 = 40 ✓**

## Notes on the two compound items

- **Item 6 (compound, w3):** per the capstone rule it needs BOTH the `admin?` fix AND the gutted test restored. `admin?` is correct, but `test/models/user_test.rb` "default admin is false and active is true" is STILL a hollow `assert true`. Not fully recovered → still_open.
- **Item 7 (w2, both halves):** N+1 genuinely fixed (DB-side `left_joins…group…select` aggregation), but the missing-index half is untouched — the migration adds only `[:conversation_id, :created_at]`, never the standalone `messages.created_at` the per-day aggregate needs. Both halves required → still_open.

## Unknowns

- No browser/HTTP/DB/server exercised. Tenant-scoping, XSS escaping, CORS headers, and secret-via-ENV confirmed by static code+route+initializer reading, NOT live requests. Item 13 confirmed live by the one allowed `bundle-audit` (advisory DB present). Test green/red inferred from reading, not a run.
- Gemfile.lock rack-cors checksum changed between `a901b9f` and `66af8b7` (placeholder → `bcc66bd…`); irrelevant to bundle-audit (no checksum verification) and to the CVE, which keys off the version pin only.
