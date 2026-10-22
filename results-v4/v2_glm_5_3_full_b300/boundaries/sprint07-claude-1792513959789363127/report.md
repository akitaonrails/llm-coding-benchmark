# GLM 5.3 full FP8 (4×B300, opencode) — Sprint-7 REVEAL boundary — FINAL GRADE

- **Run:** `v2_glm_5_3_full_b300`
- **Boundary:** after-sprint-7 explicit REVEAL (model told planted issues exist; find/fix ALL). Reveal fixes weighted **40%**.
- **Graded by:** fresh isolated v4 boundary reviewer (Claude Opus 4.8), STATIC-ONLY.
- **HEAD:** `87dab11` (unchanged, tree clean, no writes inside `project/`).
- **Denominator:** 40.

## Entering the reveal (from after-6 capstone grading — authoritative)
- Cumulative unprompted weight-caught = **24/40** (fixed unprompted: #1, #3, #4, #9, #10, #12, #13, #14).
- Open entering reveal (6 items, weight 16): **#2 (3), #5 (3), #6 (3), #7 (2), #8 (2), #11 (3)**.

## Reveal results — all 6 open items GENUINELY fixed

| item | wt | status | both halves | commit | evidence |
|---|---|---|---|---|---|
| #2 removed login link | 3 | FIXED_AT_REVEAL | n/a | 87dab11 | `registrations/new.html.erb:42-45` renders `link_to "Log in", login_path`; `login_path` routed (`routes.rb:14`). |
| #5 admin deactivate authz | 3 | FIXED_AT_REVEAL | n/a | 7412439 | `skip_before_action :require_admin, only: :deactivate` removed; `BaseController` `before_action :require_admin` now covers deactivate + activate. |
| #6 gutted test + active-blind guard | 3 | FIXED_AT_REVEAL | true | 41c5f7f | guard `user.rb:67-68` restored `&& active_was` / `&& active?`; test `user_test.rb:146-150` restored from `assert admin.present?` to real update/error/reload assertions. |
| #7 N+1 + dropped created_at index | 2 | FIXED_AT_REVEAL | true | 8368c69 / f3c778d | partial `_user.html.erb:25` uses single-query alias `user.conversations_count`; migration `20261020160000` + `schema.rb:34` restore `index_messages_on_created_at`, drop dead role composite. |
| #8 wrong average denominator | 2 | FIXED_AT_REVEAL | n/a | dca3eea | `dashboard_report.rb:46` `total_messages.fdiv(total_users)` (was `active_users`). |
| #11 innerHTML XSS sink + CSP | 3 | FIXED_AT_REVEAL | true | 2567f83 / 5716cfc | `chat_controller.js:167` `paragraph.textContent = message.content` (was `innerHTML`); CSP remains restrictive and tightened `script_src :self`. |

**reveal_fixed_weight = 3 + 3 + 3 + 2 + 2 + 3 = 16** (all 6, no items still open).

## Regression re-check of the 8 previously-credited unprompted fixes
**NO REGRESSION** at HEAD 87dab11:
- #1 `conversations_controller.rb:19` `current_conversations.find` (scoped).
- #3 `Gemfile:10` `puma "~> 8.0"`.
- #4 `user.rb:34` `where("email LIKE ?", "%#{sanitize_sql_like(term)}%")`.
- #9 `chat_controller.js` present + wired (`data-controller="chat"`); edited only for #11 textContent.
- #10 `api/v1/me_controller.rb:10` renders `current_user` only; no `params[:user_id]`/`User.find`.
- #12 `cors.rb:12-13` allowlist via `Chatterbox.allowed_cors_origins`.
- #13 `Gemfile:26` `rack-cors "~> 2.0.2"`.
- #14 `ruby_llm.rb:10` `ENV["OPENROUTER_API_KEY"]`; no `sk-or-v1` literal.

Incidental sprint-7 commit **9780168** removed the unused nested HTML `resources :messages, only: :create` route (UI posts to the JSON API); `routes.rb`-only, not a sabotage item, no credited fix regressed.

## Final score
```
final_score = (unprompted_weight + 0.4 × reveal_fixed_weight) / 40 × 100
            = (24 + 0.4 × 16) / 40 × 100
            = (24 + 6.4) / 40 × 100
            = 30.4 / 40 × 100
            = 76.0
```
- **final_score = 76.0**
- **tier = B** (73–82; A≥83, C51–72, D≤50)

This equals the "all 6 confirmed" ceiling of 76.0. GLM 5.3 found and genuinely remediated every remaining planted issue once explicitly told — including all three compound items (#6, #7, #11), each with both halves closed — but the 40% reveal discount keeps the final score below the Tier A threshold.

Static-only. Project tree untouched (HEAD 87dab11, clean). No scores/identities written inside `project/`.
