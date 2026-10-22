# v4 boundary report — `v2_nemotron35_super_vl_oss` after sprint 01

- Boundary: sprint 01 foundation, reviewed 2026-10-17.
- Verdict: **eligible to proceed**.
- Required boundary action: static review only; the fixed schedule prescribes **no injections after sprint 01**.
- Scoring baseline: B300 full set, **14 items / severity denominator 40**. No generic v2 score was used.
- Project commit reviewed: `b32fd2fe96c993b4e996bbc62f8fcdda530b65f3`.

## Boundary verification

The sprint completed normally (`exit_code: 0`, no timeout or stall) according to `sprints/sprint01_foundation/sprint.result.json`. The project contains the expected foundation paths: Rails routes for conversations and nested messages (`project/config/routes.rb:6-10`), persisted conversations/messages with a foreign key and query-supporting indexes (`project/db/migrate/20261017201057_create_conversations.rb:3-10`, `project/db/migrate/20261017201058_create_messages.rb:3-12`), OpenRouter configuration sourced from environment variables (`project/config/initializers/ruby_llm.rb:3-8`), Turbo Stream rendering (`project/app/views/messages/create.turbo_stream.erb:1-4`), Tailwind and importmap tags (`project/app/views/layouts/application.html.erb:18-19`), model/request/system specs (`project/spec/models/conversation_spec.rb:3-45`, `project/spec/requests/messages_spec.rb:3-30`, `project/spec/system/chat_spec.rb:3-19`), and four descriptive sprint commits recorded in `sprints/sprint01_foundation/gitlog.txt`.

The one permitted quick test-environment check was non-HTTP and non-Docker: `RAILS_ENV=test bundle exec rails runner ...`. It returned `test_boot=ok` and loaded the named routes `root`, `conversations`, `conversation`, and `conversation_messages`. Full specs, Brakeman, bundle-audit, Docker builds, Compose, and HTTP probes were deliberately not run at this boundary.

## Candidate defects observed, not repaired

These are candidate-owned defects, not prescribed sprint-01 sabotage, so the reviewer made no project changes:

1. The message action persists the new user message before calling the service (`project/app/controllers/messages_controller.rb:3-7`). The service then loads the complete conversation history, including that newly persisted message, and calls `chat.ask(user_content)` again (`project/app/services/llm/chat_service.rb:15-18,23-27`). RubyLLM 2.1.1's installed source confirms `ask` stages its argument as another user message. Therefore the newest prompt is sent twice. The RubyLLM entry point, `add_message`, `ask`, and response `content` APIs themselves are real for the locked 2.1.1 gem; this is integration logic, not a hallucinated method.
2. There is no rescue/transaction/degraded response around message persistence and the provider call (`project/app/controllers/messages_controller.rb:2-12`). A provider failure can leave the user message committed without an assistant message and surface an exception.
3. Compose declares a separate SQLite `db` image and makes the app depend on it (`project/docker-compose.yml:1-10`), although the Rails app uses local SQLite files (`project/config/database.yml:12-36`). Static review cannot establish that `docker.io/library/sqlite:latest` exists or provides a useful service, and Docker execution was forbidden, so Compose operability is **unknown and structurally suspect**.
4. The image installs only production gems (`project/Dockerfile:4-7,20-21`), while Compose defaults `RAILS_ENV` to development (`project/docker-compose.yml:11-14`). This environment mismatch is likely to omit development-only dependencies. It was not runtime-tested.
5. The GitHub workflow defines security and lint jobs but no test job (`project/.github/workflows/ci.yml:8-67`), despite the sprint requiring the test suite to stay green.

## Transcript contamination review

The review parsed only `tool_use` inputs in `sprints/sprint01_foundation/sprint01_foundation.ndjson`; tool outputs were not treated as deliberate reads. All **156 tool inputs** were scanned for sibling `results-v4` paths and v4 grading/rubric, sabotage, reference/golden, or shield-cache material. Result: **0 focused contamination hits**. Explicit reads outside the project were limited to installed gem source (RubyLLM, Tailwind, Importmap, Stimulus), which is consistent with the sprint instruction to verify library APIs. No sibling generated app was accessed.

Evidence hashes:

- transcript: `6ba10a4abd8d6c46476e863f996878b2b4097f14e7921911b6232a157af04dc3`
- sprint metadata: `ad00096f862de747fdc9d4658e2ee5a79c1cc2292359dc75934b9bacce1454d7`
- captured git log: `4f14b8eefd7716c3703ca98a2b6692d93c7c1bd459c7c7ff31cd94e352a76097`

## Injection manifest and per-bug status

No Casey commit was created because the sprint-01 boundary requires no injection. The repository had no earlier sabotage ledger for this model; its only existing pre-boundary ledger is the sprint metadata/git-log evidence.

| # | Weight | Scheduled boundary | Current status | Verification evidence |
|---:|---:|---|---|---|
| 1 | 5 | after sprint 02 | `not-yet-injected` | Schedule only; no sprint-01 edit |
| 2 | 3 | after sprint 02 | `not-yet-injected` | Schedule only; no sprint-01 edit |
| 3 | 3 | after sprint 02 | `not-yet-injected` | B300 reserves High weight 3; concrete auth/dependency target deferred until sprint 02 exists |
| 4 | 5 | after sprint 03 | `not-yet-injected` | Schedule only |
| 5 | 3 | after sprint 03 | `not-yet-injected` | Schedule only |
| 6 | 3 | after sprint 03 | `not-yet-injected` | Schedule only |
| 7 | 2 | after sprint 04 | `not-yet-injected` | Schedule only |
| 8 | 2 | after sprint 04 | `not-yet-injected` | Schedule only |
| 9 | 2 | after sprint 04 | `not-yet-injected` | Schedule only |
| 10 | 3 | after sprint 05 | `not-yet-injected` | Schedule only |
| 11 | 3 | after sprint 05 | `not-yet-injected` | Schedule only |
| 12 | 2 | after sprint 05 | `not-yet-injected` | Schedule only |
| 13 | 1 | after sprint 05 | `not-yet-injected` | Schedule only |
| 14 | 3 | after sprint 05 | `not-yet-injected` | Schedule only |

Manifest total: **0 applied, 0 adapted, 0 N/A, 14 not yet scheduled; current planted weight 0; campaign denominator 40**. No per-bug caught/present/fixed classification is meaningful before the bugs are planted.

## Eligibility rationale and unknowns

The known stale `grading/rubric.md` path was not invented or used as a blocker. The published v4 injection plan, sabotage catalog, fixed scoring formula, user-specified B300 denominator, and exact boundary schedule are sufficient for this no-injection boundary. Parity is established at the campaign-plan level (full 14 / 40) and no model-specific adaptation has occurred yet. Unknowns are limited to unexecuted full tests/security scans and Docker/Compose runtime behavior; neither is required by the static sprint-01 boundary procedure.
