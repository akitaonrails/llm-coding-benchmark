# NVIDIA RTX 5090 Benchmark Success Report

This report covers the **local llama-swap subset** of the LLM coding benchmark running on an NVIDIA RTX 5090 (Blackwell, sm_120, 32 GB VRAM). For the AMD Strix Halo server profile (full Q8 weights, large context, OpenRouter cloud models, Z.ai), see [`success_report.md`](success_report.md).

The infrastructure setup is documented in [`llama-swap.md`](llama-swap.md). The hardware constraints are:

- **32 GB VRAM** vs the AMD server's 128 GB unified memory
- **Q3_K_M / Q4_K_M quants** (~12-20 GB weights) vs AMD's Q8_0 (~30 GB)
- **64K-128K context** vs AMD's 200K+

So the NVIDIA results are not directly comparable to the AMD ones — same models, smaller quants, smaller context, different llama.cpp build (fresh main with sm_120 kernels vs server's older `b8643`).

---

## Results Summary (8 models)

| Model | Status | Time | Files | Tier | Why |
|---|---|---:|---:|---|---|
| **qwen3_5_27b_claude** | completed | 12m | 1662 | **Tier 3** | Hallucinated `RubyLLM::Chat.new.with_model{}` and `add_message()`. Distillation transferred Claude's code style but not the actual API. |
| **qwen3_5_35b** | completed | 5m | 128 | (not deeply audited) | The general MoE finished cleanly. |
| **gemma4_31b** | completed_with_errors | 8m | 1288 | n/a | Same Gemma 4 repetition loop pattern as on AMD server. |
| **qwen3_32b** | completed_with_errors | 4m | 1134 | n/a | Partial scaffold, did not terminate cleanly. |
| **qwen3_coder_30b** | completed_with_errors | 6m | 1333 | **Tier 3** | Created project in nested `chat_app/` subdir. Returned a hardcoded mock string instead of calling RubyLLM at all. |
| **qwen2_5_coder_32b** | timeout | 90m | **0** | — | 90 minute timeout, empty project directory. The 1.8 MB ndjson shows the model thrashed without writing a single file. |
| **qwen3_5_27b_sushi_coder** | failed | 6m | **0** | — | `ProviderModelNotFoundError` — model wasn't registered with the ollama provider config at runtime. Infrastructure failure, not the model's fault. |
| **gpt_oss_20b** | dropped | — | — | — | llama.cpp main has a regression in the harmony tool-call autoparser. Errors with `Failed to parse input at pos N: <\|channel\|>...` on multi-turn sessions. See "GPT OSS 20B" section below. |

**Bottom line: 0 of 8 NVIDIA models produced runnable code.** The two that completed cleanly (`qwen3_5_27b_claude`, `qwen3_5_35b`) hallucinated the RubyLLM API. Everything else either crashed, timed out, or produced obvious garbage.

This is consistent with the AMD profile's runtime viability findings — only Claude Opus, Claude Sonnet, and GLM 5 actually use the real RubyLLM API correctly across the entire benchmark, and none of those are available as local llama-swap models.

---

## Headline finding: Claude reasoning distillation does NOT transfer library API knowledge

The big experiment for the NVIDIA run was **Jackrong's Qwen 3.5 27B distilled from Claude 4.6 Opus reasoning traces**. The hypothesis: if Claude is the only family that consistently gets the RubyLLM API right (Opus, Sonnet, and GLM 5 are the only Tier 1 models in the entire benchmark), maybe distilling Claude's reasoning into an open-source Qwen base would transfer that correctness too.

**The answer is no.**

Both runs of the Claude-distilled Qwen 3.5 27B hallucinated the API:

### NVIDIA run (Q3_K_M, 12 minutes, completed)

`results-nvidia/qwen3_5_27b_claude/project/app/services/chat_service.rb`:

```ruby
RubyLLM::Chat.new.with_model(@model) do |chat|
  conversation_history.each do |msg|
    chat.add_message(role: :user, content: msg[:content])
    # ...
  end
  response = chat.ask(message)
  Response.new(content: response.text, usage: build_usage(response))
end
```

Every primitive in this code is fabricated:

- `RubyLLM::Chat.new` — constructor isn't public; correct entry is `RubyLLM.chat(model:)`
- `.with_model(@model) do |chat| ... end` — no such block API exists
- `chat.add_message(role:, content:)` — does not exist
- `response.text` — real API exposes `response.content`
- `response.usage.prompt_tokens` / `.completion_tokens` — not the real shape

This will raise `NoMethodError` on the very first request. The initializer at `config/initializers/ruby_llm.rb` also tries to call `config.openrouter_api_base=` which doesn't exist on `RubyLLM.configure`, so the app likely won't even boot.

### AMD run (full Q8, 90 minute timeout, partial)

`results/qwen3_5_27b_claude/project/app/services/chat_service.rb`:

```ruby
chat = RubyLLM.chat(
  model: model_name,
  provider: :openrouter
)
truncated_history.each do |msg|
  chat.add_message(role: msg[:role].to_sym, content: msg[:content])
end
response = chat.ask(message)
response_content(response)
```

Mixed: the entry point `RubyLLM.chat(model:)` is **right** (a real method), but then immediately hallucinates `chat.add_message(role:, content:)` — and the `provider: :openrouter` kwarg doesn't exist either. The `response_content(response)` helper case-matches Hash / String / `respond_to?(:content)` — pure paranoid coping, the model knew it was guessing.

Worse: the AMD Gemfile (line 60) has `gem "ruby-openai"` (the wrong gem!), no `ruby_llm` entry at all, plus `gem "minitest", "~> 6.0"` (minitest is on 5.x, no 6.0 exists) and `gem "tailwindcss"` (wrong gem name; should be `tailwindcss-rails`). The Gemfile doesn't even include the gem the service code tries to use.

### What distillation actually transferred

Both runs of the Claude-distilled model produce code that **looks** Claude-like:

- Frozen string literal pragmas
- Separate `Response` value objects with explicit attribute readers
- Three-tier service/controller/model split
- Doc comments at the top of every file
- Careful framework exclusions in `application.rb` (correctly comments out `active_record`, `active_job`, `action_mailer`, etc.)
- Defensive `case` statements that try multiple shapes for unknown return values
- Layered initialization with `RubyLLM.configure do |config| ... end` (good — that part is real)

What it did NOT transfer: **specific library API recall.** The model cargo-culted Claude's *form* without inheriting Claude's grounded recall of `RubyLLM.chat(...).ask(...).content`. Both runs invent the same set of fictional methods (`add_message`, `with_model`, `response.text`).

### Comparison with the actual Claude baseline

Claude Opus 4.6 baseline at `results/claude_opus_4_6/project/app/services/chat_service.rb`:

```ruby
@chat = RubyLLM.chat(model: model_id)
response = @chat.ask(message)
response.content
```

12 lines. No hallucinations. Includes streaming via block. The distilled model produced **3× the code volume and got the API wrong**.

### What this means for distillation as a strategy

This is a meaningful negative result. The distillation paper claims to transfer "reasoning traces" — and that part appears true for code style and architectural patterns. But **library-specific API knowledge is binary recall, not a reasoning skill that decomposes**. You either have memorized that the gem exposes `chat.ask(msg)` or you don't, and Claude's reasoning chains don't actually contain repeated mentions of obscure Ruby gem APIs in a way that can be distilled into the student.

A model that hallucinates `add_message` after distillation will keep hallucinating it because the base Qwen weights never had the right answer in the first place, and the Claude reasoning traces never had reason to spell it out explicitly.

**Practical takeaway:** if you need a model that can actually use the RubyLLM gem (or any specific less-common library), pay for the real Claude or use GLM 5. Distilled stand-ins won't help.

---

## AMD vs NVIDIA: smaller quant is not noticeably worse

The same Claude-distilled model ran very differently on the two profiles:

| | AMD server | NVIDIA workstation |
|---|---|---|
| Quant | Q8_0 (~27 GB) | Q3_K_M (~12 GB) |
| Context | (server default) | 131072 |
| Time | 90m timeout | 12m completed |
| Files | 2231 | 1662 |
| llama.cpp build | b8643 | latest main |
| Service file LoC | ~75 (with response sniffing) | ~78 (with separate Response class) |
| Entry call | `RubyLLM.chat(model:, provider:)` — half right | `RubyLLM::Chat.new.with_model{}` — fully wrong |
| `add_message` hallucination | yes | yes |
| Gemfile sanity | **broken** (`ruby-openai`, fake `minitest 6.0`, `tailwindcss`) | clean (`ruby_llm`, `tailwindcss-rails`) |
| Dockerfile | not generated in time | present but `RUBY_VERSION=4.0.2` invalid |
| Tests | 9 tests, monkey-patches `RubyLLM.chat` at module level | 3 useful + 3 skipped, no mocks |

**Counterintuitive finding: the smaller quant (NVIDIA Q3_K_M) is NOT noticeably worse than the full Q8.** In some ways it's better-formed: cleaner Gemfile, finished the project, generated docker-compose. It's worse on the *one* axis that matters (its hallucinated API call is further from reality than AMD's first line), but both fail at runtime for the same reason.

The 90-minute Q8 run produced **more typing, not more correctness**. This is consistent with the broader benchmark pattern: **API correctness is binary recall, not a function of compute budget or quantization within reason.** A model either knows the gem's API or it doesn't, and giving it more parameters and longer thinking time doesn't help if the knowledge isn't in there.

---

## GPT OSS 20B: dropped due to llama.cpp regression

GPT OSS 20B was originally in the NVIDIA profile. The fresh-built llama.cpp main (commit `b1-15f786e`) introduced a regression in the harmony tool-call autoparser that affects multi-turn agentic sessions.

### Symptoms

```
error: 'Failed to parse input at pos 755: <|channel|>write...'
```

then later, after we tried `--reasoning-format none`:

```
error: 'Failed to parse input at pos 112: commentary to=<|...'
```

opencode hits this within 3 minutes of the run starting and goes into an error loop.

### What we tried

1. **`--reasoning-format none`**: Suppressed the position-755 error but introduced a different position-112 error in multi-turn sessions. The autoparser still tries to parse `<|channel|>commentary to=<|tool_name|>` patterns and fails differently.
2. **Smoke tests with isolated requests**: Both non-streaming and streaming tool calls work in isolation. The bug is specifically in multi-turn parsing where the model is responding to a previous tool result.

### Why we dropped it instead of pinning llama.cpp

On the AMD server (older llama.cpp `b8643`), gpt-oss successfully completed **51 tool-calling steps** in the original benchmark. It failed for a different reason there — the model created the Rails app under `project/app/` instead of `project/`. So we already have data on the model's actual coding ability:

- The llama.cpp parser bug isn't a model issue — it's a recently-introduced regression in the autoparser
- Even if we pinned to `b8643` and got it parsing, the model still wouldn't follow workspace instructions any better

Re-enable when llama.cpp adds a dedicated `peg-gpt-oss` harmony parser (similar to the `peg-gemma4` fix in PR #21418), or downgrade the local Dockerfile to `b8643`. Currently marked `skip_by_default: true` in `config/models.nvidia.json`.

---

## Other model failure analysis

### qwen3_coder_30b (Tier 3)

`/mnt/data/Projects/llm-coding-benchmark/results-nvidia/qwen3_coder_30b/project/chat_app/app/controllers/api/v1/messages_controller.rb` is the entire LLM "integration":

```ruby
class Api::V1::MessagesController < ApplicationController
  def create
    render json: {
      response: "This is a mock response. In a real implementation, this would connect to RubyLLM with Claude Sonnet via OpenRouter."
    }
  end
end
```

The model literally returned a hardcoded mock string and admitted it. There is no `app/services/`, no initializer for RubyLLM, no integration whatsoever. The Gemfile *does* list `gem "ruby_llm"` but nothing imports it. The chat controller is 67 bytes (empty stub), application controller is 66 bytes (ghost), welcome controller is empty.

Also created the project in a nested `chat_app/` subdirectory instead of using the workspace root — same pattern as gpt-oss-20b on the AMD server.

**Verdict: non-functional skeleton.** Worst output of the four real ones. Would render a fake string and nothing else.

### qwen2_5_coder_32b (timeout, no output)

90 minute timeout, empty project directory. The 1.8 MB `opencode-output.ndjson` shows the model spent 90 minutes thrashing without writing a single file successfully. No code to evaluate.

Possible causes: model went into an infinite reasoning loop; hit a tool call format that opencode kept rejecting; spent all its time on planning without ever calling write tools. Without further investigation we can't tell, but the practical outcome is the same as a failure.

### qwen3_5_27b_sushi_coder (infrastructure failure, not the model's fault)

```
ProviderModelNotFoundError: providerID: "ollama", modelID: "qwen/qwen3.5-27b-sushi-coder"
```

The model wasn't registered with the ollama backend on the NVIDIA host at runtime. The benchmark generator created the entry, llama-swap had it loaded successfully in warmup, but opencode's view of the providers didn't match. Need to investigate why the generated `config/opencode.benchmark.local.json` didn't include the sushi-coder model entry — likely a name mismatch between the benchmark slug and the llama-swap model ID. **Empty project. Re-test after fixing the registration.**

---

## What the NVIDIA profile is actually good for

Given that 0 of 8 models produce runnable code, what's the point of the NVIDIA profile?

1. **Reproducibility**: Same hardware as a typical developer workstation. Anyone with a 5090 can replicate these results, unlike the AMD Strix Halo server which is rare hardware.
2. **Local-only validation**: Tests whether models that look promising on cloud APIs degrade when run locally at smaller quants. Answer for the Claude-distilled Qwen: not noticeably worse, both broken.
3. **Negative results on distillation**: The headline finding above is genuinely useful for anyone considering Claude-distilled open-source models for agentic coding tasks.
4. **Infrastructure proving ground**: We learned that fresh llama.cpp main has a gpt-oss regression, that q8 KV cache + flash-attention works on Blackwell, that Q3_K_M of a 27B model fits 128K context, and that the OLLAMA_HOST env var trap can route inference to the wrong machine.

The actionable result for someone shopping for a local agentic coding model: **none of the open-source models tested here will work out of the box** on a 5090, and the issue isn't hardware — it's that the gem-specific API knowledge isn't in the open weights. Use Claude Opus, Claude Sonnet, or GLM 5 via OpenRouter instead.

---

## See also

- [`success_report.md`](success_report.md) — main AMD profile + cloud benchmark report
- [`llama-swap.md`](llama-swap.md) — local llama-swap Docker setup, hardware tuning, common pitfalls
- [`report.nvidia.md`](report.nvidia.md) — auto-generated NVIDIA results table
- [`llama_swap_warmup.nvidia.md`](llama_swap_warmup.nvidia.md) — per-model preflight tok/s
