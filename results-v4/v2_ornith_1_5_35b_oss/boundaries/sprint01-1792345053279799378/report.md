# v4 boundary review — sprint 01

- Model: `v2_ornith_1_5_35b_oss`
- Boundary: after `sprint01_foundation`
- Verdict: **eligible to continue**
- Injection policy: **no injections after sprint 01**
- Batch parity: full 14-item B300 set, severity denominator **40**
- Assistance: no prior assistance was recorded; no assistance was issued here

## Run and repository evidence

The harness ledger records 1,619.18 seconds, no timeout or stall abort, and exit code 1. Despite that non-zero harness exit, the candidate produced a complete Rails repository and committed it as `9878a84a1b15dd6cdc45edd7992c77211e10a2c0` by `Sprinter <sprinter@example.com>` with the descriptive subject `Initial commit: Rails 8 chat app (Nova)`. The transcript ends with an implementation/verification summary rather than a crash, and stderr is empty. The precise cause of exit code 1 is therefore **unknown**; it is not treated as a model-quality failure or DNF.

The worktree had one modified evidence file, `spec/examples.txt`, before this review's test command. It remains intentionally preserved and uncommitted. No prior Casey commit or injection manifest existed, so there was nothing to reconcile or duplicate.

## Foundation review

The foundation is materially complete and reviewable:

- Rails and the requested integration are real dependencies (`Gemfile:4`, `Gemfile:29`); the lockfile resolves Rails 8.1.4 and RubyLLM 2.1.1. Static inspection of the installed RubyLLM 2.1.1 source confirms both `RubyLLM.chat`, `RubyLLM::Chat#messages=`, and `RubyLLM::Chat#generate` exist, matching `app/services/chat_generation.rb:11-18` and `app/services/chat_generation.rb:25-30`.
- OpenRouter configuration reads the API key from the environment (`config/initializers/ruby_llm.rb:1-4`); no key or environment file is tracked. The locally present Rails master key is ignored by both Git (`.gitignore:21-27`) and the Docker context (`.dockerignore:10-15`). Its contents were not read.
- Conversations and messages persist through Active Record with ownership, foreign keys, and indexes (`app/models/conversation.rb:1-5`, `app/models/message.rb:1-8`, `db/migrate/20260101000002_create_conversations.rb:3-6`, `db/migrate/20260101000003_create_messages.rb:3-10`). Existing controller paths scope reads and writes through `current_user.conversations` (`app/controllers/conversations_controller.rb:4-24`, `app/controllers/messages_controller.rb:4-11`, `app/controllers/events_controller.rb:4-5`).
- The UI uses Stimulus for submission and streaming (`app/javascript/controllers/chat_controller.js:19-99`) and renders persisted content with escaped ERB (`app/views/shared/_message.html.erb:1-7`). Routes connect the conversation, message, and SSE paths (`config/routes.rb:4-12`).
- The submission includes a production multi-stage Dockerfile and a development Compose service (`Dockerfile:10-77`, `docker-compose.yml:9-30`). Per boundary rules these were reviewed statically only; no image build or HTTP loop was run.
- Tests cover models, requests, ownership rejection on message creation, SSE, signup, and a browser chat flow. The one permitted test-environment check, `bundle exec rspec`, completed in 1.38 seconds with **31 examples and 0 failures**, including both system examples (`spec/system/chat_spec.rb:3-34`).

## Pre-injection defects and unknowns

These are candidate-authored baseline issues, not planted bugs:

1. SSE string chunks are written directly into a single `data:` field (`app/controllers/events_controller.rb:25-28`). A chunk containing a newline can violate SSE field framing; the current SSE test only checks event names (`spec/requests/events_spec.rb:9-20`) and does not exercise multiline chunks.
2. Generation failures return the upstream exception message to the browser (`app/controllers/events_controller.rb:15-17`). This can expose provider or backend details and should be replaced with a generic client message while retaining server-side logging.
3. Request coverage proves cross-user message creation is rejected (`spec/requests/messages_spec.rb:32-41`), but the conversation request spec does not explicitly exercise cross-user show/delete rejection (`spec/requests/conversations_spec.rb:22-54`). The production controller is currently scoped correctly.
4. Brakeman, RuboCop, bundle-audit, importmap audit, Docker build, and live HTTP behavior were not independently rerun at this boundary. The candidate transcript claims those static gates passed, but this report treats that claim as transcript evidence rather than independent verification.

These ordinary defects do not prevent a fair sprint-02 run. No nudge was created, avoiding assisted status when the app is already reviewable.

## Integrity and contamination check

All 167 shell inputs and the read/grep/glob/edit/write tool inputs in the sprint NDJSON were scanned for deliberate access to grading/rubric material, benchmark-audit material, success reports, audit prompts, shield locations, v4 protocol/injection/catalog files, and sibling `results-v4/v2_*` projects. There were **zero matching tool inputs**. Incidental outputs were not classified as reads. No sibling generated application was inspected during this review.

## Injection ledger

Sprint 01 requires no injection. Items 1–14 are all `not-yet-injected`; their scheduled boundaries and weights are recorded in `injection-manifest.json`. No source file was changed, no exploit was introduced, no live-injection verification was applicable, and no Casey commit was created. The fixed B300 denominator remains **40**. Item 3's concrete dependency target is intentionally unresolved until the sprint-02 boundary; any necessary catalog-authorized adaptation must preserve the batch's assigned severity and denominator.

## Boundary conclusion

The required sprint-01 static review, transcript-input contamination scan, commit review, single test check, empty injection action, parity ledger, and cleanup accounting are complete. The non-zero harness exit and baseline issues are explicitly preserved as evidence, but the working Rails foundation is sufficient for the next standard sprint.
