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

> **NVIDIA workstation profile**: this report covers the AMD Strix Halo server (full Q8 weights, 200K+ context) and OpenRouter / Z.ai cloud models. For the parallel **NVIDIA RTX 5090 workstation** results (Q3_K_M / Q4_K_M quants, 32 GB VRAM, 64-128K context), see [`success_report.nvidia.md`](success_report.nvidia.md). The headline NVIDIA finding — that Claude reasoning distillation does **not** transfer library API knowledge — is summarized below.

---

## Successful Models at a Glance

14 of 18 models completed the benchmark. All produced a recognizable Rails project with the core artifacts. The table below ranks them by overall practical quality.

| Rank | Model | Provider | Time | Tests | All Gems | Dockerfile | Compose | README | Phase 2 |
|---:|---|---|---:|---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Claude Sonnet 4.6 | OpenRouter | 16m | 30 | Yes | Yes | Yes | 126L | Yes |
| 2 | Claude Opus 4.6 | OpenRouter | 16m | 16 | Yes | Yes | Yes | 164L | Yes |
| 3 | Kimi K2.5 | OpenRouter | 29m | 37 | Yes | Yes | Yes | 181L | Yes |
| 4 | MiniMax M2.7 | OpenRouter | 14m | 12 | Yes | Yes | Yes | 121L | Yes |
| 5 | GLM 5 | OpenRouter | 17m | 7 | Yes | Yes | Yes | 99L | Yes |
| 6 | GLM 5.1 | Z.ai | 22m | 24 | Yes | Yes | Yes | ~100L | Yes |
| 7 | Qwen 3.6 Plus | OpenRouter | 17m | 7 | Yes | Yes | Yes | 107L | Yes |
| 8 | Qwen 3.5 35B | Local | 28m | 11 | Yes | Yes | Yes | 202L | No |
| 9 | Qwen 3 Coder Next | Local | 17m | 3 | Yes | Yes | Yes | 69L | No |
| 10 | DeepSeek V3.2 | OpenRouter | 60m | 11 | Yes | Yes | Yes | 265L | Yes |
| 11 | Qwen 3.5 122B | Local | 43m | 16 | No* | Yes | Yes | 167L | No |
| 12 | Step 3.5 Flash | OpenRouter | 38m | 8 | No** | Yes | Yes | 103L | Yes |
| 13 | Gemini 3.1 Pro | OpenRouter | 14m | 5 | Yes | Yes | Yes | ~100L | Yes |
| 14 | Grok 4.20 | OpenRouter | 8m | 3 | No*** | Yes | Yes | ~80L | Yes |

*Qwen 3.5 122B built a custom OpenRouter HTTP client instead of using the ruby_llm gem.
***Grok 4.20 is missing ruby_llm, bundle-audit, turbo-rails, stimulus-rails, and importmap-rails entirely.
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
| GLM 5.1 | 5 | 24 | +50% |
| **Claude Opus 4.6 (baseline)** | 4 | 16 | -- |
| Qwen 3.5 122B | 3 | 16 | 0% |
| MiniMax M2.7 | 3 | 12 | -25% |
| DeepSeek V3.2 | 3 | 11 | -31% |
| Qwen 3.5 35B | 3 | 11 | -31% |
| Step 3.5 Flash | 2 | 8 | -50% |
| GLM 5 | 5 | 7 | -56% |
| Qwen 3.6 Plus | 4 | 7 | -56% |
| Gemini 3.1 Pro | 2 | 5 | -69% |
| Qwen 3 Coder Next | 2 | 3 | -81% |
| Grok 4.20 | 2 | 3 | -81% |

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
| GLM 5.1 | Y | Y | Y | Y | Y | 5/5 |
| Gemini 3.1 Pro | Y | Y | Y | Y | Y | 5/5 |
| Step 3.5 Flash | No* | Y | Y | Y | Y | 4/5 |
| Qwen 3.5 122B | No** | Y | Y | Y | Y | 4/5 |
| Grok 4.20 | **No** | Y | Y | Y | **No** | 3/5 |

*Used `ruby-llm` (hyphenated) instead of `ruby_llm`. **Built a custom HTTP client instead.

### 4. Pricing (OpenRouter Per-Token)

| Model | Input $/M | Output $/M | Est. Cost/Run | vs Baseline |
|---|---:|---:|---:|---|
| GLM 5.1 (Z.ai) | Subscription | Subscription | Lite plan ~$3/mo | Flat-rate, includes coding |
| Qwen 3.6 Plus | $0.00 | $0.00 | $0.00 | Free |
| Step 3.5 Flash | $0.10 | $0.30 | ~$0.02 | 98% cheaper |
| Grok 4.20 | $2.00 | $6.00 | ~$0.20 | 81% cheaper |
| DeepSeek V3.2 | $0.20 | $0.77 | ~$0.04 | 96% cheaper |
| MiniMax M2.7 | $0.30 | $1.20 | ~$0.05 | 95% cheaper |
| Kimi K2.5 | $0.38 | $1.72 | ~$0.07 | 93% cheaper |
| GLM 5 | $0.72 | $2.30 | ~$0.11 | 89% cheaper |
| Gemini 3.1 Pro | $2.00 | $12.00 | ~$0.50 | 52% cheaper |
| Claude Sonnet 4.6 | $3.00 | $15.00 | ~$0.63 | 40% cheaper |
| **Claude Opus 4.6** | $5.00 | $25.00 | ~$1.05 | Baseline |
| GPT 5.4 Pro | $30.00 | $180.00 | ~$7.20 | 586% more |
| Local models | $0.00 | $0.00 | Electricity only | Hardware cost |

**Takeaway:** Chinese-origin cloud models cost 10-100x less than Anthropic models. Qwen 3.6 Plus is literally free. For the same quality output, Claude Sonnet 4.6 is the best value in the Anthropic family (40% cheaper than Opus, slightly better test coverage).

### 5. Time to Complete

| Model | Phase 1 | Phase 2 | Total | vs Baseline |
|---|---:|---:|---:|---|
| Grok 4.20 | 6m | 2m | 8m | **50% faster** |
| Gemini 3.1 Pro | 10m | 3m | 14m | 13% faster |
| MiniMax M2.7 | 12m | 2m | 14m | 13% faster |
| Claude Opus 4.6 | 10m | 7m | 16m | Baseline |
| Claude Sonnet 4.6 | 12m | 4m | 16m | Same |
| GLM 5 | 15m | 2m | 17m | 6% slower |
| Qwen 3.6 Plus | 9m | 8m | 17m | 6% slower |
| Qwen 3 Coder Next | 17m | -- | 17m | Same (phase 1 only) |
| Qwen 3.5 35B | 28m | -- | 28m | 75% slower |
| Kimi K2.5 | 22m | 7m | 29m | 81% slower |
| GLM 5.1 | 13m | 8m | 22m | 38% slower |
| Step 3.5 Flash | 27m | 11m | 38m | 138% slower |
| Qwen 3.5 122B | 43m | -- | 43m | 169% slower |
| DeepSeek V3.2 | 24m | 36m | 60m | 275% slower |

**Takeaway:** MiniMax, both Claudes, GLM 5, and Qwen 3.6 Plus all finish in under 20 minutes. DeepSeek V3.2 is the slowest despite being a cloud model — its lack of prompt caching means it re-sends full context each turn.

### 6. Token Efficiency

Models with prompt caching (Anthropic, Step, MiniMax) use dramatically fewer input tokens because cached context doesn't count as new input.

| Model | Total Tokens | Cache Read | Effective New Tokens | Caching |
|---|---:|---:|---:|:---:|
| Qwen 3 Coder Next | 39,054 | 38,636 | 418 | Yes |
| Grok 4.20 | 63,457 | 62,400 | 1,057 | Yes |
| GLM 5.1 | 81,666 | 81,216 | 450 | Yes |
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

### Gemma 4 31B via Ollama Cloud — infrastructure ceiling at ~20K tokens

After repeated failures of local Gemma 4 (infinite tool-call repetition loop on llama.cpp; see "Local Failures" below), we wired up the **Ollama Cloud** version (`gemma4:31b-cloud`) which runs the model on Ollama's hosted infrastructure rather than our own llama.cpp build. The motivating question: is Gemma 4 actually capable for agentic tool calling when not crippled by the local parser bugs?

**The model itself works correctly.** Curl tests against `https://ollama.com/v1/chat/completions` confirm:
- Plain text completion: clean response
- Single tool call (non-streaming): proper `tool_calls` array, `finish_reason: tool_calls`
- Single tool call (streaming): proper SSE deltas, no parser errors, ~67 tok/s
- 8K-token prompt: 10s round-trip, no issues

**But the benchmark fails consistently** at the same point. Two runs both failed at ~20-24K total tokens of conversation history with HTTP `504 Gateway Timeout` from Ollama Cloud:

| Run | Steps before failure | total_tokens at failure |
|---|---:|---:|
| First attempt | 6 | 24,011 |
| Second attempt (with `maxRetries: 5`) | ~25 | 21,789 |

The failures are **structural, not transient.** Adding `maxRetries: 5` to the Vercel AI SDK's openai-compatible provider didn't help — either all 5 retries failed identically, or the SDK isn't honoring the option for this error class. The consistent failure point (~22K tokens across two runs) strongly suggests Ollama Cloud has a per-request compute time limit (likely Cloudflare's 100s edge timeout) and processing 20K+ tokens of conversation history on a 31B model exceeds that.

**What we tried:**

| Fix | Result |
|---|---|
| `maxRetries: 5` in provider options | No change. Same failure at same context size. |
| Custom `User-Agent` header | No change. Cloudflare doesn't seem to discriminate on UA. |
| Compare `/v1/chat/completions` vs `/api/chat` endpoints | Both work fine on small prompts (1-2s). `/api/chat` slightly faster. opencode is locked into `/v1/chat/completions` via `@ai-sdk/openai-compatible`, so we can't switch even if `/api/chat` had different timeout behavior. |
| `limit.context: 16384` to force opencode history trimming | Pending — sets opencode to summarize older messages before any single request exceeds 16K tokens, well below the 20K failure ceiling. Trade-off: model loses long-term memory of earlier tool results. Untested as of this writing. |

**Verdict so far:** Gemma 4 via Ollama Cloud is **not viable** for long agentic coding sessions in its current configuration. The model is genuinely capable but the cloud serving infrastructure has a hard ceiling around 20K tokens per request that opencode's natural conversation growth blows past in 5-25 steps. Even if `limit.context: 16384` works to keep requests below the wall, the benchmark will run with degraded long-term memory which biases the result downward.

**Fair-comparison path:** test Gemma 4 via Google AI Studio's native Gemini API (or through OpenRouter's Google provider when one exists), which doesn't have a Cloudflare proxy in front of it. Drop Ollama Cloud as a Gemma 4 host for benchmarking purposes — it's fine for short interactive use but hits a wall on multi-turn agentic workloads.

**Marked `skip_by_default: true`** in `config/models.json` until either (a) Ollama Cloud raises the per-request timeout, or (b) we find a path to the model via a different cloud provider without the proxy ceiling.

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

### GLM 5.1 — Closest to Working After Sonnet/GLM 5

GLM 5.1 (via Z.ai's coding plan endpoint) produced one of the strongest non-Anthropic codebases we reviewed. It got the core RubyLLM API right:

```ruby
# What GLM 5.1 wrote in chat_session.rb:
chat = RubyLLM.chat(model: model_id)
response = chat.ask(content)
response.content
```

That part is correct. The streaming variant in `chat_controller.rb` also uses the correct block form: `chat.ask(content) { |chunk| ... }`.

But the multi-turn history seeding hallucinates a different fluent API:

```ruby
# build_chat helper, lines 48-58:
def build_chat
  chat = RubyLLM.chat(model: model_id)
  messages.each do |msg|
    if msg[:role] == "user"
      chat.user(msg[:content])     # NoMethodError
    else
      chat.assistant(msg[:content]) # NoMethodError
    end
  end
  chat
end
```

`chat.user(...)` and `chat.assistant(...)` do not exist in RubyLLM. The first message in a session works fine; replaying conversation history on subsequent messages crashes. Combined with a bogus `ARG RUBY_VERSION=4.0.2` in the Dockerfile (Ruby 4 doesn't exist yet — image pull will fail), this places GLM 5.1 in **Tier 2: works with caveats**, fixable with two small edits.

**Where it excels:**
- 24 test methods across 5 files (more than Opus baseline)
- All 5 required gems present
- Correct framework exclusions in `application.rb`
- Full Hotwire stack (turbo-rails, stimulus-rails, importmap-rails)
- Multi-stage Docker, proper SECRET_KEY_BASE handling
- Correct primary RubyLLM call pattern

### Grok 4.20 — Fast but Architecturally Broken

Grok 4.20 was the **fastest model in the entire benchmark at 8 minutes** (half the time of Claude Opus). It also has the most fundamental problems we've seen:

```ruby
# chats_controller.rb:11-23
require "openai"
client = OpenAI::Client.new(
  access_token: ENV["OPENROUTER_API_KEY"],
  uri_base: "https://openrouter.ai/api/v1"
)
```

Grok bypassed RubyLLM entirely and used the `ruby-openai` gem instead. That alone would put it in the "works with caveats" tier (like Step 3.5 Flash). But there's a fatal twist:

```ruby
# Gemfile
group :development, :test do
  gem "ruby-openai", require: false
end
```

The `ruby-openai` gem is **only loaded in dev/test, not production**. The controller's `require "openai"` will succeed in tests (because the gem is loaded) but `OpenAI::Client.new` will raise `NameError` in production. The tests pass; the deployment crashes.

**Other architectural problems:**
- Uses `format.turbo_stream` in the controller, but `turbo-rails`, `stimulus-rails`, and `importmap-rails` are **not in the Gemfile at all**. The format is undefined → `ActionController::UnknownFormat`.
- The model ID `anthropic/claude-3-5-sonnet-latest` is not a valid OpenRouter slug.
- Same `RUBY_VERSION=4.0.2` Dockerfile bug as GLM 5.1.
- Dockerfile exposes port 80 with Thruster, but docker-compose maps `3000:3000` — port mismatch.
- `env_file: .env` is required (no `required: false`), so compose will refuse to start without a `.env` file.
- Only 2 test files, 3 test methods, no LLM mocking, and the test file uses `require "ruby/openai"` (wrong path; the gem is `require "openai"`).
- Missing both `ruby_llm` and `bundle-audit` from the Gemfile — only 3 of 5 required gems.

**Where it excels:**
- Fastest completion time in the entire benchmark (8 minutes total)
- Multi-stage Dockerfile structure (despite the Ruby version bug)
- Reasonable Tailwind styling

This is the worst non-trivial result so far. **Tier 3: broken core.** The combination of an uninstalled production gem, a missing Hotwire stack, and a non-existent Ruby version means even a single-turn message would fail in three different ways.

### Verdict on All Deep-Reviewed Models

**Only Sonnet, Opus, and GLM 5 produce code that actually works** among the models reviewed in detail. GLM 5.1 comes closest after them — single-turn works and the fix is trivial. Kimi, MiniMax, Gemini 3.1 Pro, and Grok 4.20 all generate more test methods or more files but the core functionality is broken. The pattern is consistent: models hallucinate fluent APIs when encountering less common gems, and Grok's "use a gem you forgot to install" failure is a new variant of the same problem.

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
| **GLM 5.1** | Partial | **First msg only** | No | Correct `RubyLLM.chat`/`ask`, but invented `c.user`/`c.assistant` for history seeding. Single-turn works, multi-turn crashes. Also `RUBY_VERSION=4.0.2` Dockerfile bug. |
| **Grok 4.20** | N/A | **No** | No | Bypasses RubyLLM with `OpenAI::Client.new` from `ruby-openai` gem, but ruby-openai is only in dev/test group. NameError in production. Also `format.turbo_stream` without turbo-rails installed. |

*Step 3.5 Flash works by calling the OpenRouter REST API directly with `Net::HTTP`, completely bypassing the RubyLLM gem the prompt asked for.

### What Went Wrong

**11 out of 14 models invented non-existent APIs or got wrong gem requirements.** The most common failure mode was hallucinating an OpenAI-style client interface:

- DeepSeek V3.2 and Qwen 3 Coder Next both invented `RubyLLM::Client.new` — a class that does not exist.
- Qwen 3.5 122B invented an `Openrouter::Client` gem that does not exist at all.
- Kimi K2.5 got the initial `RubyLLM.chat()` call right but invented `add_message()` and `complete()` methods.
- MiniMax M2.7 invented a `RubyLLM.chat(messages: [...])` batch API that doesn't exist.
- Qwen 3.6 Plus invented `chat.add_message()` for history replay.
- Gemini 3.1 Pro used `RubyLLM::Chat.new(...)` constructor and invented `add_message()`.
- GLM 5.1 got the primary `RubyLLM.chat` / `chat.ask` calls right but invented `chat.user(...)`/`chat.assistant(...)` for history seeding.
- Grok 4.20 bypassed RubyLLM entirely and required `ruby-openai` from a `dev/test`-only Gemfile group, plus used `format.turbo_stream` without `turbo-rails` in the Gemfile at all.

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
| GLM 5.1 (Z.ai) | Subscription | 22m | Single-turn chat works (correct `RubyLLM.chat`/`ask`); multi-turn history seeding hallucinated `c.user`/`c.assistant`. Also `RUBY_VERSION=4.0.2` Dockerfile bug needs fixing. |
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
| Grok 4.20 | Bypassed RubyLLM with `ruby-openai`, but gem is only in dev/test group → NameError in prod |

### The Bottom Line

**If you don't want to be locked to Anthropic, GLM 5 remains the only fully-working plug-and-play alternative** — correct RubyLLM API, mocks properly in tests, completes in 17 minutes, costs ~$0.11 per run (89% cheaper than Opus).

**GLM 5.1 (Z.ai coding plan) is the closest runner-up** — single-turn chat works correctly, only the multi-turn history seeding and a Dockerfile Ruby version need a 5-minute fix. If you have a Z.ai Lite subscription (which uses a flat-rate coding endpoint instead of pay-per-token), GLM 5.1 could be viable after one patch.

**Grok 4.20 is the worst structural result** despite being the fastest model in the benchmark. It compounds three fatal bugs: bypassing RubyLLM in favor of a gem that's only in `dev/test` group, using `format.turbo_stream` without installing turbo-rails at all, and a non-existent Ruby version in the Dockerfile.

Step 3.5 Flash works at runtime but cheats by bypassing RubyLLM. Everything else either crashes on startup or fails when you try to send a message.

This reveals a critical limitation of benchmark metrics: **file count, test count, and artifact checklist do not measure whether the code actually works.** A model can score 9/9 on completeness, write 37 test methods, and still produce a non-functional application. The only reliable signal is whether the model correctly uses real APIs — and most models hallucinate API interfaces they've seen in training data rather than using the actual gem's API.

---

## NVIDIA RTX 5090 Cross-Reference: Distillation Doesn't Save You

The full NVIDIA workstation results are in [`success_report.nvidia.md`](success_report.nvidia.md), but one finding from that profile is important enough to surface here:

**Claude reasoning distillation does NOT transfer library API knowledge.** We tested [Jackrong's Qwen 3.5 27B distilled from Claude 4.6 Opus reasoning traces](https://huggingface.co/Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled) on both the AMD server (full Q8) and the NVIDIA workstation (Q3_K_M). Both runs produced code that **looks** Claude-shaped (frozen string pragmas, separate Response value objects, layered service/controller/model split, careful framework exclusions, doc comments at file headers) — but both hallucinated the RubyLLM API in the same Tier 3 way:

```ruby
# What the distilled model wrote (NVIDIA, Q3_K_M, 12 min):
RubyLLM::Chat.new.with_model(@model) do |chat|
  chat.add_message(role: :user, content: msg[:content])
  response = chat.ask(message)
  Response.new(content: response.text, ...)
end

# What it should be:
chat = RubyLLM.chat(model: model_id)
response = chat.ask(message)
response.content
```

`RubyLLM::Chat.new.with_model{}`, `chat.add_message`, and `response.text` are all fabricated. The distilled model cargo-culted Claude's *form* without inheriting Claude's grounded recall of the actual gem methods. **Distillation transferred prose style and code organization habits, not library-specific factual knowledge.**

This is a meaningful negative result for anyone considering Claude-distilled open-source models as a cheap stand-in for the real Claude. **Library API knowledge is binary recall, not a reasoning skill that decomposes through distillation.** A model either has memorized that `RubyLLM.chat(...).ask(...)` returns an object with `.content` or it doesn't, and Claude's reasoning chains don't repeatedly spell out obscure Ruby gem APIs in a way that can be distilled into the student weights.

The same pattern held across the NVIDIA profile: **0 of 8 local models produced runnable code**, including 5 different Qwen variants (general, coder, MoE, RL-tuned, and Claude-distilled). The 3 that actually completed cleanly (qwen3.5:35b, qwen3.5:27b-claude, plus the 5 with errors) all hallucinate the API the same way the AMD-server versions do.

**Practical conclusion**: if you need a model that actually uses the RubyLLM gem (or any specific less-common library), pay for the real Claude or use GLM 5. Distilled stand-ins, RL-tuned coders, and bigger contexts won't help — the knowledge isn't in the open-source weights.
