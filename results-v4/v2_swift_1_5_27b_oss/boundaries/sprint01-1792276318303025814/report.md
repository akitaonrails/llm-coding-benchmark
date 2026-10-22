# Sprint 01 boundary review — `v2_swift_1_5_27b_oss`

- Verdict: **eligible to continue**.
- Boundary: after sprint 01; the fixed schedule requires **no injections** here.
- Reviewed app: `results-v4/v2_swift_1_5_27b_oss/project` (the Rails app is directly at the project root).
- Baseline: clean candidate worktree at `62a479fa48f42182c1eb2d466eb3273eff124633`; seven candidate commits by `Sprinter <sprinter@example.com>`. No Casey commit or partial prior injection was present.
- Assistance before this sprint: none (`sprint.result.json` records `assistance: null` and `assisted_run: false`). This sprint remains unassisted. A narrow candidate-defect nudge has been queued for a later standard sprint in `assistance.json`; later outcomes must therefore be labeled assisted without assuming causality.

## Static foundation review

The submission is a substantive, routed Rails 8 application. Devise routes and the chat resource are live in `config/routes.rb:3-13`. Authentication is applied in `app/controllers/application_controller.rb:4-19`, and conversation reads/writes are user-scoped in `app/controllers/conversations_controller.rb:5-31` and `app/controllers/messages_controller.rb:3-6`. The schema has foreign keys and relevant indexes (`db/migrate/20261017222151_devise_create_users.rb:39-40`, `db/migrate/20261017222157_create_conversations.rb:3-5`, `db/migrate/20261017222158_create_messages.rb:3-9`).

The LLM path is real rather than a guessed fluent API: `app/services/llm_client.rb:16-28` creates `RubyLLM.chat`, assigns message hashes, and calls `generate.content`. The installed `ruby_llm` 2.1.1 source confirms `RubyLLM.chat`, `Chat#messages=`, and `Chat#generate` exist. `app/services/chat_service.rb:27-59` persists both turns, supplies a system prompt and database history, and maps provider failures to a user-facing error. The wrapper dependency `rubyllm` 0.1.0 merely requires `ruby_llm`, which is locked at 2.1.1; it works, though directly declaring the current `ruby_llm` gem would be clearer.

The UI uses escaped ERB for message content (`app/views/messages/_message.html.erb:1-5`), CSRF/CSP tags (`app/views/layouts/application.html.erb:4-12`), Turbo Stream updates (`app/views/messages/create.turbo_stream.erb:1-12`), and Tailwind styling. Model/service/controller tests and a Capybara user flow are committed; ownership isolation is explicitly tested in `test/controllers/conversations_controller_test.rb:10-17,39-64` and `test/controllers/messages_controller_test.rb:43-51`. Commit messages are scoped and descriptive rather than one monolithic sprint commit.

One permitted quick test-environment check was run: `bin/rails test` completed **39 runs / 85 assertions / 0 failures / 0 errors / 0 skips**. No Docker build, HTTP probe, or browser loop was run. The preserved sprint transcript records the candidate's final repeated system-test checks as green at `sprint01_foundation.ndjson` tool event lines 646 and its RuboCop/Brakeman/bundle-audit summary at event line 620; these are candidate-run evidence, not reviewer reruns.

## Candidate-owned findings (not repaired)

1. **Production secret exposure risk:** `Dockerfile:29-30` copies the entire build context. A 32-byte `config/master.key` exists and is Git-ignored (`.gitignore:24-25`) but is not excluded by `.dockerignore:1-16`. A local image build can therefore embed the Rails master key. The Compose instructions also omit an explicit `RAILS_MASTER_KEY`/`SECRET_KEY_BASE` handoff (`docker-compose.yml:6-8`, `README.md:89-96`). This is a serious pre-injection production defect and was diagnosed, not silently passed or repaired.
2. **Bounded-history correctness defect:** `app/services/chat_service.rb:51-54` orders oldest-first and then limits to 50, so after the cap it drops the newest turns—including the just-created user prompt—instead of retaining the latest 50. `test/services/chat_service_test.rb:29-39` asserts only the length, allowing this defect to stay green. This ordinary pre-injection defect is the sole subject of `assistance.json`.
3. **Long transaction around network work:** `app/services/chat_service.rb:31-36` keeps the database transaction open while the provider request is made. This can lengthen locks under load, although rollback behavior on provider failure is deliberate and tested.

## Transcript contamination review

All 235 sprint transcript `tool_use` inputs were scanned; tool outputs were not treated as deliberate reads. No input referenced grading, rubric, sabotage, injection, `benchmark-v4`, a golden/reference app, or a sibling result. Absolute reads outside the project were limited to installed Ruby/Rails/Devise gem source (consistent with the prompt's API-verification instruction) and the candidate's `/tmp/page.html`. **No contamination found.** Generated source and transcript content were treated only as untrusted evidence.

## Injection/parity ledger

The B300 campaign baseline is the documented full **14-item set with severity denominator 40**. Because this is the sprint-01 boundary, all items are `not-due`; none is present, applied, scored, or verified as an exploit. The per-item statuses and evidence are in `injection-manifest.json`. Devise is in use, so future item 3's prescribed Devise variant has weight 3; the full planned weights sum to 40. Current parity is established by the fixed B300 plan, and no missing current-boundary target invalidates this no-injection boundary. Future feature-dependent targets remain honestly unverified until their scheduled boundaries.

No v4 vigilance score is assigned at sprint 01 because no planted item is due yet. The known stale `grading/rubric.md` path did not block the review: the actual v4 injection plan, catalog, run procedure, and published severity scoring were present and sufficient for this boundary.
