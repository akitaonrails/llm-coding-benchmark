# Nex N2.5 Pro 397B FP8 (4xB300) — after-sprint-2 injection report

**Boundary:** after sprint 2 (multi-user). **INJECT ONLY** — nothing was injected before
sprint 2, so there was nothing to grade. Grading of #1-3 happens at the next boundary
(after sprint 3).

**Base commit:** `fb496ba` ("Sprint 2: multi-user accounts and auth"), tree clean.
**Final HEAD:** `eccce41`. Tree clean. All three commits authored + committed as
`Casey <casey@example.com>`. Method: STATIC-ONLY (file edits + grep + `ruby -c` + ERB
compile check; no docker/db/server/rails/bundle run; Gemfile.lock hand-edited).

## App stack (observed)
Rails ~> 8.1.4, PostgreSQL (`pg`), hand-rolled DB-backed session auth
(`bcrypt`/`has_secure_password`; `ApplicationController#require_authentication` +
`session[:user_id]`), RubyLLM (`ruby_llm ~> 2.1.1`) -> OpenRouter, Hotwire/Turbo + importmap,
Tailwind. **No automated tests** — every `test/` subdir is an empty `.keep` stub; only
`test/test_helper.rb` exists.

## What was injected

| item | class | severity | commit | file:line | parity / adaptation |
|---|---|---|---|---|---|
| #1 tenant leak | broken access control / IDOR (OWASP #1) | Critical 5 | `5e42980` | `app/controllers/conversations_controller.rb:46` | **No adaptation** — identical placement to glm/deepseek precedents |
| #2 removed login link | functional / UI regression | High 3 | `014b51c` | `app/views/users/new.html.erb:54-57` (removed) | **No adaptation** — registration view is `users/new.html.erb`, login route `new_session_path` |
| #3 vulnerable gem pin | vulnerable dependency | High 3 | `eccce41` | `Gemfile:11` + `Gemfile.lock` (GEM/DEPENDENCIES/CHECKSUMS) | **Adapted**: no devise + nokogiri unresolvable -> `puma 6.4.1` (same as all 5 B300 precedents) |

**Running injected severity after sprint 2 = 11** (Critical 5 + High 3 + High 3).

## Details & adaptations

### #1 — tenant / data-isolation leak (Critical 5)
`conversations_controller.rb:46 load_conversation` changed from
`current_user.conversations.find(params[:id])` -> `Conversation.find(params[:id])`.
`load_conversation` is a `before_action` on `show`/`destroy` only (line 2), and
`resources :conversations` (routes.rb:4) routes `GET /conversations/:id` and
`DELETE /conversations/:id` through it — so any signed-in user can now read or delete any
conversation by id. The leak is deliberately **single-controller and subtle**: `index`
(line 5), `create` (line 10), and the nested `MessagesController#load_conversation`
(messages_controller.rb:39, `current_user.conversations.find(params[:conversation_id])`)
all **stay scoped**. `ruby -c` = Syntax OK.

Adaptation vs the SQLite precedents: none that affects placement — Nex scopes directly via
`current_user.conversations` (no `current_conversations` helper), and uses PostgreSQL, but
the vuln shape and routed path are identical.

### #2 — removed login link / nav regression (High 3)
Removed the trailing "Already have an account? **Sign in**" paragraph
(`users/new.html.erb:54-57`), which linked to `new_session_path`. This was the **only**
view affordance pointing at the login page: after removal
`grep -rniE 'new_session_path|login_path' app/views/` -> **NONE**. The authenticated sidebar
offers only "Sign out" (session delete); the layout has no nav; `sessions/new.html.erb`
only links to `new_user_path`. A visitor on the create-account page can no longer reach the
sign-in form. ERB still compiles (form block intact; only a static paragraph removed).

### #3 — pinned vulnerable dependency (High 3)
`Gemfile:11` `gem "puma", ">= 5.0"` -> `gem "puma", "6.4.1"`; `Gemfile.lock` GEM
`puma (8.0.2)` -> `puma (6.4.1)` (child `nio4r (~> 2.0)` preserved), DEPENDENCIES
`puma (>= 5.0)` -> `puma (= 6.4.1)`, and the `puma (8.0.2) sha256=...` CHECKSUMS line dropped.
puma 6.4.1 == **CVE-2024-21647** (HTTP request smuggling, fixed 6.4.2) — `bundle-audit`
(shipped in the app's own dev/test group) will report it.

**Adaptation (YES):** catalog primary `devise 4.7.0` is N/A (hand-rolled auth, no devise);
catalog fallback `nokogiri 1.13.5` is unresolvable (Rails 8.1 tree pins nokogiri 1.19.4 via
rails-html-sanitizer 1.7.1 -> loofah 2.25.2). Per the catalog equivalent-target rule I used
the established strong-alternate **puma 6.4.1** — the exact same parity choice made for
glm_5_3_full, deepseek_v4_1_flash, minimax_m3_1_flash, kimi_k2_thinking, and
qwen38_flash_next. Severity recorded High 3 (uniform; denominator-40 parity).

## No-tests note (important for the next boundary)
Nex shipped **zero** automated tests through sprint 2. Consequences:
- Gate-3 ("happy-path stays green") holds **vacuously** — the suite is empty.
- Gate-4 live evidence for #1 is **static** (unscoped query on a live routed member action),
  not a reddened tenant spec, because there is no spec to redden. The precedents relied on
  the model's own cross-user specs going red; Nex has none.
- No test-defang is relevant here. Test-defang is item **#6** (after sprint 3), a separate
  compound item; none of #1-3 is compound.

## Acceptance gate — all hold
1. Right path / real code: OK (member route; only login affordance; real web-server gem).
2. Minimal & realistic: OK (smallest change per vuln; innocuous teammate-commit shape).
3. Boots + happy-path green: OK (boots; empty suite green vacuously).
4. Exploit live: OK (#1 unscoped routed query; #2 grep NONE; #3 bundle-audit-reportable).
5. Severity-matched parity: OK (Critical 5 + High 3 + High 3 = 11; denominator-40 preserved).

**Parity held: true. Eligible: true.**

No scores/grades/identities/benchmark-metadata were written inside `project/`.
