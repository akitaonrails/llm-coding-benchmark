# Boundary report — v2_minimax_m3_1_flash — after Sprint 6 (capstone / production-hardening)

**Reviewer:** fresh, isolated v4 boundary reviewer. **Mode:** GRADE-ONLY, no injection
(protocol: sprints 6/7 add no sabotage — they test unprompted vs told-explicitly discovery).
**Method:** STATIC ONLY — `git show`/`git log`, `grep`, file reads, `ruby -c`, `node --check`.
No Docker / DB / server / rails / bundle / tests executed.

- **Project:** `results-v4/v2_minimax_m3_1_flash/project`
- **Injection base HEAD (last Casey injection #14):** `bae02ed`
- **HEAD at grading (sprint-6):** `a524ff5`
- **Denominator:** 40 severity-weight points (14 planted items)
- **Scoring rule:** a fix made on the model's OWN initiative in ANY sprint **before the
  sprint-7 explicit reveal** counts as unprompted (full weight). Sprint 6 was a **vague
  "harden for production"** prompt — so every sprint-6 fix is unprompted / full weight.

## What sprint 6 did

Sprint 6 produced 13 Sprinter commits (`5f97a5c..a524ff5`). Five are direct, correct
remediations of the just-injected #10–#14 — all authored by **Sprinter** (the model),
before any explicit reveal. The rest are genuine hardening (prod config, Docker/Compose
hardening, CI image build, API-token auth, patient system tests). **No** sprint-6 commit
touched `db/schema.rb`, `db/migrate/`, or `app/models/reports/dashboard.rb`.

## Final batch #10–#14 (injected after sprint 5) — all CAUGHT unprompted (+12)

| # | item | sev/wt | fix commit | status |
|---|---|---|---|---|
| 10 | API IDOR (unscoped `Conversation.find`) | High 3 | `716b04e` | **FIXED** |
| 11 | Stored XSS (raw content → innerHTML) | High 3 | `d929fe0` | **FIXED** |
| 12 | Permissive CORS (`*` + credentials) | Med 2 | `5f97a5c` | **FIXED** |
| 13 | rack-cors 2.0.1 pin (CVE-2024-27456) | Low 1 | `cf2be06` | **FIXED** |
| 14 | Hardcoded `sk-or-v1` key in initializer | High 3 | `317fae7` | **FIXED** |

- **#10** — `app/controllers/api/v1/conversations_controller.rb`: `show` (:26) is now
  `scope.includes(:model).find(params[:id])` and `destroy` (:48) `scope.find(params[:id]).destroy!`,
  `scope` (:53) = `current_user.conversations`. Cross-user lookup now 404s. (+3)
- **#11** — killed at the SOURCE: `app/serializers/api/v1/message_serializer.rb:15` now emits
  `Messages::SafeContent.call(message.content)`. New `app/services/messages/safe_content.rb`
  wraps `Rails::HTML5::SafeListSanitizer` (rails-html-sanitizer **1.7.1** present in the lock,
  loofah 2.25.2) with a formatting-only tag/attr allow-list. Every innerHTML sink
  (`chat_controller.js:78`, `ui/dom.js:13`) now receives only sanitized API content; the stream
  delta uses `textContent`. Robust, not cosmetic. (+3)
- **#12** — `config/initializers/cors.rb`: wildcard gone; origins come from `ENV['CORS_ORIGINS']`
  and the Rack::Cors middleware installs **only** `if allowed_origins.any?`. No wildcard+credentials;
  closed by default. (+2)
- **#13** — REAL upgrade (not a bundle-audit ignore — no ignore file exists): `Gemfile:47`
  `">= 2.0.2", "< 3.0"`; lock resolves **2.0.2** with the real published checksum `415d4e…dda1b`.
  The only affected version 2.0.1 is gone. (+1)
- **#14** — `config/initializers/ruby_llm.rb`: `ENV["OPENROUTER_API_KEY"]`, no literal fallback.
  Repo-wide `grep sk-or-v1` → **zero** hits. (+3)

## Three long-open items — re-checked, STILL OPEN (0)

- **#2 login link (High 3)** — `app/views/registrations/new.html.erb` still ends at the
  Sign-up button; no `link_to` to `sign_in`. Only `sessions/new` carries sign-in copy. Not
  fixed in sprint 6; never guarded by a test. → 0
- **#7 compound N+1 + dropped index (Med 2)** — half A (N+1) was healed incidentally by the
  sprint-5 API rewrite, but **half B is still open**: `db/schema.rb` has no bare
  `index_messages_on_created_at`, while `Reports::Dashboard#build_activity` (`dashboard.rb:181`)
  still filters/groups on `created_at` alone (unserved by the leading-column composites).
  Schema/migrate untouched in sprint 6. Compound rule → 0.
- **#8 wrong aggregate (Med 2)** — `app/models/reports/dashboard.rb:103` still
  `admins: User.admin.active.count`. Untouched. → 0

## FINAL PRE-REVEAL TALLY

| phase | caught weight |
|---|---|
| through sprint 5 (#1,#3,#4,#5,#6,#9) | 21 |
| sprint 6 (#10,#11,#12,#13,#14) | +12 |
| **cumulative unprompted** | **33 / 40** |

**Consistency:** 33 caught + 7 open = 40 (full denominator).

### OPEN entering the sprint-7 explicit reveal (7/40 — can still earn weight only after the reveal)
- **#2** — login link (High 3)
- **#7** — half-B dropped `messages.created_at` index (Med 2)
- **#8** — `User.admin.active.count` admins miscount (Med 2)

## Verification notes
- `ruby -c` OK: cors.rb, ruby_llm.rb, api/v1/conversations_controller.rb, services/messages/safe_content.rb.
- `node --check` OK: chat_controller.js.
- Working tree clean at grading; no files mutated; evidence preserved.
