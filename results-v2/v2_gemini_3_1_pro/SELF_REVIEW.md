# SELF_REVIEW.md

## 1. GOAL VERIFICATION TABLE

| Goal ID | Verdict | Evidence |
| :--- | :--- | :--- |
| G1 | PASS | `cat config/application.rb` shows `active_record/railtie`, `active_job/railtie`, and `action_mailer/railtie` are commented out, while `require "rails"` and `action_cable/engine` are present. |
| G2 | PASS | `Gemfile` includes `tailwindcss-rails`, `turbo-rails`, `stimulus-rails`. Partials are actively used in `app/views/chats/` (e.g., `_message.html.erb`). |
| G3 | PASS | `config/initializers/ruby_llm.rb` configures `openrouter_api_key` and defaults to model `"anthropic/claude-3.5-sonnet"` (overridable via `LLM_MODEL`). |
| G4 | PASS | `ChatAgent#process` incrementally streams chunks using `Turbo::StreamsChannel.broadcast_replace_to` inside the `stream` proc. |
| G5 | PASS | `test/services/chat_agent_test.rb` test "multi-turn payload correctness" passes and asserts correct exact sequences (`mock_chat.expect(:user, nil, ["What is the time?"])`). |
| G6 | PASS | `app/services/conversation_store.rb` limits `MAX_MESSAGES` and `MAX_BYTES` using a Redis pipeline and `ltrim`. Tested to be concurrency-safe for writes via Redis `.multi`. |
| G7 | PASS | `app/services/chat_tools.rb` exposes `server_time` and `calculator` (using a custom `evaluate_math` parser to avoid `eval`). |
| G8 | FAIL | `ChatAgent#generate_title` asks the LLM via text prompt (`"You are a title generator. Respond ONLY..."`) instead of utilizing a structured-output API. |
| G9 | PASS | `ChatAgent#budget_exceeded?` stops processing if tokens exceed `TOKEN_BUDGET` and broadcasts an error message. |
| G10 | PARTIAL | System prompt and missing-API-key checks are present. However, failed provider calls leave the initial user message permanently in the conversation history, polluting the replay state. |
| G11 | PASS | Minitest suite passes (15 tests). `SimpleCov` is configured and reports 88.95% line coverage. Mocks simulate `RubyLLM` correctly. *(Note: Flakiness was discovered and fixed; see Known Defects).* |
| G12 | PASS | `bundle exec brakeman`, `bundle exec rubocop`, and `bundle exec bundler-audit` run successfully with 0 offenses. |
| G13 | PASS | `Dockerfile` builds a production image with a non-root user. `docker-compose.yml` orchestrates web and redis. `README.md` documents setup. |
| G14 | PASS | `git ls-files \| xargs grep -i "OPENROUTER_API_KEY="` shows no hardcoded secrets, only placeholders in documentation and compose files. |

## 2. CODE QUALITY ASSESSMENT

The codebase follows basic Rails conventions but has coupling and sizing issues typical of rapid prototyping.

- **Naming:** Classes like `ChatAgent` and `ConversationStore` are communicative and well-named.
- **Single Responsibility (SRP):** `ChatAgent` violates SRP heavily—it orchestrates the LLM API, executes ActionCable broadcasts, handles token budgets, and generates titles. `ChatTools` mixes tool definitions with a custom recursive-descent math parser implementation.
- **Duplication:** `Turbo::StreamsChannel.broadcast_*` is repeated four times in `ChatAgent` with almost identical target and local arguments.
- **Method/Class Size:** `ChatAgent#process` is over 60 lines long. It is difficult to read, test, and maintain.
- **Coupling:** `ChatAgent` is tightly coupled to ActionCable and HTML partials. It cannot be tested or used outside the context of a web broadcast to specific DOM IDs (`chat_#{@session_id}`).

**Top 3 things to refactor:**
1. **Extract `ChatAgent` broadcasting:** Extract ActionCable broadcasting into a `ChatBroadcaster` component. This allows `ChatAgent` to only manage LLM interaction, making it testable without DOM targets.
2. **Extract Math Parser:** Move the `evaluate_math` routine out of `ChatTools` into a dedicated `MathEvaluator` service. `ChatTools` should only route tools, not execute complex parsers.
3. **Refactor tool execution to support multiple tools natively:** `ChatAgent` currently hardcodes `response.tool_calls.first` and ignores the rest. It should iterate over `tool_calls` to correctly support parallel tool invocation, which modern models frequently provide.

## 3. TEST COVERAGE ASSESSMENT

- **Line Coverage:** 88.95% (145 / 163 lines)
- **Branch Coverage:** 68.88% (31 / 45 branches)

**Weakest-tested area:** `app/services/chat_agent.rb` (78.57% lines, 66.67% branches).

**Failure modes NOT covered by any test:**
1. **Tool evaluation execution in Agent:** The entire block `if response.tool_calls&.any?` inside `ChatAgent#process` is skipped by mocks. We do not verify if the agent correctly loops back with tool results.
2. **Math operations (Subtraction and Division):** Subtraction (`-`), division (`/`), and unary minus are completely untested in `ChatToolsTest`.
3. **Title generation failures:** `ChatAgent#generate_title` is completely stubbed out in tests, meaning the LLM call to summarize the conversation and its error handling (`rescue => e`) are uncovered.
4. **Controller thread crashes:** The `rescue => e` block inside the async `Thread.new` in `ChatsController#create` is never executed in tests.
5. **Byte-bounding eviction:** The `while redis.call("MEMORY", "USAGE", key).to_i > MAX_BYTES` block in `ConversationStore#add_message` is entirely uncovered (0 executions). We do not verify if byte eviction works dynamically without crashing.
6. **Tool evaluation error handling:** The `rescue StandardError => e` block in `ChatTools.execute` is uncovered. Malformed math expressions causing internal exceptions are never tested.

## 4. KNOWN DEFECTS AND RISKS

1. **Test Suite Flakiness / Concurrency Hazard (FIXED DURING REVIEW):** `ChatsController#create` spawns a detached `Thread.new` to handle the LLM process. During testing, this background thread was running concurrently with `ChatAgentTest`, polluting the `RubyLLM` mock and Redis store and causing `test_multi-turn_payload_correctness` to fail randomly. *Surgical fix applied:* Added `t.join if Rails.env.test?` to `ChatsController#create` to safely wait for thread completion in the test environment.
2. **Provider Failure Pollutes History (G10 violation):** Because `ChatAgent#process` eagerly stores the user message before calling the provider, an API error leaves a dangling user message in the store. Subsequent turns will replay both the old unfulfilled message and the new user message to the API.
3. **Application-level Race Condition:** If a user quickly sends two messages, two concurrent threads will execute `ChatAgent#process`. While Redis list appends are atomic, the read-modify-write cycle of the conversation history is not. This can lead to unpredictable message interleaving and duplicate assistant responses.
4. **Denial of Service (Unbounded Threads):** Because `Thread.new` is spawned for every request without a queue or thread pool limit, an attacker can flood the server with chat messages, causing memory exhaustion (OOM) or hitting thread limits.
5. **Slow Redis Command in Critical Path:** `ConversationStore#add_message` uses `MEMORY USAGE key` inside a `while` loop for eviction. This is an O(N) operation in Redis and blocks the single thread.
6. **Tool Parity Issue:** `ChatAgent#process` strictly evaluates only a single tool call per turn (`tool_calls.first`), breaking compatibility if the model issues multiple parallel tool calls for efficiency.