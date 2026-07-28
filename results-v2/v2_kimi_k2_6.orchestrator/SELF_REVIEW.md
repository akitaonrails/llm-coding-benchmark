# Self-Review: Rails ChatGPT-like SPA

## 1. Goal Verification Table

| Goal | Verdict | Evidence |
|------|---------|----------|
| G1 | PASS | `config/application.rb:5-15` excludes Active Record, Action Mailer, Active Job; `Gemfile:4` pins Rails ~> 8.1.3; `.ruby-version` specifies 4.0.6. |
| G2 | PASS | `app/views/conversations/show.html.erb` uses Tailwind classes; `app/javascript/controllers/stream_controller.js` uses Stimulus; `app/views/messages/_message.html.erb` is a componentized partial; Turbo Streams via `turbo_stream_from` in show view. |
| G3 | PASS | `config/initializers/ruby_llm.rb:3-6` configures OpenRouter API key and default model `anthropic/claude-sonnet-4` with `CHAT_MODEL` env override; `Gemfile:21` includes `ruby_llm`. |
| G4 | PASS | `app/controllers/streaming_controller.rb:25-39` sets SSE headers and streams chunks via `ActionController::Live::SSE`; `app/javascript/controllers/stream_controller.js:13-58` consumes the EventSource and appends tokens incrementally to the DOM. |
| G5 | PARTIAL | `app/services/chat_service.rb:82-92` builds chat history from stored messages excluding the current prompt, but `test/services/chat_service_test.rb:22-32` only asserts store state, not the actual outgoing message array passed to `RubyLLM.chat`. No mock verifies the exact payload. |
| G6 | PASS | `app/models/conversation_store.rb:14-16` uses `flock` for file locking; `app/models/conversation_store.rb:4-7` defines max 100 messages, 1 MB, 24h TTL; `app/models/conversation_store.rb:36-46` enforces message bound. |
| G7 | PASS | `app/models/tools/server_time.rb:4-10` and `app/models/tools/calculator.rb:4-115` inherit from `RubyLLM::Tool`; `app/services/chat_service.rb:85` registers both tools via `with_tools`. Calculator uses a safe recursive-descent parser (no `eval`). |
| G8 | PASS | `app/models/title_schema.rb:3-13` defines JSON schema; `app/services/chat_service.rb:43-68` generates title after first exchange using `with_schema(TitleSchema)`. |
| G9 | PASS | `app/models/token_budget.rb:4` defines default 4096; `app/models/token_budget.rb:8` reads from `TOKEN_BUDGET` env; `app/models/token_budget.rb:11-14` checks budget; `app/controllers/messages_controller.rb:18-21` refuses in UI when exceeded. |
| G10 | PARTIAL | System prompt: PASS (`app/services/chat_service.rb:84` uses `with_instructions`). Missing API key: PASS (`app/services/chat_service.rb:72-74`, `app/controllers/messages_controller.rb:13-16`). Provider failure rescue: PARTIAL — `StreamingController` rescues into SSE error (`streaming_controller.rb:48-54`), but `MessagesController` does not rescue `ChatService` errors (it never calls `ChatService`). Failed turns not stored: PARTIAL — assistant message is stored only after successful streaming (`streaming_controller.rb:42`), but user message is stored before streaming starts (`messages_controller.rb:24`), so a failed turn still leaves the user message in replay history. |
| G11 | PARTIAL | 25 tests pass, 35 assertions, SimpleCov wired. BUT: no mocks of RubyLLM API surface — `ChatService#stream` and `ChatService#generate_title` are untested. The multi-turn test does not assert the outgoing payload array as required by G5. Line coverage is 71.58% (194/271), not the high coverage claimed in prior session notes. |
| G12 | PASS | `bin/rubocop` — 36 files, 0 offenses. `bin/brakeman` — 0 security warnings. `bin/bundler-audit` — no vulnerabilities. |
| G13 | PASS | `Dockerfile:4-59` uses Ruby 4.0.6-slim, multi-stage build, non-root user (uid 1000), production env, entrypoint. `docker-compose.yml:1-26` defines app service with volume mount for conversation persistence. |
| G14 | PASS | No authentication code anywhere. `.gitignore:11` ignores `.env*`. No hardcoded secrets in source; `docker-compose.yml:13` uses `${OPENROUTER_API_KEY}` interpolation. |

---

## 2. Code Quality Assessment

### Naming
Generally clear and intention-revealing: `ChatService`, `ConversationStore`, `TokenBudget`, `Tools::ServerTime`, `Tools::Calculator`, `SafeCalculator`. Method names like `stream`, `generate_title`, `append_message`, `cleanup_expired` describe behavior accurately.

### Single Responsibility
- `ChatService` handles three concerns: streaming chat, title generation, and API key/budget preflight checks. Title generation could be extracted to a `TitleGenerator` service.
- `StreamingController#show` mixes HTTP response setup, SSE streaming, business logic orchestration, error handling, and persistence. At 59 lines it does too much.
- `ConversationStore` is well-focused on file I/O with locking.

### Duplication
Minimal. Error rendering patterns are duplicated between `MessagesController` (Turbo Stream error partials) and `StreamingController` (SSE error JSON). A shared error formatter could unify these.

### Dead Code
- `app/views/messages/_stream_chunk.html.erb` — unused. Streaming is entirely client-side via SSE; no Turbo Stream partial is rendered per chunk.
- `app/javascript/controllers/hello_controller.js` — default Stimulus scaffold, never referenced.
- `app/helpers/application_helper.rb` — empty module.
- `app/views/messages/_stream_chunk.html.erb` — confirmed unused by grep across the codebase.

### Method / Class Size
- `ChatService#stream` — 14 lines, acceptable.
- `StreamingController#show` — 59 lines, too long. Should extract SSE setup and streaming loop.
- `Tools::Calculator::SafeCalculator` — 99 lines including parser. Acceptable for a self-contained arithmetic parser, but the lexer logic (`tokenize`) could be extracted.

### Coupling
- Controllers depend directly on `ChatService` and `ConversationStore`.
- `TokenBudget` depends on `ConversationStore` for persistence.
- No abstraction layer around RubyLLM — the gem is referenced directly throughout `ChatService`.

### Top 3 Refactoring Priorities

1. **Add real RubyLLM mocking and integration tests** — `ChatService#stream` and `#generate_title` are the most critical paths and have zero test coverage. The current tests only verify store state, not that RubyLLM is called with the correct message array, tools, or schema. This is the highest-risk gap.

2. **Extract SSE streaming orchestration from `StreamingController`** — Move the streaming loop, token accumulation, and storage into a dedicated `StreamResponse` service or object. The controller should only handle HTTP concerns (headers, params, response format).

3. **Remove dead code and consolidate error handling** — Delete `_stream_chunk.html.erb`, `hello_controller.js`, and the empty `ApplicationHelper`. Extract a shared error presenter so `MessagesController` and `StreamingController` use the same error messages and formatting logic.

---

## 3. Test Coverage Assessment

**Actual metrics (re-run 2026-07-27):**
- **Line coverage:** 71.58% (194 / 271 lines)
- **Branch coverage:** Not enabled in current SimpleCov configuration
- **Test count:** 25 tests, 35 assertions, 0 failures

**Weakest-tested areas:**
1. `ChatService` — `stream` and `generate_title` methods are entirely untested. No mocks of `RubyLLM.chat`, `chat.complete`, `chat.with_tools`, `chat.with_schema`, or `chat.ask`.
2. `StreamingController` — only parameter validation is tested (blank message, missing API key). The actual SSE streaming loop, token accumulation, and storage are not covered.
3. View rendering and Stimulus controllers — no system or integration tests verify the DOM behavior, auto-scroll, or EventSource connection handling.

**Failure modes NOT covered by any test:**
- RubyLLM API returning an error or raising during `chat.complete` — the rescue in `ChatService#stream` is untested.
- Network timeout or disconnection during SSE streaming — `StreamingController` does not handle client disconnects gracefully.
- Malformed JSON in a persisted conversation file — `ConversationStore.read` rescues `JSON::ParserError` and returns `nil`, but this path is not explicitly tested.
- Concurrent write collision under `WEB_CONCURRENCY=2` — `flock` is present but no test simulates concurrent access.
- `TitleSchema` integration with RubyLLM — no test verifies `with_schema(TitleSchema)` produces a valid structured output.
- Token budget edge case: `add_usage` racing with `exceeded?` check between `MessagesController` and `StreamingController`.
- `MAX_BYTES` bound is defined in `ConversationStore` but never enforced — no test exists because the code path does not exist.

---

## 4. Known Defects and Risks

### Concurrency Hazards
- **Race condition on token budget:** `MessagesController` checks `TokenBudget.exceeded?` before storing the user message, then `StreamingController` checks it again before streaming. Between these two checks, another request could consume the remaining budget, causing the second check to pass but the provider call to fail. There is no atomic budget reservation.
- **File lock portability:** `flock` is POSIX-only. The app will not provide concurrency safety on Windows or some networked filesystems.

### Edge Cases
- **Path traversal in conversation_id:** `ConversationStore#file_path` interpolates `conversation_id` directly into the filename: `#{conversation_id}.json`. If `conversation_id` contains `../`, it could write outside `tmp/conversations`. The app currently generates UUIDs via `SecureRandom.uuid`, but a malicious direct request could bypass this.
- **MAX_BYTES never enforced:** `ConversationStore` defines `MAX_BYTES = 1_048_576` but never checks file size on write.
- **Client disconnect mid-stream:** If the browser closes the EventSource connection, `StreamingController` continues consuming the LLM stream but the accumulated `full_content` is never stored, and tokens are still counted against the budget.
- **Partial assistant message loss:** If an exception occurs after some chunks have been streamed but before `sse.write({ done: true })`, the partial content is lost and not stored.

### Security Concerns
- **No rate limiting:** Any client can create unlimited conversations and exhaust the OpenRouter API key budget or disk space.
- **No input sanitization on message content:** User messages are rendered raw in ERB partials (`app/views/messages/_message.html.erb:3`). While Rails HTML-escapes ERB output by default, the `whitespace-pre-wrap` class preserves formatting. If the app ever switches to raw output or markdown rendering, XSS becomes possible.
- **Calculator parser accepts `%` operator:** The recursive-descent parser handles modulo, but the tool description only mentions "basic arithmetic expression like '2 + 2'". The `%` operator is exposed but not documented, which could confuse the LLM.

### Operational Risks
- **No health check endpoint in Rails:** `docker-compose.yml:19` references `http://localhost:3000/up`, but `routes.rb:11` only mounts `rails/health#show` at `/up`. This works, but there is no custom health check verifying the file store or RubyLLM connectivity.
- **Docker entrypoint is a no-op:** `bin/docker-entrypoint` is just `exec "${@}"`. It does not handle database migrations (not applicable here) or pre-flight checks, but it is minimal and functional.
- **No logging of provider failures:** `StreamingController` rescues `StandardError` and sends a generic message to the client, but does not log the error class or message to Rails logger in all cases. `ChatService` does log errors, but the controller's generic rescue swallows details.
- **Conversation TTL sweep is O(n):** `cleanup_expired` iterates all files. With many conversations this could block requests. No background job runs cleanup automatically.
- **Title generation makes an extra API call:** After the first exchange, `generate_title` calls the provider again. This consumes tokens and adds latency, and if it fails, the error is silently logged but the user sees no title.
