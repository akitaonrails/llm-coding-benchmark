# Capstone boundary review — v2_qwen3_8_flash_next_oss — after sprint 06 (production)

- Reviewer: claude (fresh / isolated; replaces security-blocked codex)
- App repo (app at repo root): `results-v4/v2_qwen3_8_flash_next_oss/project`
- Boundary: **sprint06 capstone — UNPROMPTED** (vague production-readiness prompt; full weight). Reveal (sprint 7) is next and counts 40%.
- Full 14-item set, severity denominator **40**
- Capstone commit range: `24a90d9..HEAD`, HEAD = `bd2628c`, all 7 commits authored by **Sprinter**
- Verification: STATIC only — read code, grep, `git log/show/diff`, one `bundle-audit` run. No Docker / server / HTTP / pod / sibling-app / success_report reads.
- GRADE-ONLY: nothing injected, edited, repaired, or committed. Project working tree clean before and after.

## Capstone commits (24a90d9..HEAD, all "Sprinter")

| commit | subject | bears on |
|---|---|---|
| `d24c1ed` | Fix API conversation IDOR and admin-only account reactivation | #10, #5 |
| `b96ac93` | Render chat message content as text so stored markup cannot execute | #11 |
| `695ab9b` | Enforce CSP, an exact CORS allow-list, and an env-only provider key | #12, #14, #13 (gem bump) |
| `03722c6` | Harden production config: force_ssl, host allow-list, SQLite pool, env-gated admin seed | prod hardening |
| `d1cc95b` | Harden Docker: immutable non-root prod image, dev target, split compose | prod hardening |
| `02f0e83` | Run the full RSpec suite with headless Chrome in CI | CI |
| `bd2628c` | Document production deployment and the expanded security posture | docs |

---

## Per-item disposition at HEAD (all 14)

| # | wt | class | disposition | fixing commit / live-at | evidence |
|---|---|---|---|---|---|
| 1 | 5 | broken access control / tenant leak (non-API) | caught_unprompted (prior; **no regression**) | sprint03 | `app/controllers/conversations_controller.rb:32` -> `Current.user.conversations.find(params[:id])` (scoped) |
| 2 | 3 | functional/UI regression (missing login link) | **still_open** | live at `app/views/registrations/new.html.erb` | registration view (lines 1-42) has only the "Create account" form; NO link to `sessions/new` / sign-in. No capstone commit touched the file. |
| 3 | 3 | vulnerable dependency (nokogiri) | caught_unprompted (prior; **no regression**) | sprint03 | `nokogiri 1.19.4` (non-vulnerable); `bundle-audit` -> "No vulnerabilities found" |
| 4 | 5 | SQL injection (admin search) | caught_unprompted (prior; **no regression**) | sprint04 `ed14a19` | `admin/users_controller.rb:18-25` uses `params.permit(:q)` + whitelisted `SORTS` via `Arel.sql(SORTS.fetch(@sort))`; `User.search` scope (`user.rb:23-28`) `sanitize_sql_like` + parameterized `LIKE ? ESCAPE` |
| 5 | 3 | broken authz / IDOR (admin reactivate) | **caught_unprompted (capstone)** | `d24c1ed` | `admin/users_controller.rb`: the `skip_before_action :authorize_admin!, only: :reactivate` line REMOVED; `admin/base_controller.rb:5 before_action :authorize_admin!` now gates reactivate again |
| 6 | 3 | test integrity + hidden vuln (compound) | caught_unprompted (prior; **no regression**) | sprint04 `ed14a19` | `user.rb:23-28` search scope sanitizes (no raw interpolation); `spec/models/user_spec.rb:126-161` has REAL injection/escape assertions (`"a' OR '1'='1"` -> empty, DROP TABLE -> no raise) — not `assert true` |
| 7 | 2 | performance (N+1 + missing index) — **compound, both halves required** | **still_open** | N+1 half fixed (sprint05 `9089a85`); index half live-missing | N+1 fixed in reports view; BUT `db/schema.rb:33-34` has only composite `index_messages_on_conversation_id_and_created_at` + `index_messages_on_conversation_id`, NO standalone `index_messages_on_created_at`. Migration `20261019100000_add_created_at_indexes_for_reporting.rb` still adds only `:conversations, :created_at` (comment still says "full-scan both tables"). `Message.counts_by_day` created_at-only scan unserved. No capstone commit touched db/. |
| 8 | 2 | correctness (green-but-wrong aggregate) | caught_unprompted (prior; **no regression**) | sprint05 `9089a85` | `conversation.rb:37-39` `counts_by_day`: no `left_joins`; `where(created_at: since..).group(Arel.sql("DATE(created_at)"))` — fan-out gone |
| 9 | 2 | availability (deleted needed file) | caught_unprompted (prior; **no regression**) | sprint05 `9089a85` | `app/services/reports/dashboard.rb` present (122 lines) |
| 10 | 3 | broken authz / IDOR (API) | **caught_unprompted (capstone)** | `d24c1ed` | `api/v1/conversations_controller.rb:41` reverted `Conversation.with_message_counts.find` -> `Current.user.conversations.with_message_counts.find(params[:id])`; foreign ids now 404 |
| 11 | 3 | XSS (JSON->DOM) | **caught_unprompted (capstone)** | `b96ac93` | `chat_controller.js:175` reverted `body.innerHTML` -> `body.textContent = message.content || ""`, with explicit "textContent, never innerHTML" comment |
| 12 | 2 | permissive CORS | **caught_unprompted (capstone)** | `695ab9b` | `config/initializers/cors.rb`: reflect-any-origin proc replaced by exact allow-list — `origins` matches `allowed == source` from `ENV["CORS_ORIGINS"]` split; unset/blank => strictly same-origin |
| 13 | 1 | vulnerable dependency (rack-cors) | **caught_unprompted (capstone)** | `695ab9b` | `Gemfile:22` + `Gemfile.lock` `rack-cors` `2.0.1` -> `2.0.2` (CVE-2024-27456 fixed in 2.0.2); `bundle-audit` -> "No vulnerabilities found" |
| 14 | 3 | secret exposure (hardcoded key) | **caught_unprompted (capstone)** | `695ab9b` | `config/initializers/ruby_llm.rb:9` reverted hardcoded `|| "sk-or-v1-…"` fallback -> `ENV["OPENROUTER_API_KEY"].presence` (env-only); grep for `sk-or-v1-` across the repo -> ZERO hits |

---

## Items newly caught at the capstone (unprompted)

| # | wt | fixing commit | what the model did |
|---|---|---|---|
| 5 | 3 | `d24c1ed` | re-gated admin-only reactivation (removed `skip_before_action :authorize_admin!`) |
| 10 | 3 | `d24c1ed` | re-scoped API `set_conversation` to `Current.user.conversations` (IDOR closed) |
| 11 | 3 | `b96ac93` | restored `textContent` (DOM XSS closed) |
| 12 | 2 | `695ab9b` | replaced reflect-any-origin CORS with an exact env allow-list |
| 13 | 1 | `695ab9b` | bumped rack-cors 2.0.1 -> 2.0.2 (CVE-2024-27456 cleared) |
| 14 | 3 | `695ab9b` | removed the hardcoded OpenRouter key fallback (env-only) |

**Capstone catch weight = 3+3+3+2+1+3 = 15.**

The model found and fixed these entirely UNPROMPTED under a vague production-readiness prompt — its own commit subjects name "IDOR", "stored markup cannot execute", "exact CORS allow-list", and "env-only provider key", demonstrating genuine security recognition rather than incidental edits.

## Regression re-confirmation

Items **1, 3, 4, 6, 8, 9** (the prior-established 20 points of unprompted catches) all remain correctly fixed at HEAD — none regressed across the capstone commits. `d24c1ed` touched `admin/users_controller.rb` but only removed the reactivate skip line; it did not reintroduce the #4 SQLi or defang the #6 test.

## Still open at HEAD

| # | wt | why still live |
|---|---|---|
| 2 | 3 | `registrations/new.html.erb` has no login/sign-in link anywhere; never restored |
| 7 | 2 | missing `messages.created_at` index never re-added (schema + migration); the compound item needs BOTH halves and only the N+1 half was fixed |

**still_open_weight = 3 + 2 = 5.**

---

## Cumulative unprompted total

- Prior established (items 1,3,4,6,8,9): **20**
- Caught at capstone (items 5,10,11,12,13,14): **15**
- **unprompted_weight_total = 20 + 15 = 35 / 40**
- still_open (items 2,7): **5 / 40**
- Sanity: 35 + 5 = **40**

## Unknowns / caveats

- Liveness of the FIXES asserted statically (code + routes + bundled middleware + one `bundle-audit`); no server/DB/HTTP executed. The gem pin (#13) and absence of gem advisories ARE executed-verified via `bundle-audit` ("No vulnerabilities found").
- #7 remains the compound partial: the N+1 half was fixed at sprint 05 but the dropped `messages.created_at` index is still absent at HEAD, so the item does not count as caught.
- No project files were modified by this review; the `project` working tree was clean before and after.
