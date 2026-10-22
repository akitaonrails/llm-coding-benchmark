# v4 boundary review — `v2_qwen35_397b_oss` after sprint 01

- Boundary: sprint 01 foundation, review-only.
- Verdict: eligible to proceed to sprint 02.
- Injection action: none, as required at this boundary.
- Common batch set: all 14 planned items, severity denominator **40**.
- Review method: static inspection plus one quick test-environment check; no Docker, HTTP loop, pod, campaign-setting, or sibling-app access.

## Run and repository evidence

The recorded sprint ran for 337.84 seconds and produced 6,472,132 tokens, 2,888 files, and one project commit. The harness recorded exit code 1 even though the final transcript shows a successful commit and the generated repository has a complete Rails application; this unexplained harness/result discrepancy is retained as an unknown rather than treated as model failure (`sprints/sprint01_foundation/sprint.result.json`, `sprints/sprint01_foundation/sprint01_foundation.result.json`, transcript line 351).

Commit `907d78fb1ae4724ca05364642fd35f897988c8c6` is authored by `Sprinter <sprinter@example.com>` with the descriptive subject “Initial commit: RubyLLM-powered chat application.” It is the only commit. No Casey injection commit was created because sprint 01 permits no injection.

## Foundation review

### Confirmed foundation

- The routed application exposes RESTful conversations and nested message creation, with the root mapped to the conversation index (`llm-chat-app/config/routes.rb:1`).
- Conversations and messages persist through Active Record with foreign-key and query-supporting indexes (`llm-chat-app/db/migrate/20261017173727_create_conversations.rb:3`, `llm-chat-app/db/migrate/20261017173729_create_messages.rb:3`).
- The message controller force-sets the user role and permits only content, avoiding client-controlled role assignment (`llm-chat-app/app/controllers/messages_controller.rb:4`, `:27`).
- RubyLLM is configured from `OPENROUTER_API_KEY`, not an application literal (`llm-chat-app/config/initializers/ruby_llm.rb:1`). The transcript records deliberate inspection of installed RubyLLM 2.1.1 source/config/OpenRouter provider at lines 30, 45, and 51.
- Turbo Stream response templates, a Stimulus form controller, escaped message rendering, Tailwind views, Dockerfiles, Compose, README documentation, model tests, controller tests, and nominal Capybara system tests are present (`llm-chat-app/app/views/messages/create.turbo_stream.erb:1`, `llm-chat-app/app/javascript/controllers/chat_form_controller.js:1`, `llm-chat-app/app/views/messages/_message.html.erb:11`, `llm-chat-app/test/system/conversations_test.rb:1`).
- The single allowed reviewer test check passed: **23 runs, 52 assertions, 0 failures, 0 errors, 0 skips**. This independently agrees with the candidate’s final recorded unit/integration run at transcript line 339. The transcript also records clean RuboCop, Brakeman, and bundle-audit results at lines 321, 333, and 336.

### Candidate defects retained (not repaired)

- Multi-turn context is not sent to RubyLLM. `conversation_messages` is assembled but never used; `chat.ask` receives only the newest message (`llm-chat-app/app/controllers/messages_controller.rb:31`). Persistence exists, but LLM continuity does not.
- LLM exceptions are copied into an assistant message shown to the user, potentially exposing operational details (`llm-chat-app/app/controllers/messages_controller.rb:44`).
- The claimed system-test layer is not runnable as committed: `test/system/conversations_test.rb:1` requires `application_system_test_case`, but `test/application_system_test_case.rb` is absent. The executed `bin/rails test` evidence therefore validates the 23 model/controller tests, not the five browser tests.
- The controller test does not mock RubyLLM or assert a successful provider response. Its two-message assertion can pass through the broad rescue path that manufactures an assistant error message (`llm-chat-app/test/controllers/messages_controller_test.rb:4`; controller `:44`).
- Commit hygiene is poor despite the descriptive message: the sole commit tracks `config/master.key` (32-byte secret material), both SQLite databases, logs, and extensive Bootsnap cache artifacts; `.gitignore` is absent. The secret value was not displayed during this review. The prompt explicitly prohibited committing secrets.
- The show view queries `Conversation.recent` directly rather than receiving the collection from the controller, coupling data access to rendering (`llm-chat-app/app/views/conversations/show.html.erb:17`).

These are baseline implementation findings, not planted-sabotage statuses, and were intentionally left unchanged.

## Transcript contamination review

Tool inputs were extracted from the NDJSON and inspected separately from tool outputs. No deliberate input referenced a sibling generated app, `CLAUDE.md`, a grading rubric, audit prompt, success report, benchmark-audit directory, or shield path. All deliberate file reads were inside this model’s project except the three installed RubyLLM source reads listed above. Incidental command output was not classified as a read. Status: **clean**.

## Injection manifest and per-bug status

No item is eligible for planting after sprint 01. The full B300 common set remains scheduled with denominator 40:

| # | Weight | Sprint scheduled | Boundary status | Verification |
|---:|---:|---:|---|---|
| 1 | 5 | after 02 | not yet injected | prohibited at sprint-01 boundary |
| 2 | 3 | after 02 | not yet injected | prohibited at sprint-01 boundary |
| 3 | 3 | after 02 | not yet injected | target/recipe selection deferred; batch weight fixed at 3 |
| 4 | 5 | after 03 | not yet injected | future boundary |
| 5 | 3 | after 03 | not yet injected | future boundary |
| 6 | 3 | after 03 | not yet injected | future boundary |
| 7 | 2 | after 04 | not yet injected | future boundary |
| 8 | 2 | after 04 | not yet injected | future boundary |
| 9 | 2 | after 04 | not yet injected | future boundary |
| 10 | 3 | after 05 | not yet injected | future boundary |
| 11 | 3 | after 05 | not yet injected | future boundary |
| 12 | 2 | after 05 | not yet injected | future boundary |
| 13 | 1 | after 05 | not yet injected | future boundary |
| 14 | 3 | after 05 | not yet injected | future boundary |

Count by status: 0 applied-live, 0 adapted, 0 N/A, 14 not-yet-injected. Current planted severity weight is 0; the campaign scoring denominator remains the prescribed common-set **40**. No fixed/present/regressed sabotage judgment is possible before planting, so each item is honestly recorded as not yet injected rather than guessed.

## Eligibility conclusion

Required sprint-01 boundary work is complete and verified: the foundation was reviewed with concrete evidence, transcript inputs are clean, the no-injection rule was obeyed, the 14-item/40-weight batch manifest is recorded, one permitted test check passed, and candidate defects were preserved. The model is eligible to proceed to sprint 02, where items 1–3—not earlier—are to be injected and live-verified.
