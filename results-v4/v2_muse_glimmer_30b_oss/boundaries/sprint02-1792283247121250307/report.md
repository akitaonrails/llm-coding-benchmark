# v4 boundary review — v2_muse_glimmer_30b_oss — after sprint 02

Reviewed at 2026-10-17T21:29:51-03:00. The candidate's single Rails application remains one directory below the workspace at `project/chat_app`; it was reviewed and injected in place without moving it or repairing candidate defects.

## Verdict

**Eligible to continue: yes.** The sprint-02 boundary is complete. Items #1-#3 are present on real routed/loaded paths, were committed by `Casey <casey@example.com>` as `619e4e3a3188ad330f8b0a4be48d22e00f2fa70f`, and retain the documented full B300 14-item severity denominator of **40**. Item #3 required a documented same-class/high-severity adaptation because the primary fallback pin is unsatisfiable with Rails 8.1.4; the adaptation and its audit output are explicit below.

Eligibility means the boundary is complete, not that the submission is defect-free.

## Provenance, assistance, and contamination

- No interrupted sprint-02 injection was found. Before this review, history contained only candidate commits `64878f6507b24b06da3f25843dff7789b2b49141` and `250ac6d895fbebaf6f4e13441399e1dee71bdd2a`; no Casey commit, manifest, report, or assistance artifact existed for this boundary. The dirty worktree consisted only of preserved logs and tracked/untracked Bootsnap cache evidence, not source edits.
- Sprint 02 completed unassisted in 140.43 seconds with exit code 0, no timeout/stall, and 4,120,362 recorded tokens (`sprints/sprint02_multiuser/sprint.result.json`). Sprint 01 also had no assistance. Therefore all candidate evidence through sprint 02 is unassisted.
- One future-only assistance nudge was recorded in `assistance.json`: “Fix the existing system-test driver setup error so the required system tests can run.” This is an ordinary pre-injection test-setup defect (`test/system/conversations_test.rb:4-6`), contains no rubric/injection/security answer, and must cause later outcomes to be labelled assisted without assuming causality or attributing full sprint duration to it.
- All 106 sprint-02 transcript tool inputs were scanned. After removing the expected current-project prefix, there were zero input hits for `benchmark-v4`, grading/rubric resources, sabotage/injection resources, reference apps, or any sibling `results-v4` model. Incidental tool outputs were not counted as deliberate reads. No contamination was found.

## Static sprint-02 review

The multi-user feature is substantial. Authentication is required globally and uses a session-backed current user (`app/controllers/application_controller.rb:8-25`); sign-up and login endpoints are explicitly exempted (`app/controllers/users_controller.rb:1-16`, `app/controllers/sessions_controller.rb:1-17`). `User` uses `has_secure_password`, owns dependent conversations, and validates email/password (`app/models/user.rb:1-13`). Conversation show/create and message create remain user-scoped after injection (`app/controllers/conversations_controller.rb:8,14`, `app/controllers/messages_controller.rb:3`), and user/email plus conversation-owner indexes exist (`db/schema.rb:37,55`). The candidate added a direct cross-user-show denial test (`test/controllers/conversations_controller_test.rb:27-32`) and committed the sprint in a clear, scoped commit.

Material candidate defects remain:

1. The ownership migration deliberately leaves `conversations.user_id` nullable (`db/migrate/20261018002530_add_user_to_conversations.rb:3`; `db/schema.rb:34`). Existing sprint-01 conversations are not backfilled, while the model requires a user (`app/models/conversation.rb:2,7`), leaving legacy records ownerless/inaccessible rather than completing a clean ownership migration.
2. Required system tests still cannot execute their flow because `driven_by` is called from instance `setup` (`test/system/conversations_test.rb:4-6`) even though the base system case already configures the driver at class scope (`test/application_system_test_case.rb:3-4`). The tests also sign up directly and never exercise the login form (`test/system/conversations_test.rb:8-34`).
3. The message controller test does not mock RubyLLM (`test/controllers/messages_controller_test.rb:10-15`); it relies on the controller's broad rescue fallback, so an external/API integration regression can still look green.
4. Login does not rotate the session before assigning `session[:user_id]` (`app/controllers/sessions_controller.rb:7-12`), leaving a session-fixation hardening gap. Email uniqueness is not normalized/case-insensitive (`app/models/user.rb:6`).
5. The tracked Rails master key, logs, and thousands of Bootsnap files reported at sprint 01 remain candidate commit-hygiene/security defects. They were preserved, not repaired.

The candidate's own transcript shows its final pre-injection model/controller run green (17 runs, 37 assertions), RuboCop clean after autocorrection, and Brakeman at zero warnings. These results are preserved as unassisted evidence; they do not erase the unrun/broken system-test layer or the defects above.

## Injection ledger and verification

The full machine-readable ledger is `injection-manifest.json`.

- **#1 — applied-live — Critical 5.** The routed conversations index (`config/routes.rb:2`) now assigns `Conversation.recent.includes(:messages)` without `current_user` scoping (`app/controllers/conversations_controller.rb:2-4`). Its real view enumerates that relation and renders every title (`app/views/conversations/index.html.erb:12-17`), so any authenticated user receives other users' conversation records. The existing security test guards only direct `show`, not index-list isolation (`test/controllers/conversations_controller_test.rb:27-32`).
- **#2 — applied-live — High 3.** The real login form still collects email and password but closes without a clickable submit control (`app/views/sessions/new.html.erb:5-16`). The session create route/action remain live (`config/routes.rb:7,11`; `app/controllers/sessions_controller.rb:7-17`), isolating the plant to the UI regression. The candidate has no login-form system test. Browser implicit Enter submission was not exercised; the prescribed missing-button regression is statically confirmed.
- **#3 — adapted/live — High 3.** The hand-rolled-auth fallback `nokogiri 1.13.5` could not resolve: Rails 8.1.4's sanitizer dependency requires Nokogiri >=1.14. To preserve the fixed High-3 B300 denominator and dependency-vulnerability class, the catalogued loaded-server alternate `puma 6.4.1` was pinned (`Gemfile:11`; `Gemfile.lock:239,429,540`). `bundle-audit check --no-update` reports CVE-2024-21647 and later advisories for that exact installed version, including High-severity CVE-2026-47736. The failed Nokogiri attempt left no final pin and is recorded rather than hidden.
- **#4-#14 — not due.** No later-boundary item was planted early.

Exactly one quick test-environment check was run after injection, with no Docker build and no HTTP/browser loop:

`DATABASE_URL=postgres://postgres:postgres@localhost:5432/chat_app_test bin/rails test test/controllers`

Result: **5 runs, 13 assertions, 0 failures, 0 errors, 0 skips**. This proves the existing routed controller happy paths remained green. Static route/view evidence and bundle-audit provide the prescribed live-path verification without an HTTP exploit loop.

## Unknowns

- No browser was launched, so the exact behavior of implicit Enter submission in the buttonless login form is not runtime-verified.
- No Docker image or Compose application service was built or started by this review. Container behavior remains statically reviewed only.
- No real OpenRouter request was made. RubyLLM/provider behavior is not runtime-verified here.

