# Self-review

No code was changed during this review.

## 1. GOAL VERIFICATION TABLE

| Goal | Verdict | Concrete evidence |
|---|---|---|
| G1 | PASS | `ruby -v && bin/rails --version` returned Ruby 4.0.6 and Rails 8.1.3; `.ruby-version:1` pins Ruby 4.0.6, and `config/application.rb:5-15` leaves Active Record, Active Job, and Action Mailer disabled. |
| G2 | PARTIAL | Tailwind, Turbo Streams, Stimulus, and Rails partials are present (`Gemfile:11-16`, `app/views/conversations/show.html.erb:2-26`, `app/javascript/controllers/chat_controller.js:1-53`), and a fresh Compose check returned HTTP 200 for all nine referenced assets; however, status broadcasts remove the Stimulus target and header broadcasts replace an `<h1>` with a whole `<header>` (`app/services/chat_turn.rb:78-81`, `app/views/conversations/_header.html.erb:1-12`, `app/views/conversations/_status.html.erb:1`), so repeated interaction is defective. |
| G3 | PASS | RubyLLM 1.16.0 is pinned at `Gemfile:19`; OpenRouter is configured from the environment at `config/initializers/ruby_llm.rb:1-3`; `CHAT_MODEL` overrides the default Claude Sonnet alias at `app/services/chat_turn.rb:45`. |
| G4 | PASS | `app/services/chat_turn.rb:49-53` appends each provider chunk to a buffer and broadcasts each accumulated intermediate value; `tmp/phase2-local.log:144-171` records repeated assistant-bubble replacements before completion. |
| G5 | PARTIAL | `app/services/chat_turn.rb:47-50` replays stored history and then sends the new prompt once through `ask`, but the required exact outgoing multi-turn message-array test does not exist; the only tests are the two pending-render tests at `test/services/chat_turn_test.rb:16-29`. |
| G6 | PARTIAL | Persistence uses cross-process file locks, atomic rename, TTL checks, message caps, and byte caps (`app/services/conversation_store.rb:6-13,25-35,77-90`), and `tmp/phase2-multi-restart.log:5-19,79-87` records a two-worker restart check. The whole turn is not locked, though: fetch, budget check, provider call, and commit are separate (`app/services/chat_turn.rb:18-25`), so concurrent turns can use stale history, bypass the budget, and commit out of order. |
| G7 | PASS | Exactly `ServerTimeTool` and `CalculatorTool` are registered at `app/services/chat_turn.rb:45-47`; their implementations are at `app/tools/server_time_tool.rb:1-7` and `app/tools/calculator_tool.rb:1-20`; actual invocations appear at `tmp/phase2-local.log:103,172`. |
| G8 | PASS | First-exchange title generation uses `with_schema(ConversationTitleSchema)` at `app/services/chat_turn.rb:29,58-66`, with the schema at `app/schemas/conversation_title_schema.rb:1-3`; persisted review data contains generated non-default titles, and the view renders the title at `app/views/conversations/_header.html.erb:4`. |
| G9 | PASS | Approximate usage is calculated at `app/services/token_estimator.rb:1-4`, checked before the provider call and refused with an in-UI message at `app/services/chat_turn.rb:19-20,32-34`, persisted at `app/services/conversation_store.rb:44-47`, and configured by `CHAT_TOKEN_BUDGET` at `app/services/chat_turn.rb:71`. Concurrency and output-reservation limitations are recorded below. |
| G10 | PASS | The system prompt is passed through `with_instructions` (`app/services/chat_turn.rb:2-6,45-47`); missing-key preflight and friendly messages are at `app/services/chat_turn.rb:16,32-39`; the exchange is committed only after a non-empty completed reply at `app/services/chat_turn.rb:24-25,54-55`. |
| G11 | FAIL | `bin/rails test` exited 0 but ran only **2 tests / 3 assertions**; SimpleCov reports **27.10% line** and **0.00% branch** coverage (`coverage/.last_run.json:2-5`). Controllers, tools, persistence, provider/error paths, title generation, budgeting, and exact multi-turn payloads are not tested. |
| G12 | PASS | Current runs: `bin/rubocop` — 30 files, no offenses; `bin/brakeman --no-pager` — 0 errors and 0 warnings; `bin/bundler-audit` — no vulnerabilities. |
| G13 | PASS | `docker build -t v2_nex_n2_pro_self_review .` completed successfully. `HOST_PORT=3013 docker compose -p v2_nex_n2_pro_self_review up -d --build` then returned 200 for `/up`, `/`, and every referenced CSS/JS asset; Docker runs production as a non-root user (`Dockerfile:9-13,34-47`), Compose supplies Redis and persistent volumes (`compose.yaml:1-33`), and setup/run instructions are at `README.md:13-56`. |
| G14 | PASS | The application is explicitly no-auth (`README.md:3`); the provider key is read only from the environment (`config/initializers/ruby_llm.rb:2`, `compose.yaml:12`); secret-bearing files are ignored at `.gitignore:2-5` and `.dockerignore:9-12`; a source/config scan found no OpenRouter-key or private-key literal. |

## 2. CODE QUALITY ASSESSMENT

### Findings

- **Naming:** Class and method names such as `ChatTurn`, `ConversationStore`, `TokenEstimator`, and `commit_exchange` are direct and understandable. Controllers are short (`app/controllers/messages_controller.rb:1-9`, `app/controllers/conversations_controller.rb:1-11`).
- **Single responsibility:** `ChatTurn` has too many responsibilities. It validates configuration and input, checks budgets, assembles provider history, streams, persists, generates titles, renders partials, knows DOM IDs/CSS, and presents errors in one 83-line class (`app/services/chat_turn.rb:15-81`).
- **Duplication:** Model construction is repeated at `app/services/chat_turn.rb:45-46,59-60`; token-budget parsing is duplicated at `app/services/chat_turn.rb:71` and `app/controllers/conversations_controller.rb:9`; title truncation is duplicated at `app/services/chat_turn.rb:65` and `app/services/conversation_store.rb:55`.
- **Dead code:** `ChatTurn#broadcast_append` is unused (`app/services/chat_turn.rb:76`). PWA templates exist, but their routes are commented out (`config/routes.rb:8-10`).
- **Method/class size:** `ChatTurn#call` coordinates the entire transaction and its UI effects (`app/services/chat_turn.rb:15-40`). `CalculatorTool::Parser` compresses recursive-descent parsing into dense one-line methods, making error paths hard to inspect (`app/tools/calculator_tool.rb:12-20`).
- **Coupling:** The service layer depends directly on Turbo partial names, DOM IDs, CSS, and raw HTML (`app/services/chat_turn.rb:22-30,73-81`). Controllers, services, and views exchange mutable string-keyed hashes rather than a conversation abstraction (`app/controllers/conversations_controller.rb:4-9`, `app/services/chat_turn.rb:18-29`, `app/views/conversations/show.html.erb:1-18`).
- **Tests:** The two tests verify broadcast ordering by calling a private method and inspecting template source text (`test/services/chat_turn_test.rb:16-29`). They do not exercise the public chat-turn behavior.

### Top three refactors with more time

1. **Split `ChatTurn` into collaborators** for provider interaction, title generation, and Turbo presentation. This would remove presentation details from business logic and make failure handling independently testable.
2. **Introduce a per-conversation turn coordinator/transaction** covering history read, budget reservation, provider call ownership, and commit. The current short lock windows do not make concurrent turns correct.
3. **Add a `Conversation` value object plus centralized configuration** instead of passing string-keyed hashes and reparsing environment variables in multiple layers. This would reduce schema coupling and duplicated defaults.

## 3. TEST COVERAGE ASSESSMENT

Command run: `bin/rails test` — exit 0, 2 tests, 3 assertions, 0 failures.

- **SimpleCov line coverage:** 27.10% (45/166).
- **SimpleCov branch coverage:** 0.00% (0/65).
- **Weakest-tested area:** The application behavior outside pending-message rendering. Both controllers and `CalculatorTool` have 0% coverage; `ServerTimeTool`, `TokenEstimator`, `ConversationTitleSchema`, and the core `ChatTurn#call`/`ConversationStore` paths are effectively untested.

Failure modes with no test coverage include:

- Missing API key, blank input, missing/expired/corrupt conversation, and token-budget refusal.
- Exact multi-turn provider messages and prevention of duplicate prompts.
- Partial, nil-only, empty, timed-out, or failed provider streams; failed broadcast recovery; failed title parsing.
- Concurrent turns, file-lock behavior, atomic-write cleanup, TTL cleanup, and message/byte trimming.
- Forbidden conversation IDs, Turbo versus HTML controller responses, and HTTP status behavior on failed turns.
- Calculator precedence, unary operators, malformed expressions, division by zero, and recursion limits; UTC formatting in `ServerTimeTool`.
- Browser behavior after Turbo replacements, including Stimulus targets, title/header replacement, empty-state removal, and repeated submissions.

## 4. KNOWN DEFECTS AND RISKS

### Confirmed defects

- **Failed turns still return HTTP 204.** `ChatTurn` rescues and returns `nil`, but `MessagesController` always returns success (`app/services/chat_turn.rb:32-39`, `app/controllers/messages_controller.rb:6-7`). Stimulus therefore enters its success path and clears the prompt (`app/javascript/controllers/chat_controller.js:22-29`).
- **Turbo replacement targets are inconsistent.** `broadcast_header` targets the `<h1 id="conversation_title">` but renders the entire header partial, creating nested headers (`app/services/chat_turn.rb:78`, `app/views/conversations/_header.html.erb:1-12`). Status replacement HTML omits `data-chat-target="status"`, so later `statusTarget` access can raise (`app/services/chat_turn.rb:79-81`, `app/views/conversations/_status.html.erb:1`, `app/javascript/controllers/chat_controller.js:17-31`).
- **Concurrent turns are not serialized.** Two requests can read the same history and token count, call the provider concurrently, reuse the same pending DOM IDs, and commit in completion order (`app/services/chat_turn.rb:18-27`, `app/services/conversation_store.rb:25-48`).
- **Malformed calculator input can escape the tool.** `bin/rails runner` showed both `""` and `"1 +"` raise `TypeError`; `CalculatorTool#execute` rescues only `ArgumentError` and `ZeroDivisionError` (`app/tools/calculator_tool.rb:5-9,13-17`).
- **The initial welcome panel is never removed.** Pending messages append below it (`app/views/conversations/show.html.erb:11-15`, `app/views/conversations/_pending_messages.turbo_stream.erb:1-2`).
- **Title-generation failure feedback is immediately overwritten.** `generate_title` broadcasts an error, then `call` broadcasts `Ready` (`app/services/chat_turn.rb:29-30,67-68`).

### Concurrency, capacity, and operational risks

- The budget check reserves only the incoming message, not assistant output, and concurrent requests can both pass it (`app/services/chat_turn.rb:19-25`). A completed exchange can substantially exceed the configured budget.
- Each streamed chunk rerenders and rebroadcasts the entire accumulated response (`app/services/chat_turn.rb:48-53`), producing approximately quadratic transmitted bytes for long responses.
- Provider streaming and synchronous title generation occupy a Puma request thread; there is no application-level provider timeout or cancellation path (`app/services/chat_turn.rb:24-30,44-66`, `config/puma.rb:28-29`).
- Per-conversation message bytes are bounded, but total disk usage is not. Expiration is lazy and lock files are never removed (`app/services/conversation_store.rb:25-33,68,77-79`).
- Trimmed conversations reuse length-based DOM IDs while old nodes remain in the page, risking duplicate IDs and incorrect replacements (`app/services/chat_turn.rb:26-27`, `app/services/conversation_store.rb:86-90`).
- File persistence works across local Puma workers but is not safe for multiple hosts unless they share a filesystem with compatible locking semantics (`app/services/conversation_store.rb:11-13`, `compose.yaml:17-18`).

### Security and privacy risks

- There is deliberately no authentication or rate limiting. Resetting the signed conversation cookie creates another budget, so a reachable deployment can consume provider funds (`README.md:3`, `app/controllers/conversations_controller.rb:3-8`).
- User prompts are stored as plaintext JSON (`app/services/conversation_store.rb:75-82`). The `content` parameter is not in the filter list (`config/initializers/filter_parameter_logging.rb:6-8`), so request logging may also retain prompt text.
- Compose uses a dummy Rails secret and production does not force TLS; the README correctly limits this configuration to a local demo (`compose.yaml:9`, `config/environments/production.rb:24-29`, `README.md:34-36`).
- Title truncation uses `byteslice`, which can split a multibyte UTF-8 character and make persistence/rendering fail (`app/services/chat_turn.rb:65`, `app/services/conversation_store.rb:55`).
