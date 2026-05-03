# Scoring Rubric & API Verification

This file contains the detailed scoring rubric and RubyLLM API verification
rules. Load it when scoring a model's output. The 8 dimensions total 100 points.

**Canonical source of truth:** `docs/audit_prompt_template.md` in the project
root takes precedence over this file. If they conflict, the template wins.
Always verify RubyLLM API claims by grepping the gem source, not by memory.

---

## RubyLLM API Verification (1.14.1)

Grep the gem source at:
`~/.local/share/mise/installs/ruby/4.0.2/lib/ruby/gems/4.0.0/gems/ruby_llm-1.14.1/lib/ruby_llm/chat.rb`

**Valid (do NOT flag):**
- `RubyLLM.chat(model:, provider:, assume_model_exists:, context:)` — top-level entry
- `RubyLLM::Chat.new(model:, provider:, assume_model_exists:, context:)` — valid constructor
- `chat.ask(message, with: nil, &block)` — send a message
- `chat.add_message(message_or_attributes)` — accepts a `Message` or a hash.
  `chat.add_message(role: :user, content: "x")` works because Ruby parses it as
  `chat.add_message({role:, content:})` — a positional hash. This is NOT a kwargs bug.
- `chat.complete(&block)` — real public method
- `chat.with_instructions(text, append:, replace:)` — system prompt
- `chat.with_model`, `with_temperature`, `with_tools`, `with_params`,
  `with_headers`, `with_schema`, `reset_messages!`
- `response.content` — correct response accessor

**Hallucinated (flag when present):**
| Pattern | Penalty |
|---|---|
| `RubyLLM::Client.new` | -15 |
| `Openrouter::Client` (wrong casing) | -15 |
| `chat.user(msg)` / `chat.assistant(msg)` / `chat.system(msg)` | -5 |
| `RubyLLM.chat(model:, messages: [...])` batch form | -10 |
| `response.text` / `response.message` / `response.output_text` | -3 |
| `RubyLLM::Chat.new.with_model { \|chat\| ... }` block form | -15 |
| OpenAI-style `response.choices.first.message.content` | -3 |

**Bypass penalty:** If the model uses `ruby-openai` gem or `OpenAI::Client`
directly instead of `ruby_llm`, mark as ⚠️ bypass. Do NOT apply the -15
hallucination penalty. Deduct -5 for failing the explicit gem requirement.

---

## The 8 Dimensions

### 1. Deliverable Completeness (0-25)

For each missing or broken item, apply the penalty:

| Item | Penalty |
|---|---|
| Dockerfile missing or broken Ruby version (5.x, 2.x, non-numeric) | -5 |
| docker-compose.yml missing | -5 |
| README is stock template ("This README would normally document...") | -5 |
| Gemfile `ruby_llm` → uses `ruby-openai` or `rubyllm` instead | -5 |
| Each missing gem (`turbo-rails`, `stimulus-rails`, `tailwindcss-rails`, `brakeman`, `rubocop`/omakase, `simplecov`, `bundler-audit`) | -1 |
| Routes + controllers + views missing or trivial | -3 |
| No test folder | -3 |
| Nested subdirectory (`project/app/` instead of root) | -5 |
| Committed `.env` or secret files | -3 |
| `config/initializers/ruby_llm.rb` present | +0 (informational) |

### 2. RubyLLM Integration Correctness (0-20)

Verify against the API verification table above.

- Entry: `RubyLLM.chat(...)` or `RubyLLM::Chat.new(...)`? (+4)
- Send: `chat.ask(message)`? (+4)
- Response: `response.content` (not `.text`)? (+4)
- Multi-turn: reuses same chat object? (+4)
- System prompt via `with_instructions`? (+4)
- Model slug targets latest Claude Sonnet (`anthropic/claude-sonnet-4`)? (informational)
- Obsolete slug (`claude-3.7-sonnet`)? -2 (informational)

### 3. Test Quality (0-15)

Read the actual test files. Quality over quantity — number of tests is
not a valid score.

- Exercises LLM path (not just constants/guards)? No → -10
- Uses real mocks (WebMock, mocha, FakeChat with real signature)? No → -3
- Mocks a HALLUCINATED API (tests pass green but code breaks at runtime)? → -5
- Covers error paths (API failure, missing env)? No → -3
- Tests each component (controller, service, view partials)? Missing → -2 each
- Tests that mock a hallucinated API are worse than no tests — penalize.

### 4. Error Handling (0-10)

- Rescue around LLM calls? No = 500 page
- Preflight for missing API key? Friendly message?
- Degraded UI visible when LLM fails?
- No handling → -10; Partial → -5

### 5. Persistence / Multi-turn State (0-10)

| Approach | Rating |
|---|---|
| Rails cache with TTL + cap | Best (multi-worker safe) |
| Session cookie (~4KB) | Good, but penalize -2 if no message cap/limit |
| Singleton | Bad (process-local, lost on restart) |
| Class variables | Bad |
| No persistence | Demo-only |

### 6. Hotwire / Turbo / Stimulus (0-10)

- Real Turbo Streams for messages? No → -5
- `fetch()` + `innerHTML` anti-pattern? → -3
- Stimulus controllers (auto-scroll, composer, form state)? Missing → -3
- Partial decomposition (Rails partials)? Missing → -2
- Broadcast support = bonus +2 (does not reduce penalties)

### 7. Architecture (0-5)

- Service objects separate from controllers?
- PORO vs AR-like wrapper?
- View partial decomposition?
- Avoids code dumps in controllers?

### 8. Production Readiness (0-5)

- Multi-worker safe?
- No XSS (no `sanitize: false` on LLM output)?
- No leaked secrets, no committed `.env`
- CSRF not globally disabled
- No Active Record / Action Mailer / Active Job configs left behind if
  prompt explicitly excluded them? Missing cleanup → -2

---

## Golden Rules

1. **Never rely solely on file_count or test_count.** A model may generate
   1500 files and 37 tests that mock a hallucinated API. Always read the
   LLM integration code manually.

2. **Never trust the scanner alone for subjective calls.** The scanner counts
   `rescue` occurrences but cannot tell if they wrap LLM calls. It detects
   `innerHTML` but cannot distinguish Stimulus controller helpers from the
   `fetch` + `innerHTML` anti-pattern. Always read the code manually for
   dimensions 2-8.

3. **If status is failed/timeout:** still evaluate what was generated (it may be
   useful to understand where the model broke), but the final score must reflect
   the structural incompleteness.
