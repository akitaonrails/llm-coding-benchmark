# Genesys PI House — Sprint-4 boundary + post-S4 injections (#7,#8,#9)

## S4 outcome (model built reports; did not self-commit → snapshot `ccbbf5e`)
House FIXED **#1,#2,#3,#4 unprompted** during S4 (in its uncommitted work):
- #1 tenant leak → `current_conversations.find(params[:id])` restored (C5)
- #2 login submit → `form.submit "Log in"` re-added (H3)
- #3 nokogiri → `>= 1.19.4` (bumped off the CVE 1.15.7) (H3)
- #4 admin SQLi → parameterized `ILIKE ?` restored (C5)
Latent (NOT fixed): #5 authz-skip, #6 email-defang.
Running unprompted: **16** (#1=5,#2=3,#3=3,#4=5).

## Post-S4 injections (#7,#8,#9) — Casey, isolated, `ruby -c` OK
| # | sabotage | class | sev | target | commit |
|---|----------|-------|:---:|--------|--------|
| 7a | N+1 | perf | **M1** | `Admin::Report#users`: single `left_joins.group.select` → per-user loop (`User.order.each` + per-user `conversations.count` / `Message.joins(:conversation)...count`/`maximum`, exposed via singleton methods so the view's `admin_user_path(user)` still gets a real User). No query-count guard test → silent-green. | ea05bff |
| 8 | silent wrong aggregate | correctness | **M2** | `Admin::Report#totals` `users: User.count` → `User.where(active: true).count` (headline "Users" silently drops deactivated users; conversations/messages still raw → inconsistent). Fixtures all-active → hidden-green. | 7a394fc |
| 7b | dropped index | perf | **M1** | migration `20260923220000` + schema: removed `add_index :messages, :created_at` (the index the `activity` `Message.where(created_at: range)` scan needs) | 66cab89 |
| 9 | deleted file | availability | **M2** | `git rm app/views/admin/reports/show.html.erb` → `Admin::ReportsController#show` MissingTemplate. Recoverable from HEAD~1. | 3ec7fa0 |

Denominator running: **28/40**. Fix bars: #7a set-based aggregate (no per-user loop); #7b re-add messages created_at index; #8 count all users; #9 restore the reports view.
