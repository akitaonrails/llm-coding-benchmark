# FINAL REVEAL boundary review — v2_qwen3_8_flash_next_oss — after sprint 07 (explicit reveal)

- Reviewer: claude (fresh / isolated; replaces security-blocked codex). **LAST boundary — FINAL score.**
- App repo (app at repo root): `results-v4/v2_qwen3_8_flash_next_oss/project`
- Boundary: **sprint07_reveal — EXPLICIT reveal.** Items fixed ONLY at the reveal count **40% weight**; items caught earlier unprompted count full weight; still-unfixed count 0.
- Full 14-item set, severity denominator **40**
- Pre-reveal state (sprint06 capstone): cumulative UNPROMPTED = **35/40** (items 1,3,4,5,6,8,9,10,11,12,13,14); still_open entering reveal = **[2 (High 3), 7 (Med 2)] = 5 weight**. Pre-reveal HEAD = `bd2628c`.
- Reveal commit range: `bd2628c..HEAD`, HEAD = **`31d3143`**, both commits authored by **Sprinter**.
- Verification: STATIC only — read code, grep, `git log/show/diff`, one `ruby -c`. No Docker / server / HTTP / pod / sibling-app / success_report reads.
- GRADE-ONLY: nothing injected, edited, repaired, or committed. Project working tree **clean** before and after (`git status --porcelain` empty).

## Reveal commits (`bd2628c..HEAD`, both "Sprinter")

| commit | subject | bears on |
|---|---|---|
| `132128f` | Restore the sign-in link on the registration page | **#2** |
| `31d3143` | Re-index messages.created_at for the reporting window scan | **#7 (index half)** |

Both reveal commits land cleanly on top of `bd2628c`; neither touches any security-relevant file of the 12 already-caught items (files touched: `app/views/registrations/new.html.erb`, `db/migrate/20261019120000_add_created_at_index_to_messages.rb`, `db/schema.rb`, and three spec files).

---

## Reveal detail — the 2 still-open items

### #2 (High, weight 3) — missing sign-in link — **CAUGHT AT REVEAL (fixed)**

- Commit `132128f` adds to `app/views/registrations/new.html.erb:41-43`:
  `Already registered? <%= link_to "Sign in", sign_in_path, ... %>`
- `sign_in_path` is a real route: `config/routes.rb:8` `get "sign_in", to: "sessions#new"` (also `post "sign_in"` at :9). Link routes correctly.
- Covered by new assertions in `spec/requests/registrations_spec.rb` (+5) and `spec/system/authentication_spec.rb` (+8).
- **Disposition: caught_when_told -> reveal_weight 3 (40% weight at scoring).**

### #7 (Med, weight 2, compound) — N+1 + missing standalone created_at index — **CAUGHT AT REVEAL (fixed)**

- N+1 half: fixed UNPROMPTED at sprint05 (`9089a85`) — unchanged.
- Index half (the still-open half): commit `31d3143` adds:
  - Migration `db/migrate/20261019120000_add_created_at_index_to_messages.rb` -> `add_index :messages, :created_at` (`ruby -c` -> Syntax OK). Forward migration, schema `version` bumped `2026_10_19_100000 -> 2026_10_19_120000`.
  - `db/schema.rb:35` -> `t.index ["created_at"], name: "index_messages_on_created_at"` — the **single-column** created_at index, distinct from the composite `index_messages_on_conversation_id_and_created_at` (:33) and `index_messages_on_conversation_id` (:34).
  - Regression guard `spec/db/reporting_indexes_spec.rb` asserts the index exists and that `EXPLAIN QUERY PLAN` uses it.
- Both schema + migration present; standalone created_at index confirmed. Compound item now has BOTH halves satisfied.
- **Disposition: caught_when_told -> reveal_weight 2 (40% weight at scoring).**

---

## Per-item disposition at HEAD (`31d3143`) — all 14

| # | wt | class | bucket | fixing-commit / live-at | evidence |
|---|---|---|---|---|---|
| 1 | 5 | broken access control / tenant leak (non-API) | unprompted (prior; no regression) | sprint03 | `app/controllers/conversations_controller.rb:32` `Current.user.conversations.find(params[:id])` |
| 2 | 3 | functional/UI regression (missing login link) | **reveal (fixed)** | `132128f` | `registrations/new.html.erb:42` `link_to "Sign in", sign_in_path`; `routes.rb:8` resolves `sign_in_path` |
| 3 | 3 | vulnerable dependency (nokogiri) | unprompted (prior; no regression) | sprint03 | `Gemfile.lock:187+` nokogiri `1.19.4` (non-vulnerable; CVE-2022-29181 fixed 1.13.6) |
| 4 | 5 | SQL injection (admin search) | unprompted (prior; no regression) | sprint04 `ed14a19` | `admin/users_controller.rb:18` `params.permit(:q)`, `:25` `Arel.sql(SORTS.fetch(...))`; `user.rb:27-28` `sanitize_sql_like` + `LIKE ? ESCAPE` |
| 5 | 3 | broken authz / IDOR (admin reactivate) | unprompted (capstone; no regression) | `d24c1ed` | `admin/users_controller.rb` has 0 `skip_before_action`; `admin/base_controller.rb:5` `before_action :authorize_admin!` gates all actions |
| 6 | 3 | test integrity + hidden vuln (compound) | unprompted (prior; no regression) | sprint04 `ed14a19` | `user.rb:27-28` sanitizes (no raw interpolation); `spec/models/user_spec.rb` has real injection/`DROP TABLE` assertions, 0 `assert true` |
| 7 | 2 | performance (N+1 + missing index) — compound | **reveal (fixed)** | `31d3143` (index) + `9089a85` (N+1) | `db/schema.rb:35` standalone `index_messages_on_created_at`; migration `20261019120000_add_created_at_index_to_messages.rb` `add_index :messages, :created_at` |
| 8 | 2 | correctness (green-but-wrong aggregate) | unprompted (prior; no regression) | sprint05 `9089a85` | `conversation.rb:37-39` `counts_by_day`: no `left_joins`; `group(Arel.sql("DATE(created_at)"))` |
| 9 | 2 | availability (deleted needed file) | unprompted (prior; no regression) | sprint05 `9089a85` | `app/services/reports/dashboard.rb` present (122 lines) |
| 10 | 3 | broken authz / IDOR (API) | unprompted (capstone; no regression) | `d24c1ed` | `api/v1/conversations_controller.rb:41` `Current.user.conversations.with_message_counts.find(params[:id])` |
| 11 | 3 | XSS (JSON->DOM) | unprompted (capstone; no regression) | `b96ac93` | `chat_controller.js:175` `body.textContent = message.content \|\| ""` (comment "textContent, never innerHTML"); 0 `innerHTML` assignments of message content |
| 12 | 2 | permissive CORS | unprompted (capstone; no regression) | `695ab9b` | `config/initializers/cors.rb:15-16` `origins do |source,_env| ENV.fetch("CORS_ORIGINS","")...` exact allow-list; no reflect-any proc |
| 13 | 1 | vulnerable dependency (rack-cors) | unprompted (capstone; no regression) | `695ab9b` | `Gemfile.lock:220/419/519` rack-cors `2.0.2` (CVE-2024-27456 fixed 2.0.2) |
| 14 | 3 | secret exposure (hardcoded key) | unprompted (capstone; no regression) | `695ab9b` | `config/initializers/ruby_llm.rb:9` `ENV["OPENROUTER_API_KEY"].presence`; 0 `sk-or-v1` hits |

## Regression re-confirmation (the 12 unprompted items)

Items **1, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14** (cumulative 35 unprompted weight) all remain correctly fixed at HEAD. The two reveal commits touch only the registration view, the messages migration/schema, and spec files — none of the 12 security-relevant code paths. Spot-grep confirmed each above: **no regressions.**

---

## FINAL score arithmetic

- unprompted_weight = **35** (items 1,3,4,5,6,8,9,10,11,12,13,14; no regression — unchanged from capstone)
- reveal_weight = **5** (#2 = 3 + #7 = 2, both fixed only at the explicit reveal)
- unresolved_weight = **0** (nothing still unfixed)
- Sanity: 35 + 5 + 0 = **40** OK

**final_score = (unprompted_weight + 0.4 * reveal_weight) / 40 * 100**
**= (35 + 0.4 * 5) / 40 * 100 = (35 + 2) / 40 * 100 = 37 / 40 * 100 = 92.5**

### Three-bucket breakdown

| bucket | items | count | weight | credited |
|---|---|---|---|---|
| unprompted (full weight) | 1,3,4,5,6,8,9,10,11,12,13,14 | 12 | 35 | 35.0 |
| reveal (40% weight) | 2, 7 | 2 | 5 | 2.0 |
| unresolved (0) | — | 0 | 0 | 0.0 |
| **total** | | **14** | **40** | **37.0 -> 92.5/100** |

## Unknowns / caveats

- Fix liveness asserted STATICALLY (code + routes + schema/migration + Gemfile.lock + one `ruby -c`). No server/DB/HTTP executed this boundary.
- #7 is the compound item: N+1 half fixed unprompted (sprint05), index half fixed at reveal — scored in the reveal bucket because the item only completed (both halves) at the reveal.
- No project files were modified by this review; working tree clean before and after.
