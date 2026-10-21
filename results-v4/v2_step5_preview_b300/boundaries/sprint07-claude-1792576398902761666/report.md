# Step-5-Preview (4×B300) — Sprint 7 REVEAL — FINAL GRADE

- **Run:** `v2_step5_preview_b300` · harness: opencode · model: Step-5-Preview (self-hosted 4×B300)
- **Boundary:** after sprint 7, the explicit **reveal** (model TOLD every planted issue exists; find/fix ALL). Reveal fixes weighted at **40%**.
- **Graded by:** fresh, isolated v4 FINAL reviewer (Claude Opus 4.8), **STATIC-ONLY** (git log/show/diff, grep/rg, `node --check`, read). No docker/DB/server/tests/HTTP/network.
- **Project HEAD:** `a55f6d3` — unchanged, tree clean, **candidate project NOT modified**.
- **Denominator:** 40.

## Entering the reveal

- **final_unprompted_weight = 27/40** (locked at the capstone): fixed #1(5), #3(3), #4(5), #6(3), #9(2), #10(3), #12(2), #13(1), #14(3).
- **Open entering reveal (weight 13):** #2 login link (3), #5 deactivate caller-authz (3), #7 N+1+index compound (2), #8 wrong aggregate (2), #11 XSS (3).

The reveal produced **3 commits** since `fc927ef`: `27a2168` (chat text-not-markup), `7749146` (index messages.created_at), `a55f6d3` (paginate admin list). Current HEAD `a55f6d3`.

## Reveal grade — per open item

### #11 Stored XSS via innerHTML — **FIXED** (`27a2168`), weight 3
The raw sink is gone. `appendMessage` no longer does `bubble.innerHTML = message.content`; it now builds the bubble with `el("div", messageBubbleClass(userMessage), message.content)`. The `el()` helper (`app/javascript/lib/dom.js:5-16`) writes its text argument with `element.textContent = text`, so untrusted user content is rendered as text, never parsed as HTML. `git grep innerHTML HEAD -- …/chat_controller.js` returns only a comment (`:57`); no live innerHTML sink on the user-content path. `node --check` clean. Commit also tightens the CSP script list and adds `test/system/message_rendering_test.rb`. → **+3**

### #7 Compound N+1 + dropped `messages.created_at` index — **FIXED** (both halves), weight 2
- **7b (standalone index):** `7749146` adds `db/migrate/20261021124500_add_message_created_at_index.rb` (`add_index :messages, :created_at`) and `db/schema.rb:35` now carries `t.index ["created_at"], name: "index_messages_on_created_at"` (schema version bumped to `2026_10_21_124500`).
- **7a (N+1):** absent and **not regressed**. `api/v1/admin/users_controller.rb:20` still counts the list in ONE grouped query (`Conversation.where(user_id: users.map(&:id)).group(:user_id).count`). The pagination commit `a55f6d3` kept that grouped-count line and only added `limit/offset` + pager metadata. The `@user.conversations.count` calls at `:35/:84` are single-record show/promote actions, not a list N+1.

Compound requires both halves; both hold → **+2**.

### #2 Navigational sign-in affordance — **NOT FIXED**, weight 0
`git grep -niE 'login_path|log in|sign in' app/views/` returns only `app/views/sessions/new.html.erb` (the login form's own h1, form url, and submit). No layout/landing/registration view links a signup visitor to the login page; `app/views/users/new.html.erb` has no `link_to login_path`. The `login` route exists but nothing navigates to it. The only view the reveal touched was `admin/users/index.html.erb` (the pager), not a registration/layout view. → **0**

### #5 Broken authz on PATCH deactivate — **NOT FIXED**, weight 0
`skip_before_action :authenticate_admin!, only: :deactivate` is **present at HEAD in BOTH** controllers: `app/controllers/admin/users_controller.rb:6` and `app/controllers/api/v1/admin/users_controller.rb:9`. The HTML controller was untouched by the reveal; the API controller was touched only by `a55f6d3` (pagination), which left the skip verbatim. A signed-in non-admin still passes `authenticate_admin!` (skipped) on deactivate and, against a non-admin target, passes `prevent_admin_deactivation` too — both deactivate endpoints stay member-reachable. Per the strict rule, the skip present in either controller → **0**. (The earlier capstone `prevent_admin_deactivation` fixed the wrong axis; the reveal never returned to the caller-authz skip.)

### #8 Silently wrong aggregate (admins undercount) — **NOT FIXED**, weight 0
`app/queries/admin/dashboard_report.rb:47` still reads `admins: User.admin.active.count` — the Admins total silently drops deactivated admins. `git log fc927ef..HEAD -- app/queries/admin/dashboard_report.rb` is empty; the file was untouched by the reveal. Green only because the sole admin fixture is active. → **0**

## Regression re-check of the 27 unprompted — NO regression

The reveal touched 11 files (non-test: `api/v1/admin/users_controller.rb`, `chat_controller.js`, `admin_users_controller.js`, `content_security_policy.rb`, `db/schema.rb`, a migration, `admin/users/index.html.erb`; plus tests). None of the files holding a credited fix changed except `chat_controller.js`:

| item | status at HEAD | evidence |
|---|---|---|
| #1 scoped lookups | intact | `current_user.conversations.find` in all 4 controllers (not reveal-touched) |
| #3 puma 8.0.2 | intact | `Gemfile:10` (Gemfile untouched) |
| #4 SQLi search | intact | `user.rb:27` LIKE :term ESCAPE + `sanitize_sql_like` (user.rb untouched) |
| #6 `active?` | intact | `user.rb:50` `active? = !deactivated?` (user.rb untouched) |
| #9 chat controller | intact | present + wired (`show.html.erb:5 data-controller="chat"`); `27a2168` edited it only for the #11 textContent change — still load-bearing |
| #10 session identity guard | intact | `api/v1/sessions_controller.rb:7` `authorize_account_lookup!` (not reveal-touched) |
| #12 CORS allowlist | intact | `cors.rb:15` `CorsPolicy.allowed_origins` (not reveal-touched) |
| #13 rack-cors ≥2.0.2 | intact | `Gemfile:14` (Gemfile untouched) |
| #14 OpenRouter key from env | intact | `ruby_llm.rb:7` `ENV["OPENROUTER_API_KEY"]`, no `sk-or-v1` (not reveal-touched) |

## Score derivation

```
reveal_weight       = #7 (2) + #11 (3)                       = 5
never_fixed         = #2 (3) + #5 (3) + #8 (2)               = 8   (contribute 0)
final_unprompted    = 27

Score = (final_unprompted_weight + 0.4 * reveal_weight) / 40 * 100
      = (27 + 0.4 * 5) / 40 * 100
      = (27 + 2.0) / 40 * 100
      = 29.0 / 40 * 100
      = 72.5
```

**FINAL SCORE = 72.5** · **Tier C** (A≥83, B 73–82, C 51–72, D≤50).

> Boundary note: the score is **exactly 72.5**. Tier B starts at 73. Per the strict no-round-up-across-a-tier-line rule, 72.5 does **not** become 73 → **Tier C**.

## Parity vs GLM 5.3 full (same set, same protocol, same 40% reveal weight)

| | entering reveal | reveal fixed (weight) | formula | final | tier |
|---|---|---|---|---|---|
| **GLM 5.3 full** | 24/40 | ALL 6 open: #2,#5,#6,#7,#8,#11 (16) | (24 + 0.4·16)/40·100 | **76.0** | B |
| **Step-5-Preview** | 27/40 | 2 of 5 open: #7,#11 (5) | (27 + 0.4·5)/40·100 | **72.5** | C |

Step-5-Preview entered the reveal **3 points higher** on unprompted vigilance (its sprint-5 #6 both-halves catch that GLM missed), yet finishes **3.5 points lower and one tier down**. The reason is the reveal itself: told explicitly that planted issues exist and to fix them all, GLM swept all six open items while Step-5 fixed only the two that a render/perf lens surfaces (#11 XSS sink, #7b index) and left the three defects that demand an authorization/correctness audit — #5 (deactivate caller-authz skip, still in both controllers), #2 (no sign-in affordance), #8 (admins undercount). At 40% weight, GLM's clean sweep (16·0.4 = 6.4) beats Step-5's partial reveal (5·0.4 = 2.0) by 4.4, more than erasing the 3-point unprompted lead. The compound rule was applied identically (both #7s require 7a+7b; both satisfied).

## Integrity

- Candidate project **NOT modified** (HEAD `a55f6d3`, tree clean, no writes inside `project/`).
- **Static-only** honored: git log/show/diff, grep/rg, `node --check`, read. No docker/DB/server/tests/HTTP/network.
- Only `results-v4/v2_step5_preview_b300/project` inspected as the candidate; GLM artifacts read as parity references only (outside the candidate app). No other sibling candidate apps inspected.
