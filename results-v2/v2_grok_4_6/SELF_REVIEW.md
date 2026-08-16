# Self-review

Re-verified against the tree in this directory on 2026-08-15. No code was changed in this phase.

## 1. Goal verification table

| Goal | Verdict | Evidence |
| --- | --- | --- |
| G1 | PASS | `ruby -v` → 4.0.6; `bin/rails -v` → 8.1.3.1; `mise.toml` pins ruby 4.0.6; `config/application.rb:6-10` leaves Active Record / Active Job / Action Mailer commented out; no `config/database.yml`; app lives at this directory root (no nested Rails app). |
| G2 | PASS | Tailwind via `gem "tailwindcss-rails"` + `app/assets/tailwind/application.css`; Hotwire in `Gemfile:12-14` and `app/javascript/application.js`; Stimulus controllers in `app/javascript/controllers/{composer,scroll}_controller.js`; UI split into `app/views/conversations/_*.html.erb`; composer is `form_with` + Turbo Streams, not `fetch()`/`innerHTML`. |
| G3 | PASS | `Gemfile.lock` has `ruby_llm (1.16.0)`; `config/initializers/ruby_llm.rb:4-5` sets `openrouter_api_key` and `default_model` `ENV.fetch("CHAT_MODEL", "anthropic/claude-sonnet-4.6")`; `LlmClient#default_chat` (`app/services/llm_client.rb:41-42`) calls `RubyLLM.chat(..., provider: :openrouter, assume_model_exists: true)`. |
| G4 | PASS | `ChatTurn#call` (`app/services/chat_turn.rb:25-30`) yields each chunk and calls `StreamBroadcaster#token`; that method (`app/services/stream_broadcaster.rb:14-17`) `broadcast_append_to` HTML-escaped text onto `message-#{id}-tokens`; page subscribes with `turbo_stream_from "conversation", @conversation.id` (`app/views/conversations/show.html.erb:3`); HTTP response only replaces the composer (`app/controllers/messages_controller.rb:11`). `ChatTurnTest#streams tokens and persists only a successful turn` asserts 6 Action Cable broadcasts for chunks `Hel`+`lo`. |
| G5 | PASS | `ChatTurn#call` reads `@conversation.replayable_messages` before persist (`app/services/chat_turn.rb:23-25`, persist at `:47-50`). `ProviderMessagesTest#replays history without duplicating the prompt about to be sent` and `LlmClientTest#ask receives history that excludes the new prompt so each user turn is sent once` assert the exact outgoing array (`history + one new user turn`). Fake chat mirrors `RubyLLM::Chat#add_message` / `#ask` (`ruby_llm-1.16.0/lib/ruby_llm/chat.rb:39-42,165-168`). |
| G6 | PARTIAL | File store at `storage/conversations` with `flock` + atomic rename (`app/models/conversation_store.rb:40-50,85-90`); caps and TTL in `enforce_bounds!` / `expired?` (`:69-83`) using `AppConfig` env defaults; `ConversationStoreTest` covers restart-via-new-instance, caps, TTL. Not process-local, so `WEB_CONCURRENCY=2` can read the same files. **Not concurrency-safe for two in-flight turns on the same id:** lock is only around write, not the find→mutate→save window; the concurrent test only asserts `saved.messages.size >= 1` (`test/models/conversation_store_test.rb:17-35`). Last writer wins and can drop a turn. |
| G7 | PASS | Exactly two tools: `ServerTime` and `Calculator` (`app/tools/*.rb`), registered in `LlmClient#prepared_chat` (`app/services/llm_client.rb:35-38`) via `with_tools`. System prompt requires their use (`app/models/app_config.rb:8-11`). Calculator is a recursive-descent evaluator, not `eval` (`app/services/arithmetic_evaluator.rb`). Tests: `ServerTimeTest`, `CalculatorTest`, `ArithmeticEvaluatorTest`. Runtime “model must call the tool” is prompt-enforced, not mechanically gated. |
| G8 | PASS | After a successful first user+assistant pair, `ChatTurn#maybe_title` (`app/services/chat_turn.rb:54-61`) calls `LlmClient#generate_title`, which uses `chat.with_schema(ConversationTitleSchema)` (`app/services/llm_client.rb:22-30`; schema in `app/models/conversation_title_schema.rb`). Title is saved and `broadcast_replace_to` target `conversation-title` (`app/views/conversations/_title.html.erb:1`). `LlmClientTest#generate_title uses with_schema`. |
| G9 | PASS | `TokenBudget` (`app/services/token_budget.rb`) with `TOKEN_BUDGET` default 32000 (`app/models/app_config.rb:3,18-19`). `ChatTurn#call` returns before `complete` when exceeded (`app/services/chat_turn.rb:16-17`). `ChatTurnTest#refuses over-budget turns without calling the provider`. Usage partial `app/views/conversations/_usage.html.erb`. |
| G10 | PASS | Instructions via `with_instructions(AppConfig::SYSTEM_PROMPT)` (`app/services/llm_client.rb:37`). Missing key: `LlmPreflight` + `ApiKeyMissing` (`app/services/llm_preflight.rb`, `app/services/api_key_missing.rb`); shown on `conversations#show` (`app/controllers/conversations_controller.rb:10-11`) and as a turn refusal. Provider/other errors rescued in `ChatTurn#call` (`app/services/chat_turn.rb:39-42`) into a notice. Persist happens only in `persist_success`; `ChatTurnTest#does not persist failed provider turns` and `#returns a preflight error without storing history`. |
| G11 | PARTIAL | `bin/rails test` → 48 runs, 118 assertions, 0 failures. SimpleCov wired in `test/test_helper.rb:3-12` (this run: **line 100.00% (348/348), branch 84.81% (67/79)**). Per-class Minitest files exist; `FakeRubyLlmChat` matches real `with_instructions` / `with_tools` / `with_schema` / `add_message` / `ask`. Gaps: `test/integration/chat_flow_test.rb` only GETs `/` and asserts `<h1>Chat</h1>`; no system test of incremental Turbo tokens; no test of the RubyLLM tool-call loop; 5 uncovered branches in `ChatTurn`; store race test does not require both writes to survive. |
| G12 | PASS | Just ran: `bin/rubocop` → “62 files inspected, no offenses detected”; `bin/brakeman --no-pager` → “Security Warnings: 0”; `bin/bundler-audit` → “No vulnerabilities found”. |
| G13 | PASS | `Dockerfile`: `RAILS_ENV="production"` (`:24`), `USER 1000:1000` (`:66,74`), `ENTRYPOINT ["/rails/bin/docker-entrypoint"]` (`:77`). `compose.yaml` runs `web` + `redis` and publishes 3000. `README.md` documents purpose, setup, tests, and Docker. This phase did not re-run `docker build` / `compose up`. |
| G14 | PASS | No auth (`ApplicationCable::Connection` is empty; `ApplicationCable::ConnectionTest#connects without authentication`). `OPENROUTER_API_KEY` only from ENV (`.env.example` is empty). `config/master.key` exists locally but is gitignored (`git check-ignore` / `git ls-files` — not tracked). No `.env` in the tree. App is entirely under this workspace directory. |

## 2. Code quality assessment

Naming is mostly straightforward (`ChatTurn`, `ConversationStore`, `TokenBudget`). Layers are thin: controllers create a store and call `ChatTurn`; LLM I/O is isolated in `LlmClient`.

Problems:

- **`ChatTurn` mixes orchestration, persistence, titling, and error presentation** (`app/services/chat_turn.rb`, 90 lines). The `rescue StandardError` at `:41` also swallows programmer errors and surfaces them as “The model is unavailable”.
- **Duplication / unused surface:** `LlmClient#outgoing_messages` is only used by a test. `jbuilder` is in the `Gemfile` and unused. `ApplicationCable::ChannelTest` only asserts the class hierarchy.
- **Store lock is narrower than the comment implies.** `ConversationStore#save` serializes writers, but `ChatTurn` releases the lock between `find` and `save`. `all` re-enters `find` per file (N extra lock/parse cycles).
- **Show view is not a real sidebar:** `show.html.erb:11-13` hard-codes the current title; the conversation list is a separate full page (`index.html.erb`).
- **Dead-ish JS:** `app/javascript/channels/index.js` imports Action Cable but does not start a consumer; Turbo Streams use the built-in Action Cable adapter via `action_cable_meta_tag` instead. Harmless but confusing.

Top 3 refactors if there were more time:

1. **Make conversation updates atomic** — hold the exclusive lock (or use a compare-and-swap / append log) for the whole find→LLM-is-tricky, at least merge-on-write so two workers cannot drop a persisted turn. The current test documents the hole (`size >= 1`).
2. **Split `ChatTurn`** — preflight/budget, stream+complete, persist, title. Keep `rescue` on provider errors only (`RubyLLM::Error`), not `StandardError`.
3. **Drop unused gems/APIs and add one system test** that asserts two Turbo Stream token appends before the HTTP response finishes. That is the only test that would actually lock G4.

## 3. Test coverage assessment

Command: `bin/rails test`

- Line: **100.00%** (348 / 348)
- Branch: **84.81%** (67 / 79)
- 48 runs, 118 assertions, 0 failures, 0 errors, 0 skips

Weakest area: **`ChatTurn` + end-to-end chat** (`app/services/chat_turn.rb` branch 75%; `test/integration/chat_flow_test.rb` is a root-page smoke test). Stimulus JS is untested.

Failure modes with no test:

- Two concurrent `ChatTurn`s on the same conversation (lost update).
- Empty / blank stream chunks (`chat_turn.rb:27`).
- Title skipped because the conversation is already titled (`chat_turn.rb:55`).
- Hash-shaped assistant `content` (`chat_turn.rb:78`).
- `LlmClient.build` when `factory` is nil (`llm_client.rb:5`).
- `ProviderMessages.normalize` when the object does not implement `to_h` (`provider_messages.rb:14`).
- Several `ArithmeticEvaluator` error branches (empty token list after tokenize, leftover tokens, subtraction path, missing `)`).
- Live provider/tool-call loop (model ignores tools, tool result then second completion).
- Incremental tokens actually appearing in a browser / Capybara session.
- Action Cable with `WEB_CONCURRENCY=2` and the async adapter (process-local; broadcasts never reach the other worker).
- Docker volume ownership / missing `SECRET_KEY_BASE` in compose.

## 4. Known defects and risks

- **Lost updates under multi-worker / multi-tab send** on one conversation. `flock` does not cover the read-modify-write of `ChatTurn`. `ConversationStoreTest` allows `messages.size >= 1`.
- **Title is attempted only when there is exactly one user and one assistant message** (`Conversation#first_exchange_complete?`). If `generate_title` fails once (`maybe_title` rescues and returns), later turns never retry.
- **Budget is checked only against already-stored usage**, not the incoming prompt. A conversation at `limit - 1` still calls the provider.
- **Failed turns still broadcast the user bubble** (`ChatTurn#call` `:20` before `complete`). Refresh then drops that bubble because it was never saved. Easy to read as a UI bug.
- **Degraded errors include `error.class` and `error.message`** (`chat_turn.rb:72`). Provider/config exceptions can leak internals into the page.
- **Action Cable in development is process-local unless `REDIS_URL` is set** (`config/cable.yml:2`). `WEB_CONCURRENCY=2` without Redis breaks G4 delivery even though files are shared. Compose does set Redis.
- **Puma thread is blocked for the whole streamed completion** (`MessagesController#create` calls `ChatTurn#call` inline). Default 3 threads; a few long streams stall the process.
- **Expired conversations delete the `.json` but leave `.lock` files** (`conversation_store.rb:24-25`). Lock files accumulate.
- **`bin/docker-entrypoint` generates a new `SECRET_KEY_BASE` when unset** (`bin/docker-entrypoint:5-7`), so cookies/sessions reset every container start if compose is launched without the var.
- **Named volume `conversation_data:/rails/storage` can hide the image’s `chown`**. If the volume is root-owned, the non-root `mkdir` in the entrypoint fails (`set -e`).
- **No auth (required for the demo) means anyone who can reach the port spends the OpenRouter key.** No rate limit.
- **Demo `config/master.key` is on disk.** Gitignored and not tracked, but present in the workspace; do not copy it into a public artifact.
- **`jbuilder` shipped unused.** Production image sets `BUNDLE_WITHOUT=development` only, so the `:test` group (Capybara, Selenium, SimpleCov) is still installed in the image.

No other defects were confirmed. An empty list would have been false.
