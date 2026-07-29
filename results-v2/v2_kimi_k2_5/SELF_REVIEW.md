# Self-Review: ChatGPT-like Demo

## 1. GOAL VERIFICATION TABLE

| Goal | Verdict | Evidence |
|------|---------|----------|
| G1 | PASS | `config/application.rb:6-15` - Active Record, Active Job, Action Mailer all commented out; app uses file-based persistence via `PersistenceService` |
| G2 | PASS | `app/views/chat/index.html.erb:1-49` - Tailwind classes throughout; `app/views/messages/_message.html.erb` - partial component; `app/javascript/controllers/chat_controller.js` - Stimulus controller; Turbo Streams via `turbo_stream_from` in layout |
| G3 | PASS | `Gemfile:29` - `gem "ruby_llm"` v1.16.0; `app/services/llm_service.rb:7` - DEFAULT_MODEL = "anthropic/claude-sonnet-5"; lines 67-70 - OpenRouter configuration |
| G4 | PARTIAL | `app/controllers/messages_controller.rb:19-21` - streams via Thread.new; `lines 39-43` - yields chunks via `LlmService.stream`; `lines 102-109` - Turbo::StreamsChannel.broadcast_replace_to. Implementation exists but background Thread approach has operational risks (see Defects) |
| G5 | PASS | `test/services/llm_service_test.rb:64-105` - test "multi-turn conversation sends exact outgoing message array" mocks and asserts exact outgoing message array; `app/services/llm_service.rb:138-147` - build_chat excludes incomplete turns |
| G6 | PASS | `app/services/persistence_service.rb:9` - MAX_CONVERSATIONS = 100; line 10 - MAX_MESSAGES_PER_CONVERSATION = 50; line 11 - MAX_BYTES_PER_CONVERSATION = 64KB; line 12 - DEFAULT_TTL_SECONDS = 7 days; lines 90-94 - flock(LOCK_SH); lines 101-113 - flock(LOCK_EX) |
| G7 | PASS | `app/services/llm_service.rb:13-19` - ServerTimeTool < RubyLLM::Tool; lines 21-34 - CalculatorTool < RubyLLM::Tool; lines 134-135 - registered via with_tool |
| G8 | PARTIAL | `app/services/llm_service.rb:36-47` - TitleSchema class with to_json_schema; lines 109-127 - generate_title method; `app/controllers/messages_controller.rb:67-82` - maybe_generate_title. Test mocks API but actual end-to-end not verified |
| G9 | PASS | `app/services/llm_service.rb:8` - DEFAULT_TOKEN_BUDGET = 8_192; lines 62-64 - token_budget from env; lines 81-83 - raises BudgetExceededError; `app/controllers/messages_controller.rb:51-54` - catches and displays friendly message |
| G10 | PASS | `app/services/llm_service.rb:6` - SYSTEM_PROMET; lines 50-52 - configured? checks api_key; lines 76-77 - MissingApiKeyError; lines 103-105 - error logging; `app/controllers/messages_controller.rb:51-63` - error handling for BudgetExceededError, MissingApiKeyError, generic errors |
| G11 | PASS | 37 tests pass (0 failures, 0 errors); `test/test_helper.rb:8-14` - SimpleCov configured; coverage: 96.52% lines (250/259 covered); `test/services/llm_service_test.rb:64-105` - G5 multi-turn test with mocks matching RubyLLM API |
| G12 | PASS | `bundle exec rubocop` - 32 files, no offenses; `bundle exec brakeman` - 0 security warnings; `bundle exec bundler-audit` - No vulnerabilities found |
| G13 | PASS | `Dockerfile:1-80` - multi-stage build, RAILS_ENV=production, USER 1000:1000 non-root; `docker-compose.yml:1-33` - Redis dependency, env vars, volumes; `README.md:1-85` - setup, env vars, Docker instructions |
| G14 | PASS | No authentication middleware; `.gitignore:11` - ignores /.env*; no hardcoded secrets in source (only ENV.fetch references); all code in current workspace |

## 2. CODE QUALITY ASSESSMENT

### Naming
- Generally clear: `LlmService`, `PersistenceService`, `Conversation`, `ServerTimeTool`, `CalculatorTool`
- Issue: `TitleSchema` is a class but acts like a value object; `clamp_bytes` name is cryptic

### Single Responsibility
- **Violation**: `MessagesController` (110 lines) handles HTTP, streaming orchestration, error handling, title generation, and Turbo broadcasts. Should extract `StreamAssistantService`.
- **Violation**: `LlmService` mixes configuration, streaming, title generation, and tool definitions.
- **Good**: `PersistenceService` focuses only on storage concerns.

### Duplication
- `app/controllers/messages_controller.rb:84-99` - broadcast_append_message and broadcast_append_assistant_message are nearly identical (DRY violation)
- `app/services/persistence_service.rb:86-94` and `97-113` - with_read_lock and with_write_lock share file setup logic

### Dead Code
- `app/javascript/controllers/hello_controller.js` - Stimulus example, not referenced
- `app/views/pwa/service-worker.js` and `manifest.json.erb` - PWA files, not used by the chat app

### Method/Class Size
- `MessagesController#stream_assistant_response`: 34 lines (borderline)
- `LlmService#build_chat`: 19 lines (acceptable)
- `PersistenceService#save`: 34 lines (complex)

### Coupling
- `MessagesController` tightly coupled to `LlmService`, `Conversation`, `PersistenceService`, `Turbo::StreamsChannel`
- `LlmService` tightly coupled to RubyLLM gem (acceptable for a service)

### Top 3 Refactors with More Time

1. **Extract Background Job for Streaming** - Replace `Thread.new` in MessagesController with a proper job framework (or Action Cable async handler). Threads are unbounded and silently die on uncaught exceptions. File: `app/controllers/messages_controller.rb:19-21`

2. **Replace Kernel.eval in CalculatorTool** - Despite regex sanitization, `Kernel.eval` at `app/services/llm_service.rb:30` is a code injection risk. Use `dentaku` gem or a proper math parser.

3. **Split MessagesController** - Extract `MessageStreamer` service to handle the streaming lifecycle, error handling, and title generation. Controller should only handle HTTP concerns. Current 110-line controller violates SRP.

## 3. TEST COVERAGE ASSESSMENT

### Coverage Metrics
- **Line Coverage**: 96.52% (250/259 lines covered)
- **Branch Coverage**: NOT ENABLED (SimpleCov configured without branch coverage)

### Missed Lines (9 total)
- `app/controllers/messages_controller.rb:70-73` - Title generation success branch (0 hits)
- `app/controllers/messages_controller.rb:24-26` - Generic error rescue in create (0 hits)
- `app/controllers/chat_controller.rb:7-9` - Else branch when no conversations (0 hits)
- `app/services/llm_service.rb:122-123` - Title generation result handling (0 hits)

### Weakest-Tested Area
**Title Generation (G8)**: Tests mock `RubyLLM::Chat` completely; no integration test verifies the actual schema -> JSON -> title flow. The `maybe_generate_title` method in MessagesController has the success branch uncovered.

### Uncovered Failure Modes
1. **Corrupted JSON file**: PersistenceService has no test for malformed JSON in `conversations.json`
2. **Thread death**: No test for what happens when `Thread.new` raises an uncaught exception
3. **File locking timeout**: No test for flock contention under heavy load
4. **Redis unavailable**: No test for Turbo::StreamsChannel failure when Redis is down
5. **Tool execution errors**: ServerTimeTool and CalculatorTool error paths not tested
6. **Network timeouts**: LLM API timeout scenarios not tested

## 4. KNOWN DEFECTS AND RISKS

### Security
- **HIGH**: `app/services/llm_service.rb:30` - `Kernel.eval` in CalculatorTool. Regex `[^0-9+\-*/().\s]` can be bypassed. Use a safe math parser instead.
- **MEDIUM**: No rate limiting on message creation - vulnerable to spam/DDoS

### Concurrency & Threading
- **HIGH**: Unbounded Thread creation at `app/controllers/messages_controller.rb:19-21`. Each message spawns a new thread with no pool, queue, or backpressure. Under load, this exhausts system resources.
- **HIGH**: Silent thread death - exceptions in `stream_assistant_response` are caught and logged, but if the Thread itself fails to spawn or dies unexpectedly, the user sees no response.
- **MEDIUM**: File-based storage with flock does not scale across multiple servers (no shared storage)

### Data Integrity
- **MEDIUM**: `PersistenceService#clamp_bytes` (`lines 116-123`) calculates JSON size but actually removes oldest messages, not largest. Logic is inverted - it keeps messages under the limit instead of removing excess.
- **LOW**: No validation that loaded conversation data matches expected schema; malformed JSON could cause runtime errors

### Operational
- **MEDIUM**: `tmp/storage/conversations.json` stored in container - data lost on container restart unless volume mounted (Docker Compose does mount it)
- **LOW**: No health check endpoint for the chat functionality (only Rails default `/up`)
- **LOW**: Background streaming means user gets 200 OK before message is processed - no way to know if streaming failed

### Edge Cases Not Handled
- Empty assistant content (first stream chunk) not differentiated from completion
- Very long messages (>64KB after JSON serialization) could be truncated unexpectedly
- Title generation happens after first exchange but only checks `messages.count == 2` - if first response is an error, title is still generated

---

## Summary

**PASS**: 11 goals | **PARTIAL**: 2 goals (G4 streaming implementation has threading risks, G8 title generation partially tested) | **FAIL**: 0 goals

The application meets the functional requirements but has operational concerns around unbounded thread spawning and the use of `Kernel.eval`. Code quality is acceptable for a demo but would require refactoring for production use.
