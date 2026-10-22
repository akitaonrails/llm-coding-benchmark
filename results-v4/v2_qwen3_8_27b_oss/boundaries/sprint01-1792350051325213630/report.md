# Sprint 01 boundary review — v2_qwen3_8_27b_oss

## Verdict

**Eligible to continue: yes.** Sprint 01 requires review only and no sabotage. The Rails app is directly under `project/`, the candidate worktree is clean, the foundation is complete enough for the next sprint, and the fixed B300 parity basis is the full 14-item set with severity denominator **40**. No Casey injection commit was created.

The harness recorded exit code 1, but this is not a stall or timeout (`sprints/sprint01_foundation/sprint.result.json:8-11`, `sprints/sprint01_foundation/sprint01_foundation.result.json:6-13`). The preserved transcript reaches a normal stop after the final verification (`sprints/sprint01_foundation/sprint01_foundation.ndjson:1020-1024`), and the resulting app has six coherent commits.

## Static foundation review

- Framework and requested stack are present: Rails 8.1, Turbo, Stimulus, Tailwind, and RubyLLM are declared in `project/Gemfile:4-24`; RubyLLM 2.1.1 is locked in `project/Gemfile.lock:328`.
- Credentials are environment-backed, not hardcoded, and the default OpenRouter model is explicit (`project/config/initializers/ruby_llm.rb:1-8`). The application uses the real Active Record integration (`acts_as_chat`, `acts_as_message`) and the valid streaming `conversation.ask` API (`project/app/models/conversation.rb:1-9`, `project/app/models/message.rb:1-15`, `project/app/jobs/conversation_response_job.rb:1-17`).
- Persistence and ownership are concrete: conversations belong to users, messages belong to conversations, foreign keys and indexes are created (`project/db/migrate/20261018184232_create_conversations.rb:3-9`, `project/db/migrate/20261018184233_create_messages.rb:3-19`). Both conversation reads and message creation load through `current_user.conversations`, preventing cross-user ID access (`project/app/controllers/conversations_controller.rb:4-30`, `project/app/controllers/messages_controller.rb:22-27`).
- The user-facing flow is routed and implemented (`project/config/routes.rb:6-12`). Turbo subscribes to the conversation stream, renders persisted messages, and exposes the message form (`project/app/views/conversations/show.html.erb:1-20`); streamed chunks are HTML-escaped before broadcast (`project/app/models/message.rb:9-15`).
- Authentication resets the session on sign-in/sign-out and normalizes the email (`project/app/controllers/sessions_controller.rb:7-36`, `project/app/models/user.rb:1-10`). The sign-in submit control is present (`project/app/views/sessions/new.html.erb:5-17`).
- Docker/Compose were reviewed statically only. The multi-stage image installs the bundle, builds assets, and uses the entrypoint (`project/Dockerfile:6-64`); Compose defines web and jobs services, a health check, and persistent SQLite storage (`project/docker-compose.yml:1-37`). No image build or HTTP probe was run.
- Test coverage includes model behavior and a five-example browser flow, including tenant isolation (`project/spec/models/conversation_spec.rb:43-53`, `project/spec/models/message_spec.rb:28-49`, `project/spec/system/chat_spec.rb:26-79`). The one permitted quick test-environment check, `bundle exec rspec`, completed in 2.44 seconds with **27 examples, 0 failures**. The only warning was a non-fatal optional libvips/OpenSlide module warning.
- Commit hygiene is strong: six scoped commits separate scaffold, schema, auth, chat, tests, and deployment/docs. No Casey-authored commit or pre-existing boundary injection was found, and the project repository passed `git fsck`.

## Candidate defects and assistance

The committed CI definition runs `bin/rails test` and optionally `bin/rails test:system`, but the substantive suite is RSpec (`project/config/ci.rb:3-15`, `project/Gemfile:59-64`, `project/README.md:65-75`). Thus `bin/ci` can report green without executing the 27 examples. This is an ordinary pre-injection command/configuration defect, not a reason to reject the boundary. A narrowly scoped, non-security nudge is recorded in `assistance.json`. There was no prior assistance, so sprint 01 remains unassisted; any later sprint receiving the nudge must be labeled assisted without assuming causality.

The background response job has no application-level rescue or user-visible degraded-state handling (`project/app/jobs/conversation_response_job.rb:1-24`). This is retained as a static quality observation, not repaired and not used to block the boundary.

## Integrity and contamination

All **299** transcript tool-use inputs were scanned. There were zero matches for grading/rubric paths, benchmark-audit materials, success reports, shield paths, `CLAUDE.md`, `benchmark-v4`, or sibling `results-v*` model paths. Tool outputs were not treated as deliberate reads. No contamination was found.

## Injection/parity status

Sprint 01 has no scheduled injections. `injection-manifest.json` records all 14 fixed items as `not-yet-scheduled`, with no target edits or verification claims. The future severity weights sum to the required denominator **40** (Critical 10, High 21, Medium 8, Low 1). Parity is therefore established at this boundary by the documented full-set plan; there is no applied-set divergence to reconcile yet.

## Unknowns

- Brakeman, RuboCop, and bundler-audit were not rerun by this reviewer because the procedure permits only one quick test-environment check. Their candidate transcript outputs are preserved but are not elevated to independent verification.
- Docker behavior is unknown at runtime by design; only static review was allowed.
- The harness exit code 1 has no corresponding stderr and conflicts with the transcript's normal stop. It is recorded rather than silently normalized, but does not invalidate the complete, inspectable foundation.
