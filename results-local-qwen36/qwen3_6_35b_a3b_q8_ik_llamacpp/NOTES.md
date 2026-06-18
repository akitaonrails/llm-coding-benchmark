# Qwen 3.6 35B A3B Q8 on ik_llama.cpp — Integration Notes

This run was performed on a dual-RTX-3090 rig using the ik_llama.cpp Docker
container on `localhost:8000` with an OpenAI-compatible `/v1` endpoint.
The benchmark harness treated it as a remote-like provider (`llamacpp`) rather
than the built-in `ollama` local backend.

## Run metadata

- Status: `completed`
- Finish reason: `stop`
- Exit code: `0`
- Elapsed: 926.78s (~15 min)
- Total tokens: 76,784
- Files generated: 179 (excluding `node_modules`, which is not counted by the harness)

## RubyLLM integration

The generated Rails app uses the real RubyLLM API correctly.

### Controller call site (`app/controllers/chats_controller.rb`)

```ruby
chat = RubyLLM.chat(model: "claude-sonnet-4-20250514")
chat.with_instructions(system_prompt)

@messages = session[:messages] || []
@messages << { role: "user", content: user_input }

response = chat.ask(user_input)

assistant_reply = response.content.to_s
@messages << { role: "assistant", content: assistant_reply }
```

This matches the canonical RubyLLM pattern:
- `RubyLLM.chat(model: ...)` — valid entry point
- `chat.with_instructions(...)` — valid system-prompt helper
- `chat.ask(user_input)` — valid single-turn call
- `response.content.to_s` — valid response accessor

No hallucinated APIs were found (`RubyLLM::Client.new`, `chat.complete`,
`chat.user`, `chat.assistant`, `response.text`, `RubyLLM.chat(messages:)`,
or `Openrouter::Client` are all absent).

### Configuration (`config/initializers/ruby_llm.rb`)

```ruby
RubyLLM.configure do |config|
  config.openrouter_api_key = ENV.fetch("OPENROUTER_API_KEY", nil)
end
```

### Gemfile

```ruby
gem "ruby_llm", ">= 1.16"
```

Lockfile resolved to `ruby_llm (1.16.0)`.

## Tests

- 4 test files, 18 test methods total
- `test/ruby_llm_config_test.rb` validates RubyLLM configuration and chat creation
- `test/controllers/chats_controller_test.rb` covers HTTP endpoints
- Tests pass, RuboCop is clean, Brakeman reports no warnings

**Caveat for scoring:** tests do not mock the live LLM call. The
controller's `send_message` action will hit OpenRouter when an API key is
present. The audit scanner confirms `has_any_mock: false` and no `FakeChat`.

## Audit scanner summary

- `ruby_llm` gem present, `ruby_openai` absent
- Ruby version: 3.4.9 (Gemfile, Dockerfile, `.ruby-version`)
- `rails new` excluded Active Record, Action Mailer, and Active Job as requested
- Tailwind CSS, Turbo Rails, Stimulus Rails present
- Dockerfile present but does not set `SECRET_KEY_BASE`
- No `rescue` blocks around LLM calls
- No secrets committed to the repo
