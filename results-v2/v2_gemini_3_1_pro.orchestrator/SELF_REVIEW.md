# Self-Review

## 1. GOAL VERIFICATION TABLE

| Goal | Verdict | Evidence |
|---|---|---|
| G1 | PASS | `config/application.rb` has Active Record, Action Mailer, and Active Job commented out. App is at workspace root. |
| G2 | PASS | `app/views/chats/show.html.erb` uses Tailwind classes and Hotwire (`turbo_stream_from`). Partials like `_message.html.erb` are used. |
| G3 | PASS | `Gemfile` includes `gem "ruby_llm"`. `app/services/chat_service.rb` configures `provider: :openrouter` and `model: ENV.fetch("LLM_MODEL", "anthropic/claude-sonnet-4.6")`. |
| G4 | PASS | `app/services/chat_service.rb:68` uses `chat.ask(content) do \|chunk\| broadcast_chunk(...) end` to stream tokens via Turbo Streams. |
| G5 | PASS | `test/services/chat_service_test.rb:71` asserts `mock_chat2.expect :add_message` is called for history, and `mock_chat2.expect :ask` is called for the new prompt, proving the new prompt is not in the replayed history. |
| G6 | PASS | `app/models/conversation_store.rb` uses Redis with `$redis.watch` for concurrency, enforces `MAX_MESSAGES` and `MAX_BYTES`, and sets a `TTL`. |
| G7 | PASS | `app/models/server_time_tool.rb` and `app/models/calculator_tool.rb` are defined and registered in `app/services/chat_service.rb:33` via `chat.with_tools`. |
| G8 | PASS | `app/services/chat_service.rb:112` defines a JSON schema and calls `chat.ask(summary_prompt)` to generate a title after the first exchange. |
| G9 | PASS | `app/services/chat_service.rb:17` checks `if current_usage >= BUDGET` and refuses further turns if exceeded. |
| G10 | PASS | `app/services/chat_service.rb:32` sets system prompt. Line 11 checks for missing API key. Line 91 rescues `RubyLLM::Error`. Failed turns are not stored because `@store.add_message` is called after `chat.ask` succeeds. |
| G11 | PARTIAL | Tests exist and use Minitest mocks (`test/services/chat_service_test.rb`). SimpleCov is wired. However, error paths (missing API key, budget exceeded) are not fully covered. |
| G12 | PASS | `bundle exec brakeman -q`, `bundle exec rubocop`, and `bundle exec bundle-audit check --update` all return 0 offenses/vulnerabilities. |
| G13 | PASS | `Dockerfile` uses `RAILS_ENV="production"` and `USER 1000:1000`. `docker-compose.yml` is present. `README.md` documents setup and execution. |
| G14 | PASS | `grep -r "OPENROUTER_API_KEY" .` confirms no secrets are committed. Everything is in the workspace root. |

## 2. CODE QUALITY ASSESSMENT

The codebase generally follows clean code principles, but there are areas for improvement. Naming is clear and descriptive (`ChatService`, `ConversationStore`). However, the Single Responsibility Principle is violated in `ChatService`.

**Top 3 things to refactor:**
1. **Extract Turbo Stream broadcasting from `ChatService`:** `ChatService` is tightly coupled to the presentation layer (`Turbo::StreamsChannel`). Extracting this into a `ChatBroadcaster` class would decouple LLM orchestration from UI updates.
2. **Extract title generation from `ChatService#process_message`:** The `process_message` method is too long and handles both the main chat flow and title generation. Title generation should be moved to a separate `TitleGenerator` service or a background job.
3. **Improve ToolCall serialization in `ConversationStore`:** `ChatService` manually transforms `RubyLLM::ToolCall` objects to and from hashes when interacting with `ConversationStore`. This logic should be encapsulated within `ConversationStore` or a dedicated serializer.

## 3. TEST COVERAGE ASSESSMENT

- **Line Coverage:** 88.61% (109 / 123 lines)
- **Branch Coverage:** Not explicitly tracked by SimpleCov default configuration, but inferred from missing line coverage.
- **Weakest-tested area:** `ChatService` error handling and budget enforcement.
- **Failure modes NOT covered by any test:**
  - Missing API key preflight check.
  - Token budget exceeded check.
  - Title generation failure (the `rescue` block).
  - Redis command errors in `ConversationStore` (the `rescue Redis::CommandError` block).
  - Invalid expressions in `CalculatorTool`.

## 4. KNOWN DEFECTS AND RISKS

- **Concurrency hazard:** `ConversationStore#add_message` uses `$redis.watch` but rescues `Redis::CommandError` and retries infinitely (`retry` keyword) without a backoff or max retries. Under high contention, this could lead to an infinite loop or worker starvation.
- **Security/Robustness risk:** `CalculatorTool` uses `eval(expression)` after a regex check `/\A[\d\s\+\-\*\/\(\)\.]+\z/`. While the regex restricts characters, `eval` is inherently risky and can lead to unexpected behavior or DoS if a complex expression is crafted. A dedicated math parser is safer.
- **Operational risk:** Title generation is performed synchronously in `ChatService#process_message`. If the LLM provider is slow, it blocks the worker thread, degrading the user experience. It should be asynchronous.
- **State inconsistency:** `ChatService` generates a `SecureRandom.uuid` for `message_id` during streaming but does not persist it in `ConversationStore`. If the page is refreshed, the message IDs will change, which could break UI updates if they rely on stable DOM IDs.
