# SELF REVIEW

## 1. GOAL VERIFICATION TABLE

| Goal | Verdict | Evidence |
|------|---------|----------|
| G1 | PASS | Ruby 4.0.6, Rails 8.1.3.1 verified with `ruby -v` and `rails -v`. Application.rb:5-15 correctly disables Active Record, Action Mailer, Active Job, Action Mailbox, and Action Text. |
| G2 | PASS | Tailwind CSS via tailwindcss-rails gem (Gemfile:16), Hotwire via turbo-rails and stimulus-rails gems (Gemfile:12-14). Views componentized: `app/views/chats/_message.html.erb`, `app/views/chats/_input.html.erb`, `app/views/shared/_header.html.erb`. No single-file CSS/JS dumps found. |
| G3 | PASS | RubyLLM gem installed (Gemfile:23), configured in `config/initializers/ruby_llm.rb:3-7` with OpenRouter API key and model selection via CHAT_MODEL env var defaulting to `anthropic/claude-sonnet-4`. |
| G4 | PASS | True token streaming implemented in `app/controllers/chats_controller.rb:45-58`. Each token is immediately streamed via Turbo Stream using `response.stream.write()`. Tokens arrive incrementally, not batched after completion. |
| G5 | PASS | Multi-turn payload test in `test/services/chat_service_test.rb:36-51` asserts exact message array. The `build_chat` method in `app/services/chat_service.rb:65-75` correctly replays history excluding the pending message being sent. |
| G6 | PASS | `ConversationStore` uses Redis with TTL (86,400s) in `app/services/conversation_store.rb:6`. Enforces MAX_MESSAGES=100 and MAX_BYTES=100,000 at lines 83-87. Works with WEB_CONCURRENCY>1 since Redis is external process. |
| G7 | PASS | Two tools registered in `app/services/chat_service.rb:68-69`: `ServerTimeTool` and `CalculatorTool`. Test at `test/tools/tools_test.rb` verifies both tools. |
| G8 | PASS | Title generation implemented in `app/services/chat_service.rb:79-108` using RubyLLM's `with_schema` for structured output. Called after first exchange at line 57. Title displayed in header via `app/views/shared/_header.html.erb:6`. |
| G9 | PASS | Token budget tracking in `app/services/chat_service.rb:22-26`. Budget exceeded raises `BudgetExceededError` with friendly message shown in UI via `app/controllers/chats_controller.rb:84`. Configurable via TOKEN_BUDGET env var. |
| G10 | PARTIAL | System prompt set in `app/services/chat_service.rb:4-9`. API key missing preflight at line 22. Provider errors caught at lines 60-62. **FAILED TURNS ARE STORED**: Line 28 adds user message to history BEFORE the try block, so failed API calls leave the user message in history. Should be moved inside the try block. |
| G11 | PASS | Minitest suite runs: 26 tests, 63 assertions, 0 failures. SimpleCov reports 64.60% line coverage. Tests mirror RubyLLM API surface correctly. |
| G12 | PARTIAL | RuboCop: clean. Bundle-audit: clean. **Brakeman**: 1 weak-confidence warning about eval in `app/tools/calculator_tool.rb:23` - the input is sanitized but eval is inherently risky. |
| G13 | PASS | Production Dockerfile at `Dockerfile:1-51` with RAILS_ENV=production, non-root user (uid 1000), proper entrypoint. docker-compose.yml present. README.md documents setup, configuration, Docker usage, and testing. |
| G14 | PASS | No authentication implemented. No secrets committed - only env var references found in code (`grep -r "sk-\|api_key" app/ config/ --include="*.rb"` returns nothing sensitive). |

## 2. CODE QUALITY ASSESSMENT

### Naming
Good: `ChatService`, `ConversationStore`, `ServerTimeTool`, `CalculatorTool` are self-documenting. Variable names like `accumulated_content`, `stream_callback` are clear.

Issues:
- `@store` in tests is ambiguous - could be named `@conversation_store`
- `msg` abbreviation in `chat_service.rb:70-74` should be `message`

### Single Responsibility
`ChatService` handles too many concerns (chat building, streaming, title generation, error handling). Should be split into:
- `ChatBuilder` - constructs RubyLLM chat objects
- `TitleGenerator` - handles title generation logic  
- `ChatService` - orchestrates the flow

`ConversationStore` is well-focused on persistence.

### Duplication
- Error rendering in controller (`render_error_stream`) duplicates HTML structure. Could extract to partial.
- Token counter HTML repeated in two places (header and update_tokens_partial).

### Dead Code
- `app/javascript/controllers/hello_controller.js` is default Stimulus boilerplate, unused.

### Method/Class Size
- `ChatService#send_message` is 43 lines (lines 21-63), doing too much: validation, storage, chat building, streaming, token tracking, title generation. Should be extracted.
- `ChatsController#stream_tokens` is 47 lines (lines 41-87), handling success and multiple error types inline.

### Coupling
- Controller directly knows about `ChatService` and `ConversationStore` internals.
- `ChatService` directly manipulates `ConversationStore` state rather than passing messages.

### Top 3 Refactors (with more time)

1. **Extract ChatService responsibilities** - Create `ChatBuilder` and `TitleGenerator` classes. `ChatService#send_message` should orchestrate calls, not implement logic. This would reduce method from 43 to ~10 lines.

2. **Move message storage inside try block** - Fix the bug where failed turns are stored. The `conversation.add_message(role: "user", content: content)` call at line 28 should move inside the begin block, after successful API response starts.

3. **Extract error handling** - Create `ErrorHandler` service that standardizes error messages and UI responses. Currently three different error types are handled inline in the controller.

## 3. TEST COVERAGE ASSESSMENT

### Actual Coverage
- **Line coverage**: 64.60% (115/178 lines)
- **Branch coverage**: Not available (SimpleCov configured with `branch_coverage: false`)

### Weakest-Tested Area
`app/controllers/chats_controller.rb` - Only 4 integration tests covering index and new conversation actions. The streaming endpoint (`create` action) has NO tests. Error handling paths untested. The `show` action untested.

### Failure Modes NOT Covered
1. **Streaming failures mid-response** - What happens if the API connection drops during streaming?
2. **Concurrent writes to same conversation** - Race condition when two requests modify same conversation simultaneously
3. **Redis connection failures** - No tests for `ConversationStore` when Redis is unavailable
4. **Token budget boundary conditions** - What happens exactly at the budget limit?
5. **Calculator tool division by zero** - Test exists but doesn't verify the specific error path
6. **Malformed API responses** - No tests for invalid JSON, missing fields, nil values from RubyLLM
7. **Title generation failures** - Handled silently in production but untested
8. **Maximum message limit enforcement** - Test adds 105 messages but doesn't verify old messages are removed

## 4. KNOWN DEFECTS AND RISKS

### Defects

1. **CRITICAL: Failed turns stored in history** (`chat_service.rb:28`)
   - User message added to conversation before API call
   - If API fails, user message remains in history
   - Next turn will replay failed message to provider
   - **Fix**: Move `conversation.add_message` inside the try block after stream starts

2. **Security: eval in CalculatorTool** (`calculator_tool.rb:23`)
   - Uses `eval()` even with sanitization
   - Brakeman flags as weak-confidence vulnerability
   - **Fix**: Use a proper expression parser or calculate AST instead

3. **Race condition in message storage** (`conversation_store.rb:24-28`)
   - Read-modify-write without locking
   - Concurrent requests could lose messages
   - **Fix**: Use Redis WATCH/MULTI or Lua script

### Risks

4. **Unbounded memory during streaming** (`chats_controller.rb:45-58`)
   - Accumulates tokens in `accumulated_content` string
   - Very long responses could cause memory pressure
   - No size limit on response length

5. **No request timeout on streaming** (`ruby_llm.rb:6`)
   - request_timeout=120 but streaming could hang indefinitely
   - Client disconnect not detected server-side

6. **Title generation blocks response** (`chat_service.rb:79-108`)
   - Additional API call after streaming completes
   - Adds latency before client can send next message
   - Should be async/background

7. **Missing nil checks** 
   - `chat_service.rb:46`: `last_msg = conversation.raw_messages.last` - could be nil
   - `chats_controller.rb:61`: `last_msg&.dig("content")` - could return nil

8. **TTL refresh race** (`conversation_store.rb:79`)
   - TTL set on every save, but if save fails, TTL not refreshed
   - Could cause premature conversation expiration

9. **Byte limit enforcement inefficient** (`conversation_store.rb:89-91`)
   - Calls `to_json.bytesize` on every iteration of while loop
   - Should calculate incrementally or check periodically

10. **No validation of message content**
    - Empty messages accepted
    - Very long messages could exceed Redis limits
    - No sanitization of user input

### Edge Cases Not Handled

11. **Empty conversation title** - If title generation fails or returns empty string, UI shows blank
12. **Negative token counts** - If API returns negative values, total_tokens could be wrong
13. **Non-UTF-8 content** - User input with binary data could cause encoding issues

### Operational Risks

14. **Redis as single point of failure** - If Redis goes down, all conversations lost
15. **No monitoring/alerting** - Production deployment has no health checks beyond basic `/up` endpoint
16. **Docker container runs as uid 1000** - May conflict with mounted volume permissions

### Concurrency Concerns

17. **WEB_CONCURRENCY>1 with RubyLLM** - RubyLLM may have global state not safe across processes
18. **Redis connection pool** - No connection pooling configured for high concurrency
