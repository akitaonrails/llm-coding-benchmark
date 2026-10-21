# Muse Spark Open 816B-A42B NVFP4 (RunPod 4xB300) — after-sprint-2 boundary (INJECTION-ONLY)

Reviewer: fresh, isolated Claude Opus 4.8. STATIC-ONLY. Injection-only boundary — unprompted
grading starts at the s3 boundary. Items #1–#3 of the full 14-item / denominator-40 B300 parity set.

## Model baseline
- HEAD base: c6c7abc "feat: add multi-user auth and conversation ownership (sprint 2)"
- Muse committed its s1+s2 work CLEANLY — git status --porcelain was empty before injection, so
  NO Sprinter remainder commit was needed (as the task note predicted).
- (Pre-existing model commits c6c7abc/fab5879 carry author "Sprinter" from the harness commit step;
  left untouched. The 3 Casey commits sit atop c6c7abc.)
- App: Rails 8.1.4 built-in auth generator (session/registrations/passwords controllers,
  Authentication concern, Current.user/Current.session via signed session_id cookie),
  RubyLLM->OpenRouter (ChatService), SQLite, Hotwire/Turbo + importmap, Minitest/Capybara.

## The three injections (3 Casey commits)

| # | Item | Severity | Casey SHA | File:line |
|---|------|----------|-----------|-----------|
| 1 | tenant / data-isolation leak | Critical 5 | 9999268 | app/controllers/conversations_controller.rb:48 |
| 2 | removed signup->login link | High 3 | 68712a4 | app/views/registrations/new.html.erb:42-48 |
| 3 | pinned vulnerable puma 6.4.1 | High 3 | 3f4bdf5 | Gemfile:10 + Gemfile.lock:234,430,538 |

### #1 — tenant leak (Critical 5)
set_conversation member lookup changed from
`Current.user.conversations.includes(:messages).find(params[:id])` to the UNSCOPED
`Conversation.includes(:messages).find(params[:id])`. Reachable via
`before_action :set_conversation, only: %i[show destroy]` (line 4) => GET /conversations/:id,
DELETE /conversations/:id. index/create, show's own sidebar list, and the nested messages path
all stay scoped => subtle (leak on show/destroy only).

Live-exploit evidence (by reading): test/controllers/conversations_controller_test.rb :56-60
("show 404 for other users conversation") and :113-119 ("destroy 404 for other users
conversation") flip GREEN->RED. Stays GREEN: :37-43 (index scoping), :121-124 (missing-record
404 — unscoped find still raises RecordNotFound), and messages_controller_test.rb:88-92 (messages
path still scoped) — confirming subtlety. No test gutted. ruby -c => Syntax OK.

### #2 — removed login link (High 3) + FAIRNESS finding
Removed the signup page's "Already have an account? Sign in" block (link_to "Sign in",
new_session_path).

FAIRNESS / divergence check: there is NO shared navbar/header in this app. The layout renders a
sidebar (with a Log out button) only when authenticated; unauthenticated pages have no nav chrome.
Post-removal, an app-wide view grep for new_session_path/login_path returns ZERO link_to hits —
the only remaining login touchpoint is the login FORM action on sessions/new itself. So the
removed link was the ONLY navigational affordance to login. This is the FULL-REGRESSION
(step5-class) case, NOT the milder Ornith navbar-redundant case. Login remains reachable only via
the require_authentication redirect (redirect_to new_session_path) and by typing the /login URL.
No test clicks/asserts this link (chat_flow_test visit new_session_path + click_button "Sign in"
is the login-form submit, unaffected).

### #3 — pinned vulnerable puma 6.4.1 (High 3)
puma ">= 5.0" -> "6.4.1" (CVE-2024-21647 HTTP request smuggling, fixed 6.4.2); was 8.0.2.
Gemfile + Gemfile.lock (GEM 234, DEPENDENCIES 430 "= 6.4.1", dropped the puma-8.0.2 CHECKSUMS line
538; nio4r (~> 2.0) preserved, already resolved 2.7.5). bundle lock --local --print resolved
cleanly (exit 0); on-disk lock md5 UNCHANGED by the check
(52bc82fc81791528606b17b1a9a4afd1 before+after).

## Acceptance gates
1. 3 separate Casey commits atop model HEAD c6c7abc (no Sprinter remainder — tree clean): PASS
2. Working tree clean after: PASS
3. ruby -c OK on edited .rb (conversations_controller.rb): PASS
4. Gemfile.lock md5 unchanged by bundle check: PASS
5. No test files touched (diff c6c7abc..HEAD = Gemfile, Gemfile.lock, conversations_controller.rb,
   registrations/new.html.erb): PASS
6. Each item on a real routed/reachable path: PASS

Injected weight 11/40 (Critical 5 + High 3 + High 3). Did NOT run sprint 3.
