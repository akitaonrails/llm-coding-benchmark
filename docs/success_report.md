# LLM Coding Benchmark: Comprehensive Success Report

## What Was Tested

Each model was given an identical prompt to autonomously build a Ruby on Rails SPA chat application (a ChatGPT-like interface using RubyLLM). The task requires:

- Rails app with Hotwire/Stimulus/Turbo Streams, Tailwind CSS
- RubyLLM gem configured for OpenRouter + Claude Sonnet
- Minitest unit tests
- CI tools (Brakeman, RuboCop, SimpleCov, bundle-audit)
- Dockerfile and docker-compose
- README with setup instructions

Cloud models ran a two-phase flow (phase 1: build, phase 2: validate boot/Docker). Local models ran phase 1 only. All models used `opencode run --agent build --format json` as the harness.

**Baseline: Claude Opus 4.6** is treated as the gold standard throughout this report.

---

## Successful Models at a Glance

11 of 16 models completed the benchmark. Of the 11, all produced a recognizable Rails project with the core artifacts. The table below ranks them by overall practical quality.

| Rank | Model | Provider | Time | Tests | All Gems | Dockerfile | Compose | README | Phase 2 |
|---:|---|---|---:|---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Claude Sonnet 4.6 | OpenRouter | 16m | 30 | Yes | Yes | Yes | 126L | Yes |
| 2 | Claude Opus 4.6 | OpenRouter | 16m | 16 | Yes | Yes | Yes | 164L | Yes |
| 3 | Kimi K2.5 | OpenRouter | 29m | 37 | Yes | Yes | Yes | 181L | Yes |
| 4 | MiniMax M2.7 | OpenRouter | 14m | 12 | Yes | Yes | Yes | 121L | Yes |
| 5 | GLM 5 | OpenRouter | 17m | 7 | Yes | Yes | Yes | 99L | Yes |
| 6 | Qwen 3.6 Plus | OpenRouter | 17m | 7 | Yes | Yes | Yes | 107L | Yes |
| 7 | Qwen 3.5 35B | Local | 28m | 11 | Yes | Yes | Yes | 202L | No |
| 8 | Qwen 3 Coder Next | Local | 17m | 3 | Yes | Yes | Yes | 69L | No |
| 9 | DeepSeek V3.2 | OpenRouter | 60m | 11 | Yes | Yes | Yes | 265L | Yes |
| 10 | Qwen 3.5 122B | Local | 43m | 16 | No* | Yes | Yes | 167L | No |
| 11 | Step 3.5 Flash | OpenRouter | 38m | 8 | No** | Yes | Yes | 103L | Yes |
| 12 | Gemini 3.1 Pro | OpenRouter | 14m | 5 | Yes | Yes | Yes | ~100L | Yes |

*Qwen 3.5 122B built a custom OpenRouter HTTP client instead of using the ruby_llm gem.
**Step 3.5 Flash used `ruby-llm` (hyphenated) gem name variant.

---

## Evaluation Criteria

### 1. Project Completeness

Does the generated project have all the requested artifacts?

| Model | Gemfile | Routes | App | Views | JS | Tests | README | Dockerfile | Compose | Score |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---:|
| Claude Opus 4.6 | Y | Y | Y | Y | Y | Y | Y | Y | Y | 9/9 |
| Claude Sonnet 4.6 | Y | Y | Y | Y | Y | Y | Y | Y | Y | 9/9 |
| Kimi K2.5 | Y | Y | Y | Y | Y | Y | Y | Y | Y | 9/9 |
| MiniMax M2.7 | Y | Y | Y | Y | Y | Y | Y | Y | Y | 9/9 |
| GLM 5 | Y | Y | Y | Y | Y | Y | Y | Y | Y | 9/9 |
| Qwen 3.6 Plus | Y | Y | Y | Y | Y | Y | Y | Y | Y | 9/9 |
| Qwen 3.5 35B | Y | Y | Y | Y | Y | Y | Y | Y | Y | 9/9 |
| Qwen 3 Coder Next | Y | Y | Y | Y | Y | Y | Y | Y | Y | 9/9 |
| DeepSeek V3.2 | Y | Y | Y | Y | Y | Y | Y | Y | Y | 9/9 |
| Qwen 3.5 122B | Y | Y | Y | Y | Y | Y | Y | Y | Y | 9/9 |
| Step 3.5 Flash | Y | Y | Y | Y | Y | Y | Y | Y | Y | 9/9 |

All 11 successful models achieved 9/9 on structural completeness.

### 2. Test Coverage

Number of test files and test methods (assertions/test cases) written by each model.

| Model | Test Files | Test Methods | vs Baseline |
|---|---:|---:|---|
| Kimi K2.5 | 5 | 37 | +131% |
| **Claude Sonnet 4.6** | 5 | 30 | +88% |
| **Claude Opus 4.6 (baseline)** | 4 | 16 | -- |
| Qwen 3.5 122B | 3 | 16 | 0% |
| MiniMax M2.7 | 3 | 12 | -25% |
| DeepSeek V3.2 | 3 | 11 | -31% |
| Qwen 3.5 35B | 3 | 11 | -31% |
| Step 3.5 Flash | 2 | 8 | -50% |
| GLM 5 | 5 | 7 | -56% |
| Qwen 3.6 Plus | 4 | 7 | -56% |
| Qwen 3 Coder Next | 2 | 3 | -81% |

**Takeaway:** Kimi K2.5 wrote the most thorough tests (37 methods). Claude Sonnet 4.6 surpassed Opus. Most Chinese-origin models wrote fewer tests. Qwen 3 Coder Next wrote the bare minimum.

### 3. Code Quality (Gem Coverage)

The prompt explicitly required ruby_llm, brakeman, rubocop, simplecov, and bundle-audit.

| Model | ruby_llm | brakeman | rubocop | simplecov | bundle-audit | Score |
|---|:---:|:---:|:---:|:---:|:---:|---:|
| Claude Opus 4.6 | Y | Y | Y | Y | Y | 5/5 |
| Claude Sonnet 4.6 | Y | Y | Y | Y | Y | 5/5 |
| Kimi K2.5 | Y | Y | Y | Y | Y | 5/5 |
| MiniMax M2.7 | Y | Y | Y | Y | Y | 5/5 |
| GLM 5 | Y | Y | Y | Y | Y | 5/5 |
| Qwen 3.6 Plus | Y | Y | Y | Y | Y | 5/5 |
| DeepSeek V3.2 | Y | Y | Y | Y | Y | 5/5 |
| Qwen 3.5 35B | Y | Y | Y | Y | Y | 5/5 |
| Qwen 3 Coder Next | Y | Y | Y | Y | Y | 5/5 |
| Step 3.5 Flash | No* | Y | Y | Y | Y | 4/5 |
| Qwen 3.5 122B | No** | Y | Y | Y | Y | 4/5 |

*Used `ruby-llm` (hyphenated) instead of `ruby_llm`. **Built a custom HTTP client instead.

### 4. Pricing (OpenRouter Per-Token)

| Model | Input $/M | Output $/M | Est. Cost/Run | vs Baseline |
|---|---:|---:|---:|---|
| Qwen 3.6 Plus | $0.00 | $0.00 | $0.00 | Free |
| Step 3.5 Flash | $0.10 | $0.30 | ~$0.02 | 98% cheaper |
| DeepSeek V3.2 | $0.20 | $0.77 | ~$0.04 | 96% cheaper |
| MiniMax M2.7 | $0.30 | $1.20 | ~$0.05 | 95% cheaper |
| Kimi K2.5 | $0.38 | $1.72 | ~$0.07 | 93% cheaper |
| GLM 5 | $0.72 | $2.30 | ~$0.11 | 89% cheaper |
| Claude Sonnet 4.6 | $3.00 | $15.00 | ~$0.63 | 40% cheaper |
| **Claude Opus 4.6** | $5.00 | $25.00 | ~$1.05 | Baseline |
| Gemini 3.1 Pro | $2.00 | $12.00 | ~$0.50 | 52% cheaper |
| GPT 5.4 Pro | $30.00 | $180.00 | ~$7.20 | 586% more |
| Local models | $0.00 | $0.00 | Electricity only | Hardware cost |

**Takeaway:** Chinese-origin cloud models cost 10-100x less than Anthropic models. Qwen 3.6 Plus is literally free. For the same quality output, Claude Sonnet 4.6 is the best value in the Anthropic family (40% cheaper than Opus, slightly better test coverage).

### 5. Time to Complete

| Model | Phase 1 | Phase 2 | Total | vs Baseline |
|---|---:|---:|---:|---|
| Gemini 3.1 Pro | 10m | 3m | 14m | 13% faster |
| MiniMax M2.7 | 12m | 2m | 14m | 13% faster |
| Claude Opus 4.6 | 10m | 7m | 16m | Baseline |
| Claude Sonnet 4.6 | 12m | 4m | 16m | Same |
| GLM 5 | 15m | 2m | 17m | 6% slower |
| Qwen 3.6 Plus | 9m | 8m | 17m | 6% slower |
| Qwen 3 Coder Next | 17m | -- | 17m | Same (phase 1 only) |
| Qwen 3.5 35B | 28m | -- | 28m | 75% slower |
| Kimi K2.5 | 22m | 7m | 29m | 81% slower |
| Step 3.5 Flash | 27m | 11m | 38m | 138% slower |
| Qwen 3.5 122B | 43m | -- | 43m | 169% slower |
| DeepSeek V3.2 | 24m | 36m | 60m | 275% slower |

**Takeaway:** MiniMax, both Claudes, GLM 5, and Qwen 3.6 Plus all finish in under 20 minutes. DeepSeek V3.2 is the slowest despite being a cloud model — its lack of prompt caching means it re-sends full context each turn.

### 6. Token Efficiency

Models with prompt caching (Anthropic, Step, MiniMax) use dramatically fewer input tokens because cached context doesn't count as new input.

| Model | Total Tokens | Cache Read | Effective New Tokens | Caching |
|---|---:|---:|---:|:---:|
| Qwen 3 Coder Next | 39,054 | 38,636 | 418 | Yes |
| Qwen 3.5 122B | 57,472 | 56,251 | 1,221 | Yes |
| GLM 5 | 59,378 | 58,240 | 1,138 | Yes |
| Kimi K2.5 | 63,638 | 0 | 63,638 | No |
| Qwen 3.5 35B | 76,919 | 76,032 | 887 | Yes |
| MiniMax M2.7 | 79,743 | 79,291 | 452 | Yes |
| Qwen 3.6 Plus | 88,940 | 0 | 88,940 | No |
| DeepSeek V3.2 | 115,278 | 0 | 115,278 | No |
| Claude Sonnet 4.6 | 127,067 | 126,429 | 638 | Yes |
| Claude Opus 4.6 | 136,806 | 135,976 | 830 | Yes |
| Step 3.5 Flash | 156,267 | 155,008 | 1,259 | Yes |

---

## Failed Models

### Cloud Failures

| Model | Issue | Root Cause |
|---|---|---|
| **GPT 5.4 Pro** | Stalled after tool-calls, never reached `stop` | opencode's tool calling integration does not support OpenAI's native function calling format. The model emits `finish_reason: tool-calls` but opencode can't process the response chain. Produced 1118 files but no docker-compose. |

**Note on GPT 5.4 Pro:** This failure is an **opencode tooling limitation**, not a model capability issue. GPT 5.4 Pro's function calling works correctly through OpenAI's native API and tooling (ChatGPT, Cursor, etc.). In the author's experience with other coding tools, GPT 5.4 Pro performs on par with Claude Opus 4.6 for autonomous coding tasks. It failed this benchmark solely because opencode's OpenRouter integration cannot handle OpenAI's tool calling response format. A fair comparison would require testing GPT 5.4 Pro through its native tooling (e.g., Codex CLI, ChatGPT Pro) rather than through an intermediary like OpenRouter. At $7.20/run through OpenRouter it is also prohibitively expensive — the ChatGPT Pro subscription ($200/month) would be far more cost-effective for heavy usage.

### Local Failures (llama-swap / llama.cpp)

| Model | Issue | Root Cause | Fixable? |
|---|---|---|---|
| **Gemma 4 31B** | Infinite tool call repetition after ~11 steps | Known llama.cpp bug [#21375](https://github.com/ggml-org/llama.cpp/issues/21375). Model loops empty `<\|channel>thought` tokens. PR #21418 (b8665+) partially helps but doesn't fully resolve. | Waiting on upstream |
| **Llama 4 Scout** | Tool calls emitted as plain text | llama.cpp has no parser for Llama 4's pythonic format. vLLM has one (`llama4_pythonic`) but llama.cpp doesn't. | Waiting on upstream |
| **GPT OSS 20B** | Created Rails app in wrong directory | Model put everything under `project/app/` instead of `project/`. 20B model can't reliably follow workspace instructions. | No (model capability) |
| **Qwen 3 32B** | Too slow (7.3 tok/s) | Hardware bottleneck. Model works but GPU can't serve it fast enough. | Faster hardware |
| **GLM 4.7 Flash (local)** | Ended mid-tool-call | Produced 2029 files with all artifacts but session didn't terminate cleanly. The *cloud* GLM 5 version works perfectly. | Partial success |

---

## Why Ollama Fails for Benchmarks

Ollama was the original local model backend. It failed for 6 of 8 models:

1. **Silent model unloading.** Ollama unloads models mid-session during long autonomous runs, causing opencode to hang waiting for a response from a model that's no longer loaded.
2. **Context drift.** Ollama ignores the requested `num_ctx` and reverts to default context sizes mid-run, causing OOM or degraded output.
3. **Flaky lifecycle.** `keep_alive: 0` unload requests don't always work. Models stay resident and block the next model from loading.
4. **Format mismatches.** Ollama-native model entries (bf16 variants) often fail to load, while the same model as a HuggingFace GGUF Q8 works fine under llama-swap.

## Why "Just Use llama.cpp" Isn't Magic Either

llama-swap (which wraps llama-server from llama.cpp) solves Ollama's lifecycle problems but introduces its own:

1. **Tool call parser gaps.** llama.cpp needs a dedicated parser for each model's tool call format. Llama 4 (pythonic), and partially Gemma 4 (repetition loops), simply don't work.
2. **Reasoning token handling.** Models like GLM and Qwen 3.5 emit `reasoning_content` or `<think>` tags that require `--reasoning-format none` on the server. Without it, clients may hang or misparse.
3. **Build version sensitivity.** Gemma 4 requires build b8665+ for its parser. Running an older build gives cryptic "Failed to parse input at pos 13" errors.
4. **Repetition loops.** Even with the correct parser, Gemma 4 enters infinite loops after ~11 tool calls in long agentic sessions. This is a known upstream issue.

**Bottom line:** llama.cpp is better than Ollama for unattended runs, but "plug and play" it is not. Each model needs specific flags (`--jinja`, `--reasoning-format`, correct build version), and some models simply can't do agentic tool calling yet.

---

## The Practical Question: What Are the Alternatives to Anthropic?

If you want to avoid lock-in to Anthropic but need a model that works reliably with opencode for autonomous coding, here's the honest assessment:

### Tier 1: Drop-in Replacements (plug and play via OpenRouter)

These models completed both phases, produced all artifacts, and required zero configuration beyond adding them to the model list:

| Model | Quality | Speed | Cost | Trade-off vs Opus |
|---|---|---|---|---|
| **Claude Sonnet 4.6** | Better tests (30 vs 16) | Same (16m) | 40% cheaper | Still Anthropic, but cheaper and slightly better |
| **Kimi K2.5** | Best tests (37) | Slower (29m) | 93% cheaper | Slower but much cheaper with best test coverage |
| **MiniMax M2.7** | Good (12 tests) | Fastest (14m) | 95% cheaper | Fewer tests but fastest and very cheap |
| **GLM 5** | Good (7 tests) | Same (17m) | 89% cheaper | Fewer tests but fast and cheap |

### Tier 2: Viable with Caveats

| Model | Quality | Speed | Cost | Caveat |
|---|---|---|---|---|
| **Qwen 3.6 Plus** | Good (7 tests) | Same (17m) | Free | Free tier has rate limits. Fewer tests. |
| **DeepSeek V3.2** | Good (11 tests) | Slow (60m) | 96% cheaper | Very slow due to no prompt caching. |
| **Step 3.5 Flash** | OK (8 tests) | Slow (38m) | 98% cheaper | Missed ruby_llm gem name. Slow. |

### Tier 3: Local Models (free but require setup)

| Model | Quality | Speed | Cost | Caveat |
|---|---|---|---|---|
| **Qwen 3 Coder Next** | OK (3 tests) | Same (17m) | Free | Minimal tests. Needs llama-swap setup. |
| **Qwen 3.5 35B** | Good (11 tests) | Slower (28m) | Free | Phase 1 only. Needs llama-swap + GPU. |
| **Qwen 3.5 122B** | OK (16 tests) | Slow (43m) | Free | Skipped ruby_llm gem entirely. Needs 48GB+ VRAM. |

### Not Viable

| Model | Why |
|---|---|
| GPT 5.4 Pro | opencode tooling incompatibility (not a model issue — see note below) |
| Gemma 4 31B (local) | Infinite repetition loop after ~11 steps |
| Llama 4 Scout (local) | No tool call parser in llama.cpp |
| GPT OSS 20B (local) | Too small to follow workspace instructions |
| Qwen 3 32B (local) | Too slow on current hardware |

**Note on GPT 5.4 Pro:** In the author's experience, GPT 5.4 Pro performs on par with Claude Opus 4.6 for coding tasks when used through native OpenAI tooling (Codex CLI, ChatGPT Pro). Its failure here is purely an opencode/OpenRouter integration issue.

### Recommendation

**If cost matters most and code must actually work:** GLM 5 at $0.11/run — the only non-Anthropic model that correctly uses the RubyLLM API and properly mocks tests. However, see the deep code review below — most "cheap" models hallucinate APIs despite producing complete-looking projects.

**If you want the best output regardless of cost:** Claude Sonnet 4.6. It's cheaper than Opus, faster, and actually wrote more tests. There's no reason to use Opus over Sonnet for this benchmark.

**If you want to avoid all vendor lock-in:** Qwen 3 Coder Next or Qwen 3.5 35B running locally via llama-swap. Free, but requires a GPU server and some configuration. Test coverage will be lower than cloud models.

**If you want free cloud:** Qwen 3.6 Plus on OpenRouter's free tier. It works, but rate limits may slow repeated runs.

---

## Deep Code Review: Sonnet vs Kimi vs MiniMax

The benchmark tables above measure structural completeness (are the files there?) and test counts. But do the projects actually *work*? We performed a detailed code review of the top 3 price-competitive models to find out.

### Head-to-Head Scorecard

| Criterion | Sonnet 4.6 | Kimi K2.5 | MiniMax M2.7 |
|---|:---:|:---:|:---:|
| Rails structure | Correct | Disables test railtie by mistake | Correct (minor noise) |
| RubyLLM integration | Works (duplicate model const) | Broken (ActionCable disabled) | **Crashes** (wrong API call) |
| Controller quality | Clean, working Turbo Streams | Broken streaming, no validation | Clean, but no message persistence |
| View quality | 7 well-decomposed partials | More partials but dead code | Good partials, duplicate HTML document |
| Stimulus/JS | 2 focused controllers (minor leak) | 1 broken controller + scaffold leftover | Minimal, scroll never called |
| Test quality | 30 tests, proper LLM mocking | 37 tests, no LLM mocking | 12 tests, mocks LLM |
| Docker | Multi-stage, minimal compose | Dual Dockerfiles, dev/prod profiles | No multi-stage, missing SECRET_KEY_BASE |
| README | Concise, accurate | Thorough but config inaccuracy | Clear, overclaims streaming |
| Security | Clean | Clean | master.key committed |
| Code smells | Minor (duplicate const) | Major (broken streaming, thread-unsafe) | Major (stateless chat, wrong API) |
| **Would it actually run?** | **Yes** | **No** (streaming depends on disabled ActionCable) | **No** (RubyLLM API call is wrong) |

### Claude Sonnet 4.6 — Actually Works

Sonnet produced the only project among these three that would function correctly at runtime. Key decisions:

- **Synchronous Turbo Stream responses.** Instead of attempting real-time streaming (which requires ActionCable and background jobs), Sonnet sends the LLM request synchronously and responds with a 3-part Turbo Stream (messages, sidebar, form). Simple, but it works.
- **Session-based persistence.** Chat history lives in the Rails session cookie. Limited to ~4KB but appropriate for a demo app without a database.
- **Proper LLM mocking in tests.** Uses the `mocha` gem to stub `LlmChatService` in controller tests and `RubyLLM::Chat` in service tests. Tests actually verify behavior, not just existence.
- **Minor issues:** Duplicate model constant between initializer and service. Event listener leak in the JS auto-resize handler. Neither is a runtime blocker.

### Kimi K2.5 — Ambitious but Broken

Kimi attempted the most sophisticated architecture (ActionCable streaming, configurable models, dual Docker environments) but the implementation has fundamental flaws:

- **Streaming depends on ActionCable, which is disabled.** The `MessagesController#stream_assistant_response` method calls `Turbo::StreamsChannel.broadcast_*`, but `ActionCable` is commented out in `config/application.rb`. The `return unless defined?(ActionCable)` guard means the method silently does nothing. The assistant never actually responds.
- **Stimulus controller has a scope bug.** The `autogrow` controller is attached to the textarea element, but `submitTarget` references a button *outside* the controller's element scope. Stimulus can only find targets within the controller's DOM subtree, so `this.submitTarget` throws an error.
- **37 test methods but no LLM mocking.** The model and chat tests are thorough (11 and 10 tests respectively), but `MessagesControllerTest` hits the real LLM API (no mock/stub), and `LlmServiceTest` only checks `assert_respond_to` — it never tests the actual chat method.
- **Thread-unsafe in-memory storage.** `Chat.storage` uses a class-level instance variable (`@storage ||= {}`). With Puma's threaded workers, concurrent requests can corrupt the hash.
- **Where it excels:** Docker setup (dev + prod Dockerfiles, comprehensive docker-compose with profiles), defensive initializer (raises on missing API key in non-test environments), ENV-configurable model name.

### MiniMax M2.7 — Looks Right, Crashes at Runtime

MiniMax produced a clean-looking project that passes its own tests but would not function as a chat application:

- **Wrong RubyLLM API call.** The service calls `RubyLLM.chat(model: '...', messages: [...])` — this method signature does not exist in the RubyLLM gem. The correct API is `RubyLLM.chat(model: '...')` which returns a `Chat` object, then `.ask("message")`. This would crash with `NoMethodError` at runtime.
- **No message persistence.** `ChatService` creates a new `@messages = []` on every request. The controller's `clear` action manipulates `session[:chat_messages]` but nothing else reads or writes that key. Conversation history is lost on every request.
- **Duplicate HTML document.** `index.html.erb` includes a full `<!DOCTYPE html>` with `<head>` and `<body>`, which renders inside the layout's existing `<body>`. This produces invalid nested HTML documents.
- **master.key committed.** The Rails master key is in the repo despite `.gitignore` having `*.key`.
- **Tests mock the broken API.** The test suite stubs `RubyLLM.chat` to match the service's (wrong) call signature, so tests pass despite the API being incorrect. This is a classic case of tests that verify internal consistency but not correctness.
- **Where it excels:** Fastest completion (14 min), clean Tailwind dark theme, well-structured partials for messages and errors.

### Gemini 3.1 Pro — Close but Still Hallucinated

Gemini 3.1 Pro produced the best-structured app among the non-Anthropic models: proper Rails 8 conventions, excellent Turbo Stream integration, session state via `Rails.cache` with expiry, multi-stage Docker build, and 5 meaningful tests. The non-LLM parts of this codebase are genuinely good.

But the LLM integration is wrong:

```ruby
# What Gemini wrote:
chat = RubyLLM::Chat.new(model: '...', provider: :openrouter, assume_model_exists: true)
chat.add_message(role: msg[:role], content: msg[:content])
response = chat.ask(current_message)

# What the real API is:
chat = RubyLLM.chat(model: '...')
response = chat.ask("message")
```

`RubyLLM::Chat.new` is not the public API (should be `RubyLLM.chat`), and `add_message()` does not exist. This is a *milder* hallucination than other models — the overall shape (Chat object → ask → content) is correct, and a developer could fix it in 5 minutes. But it would still crash at runtime as-is.

**Completion time: 13.5 minutes** (fastest after MiniMax). **Pricing: ~$0.50/run** (competitive with Sonnet at $0.63).

### Verdict on All Deep-Reviewed Models

**Only Sonnet produces code that actually works** among the models reviewed in detail. Kimi and MiniMax both generate more test methods and more files, but the core functionality — the actual chat with the LLM — is broken in both. Gemini 3.1 Pro comes closest to correct but still fails on the LLM integration. The pattern is consistent: models hallucinate OpenAI-style APIs when encountering less common gems.

---

## Does ANY Other Model's Code Actually Work?

After finding that Kimi and MiniMax produced non-functional code despite passing all structural checks, we audited every remaining model's RubyLLM integration — the critical path that determines whether the chat actually works.

The correct RubyLLM API is:
```ruby
chat = RubyLLM.chat(model: "anthropic/claude-sonnet-4")
response = chat.ask("Hello")
response.content  # => "Hi there!"
```

### Runtime Viability of All 11 Completed Models

| Model | RubyLLM API Correct? | Would Run? | Tests Mock LLM? | Issue |
|---|:---:|:---:|:---:|---|
| **Claude Opus 4.6** | Yes | **Yes** | Yes (mocha) | Clean implementation |
| **Claude Sonnet 4.6** | Yes | **Yes** | Yes (mocha) | Clean, minor duplicate const |
| **GLM 5** | Yes | **Yes** | Yes (mocha) | Standard API, works |
| **Step 3.5 Flash** | N/A | **Yes*** | No | Bypasses RubyLLM, uses raw `Net::HTTP` to OpenRouter API directly |
| **Qwen 3.6 Plus** | Partial | **First msg only** | No | `chat.add_message()` doesn't exist — history replay crashes |
| **Qwen 3.5 35B** | Partial | **Maybe** | No | `RubyLLM.chat` without model param — works only if default configured |
| **Kimi K2.5** | No | **No** | No | `add_message()` and `complete()` don't exist in RubyLLM |
| **MiniMax M2.7** | No | **No** | No | `RubyLLM.chat(model:, messages:)` signature doesn't exist |
| **DeepSeek V3.2** | No | **No** | No | `RubyLLM::Client` class doesn't exist — immediate `NameError` |
| **Qwen 3 Coder Next** | No | **No** | No | `RubyLLM::Client` class doesn't exist — immediate `NameError` |
| **Qwen 3.5 122B** | No | **No** | No | `Openrouter::Client` gem doesn't exist — immediate `NameError` |
| **Gemini 3.1 Pro** | Partial | **No** | Yes (wrong API) | `RubyLLM::Chat.new` instead of `RubyLLM.chat`, invented `add_message()` |

*Step 3.5 Flash works by calling the OpenRouter REST API directly with `Net::HTTP`, completely bypassing the RubyLLM gem the prompt asked for.

### What Went Wrong

**7 out of 11 models invented non-existent APIs.** The most common failure mode was hallucinating an OpenAI-style client interface:

- DeepSeek V3.2 and Qwen 3 Coder Next both invented `RubyLLM::Client.new` — a class that does not exist.
- Qwen 3.5 122B invented an `Openrouter::Client` gem that does not exist at all.
- Kimi K2.5 got the initial `RubyLLM.chat()` call right but invented `add_message()` and `complete()` methods.
- MiniMax M2.7 invented a `RubyLLM.chat(messages: [...])` batch API that doesn't exist.
- Qwen 3.6 Plus invented `chat.add_message()` for history replay.

The models that got it right — both Claudes and GLM 5 — used the simple two-step pattern (`chat = RubyLLM.chat(model:)` then `chat.ask(message)`). The models that failed tried to make RubyLLM look like the OpenAI Python SDK, which it isn't.

**Tests don't catch this.** Only the Anthropic models (Opus and Sonnet) and GLM 5 properly mocked the LLM calls in their tests. Every other model either hit the real API (which would fail without a key) or mocked the invented API (which passes tests but doesn't prove correctness). This is why test count alone is a misleading metric.

### Revised Model Tiers

Based on actual runtime viability, not just structural completeness:

**Tier 1: Actually Works**
| Model | Cost/Run | Time | Why |
|---|---:|---:|---|
| Claude Sonnet 4.6 | ~$0.63 | 16m | Correct API, proper mocking, clean architecture |
| Claude Opus 4.6 | ~$1.05 | 16m | Correct API, proper mocking, streaming support |
| GLM 5 | ~$0.11 | 17m | Correct API, proper mocking, 89% cheaper than Opus |

**Tier 2: Works with Caveats**
| Model | Cost/Run | Time | Caveat |
|---|---:|---:|---|
| Step 3.5 Flash | ~$0.02 | 38m | Bypasses RubyLLM entirely (raw HTTP). Functional but doesn't use the requested gem. |
| Qwen 3.5 35B | Free | 28m | May work if RubyLLM default model is configured. No test mocking. |

**Tier 3: Broken Core Functionality**
| Model | Failure Mode |
|---|---|
| Kimi K2.5 | Invented `add_message()`/`complete()` methods |
| MiniMax M2.7 | Invented `RubyLLM.chat(messages:)` batch signature |
| Qwen 3.6 Plus | Invented `chat.add_message()` for history |
| DeepSeek V3.2 | Invented `RubyLLM::Client` class |
| Qwen 3 Coder Next | Invented `RubyLLM::Client` class |
| Qwen 3.5 122B | Invented `Openrouter::Client` gem |
| Gemini 3.1 Pro | Invented `Chat.new` constructor + `add_message()` method |

### The Bottom Line

**If you don't want to be locked to Anthropic, GLM 5 is the only viable plug-and-play alternative** — it uses the correct RubyLLM API, mocks properly in tests, completes in 17 minutes, and costs ~$0.11 per run (89% cheaper than Opus).

Step 3.5 Flash works at runtime but cheats by bypassing RubyLLM. Everything else either crashes on startup or fails when you try to send a message.

This reveals a critical limitation of benchmark metrics: **file count, test count, and artifact checklist do not measure whether the code actually works.** A model can score 9/9 on completeness, write 37 test methods, and still produce a non-functional application. The only reliable signal is whether the model correctly uses real APIs — and most models hallucinate API interfaces they've seen in training data rather than using the actual gem's API.
