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
| GPT 5.4 Pro | $30.00 | $180.00 | ~$7.20 | 586% more |
| Local models | $0.00 | $0.00 | Electricity only | Hardware cost |

**Takeaway:** Chinese-origin cloud models cost 10-100x less than Anthropic models. Qwen 3.6 Plus is literally free. For the same quality output, Claude Sonnet 4.6 is the best value in the Anthropic family (40% cheaper than Opus, slightly better test coverage).

### 5. Time to Complete

| Model | Phase 1 | Phase 2 | Total | vs Baseline |
|---|---:|---:|---:|---|
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
| **GPT 5.4 Pro** | Stalled after tool-calls, never reached `stop` | OpenAI's native function calling format is incompatible with opencode's tool schema. The model emits `finish_reason: tool-calls` but opencode can't process the response chain. Produced 1118 files but no docker-compose. Most expensive model at $7.20/run. |

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
| GPT 5.4 Pro | $7.20/run, stalls on tool calls, no docker-compose |
| Gemma 4 31B (local) | Infinite repetition loop after ~11 steps |
| Llama 4 Scout (local) | No tool call parser in llama.cpp |
| GPT OSS 20B (local) | Too small to follow workspace instructions |
| Qwen 3 32B (local) | Too slow on current hardware |

### Recommendation

**If cost matters most:** Kimi K2.5 or MiniMax M2.7 via OpenRouter. Both are plug-and-play, 90%+ cheaper than Opus, and produce complete projects. Kimi has the best test coverage of any model tested. However, see the deep code review below — quantity of artifacts does not equal quality.

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

### Verdict

**Only Sonnet produces code that actually works.** Kimi and MiniMax both generate more test methods and more files, but the core functionality — the actual chat with the LLM — is broken in both. Kimi's streaming architecture is dead code because ActionCable is disabled. MiniMax calls a non-existent RubyLLM API.

This reveals a critical limitation of benchmark metrics: **file count, test count, and artifact checklist do not measure whether the code actually works.** A model can score 9/9 on completeness, write 37 test methods, and still produce a non-functional application.

For practical use, Claude Sonnet 4.6 is the clear winner — not because it's the most ambitious, but because it makes correct architectural decisions (synchronous over broken streaming, session cookies over thread-unsafe in-memory storage) and produces code that runs without modification.
