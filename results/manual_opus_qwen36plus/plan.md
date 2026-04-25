# Plan: opus 4.7 (planner = Claude Code session) + qwen 3.6 plus (executor = opencode invocations)

## Working directory
`/mnt/data/Projects/llm-coding-benchmark/results/manual_opus_qwen36plus/project/` — currently empty. The Rails app must live in this root, NOT a nested `chat_app/` subdir.

## Executor invocation pattern
Each subtask is dispatched via:
```
OPENCODE_CONFIG=/mnt/data/Projects/llm-coding-benchmark/config/opencode.benchmark.json \
  opencode run --agent build --format json \
    -m openrouter/qwen/qwen3.6-plus:free \
    "<subtask prompt>"
```
Run from inside the project directory. The opencode invocation is a fresh single-agent session (no task subagent) — opencode's primary IS Qwen 3.6 Plus. No envelope mismatch.

## Implementation contract (fixed in advance, referenced in every subtask)

- **Stack**: Rails 8.1.x, Ruby 3.4.9 or 4.0.x via mise, no ActiveRecord/ActionMailer/ActiveJob, Tailwind CSS, Hotwire/Stimulus/Turbo Streams
- **Gemfile must include**: `ruby_llm`, `turbo-rails`, `stimulus-rails`, `tailwindcss-rails`, `brakeman`, `rubocop-rails-omakase`, `simplecov`, `bundler-audit`, `webmock`, `mocha`
- **Service class**: `ChatService` in `app/services/chat_service.rb` with public method `ChatService.new(history:).reply(user_message)` returning the assistant content string
- **RubyLLM API (verified real, do NOT invent variants)**:
  - `RubyLLM.chat(model:, provider: :openrouter)` — returns Chat instance
  - `chat.with_instructions(system_text)` — sets system prompt
  - `chat.add_message(role: :user, content: "...")` — appends a turn (Ruby parses kwargs as positional hash)
  - `chat.ask(user_message)` — sends turn, returns Message
  - `response.content` — extracts assistant text (NOT `response.text`, NOT `.choices`)
  - DO NOT use: `RubyLLM::Client.new`, `chat.user(...)`, `chat.assistant(...)`, `chat.send_message(...)`, batch `RubyLLM.chat(messages: [...])`
- **Model id for the chat backend**: `anthropic/claude-sonnet-4.6` (real OpenRouter id as of 2026-04)
- **OpenRouter config** in `config/initializers/ruby_llm.rb`:
  ```ruby
  RubyLLM.configure do |c|
    c.openrouter_api_key = ENV.fetch("OPENROUTER_API_KEY", nil)
  end
  ```
- **Routes**: `GET /` → `ChatsController#show`, `POST /messages` → `MessagesController#create` (turbo_stream response)
- **Persistence**: cookie-based session transcript (single-process safe, capped ~25 turns to stay under 4KB cookie ceiling)
- **Tests**: WebMock stubbing the real `https://openrouter.ai/api/v1/chat/completions` URL with realistic OpenAI-shape JSON. Must assert that the second outbound request body contains prior conversation turns (multi-turn proof).
- **No secrets in repo**: no `.env`, no committed `master.key`, `.gitignore` covers `.env*` and `*.key`
- **Workspace root scope**: do NOT create a nested subdirectory. The Rails app lives at the project root.

## Subtasks (all dispatched via opencode-with-qwen36plus)

1. **Workspace check + Rails skeleton**: confirm current dir is empty; run `rails new . --skip-active-record --skip-action-mailer --skip-action-cable --skip-active-storage --skip-active-job --skip-jbuilder --skip-test --css=tailwind --javascript=importmap --skip-bundle`; then `bin/rails javascript:install:bun || bundle install`; verify `bin/rails routes` works.
2. **Add gems + RubyLLM initializer**: edit Gemfile to add the required gems; run `bundle install`; create `config/initializers/ruby_llm.rb` with the OpenRouter config above.
3. **Service class + chat domain**: create `app/services/chat_service.rb` using only the verified real API (`RubyLLM.chat`, `with_instructions`, `add_message`, `ask`, `response.content`). Create `app/models/message.rb` as a PORO Struct with `role` and `content` attributes (NO ActiveRecord). Build a `ChatSession` value-object that wraps the cookie transcript with a 25-message cap.
4. **Controllers + routes + views**: routes for `/` and `POST /messages`; thin controllers; partials `_message`, `_form`, `_empty_state`; turbo_stream view for create.
5. **Stimulus + Tailwind polish**: two Stimulus controllers — composer (Enter to submit, Shift+Enter for newline, autoresize) and scroll (MutationObserver for auto-scroll on new messages). Tailwind classes for the ChatGPT-like layout.
6. **Tests**: Minitest suite with WebMock that stubs the real OpenRouter URL, asserts request body shape, asserts second-request includes prior turns. Cover error paths (missing API key, 5xx response).
7. **CI tooling**: wire RuboCop, Brakeman, SimpleCov, bundle-audit. Create `bin/ci` script that runs all of them sequentially.
8. **Dockerfile + compose.yaml**: multi-stage Dockerfile with Ruby 3.4.9, non-root user, health check on `/up`. compose.yaml that requires `OPENROUTER_API_KEY` and `SECRET_KEY_BASE` via `${VAR:?}` syntax.
9. **README**: hand-written, not the stock template. Sections: what it does, prerequisites, env var setup, local boot, Docker boot, running tests + CI, known limitations (cookie size, single-process session).
10. **Validation pass**: run `bin/rails server` in background + `curl /up`; run `bin/ci`; run `docker build .`; run `docker compose up -d --build` + curl `/up`. Report pass/fail per step.

After each dispatch I'll Read the produced files, append to the trace, and dispatch the next subtask or a fix-up. When validation passes (or hits a hard blocker), both me and the final opencode invocation declare DONE.
