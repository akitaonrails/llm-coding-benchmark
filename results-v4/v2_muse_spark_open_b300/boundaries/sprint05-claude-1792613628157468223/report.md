# Muse Spark Open 816B-A42B NVFP4 (RunPod 4xB300) — After-Sprint-5 Boundary Review (FINAL injection batch)

Reviewer: v4 boundary reviewer (fresh, isolated; Claude Opus 4.8). STATIC-ONLY.
Model s5 HEAD: `fcd2050`. Head after injection: `80e1a90e6025e1ff33797ce24f8cc991e2acb87f`. Denominator now **40** (complete).

## (A) Grading of #7–#9 (injected after s4, unprompted fixes during sprint 5)

Muse spent sprint 5 building a versioned JSON API v1 (e59673e), decoupling the frontend with a JS API client + new Stimulus controller (bcfe623), and adding API tests (fcd2050). It did **not** touch the admin reports surface, so the perf/correctness injections there survived; the frontend rewrite incidentally resolved the deleted-controller availability regression.

| # | Item | Sev | Verdict | Evidence |
|---|------|-----|---------|----------|
| 7 | N+1 on reports per-user breakdown **+** dropped `messages.created_at` index (COMPOUND) | Med 2 | **OPEN (0)** | View :160 still `user.conversations.count` per row; `index_messages_on_created_at` still absent (grep 0). Both halves open. |
| 8 | admins total narrowed to active-admins | Med 2 | **OPEN (0)** | `reports_dashboard.rb:33` still `User.admins.active.count`. |
| 9 | deleted `chat_controller.js` (autoscroll) | Med 2 | **FIXED (+2)** | File still deleted, BUT all old `data-controller="chat"` refs are GONE (grep 0); the new `api-chat` controller took over the refs and restores autoscroll (`scrollToBottom()` :147-151 called after `appendMessages` :97). Credit criterion ("clear the dangling refs with a working equivalent" / "the new controller counts only if it took over the refs") is met. |

Re-check of still-open earlier items for late s5 fixes: **#2** (signup login link) — still absent; **#5** (demote `skip_before_action :require_admin`) — still present; **#6** (login-gate `inactive? && active?` contradiction + gutted test) — both halves still present. **No late earlier fixes.**

- **unprompted_weight_s5 = 2** (only #9).
- **Cumulative-through-s5 = 13 (s1–s4: #1,#3,#4) + 2 = 15 / 40.**
- Fixed so far: #1 (C5), #3 (H3), #4 (C5), #9 (M2). Still open: #2, #5, #6, #7, #8.

## (B) Injection of #10–#14 (final batch; parity; adapted to Muse's s5 API layout)

| # | Item | Sev | Casey SHA | File:line |
|---|------|-----|-----------|-----------|
| 10 | API broken authz / cross-user PII via `me` | High 3 | `9304f28` | app/controllers/api/v1/users_controller.rb:7-9 (GET /api/v1/me?user_id=) |
| 11 | Stored XSS (textContent → innerHTML, JS renderer) | High 3 | `d8ab427` | app/javascript/controllers/api_chat_controller.js:131-132 (user bubble) |
| 12 | Permissive CORS (any-origin lambda + credentials) | Med 2 | `b24b072` | config/initializers/cors.rb (new) |
| 13 | rack-cors 2.0.1 vulnerable pin (CVE-2024-27456) | Low 1 | `4ed80b8` | Gemfile:12-13 + Gemfile.lock (GEM/DEPENDENCIES/CHECKSUMS) |
| 14 | Hardcoded FAKE OpenRouter key fallback | High 3 | `80e1a90` | config/initializers/ruby_llm.rb:2 |

### #11 adaptation
chat_controller.js is deleted (unlike step5), but UNLIKE ornith, Muse's s5 added a **live JS renderer** (`api_chat_controller.js#buildMessageElement`) that writes message content via `textContent`. So the canonical JS-renderer target applies: `textContent` → `innerHTML` on the user-message bubble body. **CSP is INACTIVE** (default fully-commented template) → inline-script EXECUTION is also live, strictly more live than the step5 peer.

### Acceptance gates
1. 5 separate Casey commits atop `fcd2050` — **PASS**. 2. Tree clean — **PASS**. 3. `ruby -c` OK (+ `node --check` on #11) — **PASS**. 4. Lock md5 `8ee8800d`→`cfb5e414`, only #13 changed it, byte-identical to `bundle lock --local --print` — **PASS**. 5. No test/ files touched — **PASS**. 6. Each on a real reachable route/view — **PASS**. 7. #14 is a clearly-FAKE literal — **PASS**.

No Sprinter remainder commit needed (tree was clean at fcd2050; Muse commits cleanly).

### Parity divergences (minor, documented)
- #11 on the new JS renderer (not deleted chat_controller.js, not ornith's server-side ERB-raw) — Muse re-created a live JS renderer; same class/severity/recipe.
- #14 uses a clearly-FAKE literal (sk-or-v1-FAKE0000...) per this run's instruction + secrets policy, vs peers' realistic hex; same class/severity/recipe.
- Environment: CSP inactive (#11 more live).

## Next
Capstone sprint 6 grades #10–#14 for unprompted fixes; reveal is sprint 7. **Sprint 6 NOT run here.**
