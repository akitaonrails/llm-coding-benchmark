# Muse Spark Open 816B-A42B NVFP4 (RunPod 4xB300) — Sprint 7 REVEAL grade

**Harness:** opencode · **Method:** STATIC-ONLY (git/grep/read, `ruby -c` read-to-decide; no docker/db/server/rails/test exec)
**Reveal commit:** `8819ce0 fix(security): restore SPRINT 7 pre-deploy hardening` · **Diff range:** `06fe173..HEAD`
**Run health:** exit 0, no timeout, no stall, **0 nudges**

## Pre-reveal state (capstone, after sprint 6)
final_unprompted_weight = **21/40**. Items OPEN entering the reveal (weight 19): #2, #5, #6, #7, #8, #10, #11.

## Per-item reveal verdict

| # | Item | Sev | Wt | Fixed? | Evidence |
|---|------|-----|----|--------|----------|
| 2 | removed signup→login link | H | 3 | **YES (+3)** | registrations/new.html.erb:42-48 — `link_to "Sign in", new_session_path` restored |
| 5 | skip require_admin on :demote | H | 3 | **YES (+3)** | `skip_before_action :require_admin, only: :demote` deleted; base_controller.rb:5 `before_action :require_admin` now covers :demote |
| 6 | login-gate contradiction + gutted test (compound) | H | 3 | **YES (+3)** | 6a: sessions_controller.rb:10 `if user.inactive?` (`&& user.active?` removed; `inactive?`=`!active`). 6b: users_controller_test.rb:224-229 real `post session_path` + redirect/flash/cookie assertions restored |
| 7 | N+1 + dropped messages.created_at index (compound) | M | 2 | **YES (+2)** | 7a: reports/index.html.erb:160 `user.conversations.count` → `read_attribute(:conversations_count)` reading the grouped LEFT-JOIN alias (reports_dashboard.rb:110-118). 7b: migration + schema.rb:45 restore `index_messages_on_created_at` |
| 8 | admin_users undercount `User.admins.active.count` | M | 2 | **NO (0)** | reports_dashboard.rb:33 unchanged — not in reveal diff, not reverted to `User.admins.count` |
| 10 | API cross-user `me?user_id=` IDOR | H | 3 | **YES (+3)** | api/v1/users_controller.rb:8 → `user_json(Current.user)` only; `params[:user_id]` lookup deleted |
| 11 | stored XSS innerHTML (user bubble) | H | 3 | **YES (+3)** | api_chat_controller.js:137 user branch `innerHTML` → `textContent`; remaining innerHTML (:131/:139) is static template, flash (:177) escaped via `escapeHtml` |

**Fixed on reveal:** #2, #5, #6, #7, #10, #11 (6 of 7) · **Missed:** #8

## Compute
- reveal_weight = 3 + 3 + 3 + 2 + 3 + 3 = **17** (all open except #8's 2)
- **FINAL SCORE = (21 + 0.4 × 17) / 40 × 100 = 27.8 / 40 × 100 = 69.5**
- **Tier C** (51–72; anchored Opus 4.6 = 83)
- open_at_end = **#8** · nudges = 0

## Reveal narrative
Told explicitly to hunt and fix everything, Muse swept **6 of its 7 remaining open items** in one commit. Crucially it caught **both authorization items it had missed unprompted** — #5 (`:demote` privilege escalation) and #10 (the `me?user_id=` IDOR) — plus the stored-XSS sink (#11), both compound pairs in full (#6 gate+test, #7 N+1+index), and the signup→login UI affordance (#2).

The one miss is **#8**, the silently-wrong `User.admins.active.count` aggregate: no runtime error, no visible symptom, and outside any security/UX checklist surface, so it slipped through even a directed hunt. Everything the reveal touched is in `8819ce0`; #8 is the sole file in the open set the commit never opened.

## Sibling comparison

| Model | Reveal result | Final | Tier |
|-------|---------------|-------|------|
| Step-5 | fixed 2/5 open (#7 index, #11 XSS) | 72.5 | C |
| GLM 5.3 | swept all 6 open | 76.0 | B |
| **Muse Spark Open** | **fixed 6/7 open (missed #8)** | **69.5** | **C** |
| Ornith | pending | — | — |

Muse's reveal catch-rate (6/7) is the strongest of the three by raw count, but its lower pre-reveal base (21/40) and the reveal formula's 0.4 weighting on recovered weight leave the final at 69.5/C — just under Step-5 despite fixing far more, because Step-5 entered the reveal with more already-fixed weight. Headline: **when told to hunt, Muse found the authz bugs (#5/#10) it blew past unprompted** — directed attention closed the authorization gap passive hardening had left open.
