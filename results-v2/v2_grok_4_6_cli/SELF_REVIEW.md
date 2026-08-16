# Self-review (phase 3)

Reviewed against the current tree on 2026-08-16. Goals G1–G14 are from the original phase-1 brief. No surgical fixes were made in this phase; `bin/rails test`, RuboCop, Brakeman, and bundler-audit were already clean.

## 1. Goal verification table

| Goal | Verdict | Evidence |
| --- | --- | --- |
| G1 | PASS | `ruby -v` → `ruby 4.0.6`; `mise.toml` pins `ruby = "4.0.6"` (newest install listed by `mise ls ruby`); `Gemfile:4` / lock `rails (8.1.3.1)` matches `gem search rails --exact --remote`; `config/application.rb:6-10` leaves Active Record, Active Job, and Action Mailer commented out; no `config/database.yml`, `app/jobs`, or `app/mailers`; Rails app lives at the workspace root (`Gemfile`, `config/`, `app/`). |
| G2 | PASS | Tailwind via `gem "tailwindcss-rails"` and a small theme in `app/assets/tailwind/application.css:1-22` (not a hand-rolled dump); Hotwire via `turbo-rails` / `stimulus-rails` and `<%= turbo_stream_from current_conversation.stream_name %>` in `app/views/chats/show.html.erb:9`; UI split into `app/views/chats/_*.html.erb` and `app/views/messages/_*.html.erb`; Stimulus controllers in `app/javascript/controllers/{auto_scroll,composer}_controller.js`; `rg 'fetch\(|innerHTML' app/javascript` returned no matches. |
| G3 | PASS | `Gemfile:22` `gem "ruby_llm", "~> 1.16"` / lock `ruby_llm (1.16.0)`; `gem search '^ruby_llm$' --remote` lists `1.16.0` as newest; `config/initializers/ruby_llm.rb:2-3` sets `openrouter_api_key` and default model; `ChatConfig::DEFAULT_MODEL` is `anthropic/claude-sonnet-4.6` (`app/models/chat_config.rb:2,16-18`); override via `OPENROUTER_MODEL` tested in `ChatConfigTest#test_model_can_be_overridden_by_env`. |
| G4 | PASS | `ChatCompletion#complete_with_stream` yields each RubyLLM chunk and calls `assistant_delta` with the accumulated text (`app/services/chat_completion.rb:60-68`); `ConversationBroadcaster#assistant_delta` does `Turbo::StreamsChannel.broadcast_replace_to` on `message_<id>_content` (`app/services/conversation_broadcaster.rb:16-24`); `ChatCompletionTest#test_streams_each_token_to_the_page_via_the_broadcaster` asserts deltas `"Hel"` then `"Hello"`; `ConversationBroadcasterTest#test_broadcasts_incremental_assistant_content_to_the_message_target` asserts two `broadcast_replace_to` calls. Not re-run against a live WebSocket in this phase. |
| G5 | PASS | Replay is prior turns only; `ask` adds the new prompt (`app/services/chat_completion.rb:20-21,56-61` + comment at `app/services/conversation_payload.rb:1-5`); `ConversationPayloadTest#test_multi-turn_outgoing_array_includes_prior_turns_plus_the_new_prompt_exactly_once` asserts the exact five-element array; `ChatCompletionTest#test_sends_prior_history_then_asks_the_new_prompt_exactly_once` asserts `ask_count == 1`, replayed history on `chat.messages`, and the new user turn appearing once. |
| G6 | PASS | File store under `ChatConfig.storage_path` with `flock` (`app/services/conversation_store.rb:3-4,81-92,144-148`); `ConversationStoreTest#test_history_survives_a_new_store_instance_like_an_app_restart`; `#test_concurrent_workers_can_append_without_losing_turns` (two store instances / threads); `#test_enforces_a_message-count_cap`; `#test_enforces_a_byte_cap`; `#test_expired_conversations_are_removed_by_TTL`; defaults in `ChatConfig` (`max_messages=80`, `max_bytes=262144`, `ttl_seconds=7.days`). |
| G7 | PASS | Exactly two `RubyLLM::Tool` subclasses: `ServerTime` (`app/tools/server_time.rb`) and `Calculator` (`app/tools/calculator.rb`); attached with `chat.with_tools(ServerTime, Calculator)` (`app/services/chat_completion.rb:54`); system prompt requires their use (`app/models/chat_config.rb:9-11`); `CalculatorTest` / `ServerTimeTest` exercise `execute` and `Calculator#call`; `ChatCompletionTest#test_attaches_instructions_and_both_tools_before_asking` asserts tool keys `:server_time` and `:calculator`. Live model compliance was not re-invoked in this phase. |
| G8 | PASS | `ConversationTitleSchema < RubyLLM::Schema` with `string :title` (`app/schemas/conversation_title_schema.rb:3-5`); `TitleGenerator` calls `chat.with_schema(ConversationTitleSchema)` then `ask` (`app/services/title_generator.rb:16-18`); invoked after the first persisted exchange (`app/services/chat_completion.rb:83-91`); rendered at `app/views/chats/_title.html.erb:1-3`; `TitleGeneratorTest#test_asks_with_a_schema_and_reads_the_title_from_structured_output`; `ChatCompletionTest#test_generates_a_title_after_the_first_completed_exchange` and `#test_does_not_regenerate_a_title_on_later_turns`. |
| G9 | PASS | `TOKEN_BUDGET` env, default `32_000` (`app/models/chat_config.rb:3,20-22`); `Conversation#over_budget?` (`app/models/conversation.rb:26-28`); `ChatCompletion#ensure_budget!` raises before `default_chat` (`app/services/chat_completion.rb:18,96-98`); UI via `ConversationBroadcaster#budget` + `app/views/messages/_budget.html.erb`; usage bar in `app/views/chats/_usage.html.erb`; `ChatCompletionTest#test_refuses_over-budget_turns_without_calling_the_provider` asserts the factory is never called and a `:budget` event is broadcast. |
| G10 | PASS | Instructions set with `chat.with_instructions(ChatConfig.system_prompt)` (`app/services/chat_completion.rb:53`); missing-key banner `app/views/chats/_preflight.html.erb:1-9` and `ApiKeyPreflight::MESSAGE` (`app/services/api_key_preflight.rb:4-8`); `ChatCompletion#call` rescues preflight, budget, and `StandardError` into broadcasts (`app/services/chat_completion.rb:37-46`); `persist_success` is only on the happy path (`app/services/chat_completion.rb:34,73-81`); `ChatCompletionTest#test_does_not_persist_a_failed_provider_turn` and `#test_missing_API_key_is_a_friendly_error_and_never_calls_the_provider`. |
| G11 | PARTIAL | 18 `*_test.rb` files, `bin/rails test` → `49 runs, 172 assertions, 0 failures`; SimpleCov in `test/test_helper.rb:1-15` with `enable_coverage :branch`; `FakeRubyLLMChat` mirrors `ask` / `with_instructions` / `with_tool(s)` / `with_schema` / `add_message` as defined in ruby_llm 1.16.0 `lib/ruby_llm/chat.rb`. Gaps: branch coverage is 68.03%; no tests for Stimulus controllers; `ChatCompletion#friendly_error` type branches, title-generator failure, empty-chunk fallback, and a tool-call turn through `ChatCompletion` are untested (see §3). |
| G12 | PASS | `bin/rubocop --format simple` → `59 files inspected, no offenses detected`; `bin/brakeman --no-pager --quiet` → `Security Warnings: 0`; `bin/bundler-audit` → `No vulnerabilities found`. |
| G13 | PASS | `Dockerfile:18` `RAILS_ENV=production`; `Dockerfile:44-52` `useradd` uid 1000 then `USER 1000:1000`; `Dockerfile:54` `ENTRYPOINT ["/rails/bin/docker-entrypoint"]`; `docker-compose.yml` runs Redis + web with `OPENROUTER_API_KEY` from the host env; `README.md` documents purpose, setup, tests, and compose. Docker image was not rebuilt in this phase. |
| G14 | PASS | No auth: `ApplicationCable::Connection` is empty (`app/channels/application_cable/connection.rb`) and `ApplicationCable::ConnectionTest#test_connects_without_authentication`; no Devise/login routes (`config/routes.rb`). Keys read only from `ENV` (`config/initializers/ruby_llm.rb:2`). `git check-ignore -v config/master.key` → `.gitignore:27:/config/*.key`. `git log` → no commits, so nothing is committed. App is entirely under this workspace. `.env` files are absent. |

## 2. Code quality assessment

The Ruby side is small (~920 lines under `app/`) and mostly single-purpose objects: controllers stay thin (`ChatsController` 11 lines, `MessagesController` 24), tools wrap one action, views are one-partial-per-surface. Names match their jobs (`ConversationStore`, `TokenEstimator`, `ApiKeyPreflight`). Layers are clear: controllers → `ChatCompletion` → store / broadcaster / RubyLLM.

What is not clean:

- **`ChatCompletion` (134 lines)** is an orchestrator that also owns streaming, token accounting, title side-effects, and provider-error copy. `app/services/chat_completion.rb:16-47` and `51-133` mix those concerns.
- **`ConversationStore` (164 lines)** mixes persistence, locking, TTL, and two different write strategies: `write_atomic` (`app/services/conversation_store.rb:132-142`) vs in-place rewrite in `mutate` (`81-92`).
- **Duplication:** `parse_time` is copy-pasted in `Conversation` (`app/models/conversation.rb:47-55`) and `ConversationMessage` (`app/models/conversation_message.rb:35-43`).
- **Dead / unused API:** `ConversationStore#find!` (`app/services/conversation_store.rb:47-49`) and `#sweep` (`66-72`) have no production callers. `ConversationPayload.serialize` fallbacks for objects without `as_payload` (`app/services/conversation_payload.rb:18-23`) are unused in the app path (every stored message is a `ConversationMessage`).
- **Test helper smell:** `test/support/stub.rb` reopens `Object` to restore Minitest 5 `Object#stub` for Minitest 6. Isolated to tests, but it is a global monkeypatch.
- **Coupling:** `MessagesController#create` blocks the request thread until `ChatCompletion#call` returns (`app/controllers/messages_controller.rb:11`). The HTTP turbo response only replaces the composer (`13-19`); visible tokens depend on Action Cable. That couples UX completeness to the Cable adapter.
- **Method size** is otherwise fine. `SafeCalculator` is long (124 lines) but it is a recursive-descent parser with a single reason to change.

### Top 3 refactors (if there were more time)

1. **Make `ConversationStore#mutate` use the same temp-file + `rename` path as `write_atomic`, and invoke `#sweep` on boot (and periodically).** A crash between `write` and `truncate` in `mutate` can leave truncated JSON; `#sweep` is implemented and tested only via `find`, so untouched expired files never go away.
2. **Split `ChatCompletion` into “run the model + stream” and “persist / title / error copy”.** The class is the highest-churn file and the weakest-tested one. Smaller units would make the untested `friendly_error` branches and the empty-chunk fallback (`app/services/chat_completion.rb:104-116,118-133`) cheap to cover.
3. **Drop or test the unused serialize / `find!` / `#sweep` surfaces, and persist tool-call transcripts or document that they are discarded.** Today only final user/assistant text is stored (`ConversationStore#append_turn`). The next `ask` never sees `tool` role messages, so a follow-up that depends on the raw tool result has to re-call the tool.

## 3. Test coverage assessment

Command: `bin/rails test`

Result: `49 runs, 172 assertions, 0 failures, 0 errors, 0 skips`

SimpleCov (from that run, also printed at suite end and stored in `coverage/coverage.json`):

- **Line:** 454 / 485 = **93.60%**
- **Branch:** 83 / 122 = **68.03%**

**Weakest-tested area:** `app/services/conversation_payload.rb` has the lowest line coverage (**66.7%**, 4/12 lines, **25%** branch) because only the `as_payload` path is exercised. The more important gap is `app/services/chat_completion.rb` (**87.5%** line, **46.4%** branch, 15 missed branches): `default_chat`, title-generator rescue, `assistant_content` fallbacks, and every `friendly_error` `when` except the generic `StandardError` / `RubyLLM::ServerError` path.

Stimulus (`auto_scroll_controller.js`, `composer_controller.js`) has no tests. `test/integration/` is empty.

### Failure modes with no test

- Distinct mapping of `RubyLLM::UnauthorizedError`, `RateLimitError`, `PaymentRequiredError`, `ServiceUnavailableError`, `OverloadedError` (`app/services/chat_completion.rb:120-127`).
- Title generation raising (`app/services/chat_completion.rb:92-93`) or returning a non-Hash / invalid JSON body (`app/services/title_generator.rb:39-43`).
- Stream block yielding empty chunks, then filling content from the final response (`app/services/chat_completion.rb:69-70,104-116`) — this is the “append after completion” fallback that would violate G4 at runtime.
- A RubyLLM tool-call response flowing through `ChatCompletion` (the fake chat never sets `tool_call?` or invokes `Calculator` / `ServerTime`).
- Corrupt / empty JSON on read (`ConversationStore#parse_json` rescue, `mutate` `data.nil?` raise).
- `ConversationStore#sweep` over the directory (untouched expired files).
- `SystemStackError` from a long unary `---` chain in `SafeCalculator#parse_unary` (inherits `Exception`, not `StandardError`, so `ChatCompletion` will not rescue it).
- Action Cable / Redis down while `WEB_CONCURRENCY=2` (history still writes; the page never receives deltas).
- Two OS processes appending (the concurrent test uses threads, not `WEB_CONCURRENCY=2` processes).
- Composer / auto-scroll Stimulus behavior, including double-submit without JavaScript.

## 4. Known defects and risks

1. **`mutate` is not crash-safe.** `ConversationStore#mutate` rewrites the JSON file in place (`rewind` / `write` / `truncate` at `app/services/conversation_store.rb:88-91`). A kill in the middle can leave unreadable JSON; `find` then returns `nil` and the conversation is gone.
2. **TTL does not bound disk globally.** Expiry runs in `sweep_one` during `find` of that id. `#sweep` is never called from app code. Abandoned conversations (cookie gone, id never requested again) stay on disk until something deletes them.
3. **Byte cap can still be exceeded.** `apply_bounds` stops shrinking at 2 messages (`app/services/conversation_store.rb:101-104`). Two large messages can remain over `CONVERSATION_MAX_BYTES`.
4. **Odd `CONVERSATION_MAX_MESSAGES` can un-pair history.** Append always writes a user+assistant pair, but `messages.shift` drops one message at a time. An odd cap can leave an assistant turn first in the replay array.
5. **No prompt / expression size limit.** `MessagesController` only rejects blank content. A huge prompt is sent to the provider (cost). A long `----+digits` calculator expression recurses in `parse_unary` (`app/services/safe_calculator.rb:75-85`) and can raise `SystemStackError`, which is not caught by `rescue StandardError` in `ChatCompletion#call`.
6. **One Puma thread is held for the whole provider call.** `worker_timeout` is 180s (`config/puma.rb:35`) and `RAILS_MAX_THREADS` defaults to 3. A few slow OpenRouter calls saturate a worker. There is no `max_tokens` cap on `RubyLLM.chat`, so a single turn can also jump `token_usage` far past `TOKEN_BUDGET`.
7. **Streaming UX is Cable-only.** After a successful turn the HTTP turbo stream replaces `#composer` only (`app/controllers/messages_controller.rb:13-19`). If Redis is missing under `WEB_CONCURRENCY=2` (async adapter is process-local; `config/cable.yml:1-3,9-12`), the user sees no incremental tokens and no persisted messages until a full reload. README states the Redis requirement; the code does not degrade to an HTTP append.
8. **`sweep_one` deletes after releasing the shared lock** (`app/services/conversation_store.rb:116-120`). A writer can update the file between the TTL check and `File.delete` (TOCTOU).
9. **Unauthenticated spend + subscribe.** G14 forbids auth, so anyone who can reach the process can spend `OPENROUTER_API_KEY`. There is no rate limit. Action Cable accepts any connection; the stream name is `conversation_<uuid>` and the UUID is in the page. Knowing another conversation’s id is enough to subscribe to its live tokens. Files are mode `0644`.
10. **Prompts are loggable.** `config/initializers/filter_parameter_logging.rb` does not filter `:content` / `:message`. Development logs can retain user text. `Calculator` also logs the expression (`app/tools/calculator.rb:8`).
11. **`config/master.key` is on disk** (32 bytes, mode 0600). It is gitignored and this repo has no commits, so it is not committed. It is still a secret in the workspace. `credentials.yml.enc` is the usual Rails encrypted file.
12. **Ephemeral `SECRET_KEY_BASE` in Docker.** `bin/docker-entrypoint:5-8` generates a key when none is provided. Signed `conversation_id` cookies will not survive a container replace unless compose is given a stable `SECRET_KEY_BASE` (README tells you to export one).
13. **Budget check is racy.** Two overlapping POSTs can both see `token_usage` under budget and both call the provider. The composer disables submit in JS only (`app/javascript/controllers/composer_controller.js:14-16`).
14. **Title generation is a second, unbudgeted provider call** (`TitleGenerator#call`). Failures are swallowed (`app/services/chat_completion.rb:92-93`), so a persistent schema failure is silent and retried every turn until a title sticks.
15. **Tool transcripts are not stored.** RubyLLM’s `ask` loop adds tool-call / tool-result messages in memory; `append_turn` keeps only the final assistant string. Follow-up turns cannot see the raw tool output.
16. **CSP is disabled** (`config/initializers/content_security_policy.rb` is fully commented out). Fine for a demo; it is still an open XSS blast radius if a future view stops escaping. Current templates use `<%= %>` (escaped).
17. **`SafeCalculator` integer size is unbounded.** Repeated multiplication of large literals can allocate huge Bignums in the request process.

No item above was producing a failing test or a red quality gate at review time. They are residual defects and operational risks, not a claim that the suite is red.
