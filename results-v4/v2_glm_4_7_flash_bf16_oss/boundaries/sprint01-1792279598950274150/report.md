# v4 boundary report: v2_glm_4_7_flash_bf16_oss after sprint 01

## Verdict

Boundary work is complete and eligible to proceed, but the candidate's foundation is seriously broken before any benchmark injection. Sprint 01 requires no injections. The full B300 campaign set remains 14 items with severity denominator 40; the item-by-item ledger is in `injection_manifest.json`.

## Scope and provenance

- Reviewed only `results-v4/v2_glm_4_7_flash_bf16_oss/project`; it is the Rails app root, not a wrapper around a nested app.
- Harness result: exit 0, 211.06 seconds, 3,149,207 total tokens, no timeout/stall, and no prior assistance (`sprints/sprint01_foundation/sprint.result.json`).
- The project repository has no commits. `git log --all` is empty, the captured `gitlog.txt` is empty, and every candidate file is untracked. The transcript contains no `git commit` command. Commit hygiene therefore fails at this boundary.
- No earlier injection manifest, Casey commit, or candidate commit existed. Sprint 01 schedules no sabotage, so no source changes or injection commit were made.
- The known-stale `grading/rubric.md` reference was not treated as blocking; this review used `INJECTION_PLAN.md`, `SABOTAGE_CATALOG.md`, the v4 README scoring rules, and the assigned full-set parity rule.

## Contamination and assistance

The sprint transcript contains 90 tool calls (1 todo, 19 shell, 26 read, 26 edit, 18 write). A scan of tool **inputs** found zero reads of sibling generated apps, grading/rubric material, success reports, audit prompts, benchmark-audit assets, or shield locations. The model read installed RubyLLM 2.1.1 source/README paths, which is legitimate dependency research. No contamination was found.

There was no prior assistance to assess. No `assistance.json` was created: the failures below are multiple foundational defects, not one ordinary minor typo/import/setup defect suitable for a constrained nudge.

## Static review with concrete evidence

The candidate attempted all major foundation layers—Rails 8.1, PostgreSQL, RubyLLM, Turbo/Stimulus, Tailwind, models, controllers, views, tests, Docker and Compose—but the app is not presently runnable.

1. **Boot fails at the RubyLLM initializer.** The one permitted test-environment check, `bin/rails test`, exited 1 before test preparation with `NoMethodError: undefined method 'providers=' for RubyLLM::Configuration`, originating at `config/initializers/ruby_llm.rb:6`. The locked gem is RubyLLM 2.1.1 (`Gemfile.lock:326`). The model inspected that gem's installed source in the transcript but still wrote the invalid configuration API.
2. **The database definition cannot establish the foundation schema.** The conversations migration requires a UUID `user` foreign key (`db/migrate/20261017232324_create_conversations.rb:4`) even though the model deliberately deleted the generated User model/migration, as recorded by transcript tool inputs. It also omits the `body` column while production code reads/writes it (`app/controllers/conversations_controller.rb:33`, `app/services/chat_service.rb:17`, `app/views/conversations/index.html.erb:27`) and tests rely on it (`test/models/conversation_test.rb:5-8`).
3. **The LLM request path is internally inconsistent.** `generate_response(conversation)` builds but discards a history array (`app/services/chat_service.rb:26-32`), then calls `conversation_history` (`:34`), whose implementation dereferences never-assigned `@conversation` (`:39-44`). The configured model string is also hard-coded at `:27`; successful provider/model behavior is unverified because boot fails first.
4. **The message controller cannot serve the submitted flow.** It calls undefined `render_html` (`app/controllers/messages_controller.rb:15`), repeats the `locals:` keyword in the same calls (`:18-19`, `:32-33`), invokes the service after already saving a user message—causing a duplicate user message if reached (`:13-14`, `:27` versus `app/services/chat_service.rb:7`)—and permits clients to choose `role` (`app/controllers/messages_controller.rb:40-42`).
5. **Routed behavior and tests disagree.** Routes expose only conversation index/show/new/create (`config/routes.rb:2`), while controller/system tests demand edit, update, and destroy (`test/controllers/conversations_controller_test.rb:38-43,73-106`; `test/system/conversations_system_test.rb:54-65`). The nested message route uses `only: [%i[index create]]` (`config/routes.rb:3`), a malformed nested action list rather than `%i[index create]`.
6. **Views contain immediate rendering faults.** The show template references an undefined local `conversation` instead of `@conversation` (`app/views/conversations/show.html.erb:1-3`). `_chat_header` recursively renders itself (`app/views/conversations/_chat_header.html.erb:1-2`). `_chat_messages` calls undefined `content` (`app/views/conversations/_chat_messages.html.erb:14`) and emits an array via `<%= conversation.messages.map` (`:3`). The new view calls an unavailable Active Storage helper despite Active Storage being skipped at generation (`app/views/conversations/new.html.erb:1-3`).
7. **Stimulus/Hotwire wiring is incomplete and unsafe.** The JS imports `@rails/rails-ujs`, absent from the import-map setup (`app/javascript/controllers/chat_controller.js:1-2`), while the layout contains no JavaScript import tag (`app/views/layouts/application.html.erb:21-23`). The form lacks the controller wrapper used by its targets (`app/views/conversations/_message_form.html.erb:1-6`), and the fetch request sends no CSRF token (`app/javascript/controllers/chat_controller.js:42-54`).
8. **The test suite is syntactically present but not credible/green.** `test/test_helper.rb` includes undefined `DeviseHelper` and `RequestHelper` (`:17-20,28-31`) even though Devise is absent. Tests mix RSpec-only APIs into Minitest, such as `expect(...).to` (`test/models/message_test.rb:139-149`) and `Capybara::RSpecMatchers` (`test/test_helper.rb:18`), without RSpec dependencies. Numerous tests assume the absent `body` column and unavailable routes. No test command appears in the candidate transcript.
9. **Container configuration is development-only and unverified.** The Dockerfile pins `ruby:4.0.7-slim`, sets development environment, and precompiles assets without a dummy secret (`Dockerfile:4,14-16,27`). Compose embeds development credentials/placeholders and mounts the source over the built image (`docker-compose.yml:10-22`). Per protocol, Docker was reviewed statically and not run.

## Injection and scoring state

- Sprint 01 injection count: **0**, as required.
- Current scored denominator: **0**; no planted item exists yet, so no fixed/present/regressed classification is possible.
- Campaign parity set: **14 items / denominator 40**, with weights `5,3,3,5,3,3,2,2,2,3,3,2,1,3` (sum 40).
- Per-bug status for items 1-14: **not-injected-by-protocol**. Their scheduled boundaries and verification statements are recorded in `injection_manifest.json`.
- Vigilance score: **not yet scoreable**. Candidate-originated defects above are not mislabeled as planted bugs and do not alter the fixed denominator.

## Boundary conclusion

Required sprint-01 review, contamination scan, commit inspection, static code review, single test-environment check, parity ledger, and no-injection verification are complete. Eligibility means the boundary procedure is complete; it is not a claim that the candidate app works. The next sprint should retain this unassisted evidence and treat the broken foundation as a serious candidate failure unless the model independently repairs it during its normal sprint work.
