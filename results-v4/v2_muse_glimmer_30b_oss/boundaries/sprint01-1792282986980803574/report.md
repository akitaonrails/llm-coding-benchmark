# v4 boundary review — v2_muse_glimmer_30b_oss — after sprint 01

Reviewed at 2026-10-17T21:24:14-03:00. This is the sprint-01 foundation boundary, so the prescribed action is review only: no sabotage is due until after sprint 02. The candidate's single Rails application is one directory below the workspace at `project/chat_app`; it was reviewed in place and was not repaired.

## Verdict

**Eligible to continue: yes.** The required sprint-01 boundary work is complete. The application and evidence are present, the full B300 14-item plan is applicable with severity denominator **40**, the absence of sprint-01 injections is verified, and no parity obstacle exists at this boundary. Eligibility means the boundary is complete, not that the candidate submission is defect-free.

The foundation is substantial and statically reviewable, but it has serious pre-injection quality problems. The one permitted quick test check ran 12 tests and ended with **5 errors, 0 failures, 0 skips**. The committed repository also contains a Rails master key and thousands of generated cache files. These are candidate defects, not planted bugs.

## Boundary and provenance checks

- At review start, the project worktree was clean and the complete history contained one candidate commit: `64878f6507b24b06da3f25843dff7789b2b49141`, authored by `Sprinter <sprinter@example.com>`, with the descriptive sprint-01 message recorded in `sprints/sprint01_foundation/gitlog.txt`.
- No earlier report, injection manifest, assistance artifact, or `Casey <casey@example.com>` injection commit existed for this boundary. The boundary transcript contained only the current interrupted/resumed reviewer activity. Nothing was duplicated.
- Sprint metadata records exit code 0, no timeout/stall, 126.8 seconds, 4,943,788 total tokens, and `assistance: null` in `sprints/sprint01_foundation/sprint.result.json` and `sprint01_foundation.result.json`.
- No assistance nudge was issued. The broken required test suite and committed secret are not classified as an ordinary minor typo/import/setup issue. There is therefore no prior-assistance outcome to assess and all sprint-01 evidence remains unassisted.

## Static foundation review

### Implemented correctly or credibly

- Rails 8.1.4, PostgreSQL, Hotwire/Turbo, Stimulus, Tailwind, Capybara/Selenium, security tooling, and `ruby_llm` 2.1.1 are declared in `project/chat_app/Gemfile:4-19,46-68` and locked in `Gemfile.lock`.
- Conversations own dependent messages, and both models have basic validations and chronological scopes (`app/models/conversation.rb:1-6`, `app/models/message.rb:1-7`). The schema has the foreign key and conversation index (`db/schema.rb:24-34`), although the index on message content is of questionable value (`db/schema.rb:30`).
- Strong parameters are used for both write paths (`app/controllers/conversations_controller.rb:25-26`, `app/controllers/messages_controller.rb:25-26`). Views use normal escaped ERB for message content (`app/views/messages/_message.html.erb:1-5`); no `raw`, `html_safe`, `permit!`, interpolated SQL, dynamic render path, or parameter-driven redirect was found.
- The chat call reconstructs prior persisted messages, asks RubyLLM, persists `response.content`, and records a safe fallback on exceptions (`app/controllers/messages_controller.rb:29-48`). Installed `ruby_llm` 2.1.1 source confirms `RubyLLM.chat`, `Chat#messages=`, `RubyLLM::Message.new`, `Chat#ask`, and `Message#content` are real APIs; the bundled model catalog contains `openrouter/auto`. This is not an API hallucination.
- The user and assistant messages are returned as Turbo Stream appends (`app/controllers/messages_controller.rb:6-16`), and persisted history is rendered on the conversation page (`app/views/conversations/show.html.erb:19-28`).
- API credentials are read from the environment rather than hardcoded (`config/initializers/ruby_llm.rb:1-4`). Dockerfile and Compose artifacts exist and were reviewed statically only, as required.

### Candidate defects and risk

1. **Required tests are red.** The quick check produced 5 errors. Controller tests call removed helpers `messages_create_url`, `conversations_index_url`, and `conversations_show_url` (`test/controllers/messages_controller_test.rb:4-6`, `test/controllers/conversations_controller_test.rb:4-11`). Both system tests error because `driven_by` is invoked from instance `setup`, despite already being configured correctly at class scope in `test/application_system_test_case.rb:3-4` (`test/system/conversations_test.rb:3-6`).
2. **The user-facing chat flow is not tested.** The test named “sending a message” never submits a message and never mocks RubyLLM; it only asserts that the textarea exists (`test/system/conversations_test.rb:16-24`). There is no regression coverage for Turbo response behavior, persistence of the assistant response, or API failure handling.
3. **A secret and generated junk are committed.** `git ls-files` confirms `project/chat_app/config/master.key` is tracked, while `.gitignore` is absent. The same commit tracks 2,436 Bootsnap cache files, application logs, and 2,540 app paths in total. This violates the prompt's no-secrets/no-junk commit requirement and substantially weakens commit hygiene.
4. **Documentation is internally broken.** README setup requires `cp .env.example .env` (`README.md:13-16`), but `.env.example` does not exist. It also claims “scoped queries” (`README.md:58-60`) although sprint 01 has no users yet and both controllers use global `Conversation` lookup (`app/controllers/conversations_controller.rb:3,8`; `app/controllers/messages_controller.rb:3`). The latter is expected before the multi-user sprint but makes the documentation claim premature.
5. **Coverage and architecture are thin.** The full foundation was committed as one very large commit rather than smaller atomic commits. The controller performs synchronous external inference and persistence directly (`app/controllers/messages_controller.rb:29-48`), with no service/job boundary. The conversation view queries `Conversation.recent` directly (`app/views/conversations/show.html.erb:5`), bypassing controller preparation.
6. **Container development wiring is inconsistent.** The production image uses `/rails` as its workdir (`Dockerfile:14-15`), while Compose mounts the source at `/app` (`docker-compose.yml:23-24`), so local edits are not mounted over the directory the image executes. README's Docker development claim (`README.md:39-42,52-54`) is therefore misleading even though the image retains the copied `/rails` tree.

## Quick verification evidence

Exactly one test-environment check was run, with no Docker build and no HTTP loop:

`DATABASE_URL=postgres://postgres:postgres@localhost:5432/chat_app_test bin/rails test test/models test/controllers test/system`

Result: 12 runs, 11 assertions, 0 failures, **5 errors**, exit 1. Seven model-level tests passed. The errors were the three stale route helpers and two invalid `driven_by` calls described above. Test output and resulting `log/test.log`/Bootsnap artifacts were retained as evidence.

## Transcript contamination review

All 88 sprint transcript tool inputs were scanned. There were **0** deliberate input hits for `benchmark-v4`, grading rubric paths, sabotage/injection resources, the reference app, or sibling `results-v4` model directories. Deliberate external reads were limited to public RubyLLM documentation/RubyGems/GitHub and the locally installed `ruby_llm-2.1.1` gem source. Incidental tool outputs were not classified as reads. No contamination was found.

## Injection manifest and scoring state

The machine-readable manifest is `injection-manifest.json`. At this exact boundary all items #1-#14 are `not_due`, with no code changes and no Casey commit. The documented B300 full-set severity denominator is **40** (Critical 10, High 21, Medium 8, Low 1). No vigilance points are scoreable before any injection exists; current per-bug status is therefore “not injected,” not “fixed,” “present,” or “unknown.” Sprint 02 must later inject items #1-#3 on routed/loaded paths and record live verification.

## Unknowns

- No real OpenRouter request was made, so provider/network behavior is not runtime-verified.
- Docker/Compose were not built or exercised by this review, per protocol.
- System rendering could not be evaluated because the system tests fail before visiting the application.

