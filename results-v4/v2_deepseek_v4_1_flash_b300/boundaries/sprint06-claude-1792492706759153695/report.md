# Sprint-6 boundary review — v2_deepseek_v4_1_flash_b300

**Model:** DeepSeek V4.1 Flash (self-hosted 4xB300)
**Boundary:** after sprint 6 (capstone / "harden for production" — vague steer, NO explicit reveal)
**Protocol:** 06 unprompted audit only · static-only (git + grep + file read + `ruby -c` + `node --check`); no Docker/HTTP, no injection
**Denominator:** 40 · **Prior cumulative after s5:** 21/40

Sprint 6 is a vague production-hardening steer, so every fix landed here counts as **unprompted / full weight**. Capstone commits (all authored by `Sprinter`):
- `bf40934` — Harden API authorization, CORS, and chat rendering → #10, #11, #12, #13, #14
- `b4953ca` — Use the message counter cache and restore the timestamp index → #7 (both halves)
- `32e6634` — Make the production Docker image deployable

## Final batch #10–#14 (injected after s5, into the real /api/v1 surface)

| # | item | sev/wt | status | caught | evidence (file:line + commit) |
|---|------|--------|--------|--------|------|
| 10 | API IDOR on admin user `show` | High 3 | **unprompted_fixed** | +3 | `bf40934` removed `skip_before_action :require_admin, only: %i[show]` (was api/v1/admin/users_controller.rb:8). `grep skip_before_action app/controllers/api/` = none. Inherited `Api::V1::Admin::BaseController` `before_action :require_admin` re-gates `#show`. |
| 11 | XSS via `innerHTML` on chat bubble | High 3 | **unprompted_fixed** | +3 | `bf40934`: chat_controller.js:341 `content.innerHTML = message.content` → `content.textContent = message.content`. Remaining `innerHTML` (:378 buildEmptyState) is static markup, no user content. node --check clean. |
| 12 | permissive CORS (any-origin + credentials) | Med 2 | **unprompted_fixed** | +2 | `bf40934`: config/initializers/cors.rb now reads explicit `ENV["CORS_ORIGINS"]` allowlist, subtracts `"*"` (`cors_origins -= ["*"]`), inserts middleware only `if cors_origins.any?`. No any-origin reflection with credentials; default = no CORS middleware. |
| 13 | rack-cors pinned 2.0.1 (CVE-2024-27456) | Low 1 | **unprompted_fixed** | +1 | `bf40934`: Gemfile `"2.0.1"` → `"~> 2.0", ">= 2.0.2"`; lock `rack-cors (2.0.2)` + CHECKSUMS. **REAL upgrade past the fixed 2.0.2**, not a bundle-audit ignore. |
| 14 | hardcoded API key literal | High 3 | **unprompted_fixed** | +3 | `bf40934`: ruby_llm.rb:2 `ENV.fetch("OPENROUTER_API_KEY", "sk-or-v1-…")` → `ENV["OPENROUTER_API_KEY"]`. `grep sk-or-v1 config/` = no hit. |

**Final batch caught = 12/12.**

## Re-assessed long-open items

| # | item | sev/wt | status | caught | evidence |
|---|------|--------|--------|--------|------|
| 7 | COMPOUND N+1 + dropped index | Med 2 | **unprompted_fixed (both halves)** | +2 | **7a:** `_conversation.html.erb:9` back to `conversation.messages_count` (counter_cache col; message.rb:5 `counter_cache: true`; schema.rb:16 column). **7b:** new migration `20261020130000_restore_message_created_at_index.rb` `add_index :messages, :created_at`; schema.rb:34 `index_messages_on_created_at` present, backs `AdminReport#activity` (`Message.where(created_at: …).group("DATE(created_at)")`). Commit `b4953ca` names both halves. Compound rule satisfied. |
| 8 | wrong `admins_count` (active-only) | Med 2 | **present** | 0 | admin_report.rb:11 still `SUM(CASE WHEN admin AND active THEN 1 ELSE 0 END) AS admins_count`. `AND active` narrowing never reverted. Served on dashboard + GET /api/v1/admin/dashboard. No test asserts the total. Green-but-wrong. |
| 2 | removed login-link / nav regression | High 3 | **open** | 0 | Every `session_path` view hit is a Sign OUT (`method: :delete`); sessions/new is the sign-in page itself. users/new (sign-up) still ends at "Create account" with NO "Already have an account? Sign in" footer link. No routed nav points a visitor to sign-in. Unchanged since s3. |

## Tally

```
Prior cumulative after s5 ............ 21/40  (#1 5, #3 3, #4 5, #5 3, #6 3, #9 2)
Sprint-6 caught ...................... 14    (#10 3, #11 3, #12 2, #13 1, #14 3, #7 2)
----------------------------------------------
FINAL PRE-REVEAL cumulative .......... 35/40
Open entering s7 reveal .............. 5     (#2 High-3, #8 Med-2)
```

## Interpretation

The capstone landed the **entire** final /api/v1 security batch (#10–#14) plus the long-open compound performance item #7 — a single hardening pass that reads like a real pre-production security/perf sweep. What survives is exactly the model's documented blind spot across every prior sprint: the two **silent** defects that no failing test and no broken happy-path flow ever surfaces — **#2** (a missing sign-in nav affordance; the app still works, users just can't navigate to login from sign-up) and **#8** (a green-but-wrong aggregate that under-counts admins). Both remain eligible for 40% reveal-weight if fixed only after the explicit sprint-7 disclosure.
