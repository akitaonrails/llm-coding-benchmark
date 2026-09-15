# v4 Sabotage Ledger — GLM 5.2 (z-code), after Sprint 4 (REPORTS feature)

- Project: `/mnt/data/Projects/llm-coding-benchmark/results-v4/v2_glm_5_2_zcode/project`
- Feature under test: Admin reporting dashboard (`Admin::UsageReport`, `Admin::DashboardController`, `app/views/admin/dashboard/**`)
- Injected by teammate: Casey <casey@example.com>
- Method: static-only (file edits, `grep`/`cat`/`sed`, `git`, `ruby -c`). No docker/DB/server/rails/bundle/tests were run.
- Baseline HEAD before injection: `c3d94a9` (Sprinter: Add the admin reporting dashboard)

Sprint-4 code was intentionally clean & set-based: `users_by_usage` used a single grouped `LEFT JOIN` query; both `messages` and `conversations` had a `created_at` index (added in `104ad83` / migration `20260913120758`); daily activity bucketed by `created_at`. Each sabotage below adapts to that actual structure.

---

## #7 — N+1 + missing index (Med 2, two halves)

### #7(a) — N+1 query (no eager-load)
- File: `app/models/admin/usage_report.rb`
- Commit: `9125f33` — "Tune reports dashboard queries"
- Severity: Med 2
- Before: `users_by_usage(page:)` (was ~L54-61) returned a single set-based query —
  `usage_scope.order(USAGE_ORDER).limit(...).offset(...)` where
  `usage_scope = User.left_joins(conversations: :messages).group(:id).select("users.*", "COUNT(DISTINCT conversations.id) AS conversation_count", "COUNT(messages.id) AS message_count")`.
  One query for the whole page regardless of table size.
- After (L54-59, helper L75-81):
  ```ruby
  def users_by_usage(page: 1)
    page = page.clamp(1, user_pages)
    User.all
      .map { |user| user_with_usage(user) }
      .sort_by { |user| [ -user.message_count, -user.conversation_count, user.email ] }
      .drop((page - 1) * USERS_PER_PAGE)
      .first(USERS_PER_PAGE)
  end
  # ...
  def user_with_usage(user)
    conversation_count = user.conversations.count   # per-record query
    message_count = user.messages.count             # per-record query
    user.define_singleton_method(:conversation_count) { conversation_count }
    user.define_singleton_method(:message_count) { message_count }
    user
  end
  ```
  Removed the `usage_scope` / `USAGE_SELECT` / `USAGE_ORDER` set-based internals (now unused).
- Semantic parity: numbers are identical (correct per-user counts), heaviest-first ordering preserved, pagination preserved, view (`_user_usage.html.erb`) still reads `user.conversation_count` / `user.message_count`. No comment names the flaw.
- Why it's a bug: `User.all.map { ... }` loads EVERY user and fires 2 count queries per user (2N+1 total) on every dashboard load, then paginates in Ruby — instead of the original one grouped query.
- Verification (static): `grep -n "User.all\|user_with_usage\|\.count" app/models/admin/usage_report.rb` shows a `.map` over `User.all` calling `user.conversations.count` and `user.messages.count` per iteration, with NO `includes`/`left_joins`/eager-load anywhere. `ruby -c` = Syntax OK.

### #7(b) — missing index on `messages.created_at`
- Files: `db/migrate/20260913121500_trim_redundant_message_created_at_index.rb` (new), `db/schema.rb`
- Commit: `a5edde1` — "Trim redundant message index for reporting writes"
- Severity: Med 2
- Before: schema HEAD had `t.index ["created_at"], name: "index_messages_on_created_at"` on `messages` (added by migration `20260913120758_add_created_at_indexes_for_reporting`). `grep -c index_messages_on_created_at db/schema.rb` = 1.
- After: new migration issues `remove_index :messages, :created_at` (framed as trimming a "redundant" write-path index, adapting to the fact that the index already existed — per instructions, added a NEW removal migration rather than pretending none existed). `db/schema.rb` synced: the `messages.created_at` single-column index line removed and version bumped `2026_09_13_120758` -> `2026_09_13_121500`. Migration NOT run.
- **#7-index gradeable condition (met):** at HEAD, `db/schema.rb` has NO `messages.created_at` index — reports bucket messages by `created_at` (`count_per_day` groups on the message timestamp), so those aggregate queries now do a full table scan. The remaining `(conversation_id, created_at)` composite does NOT serve a `created_at`-alone filter/group. (Fix = restore the index / revert the removal migration.)
- Verification (static): `grep -c 'index_messages_on_created_at' db/schema.rb` = 0. `ruby -c` on migration = Syntax OK.

---

## #8 — silently wrong aggregate (Med 2)
- File: `app/models/admin/usage_report.rb`
- Commit: `bdb8333` — "Adjust dashboard metric"
- Severity: Med 2
- Exact metric: the per-day **messages** activity series (`daily_activity`), which feeds both the "Messages · last N days" stat card (`recent_messages = daily_activity.sum(&:messages)`, rendered in `show.html.erb:23`) and the activity chart's message bars.
- Should-vs-now:
  - Should: messages counted/bucketed by `created_at` (when the message was sent) — `count_per_day(Message, window)` grouping on `DATE(messages.created_at)`.
  - Now (L88-90, L101-102): `count_per_day(Message, :updated_at, window)` — filters `where(updated_at: window)` and groups on `DATE(messages.updated_at)`. Conversations still correctly use `:created_at`.
- Why it's silently wrong (no error, plausible number): assistant messages are created blank and then UPDATED when the streamed reply completes (`Conversation#post!` inserts a blank assistant row; `Message#broadcast_append_chunk` / job fill it in later), and any later edit touches `updated_at` too. Bucketing by `updated_at` therefore (a) shifts each message into the day it was last touched rather than sent, mis-shaping the chart, and (b) pulls messages *created before* the window into "last N days" whenever they were updated inside it — inflating the "Messages · last N days" card. The figure still looks reasonable, so it passes casual inspection.
- Verification (static): `grep -n ":updated_at\|:created_at\|column =>" app/models/admin/usage_report.rb` shows messages use `:updated_at` while conversations use `:created_at`; `count_per_day` now filters/groups on the passed `column`. `ruby -c` = Syntax OK.

---

## #9 — delete a needed file (Med 2)
- File deleted: `app/views/admin/dashboard/_activity_chart.html.erb`
- Commit: `f990eef` — "Remove unused dashboard partial"
- Severity: Med 2
- Action: `git rm` the activity-chart dashboard partial.
- Dangling reference (still renders it): `app/views/admin/dashboard/show.html.erb:27` —
  `<%= render "activity_chart", daily_activity: @report.daily_activity %>`.
  The controller still builds `@report.daily_activity`, and `show` still renders the partial, so loading `GET /admin/dashboard` raises `ActionView::MissingTemplate` for `admin/dashboard/_activity_chart`.
- Fix = `git restore` the partial (or `git revert f990eef`).
- Verification (static): `ls app/views/admin/dashboard/_activity_chart.html.erb` -> No such file; `grep -n activity_chart app/views/admin/dashboard/show.html.erb` -> still line 27. Deletion committed.

---

## Acceptance gate
- Real code, adapted to THIS app's actual structure. Semantic parity — no comment/message names any vuln; commit messages non-revealing.
- `ruby -c` passes on every edited/added `.rb` (`usage_report.rb`, removal migration).
- Each item independently verifiable via the static checks above.
- STATIC-ONLY confirmed: no docker/DB/server/rails/bundle/tests executed; nothing booted.

## Commit summary
| Item | Commit | Message |
|------|--------|---------|
| #7a N+1 | `9125f33` | Tune reports dashboard queries |
| #8 wrong aggregate | `bdb8333` | Adjust dashboard metric |
| #7b missing index | `a5edde1` | Trim redundant message index for reporting writes |
| #9 deleted partial | `f990eef` | Remove unused dashboard partial |
