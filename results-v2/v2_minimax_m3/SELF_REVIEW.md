# Self-review

Review performed against the G1-G14 contract in `../phase1.prompt.txt:9-35`. No application source fixes were made during this review.

## 1. Goal verification table

| Goal | Verdict | Concrete evidence |
|---|---|---|
| G1 | PASS | `.ruby-version:1` selects Ruby 4.0.6 and `Gemfile:4` selects Rails 8.1.3; `ruby --version && bin/rails --version && mise current ruby` returned Ruby 4.0.6, Rails 8.1.3, and mise Ruby 4.0.6. `config/application.rb:5-15` omits Active Record, Active Job, and Action Mailer; a Rails runner check returned `[nil, nil, nil]`. The generated Rails layout is at the workspace root. |
| G2 | PARTIAL | Tailwind, Stimulus, Turbo, and partial-based UI work is present (`app/views/home/index.html.erb:17-40`, `app/javascript/controllers/composer_controller.js:1-32`, `app/views/shared/_composer.html.erb:3-13`). However, `config/routes.rb:12-14` routes to two nonexistent controllers; a current root-request runner failed with `uninitialized constant ConversationsController`, so the SPA is not usable. |
| G3 | PARTIAL | `ruby_llm` 1.16.0 is locked (`Gemfile.lock:306`) and the OpenRouter key is read from the environment (`config/initializers/ruby_llm.rb:4-6`). No code constructs a RubyLLM chat, chooses Claude Sonnet, chooses OpenRouter as provider, or reads a model override. |
| G4 | FAIL | The page subscribes to a Turbo stream (`app/views/home/index.html.erb:24-26`), but a source search found no RubyLLM `ask` streaming block and no Turbo broadcast call. No message controller or chat service exists. |
| G5 | FAIL | There is no provider request/history replay implementation. `bin/rails test` ran 0 tests and 0 assertions, so the required exact outgoing multi-turn message-array test does not exist. |
| G6 | FAIL | `Conversation` is a transient ActiveModel value object (`app/models/conversation.rb:1-24`); there is no store, TTL, locking, message-count cap, or byte cap. Redis is configured only for Action Cable (`config/cable.yml:1-12`), so restart and two-worker history behavior are not implemented. |
| G7 | PARTIAL | Exactly two tool classes exist (`app/tools/server_time.rb:1-7`, `app/tools/calculator.rb:1-121`), but neither is registered with a chat. `ruby -c app/tools/calculator.rb` failed with syntax errors at lines 22 and 24, so the calculator cannot currently load. |
| G8 | PARTIAL | A RubyLLM schema is declared (`app/models/conversation_title_schema.rb:1-3`) and the header displays a supplied title (`app/views/shared/_header.html.erb:6-10`). There is no schema call, first-exchange trigger, or title persistence. |
| G9 | FAIL | `Conversation` merely accepts `used_tokens` and `reserved_tokens` values (`app/models/conversation.rb:4,11-12`). There is no token estimation, configurable budget, pre-provider refusal, or friendly budget state. |
| G10 | FAIL | The initializer only assigns the API key (`config/initializers/ruby_llm.rb:4-6`). There is no instructions API call, missing-key preflight, provider rescue path, or successful-turn-only history logic; its comment about a coordinator (`:1-3`) refers to code that does not exist. |
| G11 | FAIL | `test/test_helper.rb:1-12` is generated setup only and all test directories contain only `.keep` files. `bin/rails test` returned `0 runs, 0 assertions`; `bundle info simplecov` returned `Could not find gem 'simplecov'`, and no coverage output exists. |
| G12 | FAIL | `bundle exec bundle-audit check` returned `No vulnerabilities found`, but `bundle exec rubocop` reported 7 syntax offenses in `app/tools/calculator.rb:22,24`, and Brakeman reported one parse error for the same file. The three required gates do not all pass cleanly. |
| G13 | PARTIAL | `Dockerfile:23-28,63-77` sets production mode, creates a non-root user, and uses an entrypoint. `docker compose config` failed with `no configuration file provided: not found`, and `README.md:1-24` is the stock placeholder rather than setup/run documentation. |
| G14 | PASS | There are no authentication routes or controllers (`config/routes.rb:1-15`, `app/controllers/application_controller.rb:1-7`). The OpenRouter key is environment-only (`config/initializers/ruby_llm.rb:5`), `.gitignore:2-4,16-18` excludes secret-bearing paths, and `git ls-files -- .` returned no tracked workspace files, so no workspace secret is committed. `tmp/local_secret.txt` exists locally but is ignored by `.gitignore:6`; all application artifacts inspected are under this workspace. |

## 2. Code quality assessment

### Naming and structure

Custom names such as `Conversation`, `ChatMessage`, `ServerTime`, `Calculator::Parser`, and `chat_scroll_controller` state their intended roles clearly. The larger problem is that the names imply a functioning domain that does not exist: `Conversation` and `ChatMessage` are passive wrappers with no validation or persistence (`app/models/conversation.rb:1-24`, `app/models/chat_message.rb:1-16`), and `ChatMessage#persisted?` always returns true (`app/models/chat_message.rb:13-15`).

### Single responsibility and size

Most existing classes and Stimulus controllers are short. `Calculator` is the exception: its 121 lines combine the RubyLLM adapter and a recursive-descent arithmetic parser (`app/tools/calculator.rb:1-121`). The parser methods are individually small, but the combination makes the tool harder to test independently and currently hides syntax errors in an otherwise unused class.

### Duplication and dead code

The hash-or-object extraction lambda is duplicated in `app/views/home/index.html.erb:2-11` and `app/views/shared/_message.html.erb:1-5`. It weakens the presentation contract by silently accepting several unrelated record shapes. `app/javascript/controllers/hello_controller.js:1-7` is unused generated code. The PWA templates are unreachable because their routes remain commented (`config/routes.rb:8-10`). The main home template, models, schema, and tools are also effectively dead because no application controller or chat coordinator references them.

### Coupling between layers

There is too little implemented application flow to judge healthy layer boundaries. Routes are coupled to absent controller constants (`config/routes.rb:12-14`), while views use reflection to compensate for an undefined data contract. No controller/service/store/provider boundary exists. The initializer's reference to a coordinator that was never created (`config/initializers/ruby_llm.rb:1-3`) is stale documentation.

### Top three refactors with more time

1. **Define one presenter/view-model contract.** Replace both `read_value` lambdas with explicit objects or a helper so missing fields fail visibly and templates do not normalize arbitrary hashes and objects.
2. **Separate the calculator parser from the RubyLLM tool adapter.** A standalone parser would allow direct syntax, precedence, depth, magnitude, division-by-zero, and malformed-input tests; the tool class should only map provider arguments and results.
3. **Remove orphaned generated code and establish explicit runtime boundaries.** Delete unused controllers/templates/dependencies, then align each route with one controller, one chat coordinator, and one persistence interface. At present the central path is absent rather than merely untidy.

## 3. Test coverage assessment

- **SimpleCov line coverage: N/A (no percentage was produced).**
- **SimpleCov branch coverage: N/A (no percentage was produced).**

These values are not 0.0% measurements. SimpleCov is not installed (`bundle info simplecov` returned `Could not find gem 'simplecov'`), is not started by `test/test_helper.rb:1-12`, and no `coverage/` files exist. The current full suite command, `bin/rails test`, completed with `0 runs, 0 assertions, 0 failures, 0 errors, 0 skips`; that green exit is not evidence of tested behavior.

The weakest-tested area is the **message-to-provider lifecycle**, which is both untested and unimplemented: request validation, exact-once history replay, provider invocation, streaming broadcasts, tool calls, title generation, token accounting, persistence, and visible error handling.

No test covers any of these failure modes:

- missing API key; provider timeout, 429, 5xx, disconnect, or failure after partial streaming;
- duplicate user turns, replay of the current prompt, concurrent submissions, request idempotency, or stream ordering;
- restart recovery, two-worker access, stale locks, Redis outage, TTL expiry, message cap, or byte cap;
- token estimation, budget exhaustion, reservation rollback, or invalid/negative counters;
- tool registration and invocation; malformed calculator input, division by zero, exponent/magnitude/depth limits, or calculator precedence;
- malformed structured title output, title-generation failure, first-exchange triggering, or title length;
- controller routing, blank/oversized messages, arbitrary roles, missing conversation IDs, or cross-conversation access;
- Turbo Stream delivery, Action Cable failure, DOM identity collisions, or user scroll behavior during streaming;
- production boot, Docker image behavior, Redis connectivity, Compose startup ordering, or container health.

## 4. Known defects and risks

1. **Primary endpoints are broken.** `GET /`, `GET /conversations/:id`, and `POST /messages` point to missing controllers (`config/routes.rb:12-14`). A current root request failed with `uninitialized constant ConversationsController`.
2. **The requested chat behavior does not exist.** There is no RubyLLM chat construction, model/provider selection, prompt replay, provider call, streaming callback, tool registration, title call, budget gate, or provider rescue path.
3. **No persistence exists.** Conversation history cannot survive restart and has no concurrency control, TTL, or bounds. The SQLite dependency at `Gemfile:21` is unused.
4. **The calculator is syntactically invalid.** Ruby 4.0 parses the unescaped `/` characters in the regex literals at `app/tools/calculator.rb:22,24` as delimiters. This also prevents RuboCop and Brakeman from completing clean analysis.
5. **Duplicate and out-of-order submissions would be possible.** The composer re-enables its button at `turbo:submit-end` (`app/javascript/controllers/composer_controller.js:23-31`), not after provider completion, and the form has no idempotency key (`app/views/shared/_composer.html.erb:3-10`).
6. **Input and domain values are unbounded or weakly validated.** The message has only browser-side `required` validation (`app/views/shared/_composer.html.erb:3-6`); title length is descriptive rather than enforced (`app/models/conversation_title_schema.rb:2`); token counters accept arbitrary values through `to_i` (`app/models/conversation.rb:11-12`); roles are unrestricted (`app/models/chat_message.rb:6-10`).
7. **Production Action Cable depends on an undeployed Redis.** `config/cable.yml:9-12` defaults to `localhost`, no Compose service exists, and the Kamal Redis accessory is commented out (`config/deploy.yml:84-104`).
8. **Production environment injection is incomplete.** `config/deploy.yml:39-45` injects only `RAILS_MASTER_KEY`, not `OPENROUTER_API_KEY` or `REDIS_URL`.
9. **The production image retains test dependencies.** `Dockerfile:24-28` excludes only the development group, so Capybara and Selenium from `Gemfile:58-62` remain in the final bundle.
10. **Privacy wording is misleading.** The UI says `Private space` (`app/views/shared/_header.html.erb:10`) although authentication is deliberately absent. A future client-supplied `conversation_id` (`app/views/shared/_composer.html.erb:4`) would be an insecure-direct-object-reference risk unless server-side ownership or unguessable capability semantics are enforced.
11. **Prompt content is not explicitly filtered from logs.** The default parameter filter has no `message` or `content` entry, so future request logging may retain user prompts.
12. **Streaming scroll behavior may be disruptive.** Every subtree mutation triggers a smooth scroll (`app/javascript/controllers/chat_scroll_controller.js:8-17`), which can repeatedly pull a reader to the bottom during token streaming.
13. **The Docker/operations story is incomplete.** There is no Compose file, container health check, Redis readiness ordering, or useful README. `/up` checks only Rails boot and would not establish provider or Redis readiness.
