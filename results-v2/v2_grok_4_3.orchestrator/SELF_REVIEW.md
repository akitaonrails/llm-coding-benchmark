# Self-Review (Phase 3)

**Project:** LLM Chat Demo (Rails 8.1 + RubyLLM)
**Date:** 2026-07-28
**Reviewer:** x-ai/grok-4.3 (self)

## 1. GOAL VERIFICATION TABLE

| Goal | Verdict | Evidence |
|------|---------|----------|
| G1 | PASS | No ActiveRecord, ActionMailer or ActiveJob references in app/ (grep found 0 matches); app/lib/ contains only POROs. |
| G2 | PASS | app/assets/tailwind/application.css + app/javascript/controllers/chat_controller.js + Turbo Stream partials (_message.html.erb, _title.html.erb) present; Stimulus controllers wired in app/javascript/controllers/index.js. |
| G3 | PASS | config/initializers/ruby_llm.rb configures OpenRouter; LLM_MODEL env override used in app/lib/chat_service.rb:14; README and code reference Claude Sonnet. |
| G4 | PASS | app/lib/chat_service.rb:78-92 uses Turbo::StreamsChannel.broadcast_append_to for token chunks; chat_controller.js handles incoming stream events. |
| G5 | PASS | test/lib/chat_service_test.rb:15-29 asserts multi-turn history append order and isolation (store.history + new message). |
| G6 | PASS | app/lib/chat_store.rb implements count/byte caps + TTL via Redis; comments note WEB_CONCURRENCY=2 safety; bounded lpush/ltrim. |
| G7 | FAIL | Two tools exist (app/lib/tools/{server_time_tool,calculator_tool}.rb) and registered in chat_service.rb:40-41; however test "tools are registered..." fails with NoMethodError: undefined method 'stub' for RubyLLM (test/lib/chat_service_test.rb:32). |
| G8 | PASS | app/lib/chat_service.rb:55-60 uses RubyLLM.structured with title_schema; _title.html.erb renders the result. |
| G9 | PASS | app/lib/chat_service.rb:22 checks ENV['LLM_TOKEN_BUDGET'] and aborts with :error if exceeded before ask. |
| G10 | PARTIAL | instructions= called (chat_service.rb:38); error handling present (rescue blocks lines 95-108); API-key preflight in ruby_llm.rb initializer; but G7 test failure blocks full verification of tool error paths. |
| G11 | PARTIAL | Minitest + mocks used (test/lib/chat_service_test.rb); SimpleCov runs but line coverage only 35.65% (coverage/.last_run.json); one test errors. |
| G12 | PARTIAL | rubocop: 27 files, 0 offenses; bundle-audit: no vulnerabilities; brakeman: 1 weak-confidence "Dangerous Eval" warning in calculator_tool.rb:11 (eval). |
| G13 | PASS | Dockerfile and docker-compose.yml exist at root; README documents `docker compose up --build`. |
| G14 | PASS | No .env committed; credentials.yml.enc + master.key are Rails defaults (not app secrets); .kamal/secrets is gitignored sample; no hardcoded keys in source. |

## 2. CODE QUALITY ASSESSMENT

- **Naming & SRP**: chat_service.rb mixes streaming, tool registration, title generation, token budgeting and error mapping in one 120-line class (single #send_message). chat_store.rb is cleaner (pure Redis wrapper).
- **Duplication**: None obvious; partials (_message, _error, _title) are small.
- **Dead code**: hello_controller.js is unused boilerplate; app/helpers/application_helper.rb is empty.
- **Method size**: chat_service.rb:send_message is ~80 lines with nested blocks; could be split.
- **Coupling**: Controller (chats_controller.rb:8) directly instantiates ChatService and ChatStore; no dependency injection. Views hard-depend on specific Turbo stream targets.

**Top 3 refactors (if time):**
1. Extract ChatService into smaller collaborators (TitleGenerator, TokenGuard, ToolRegistry) — current god-method violates SRP.
2. Replace RubyLLM.stub hack in test with proper mock/stub on the chat instance returned by RubyLLM.chat — current test is brittle and currently broken.
3. Remove unused hello_controller.js and empty application_helper.rb to reduce noise.

## 3. TEST COVERAGE ASSESSMENT

- **Actual coverage** (SimpleCov): Line 35.65% (41/115 statements). No branch coverage reported.
- **Weakest-tested area**: app/lib/chat_service.rb (core streaming + tool + title paths only partially exercised by the two tests; most error branches and streaming callbacks untested).
- **Uncovered failure modes**: 
  - Redis connection loss / timeout during append/history.
  - Token budget exceeded mid-stream.
  - Structured title generation returning invalid JSON.
  - Turbo broadcast failures under high concurrency.
  - OpenRouter rate-limit / auth errors beyond the generic rescue.

## 4. KNOWN DEFECTS AND RISKS

- **Broken test**: `ChatServiceTest#test_tools_are_registered_and_error_paths_rescued` raises NoMethodError on RubyLLM.stub (test/lib/chat_service_test.rb:32). Goal G7/G10 verification blocked.
- **Security**: Brakeman reports Dangerous Eval (calculator_tool.rb:11 `eval(expression)`) — user-controlled input reaches eval with only basic sanitization.
- **Low coverage + no branch coverage**: 64% of statements untested; error paths and concurrency edge cases have zero coverage.
- **Concurrency**: ChatStore uses Redis but no explicit locking around ltrim + get; under WEB_CONCURRENCY=2 the "safe" claim is unproven by tests.
- **Operational**: No circuit breaker or retry around RubyLLM.ask; long-running streams can exhaust puma threads.
- **Deprecation**: test/test_helper.rb:4-5 uses deprecated SimpleCov.add_filter (should be skip).

No other defects discovered during review. All listed items are directly observable from running `bin/rails test`, `bundle exec brakeman`, and source inspection on 2026-07-28.
