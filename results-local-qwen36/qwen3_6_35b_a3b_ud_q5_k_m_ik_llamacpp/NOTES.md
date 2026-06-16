# Qwen 3.6 35B A3B UD-Q5_K_M on ik_llama.cpp — Integration Notes

This run was performed on a dual-RTX-3090 rig using the ik_llama.cpp Docker
container on `localhost:8000` with an OpenAI-compatible `/v1` endpoint.
The first GPU was capped to 200W to limit thermal throttling, so inference
speed is not representative of the hardware.

## Run metadata

- Status: `completed`
- Finish reason: `stop`
- Exit code: `0`
- Elapsed: 1201.73s (~20 min)
- Total tokens: 118,742
- Files generated: 87 (excluding `node_modules`, which is not counted by the harness)

## RubyLLM integration

The generated app uses a mix of real and hallucinated RubyLLM APIs.

### Service call site (`app/services/llm_service.rb`)

```ruby
RubyLLM.configure do |config|
  config.default_provider = :openrouter
  config.providers[:openrouter] = {
    api_key: api_key,
    base_url: "https://openrouter.ai/api/v1"
  }
end

RubyLLM::Client.new(provider: :openrouter)
```

`RubyLLM::Client.new` is a hallucinated API — the real gem uses
`RubyLLM.chat(provider: ...)` to obtain a `RubyLLM::Chat` instance.

```ruby
client.chat do |c|
  c.system chat.system_prompt
  chat.messages.each do |msg|
    c.send(msg.role, msg.content)
  end
end
```

`c.system` and `c.send(role, content)` are also hallucinated DSL methods.
The real RubyLLM API is:

```ruby
chat = RubyLLM.chat(model: "anthropic/claude-sonnet-4-20250514")
chat.with_instructions(system_prompt)
response = chat.ask(user_input)
reply = response.content.to_s
```

### Controller (`app/controllers/chats_controller.rb`)

```ruby
@chat.add_message(role: "user", content: message)
assistant_reply = LlmService.chat(@chat)
@chat.add_message(role: "assistant", content: assistant_reply)
```

The controller is clean but delegates to the hallucinated `LlmService`.

## Tests

- 5 test files, 44 test methods total
- Tests pass, RuboCop is clean, Brakeman reports no warnings
- Dockerfile sets `SECRET_KEY_BASE`
- No secrets committed to the repo

**Caveat for scoring:** tests do not mock the live LLM call and will hit
OpenRouter when an API key is present. The audit scanner confirms
`has_any_mock: false`.

## Audit scanner summary

- `ruby_llm` gem present, `ruby_openai` absent
- Ruby version: 3.4.9
- `hallucinated_client`: 1 (`RubyLLM::Client.new`)
- `hallucinated_system_dsl`: 2 (`c.system ...`)
- `valid_content`: 3 (uses `response.content`)
- `valid_add_message`: 2 (controller calls `chat.add_message`)
- `rescue_count`: 2 around LLM calls
- No RubyLLM initializer file (`has_ruby_llm_initializer: false`)
