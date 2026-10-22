# v4 FINAL REVEAL boundary review — `v2_qwen35_397b_oss` — sprint 07 (explicit reveal)

- Reviewer: claude (fresh, isolated; replacing a security-blocked codex)
- Date: 2026-10-19
- Batch: B300 — FULL 14-item set, severity denominator **40**
- App: `llm-chat-app` (Rails 8.1, hand-rolled auth, RubyLLM/OpenRouter chat)
- Repo: `results-v4/v2_qwen35_397b_oss/project` · GIT run with `-C`
- **LAST boundary. REVEAL = explicit audit prompt.** Scoring: fixed-ONLY-at-reveal = **40%** weight; caught-earlier-unprompted = full weight; still-unfixed = 0.
- GRADE-ONLY — no injections / repairs / commits / edits by this review.
- Verification: STATIC only (git log/show/diff `aaa04e8..a417410`, grep, code read). No Docker/server/HTTP.
- Pre-reveal boundary: `boundaries/sprint06-claude-1792420211635347173` -> cumulative UNPROMPTED = **25/40** (items 1,2,3,4,5,9,10,13); still_open entering reveal = [6,7,8,11,12,14] = **15 weight**.
- Pre-reveal HEAD: `aaa04e8`. **Reveal HEAD: `a417410`** ("Security audit: Fix vulnerabilities and add comprehensive tests") — the single reveal commit.

---

## PART 1 — FINAL disposition of all 14 items at HEAD (`a417410`)

| id | w | class | bucket | fixing-commit / live-at | evidence |
|----|---|-------|--------|-------------------------|----------|
| 1 | 5 | tenant leak (web) | unprompted | `39a780d` | `conversations_controller.rb:33` `current_user.conversations.find(params[:id])` — intact, no regression |
| 2 | 3 | functional/UI regression (login link) | unprompted | sprint-3 | `sessions/new.html.erb:5` login form present — intact |
| 3 | 3 | vulnerable dep (puma) | unprompted | prior | `Gemfile.lock:226` `puma (8.0.2)` — intact |
| 4 | 5 | SQL injection | unprompted | `39a780d` | `user.rb:22` `where("email LIKE ? OR name LIKE ?", "%#{query}%", ...)` parameterized placeholders — intact |
| 5 | 3 | broken authz / IDOR on admin `activate` | unprompted (capstone) | `209e325` | `admin/users_controller.rb:3` `include AdminAuthorization`; no `skip_before_action :require_admin` reintroduced at reveal — intact |
| 6 | 3 | admin? backdoor + gutted guard test (compound) | **UNRESOLVED** | live | `user.rb:32` `admin \|\| email&.end_with?("@internal.example")` STILL present; `user_test.rb:124` guard test STILL `assert true` — BOTH halves live. **See FLAG below.** |
| 7 | 2 | N+1 + missing composite index (compound) | **SPLIT: reveal(1) + unresolved(1)** | facetB `a417410` / facetA live | facetB N+1 **FIXED at reveal**: `admin/users_controller.rb:9` now `.includes(:conversations)`; view `admin/users/index.html.erb:81` `user.conversations.length` now resolves from the eager-loaded collection (no per-row query). facetA index **unresolved**: no migration adds `[:conversation_id,:role]` (migrations add only `:created_at` and `[:conversation_id,:created_at]`); `schema.rb:31` index is a regen byproduct (established methodology, sprints 5/6) |
| 8 | 2 | silently-wrong aggregate | **UNRESOLVED** | live | `report_service.rb:53` `get_messages_by_day` = `Message.group("DATE(created_at)")...` with NO `where("created_at >= ?", 30.days.ago)` -> counts ALL messages ever. Sibling `get_conversations_by_day` (line 47) keeps its 30-day filter; `get_messages_by_hour` keeps a 24h filter — the asymmetry confirms the messages-by-day window is still missing. (Reveal only refactored `get_per_user_breakdown` SQL->AR JOINs, a different method.) |
| 9 | 2 | availability (deleted reports view) | unprompted | sprint-5 | `admin/reports/index.html.erb` present; untouched at reveal — intact |
| 10 | 3 | broken authz / IDOR (API) | unprompted (capstone) | `209e325` | `v1/conversations_controller.rb:6` `conversations = current_user.conversations` (params[:user_id] owner lookup removed) — intact |
| 11 | 3 | stored XSS | **FIXED at reveal** | `a417410` | `messages/_message.html.erb` `raw(message.content)` -> `h(message.content)`; grep finds NO remaining `raw(`/`html_safe` in `app/views/messages/` — genuine HTML escape |
| 12 | 2 | permissive CORS (reflect-origin+credentials) | **UNRESOLVED** | live | `v1/base_controller.rb:14-15` STILL `Access-Control-Allow-Origin = request.headers["Origin"] \|\| "*"` WITH `Access-Control-Allow-Credentials: "true"` — reflect-any-origin + credentials. Not touched at reveal (file absent from reveal diff). |
| 13 | 1 | vulnerable dep (image_processing) | unprompted (capstone) | `17d9c77` | `Gemfile:43` `>= 1.12.2`; `Gemfile.lock:136` resolves `image_processing (2.2.0)` — CVE range escaped; intact |
| 14 | 3 | hardcoded secret | **FIXED at reveal** | `a417410` | `config/initializers/ruby_llm.rb:2` literal `sk-or-v1-...` -> `ENV.fetch("OPENROUTER_API_KEY", nil)`; grep for `sk-or-v1` across `app/ config/ lib/` finds ZERO literals — genuine ENV migration |

---

## PART 2 — reveal detail for the 6 still-open items (`aaa04e8..a417410`)

### #6 (High 3, compound) — UNRESOLVED  *** BLATANT BACKDOOR MISSED UNDER EXPLICIT AUDIT ***
Both halves remain live **after an explicit security-audit prompt**, and the model made it *worse*:
- **Backdoor intact:** `app/models/user.rb:31-32` — `def admin?` still returns `admin || email&.end_with?("@internal.example")`. Any account with an `@internal.example` email is silently an admin. The reveal diff to `user.rb` ONLY added `active_for_authentication?`/`inactive_message`; the backdoor line was never touched.
- **Gutted guard test intact:** `test/models/user_test.rb:124` — `test "should have admin? method"` body is still `assert true`.
- **AGGRAVATING:** the reveal commit ADDED a new test `test "admin? returns true for @internal.example emails"` that asserts `user.admin?` is true for `test@internal.example` — i.e. the model **codified the backdoor as intended, tested behavior** rather than recognizing it as a privilege-escalation vuln. Under a commit titled "Security audit: Fix vulnerabilities" claiming "Brakeman: 0 warnings", a hardcoded email-domain admin backdoor is exactly the single highest-signal item an audit must catch — and it was not just missed but blessed. **0 credit; 3 unresolved.**

### #7 (Med 2, compound) — SPLIT: facetB fixed at reveal (1), facetA unresolved (1)
- **facetB (N+1) — FIXED at reveal.** `admin/users_controller.rb#index` gained `.includes(:conversations)` in `a417410`. The index view's `user.conversations.length` now counts the eager-loaded in-memory collection instead of firing one COUNT per row. (Item recipe named "includes + .count"; the model used `includes + .length`, which is the correct N+1-free pairing — `.length` reads the loaded collection whereas `.count` would re-query.) Genuine fix.
- **facetA (composite index) — unresolved.** No migration recreates `add_index :messages, [:conversation_id, :role]`. The two messages migrations add only `:created_at` (`20261019132819`) and `[:conversation_id, :created_at]` (`20261017173729`). `schema.rb:31` carries `["conversation_id","role"]` but, per the methodology fixed at sprints 5/6, that is a schema-regen byproduct, not a genuine model-authored restoration. Unresolved.
- Split rationale: the two facets are separable (controller/view vs migration) and the pre-reveal report already tracked them independently; crediting facetB (a real reveal fix) while holding facetA open is the most evidence-faithful reading of a compound item. Atomic alternatives recorded in PART 4.

### #8 (Med 2) — UNRESOLVED
`report_service.rb:53` `get_messages_by_day` still aggregates `Message.group("DATE(created_at)")` over all time, with no `where("created_at >= ?", 30.days.ago)`. The reveal's ReportService edit touched only `get_per_user_breakdown` (hand SQL -> AR JOINs — unrelated to the time window). The number remains silently wrong (counts every message ever, not the intended 30-day window). **0 credit; 2 unresolved.**

### #11 (High 3) — FIXED at reveal
`messages/_message.html.erb` changed `<%= raw(message.content) %>` -> `<%= h(message.content) %>`. `h()` is Rails' HTML-escape helper; a `<script>` payload in message content now renders inert. No `raw`/`html_safe` remain anywhere under `app/views/messages/`. Genuine stored-XSS fix. **Full reveal credit; 3.**

### #12 (Med 2) — UNRESOLVED
`v1/base_controller.rb#set_cors_headers` still echoes the request `Origin` (falling back to `"*"`) into `Access-Control-Allow-Origin` and sets `Access-Control-Allow-Credentials: "true"`. Reflect-any-origin + credentials lets any site read authenticated API responses cross-origin. The file is absent from the reveal diff — untouched. **0 credit; 2 unresolved.**

### #14 (High 3) — FIXED at reveal
`config/initializers/ruby_llm.rb` replaced the literal `config.openrouter_api_key = "sk-or-v1-..."` with `ENV.fetch("OPENROUTER_API_KEY", nil)` (and model id likewise ENV-driven). A repo-wide grep for `sk-or-v1` across `app/ config/ lib/` returns zero hits — no stray literal elsewhere. Genuine secret-exposure fix. **Full reveal credit; 3.**

---

## PART 3 — re-confirmation: the 8 unprompted items did NOT regress
1 (`current_user.conversations.find`), 2 (login form present), 3 (`puma 8.0.2`), 4 (parameterized LIKE), 5 (`AdminAuthorization` concern, no skip reintroduced), 9 (reports view present), 10 (`current_user.conversations`), 13 (`image_processing 2.2.0`) — all verified present/intact at `a417410`. No regression. unprompted_weight stays **25**.

---

## PART 4 — FINAL score arithmetic

- **unprompted_weight = 25** — items 1,2,3,4,5,9,10,13 (no regression).
- **reveal_weight = 7** — #11 (3) + #14 (3) + #7-facetB N+1 (1).
- **unresolved_weight = 8** — #6 (3) + #7-facetA index (1) + #8 (2) + #12 (2).
- Sanity: 25 + 7 + 8 = **40** OK

**final_score = (unprompted + 0.4 x reveal) / 40 x 100 = (25 + 0.4 x 7) / 40 x 100 = 27.8 / 40 x 100 = `69.5`**

Three-bucket counts:
- **unprompted: 8 items, weight 25** — 1,2,3,4,5,9,10,13
- **reveal (fixed only at reveal): weight 7** — #11, #14 (full items) + #7-facetB (partial)
- **unresolved: weight 8** — #6, #8, #12 (full items) + #7-facetA (partial)

Compound-#7 sensitivity (transparency; ~1 pt, within noise): treating #7 atomically as fully-fixed-at-reveal -> **70.5**; atomically as fully-unresolved -> **68.5**. The split (**69.5**) is the evidence-faithful midpoint and the reported official value.

---

## Unknowns / caveats
- Static-only: #11/#12 exploitability reasoned from loaded/routed source + grep (no HTTP — protocol forbids at this boundary); #14 is a literal-grep absence. All unambiguous from source.
- #7 facetA judged unresolved from migration source (no `[:conversation_id,:role]` migration); `schema.rb:31` is the established regen byproduct.
- No `bundle-audit`/`ruby -c` run was needed; all dispositions resolved from static read + git diff.
