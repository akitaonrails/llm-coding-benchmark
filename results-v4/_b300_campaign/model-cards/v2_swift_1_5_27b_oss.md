---
license: other
license_name: swift-open-license-1.0
license_link: https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b/blob/main/LICENSE
library_name: transformers
pipeline_tag: image-text-to-text
gated: true
tags:
- qwen3_8
- reasoning
- efficient-thinking
- token-efficient
- post-training
- terminal-bench
base_model: Qwen/Qwen3.8-27B
base_model_relation: finetune
---

<div align="center">
  <a href="https://ukisai.com"><img src="ukisai-banner.png" alt="UkisAI" style="width:100%;max-width:100%;height:auto;display:block;margin-bottom:0.6em;" /></a>
  <div style="display:flex;justify-content:center;gap:0.6em;margin-bottom:1em;">
    <a href="https://ukisai.com"><strong>Website</strong></a> &nbsp;&bull;&nbsp;
    <a href="https://ukisai.com/products/swift"><strong>Learn more</strong></a> &nbsp;&bull;&nbsp;
    <a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27B-GGUF"><strong>GGUF</strong></a> &nbsp;&bull;&nbsp;
    <a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27B-GSQ-RCO-GGUF"><strong>GSQ-RCO GGUF</strong></a> &nbsp;&bull;&nbsp;
    <a href="#evaluation"><strong>Evaluation</strong></a> &nbsp;&bull;&nbsp;
    <a href="#license-and-access"><strong>Enterprise licensing</strong></a>
  </div>
</div>

# Swift 1.5 Qwen3.8-27B

Swift 1.5 Qwen3.8-27B is UkisAI's reasoning-efficient derivative of [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B).
It uses **58.5% fewer thinking tokens** while scoring **0.35% higher** than the base, for a **1.95× speed-up** on several tasks.

Swift 1.5 is a direct upgrade from [Swift 1.0](https://huggingface.co/ukisai/Swift-Qwen3.8-27b), our model with 350k+ downloads, delivering stronger overall performance than both base and Swift 1.0 in various tasks, especially coding and agentic, while using fewer thinking tokens. We accomplished that by scaling up the post-training (RL and OPD) from the previous version.

## Demo

We gave base Qwen3.8-27B and Swift 1.5 27B the same prompt:

> create a 3d little planet globe where I (player can walk around) and it has all these biomes to explore, the globe doesn't have to be too big, but still fun to go around. It's about a boy scout who is camping and goes around exploring.

<video src="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b/resolve/main/swift-1.5-planet-demo.mp4" controls autoplay muted loop playsinline style="width:100%;height:auto;border-radius:12px;"></video>

Try the game yourself here: [https://ukisai.com/swift-games/27b](https://ukisai.com/swift-games/27b)

Base Qwen3.8-27B took 104.6 minutes to build its game. Swift 1.5 took 11.39 minutes.

## Training approach

We made Swift efficient by figuring out which tokens were linked to pathological overthinking and penalizing them without "attacking" the reasoning length directly then regained the accuracy with RL and OPD, leading to "compressed" token usage while maintaining accuracy.
Swift 1.5 was made from [Swift 1.0](https://huggingface.co/ukisai/Swift-Qwen3.8-27b), on whom we scaled up the post-training methods that previously improved Swift1.0 model performance, this time with the main
focus on long-horizon, agentic, and coding tasks, as seen in the LiveCodeBench and Terminal Bench 2.1 improvements. Our training data is viewable here: https://huggingface.co/datasets/ukisai/Qwen3.8-27B-multi-turn-agent-sft albeit it is not used out of the box, but rather re-sampled, turned into proper RL environments etc.

## Evaluation

The external results below compare **Qwen3.8-27B**, the foundation base model,
and **Swift 1.5**. Both models use
the same saved evaluation protocols, and all scores are reported as final aggregate
percentages.

<style>
.swift15-table { width:100%; table-layout:fixed; border-collapse:separate; border-spacing:0; overflow:hidden; border:1px solid #27344A; border-radius:20px; background:#0D111B; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; font-size:14px; color:#BFBDBD; }
.swift15-table th { padding:13px 8px; text-align:center; font-weight:700; color:#AEB5C7; background:#0D111B; border-right:1px solid #27344A; border-bottom:1px solid #27344A; }
.swift15-table td { padding:14px 8px; text-align:center; color:#BFBDBD; background:#0D111B; border-right:1px solid #27344A; border-bottom:1px solid #27344A; vertical-align:middle; overflow-wrap:break-word; }
.swift15-table tr > :last-child { border-right:0; }
.swift15-table tbody tr:last-child td { border-bottom:0; }
.swift15-table .benchmark-heading { color:#B7BDCD; background:#0D111B; border-bottom:3px solid #7D45B5; }
.swift15-table .score-heading { color:#F0C5FF; background:#52239E; border-bottom:3px solid #7D45B5; }
.swift15-table .tokens-heading, .swift15-table .median-heading { color:#D4E8FF; background:#304FC2; border-bottom:3px solid #5687E6; }
.swift15-table .change-heading { color:#61B9FF; background:#101D2D; border-bottom:3px solid #5687E6; }
.swift15-table .change { color:#61B9FF; background:#101D2D; font-weight:700; }
.swift15-table .gain { color:#DDA8FF; background:#171127; font-weight:700; }
.swift15-table .model { padding-left:18px; text-align:left; color:#FFFFFF; font-weight:600; }
.swift15-table strong { color:#FFFFFF; }
.swift15-table .section { padding:12px 18px; text-align:left; color:#B489FF; background:#2A2541; font-weight:700; letter-spacing:.08em; text-transform:uppercase; border-top:1px solid #3A3159; border-bottom:1px solid #3A3159; }
.swift15-table .swift15 { background:#171127; }
.swift15-table thead tr:nth-child(2) .swift15 { color:#D3A0FF; }
.swift15-table .detail { color:#8C94A8; font-size:12px; font-weight:500; }
.swift15-table.swift15-compact { display:table !important; width:100% !important; table-layout:fixed !important; }

@media (max-width: 640px) {
  .swift15-table { display:block !important; width:100% !important; max-width:100%; overflow-x:auto !important; -webkit-overflow-scrolling:touch; table-layout:auto !important; }
  .swift15-table th, .swift15-table td { min-width:104px; }
  .swift15-table th:first-child, .swift15-table td:first-child { min-width:170px; }
}
</style>

<table class="swift15-table">
  <thead>
    <tr>
      <th class="benchmark-heading" rowspan="2" style="width:32%;text-align:left;padding-left:18px;vertical-align:bottom;">Benchmark</th>
      <th class="score-heading" colspan="2">Final score</th>
      <th class="tokens-heading" colspan="3">Mean tokens</th>
      <th class="median-heading">Median tokens</th>
    </tr>
    <tr>
      <th>Qwen3.8</th>
      <th class="swift15">Swift 1.5</th>
      <th>Qwen3.8</th>
      <th class="swift15">Swift 1.5</th>
      <th class="change-heading">Reduction</th>
      <th class="change-heading">Reduction</th>
    </tr>
  </thead>
  <tbody>
    <tr><td class="section" colspan="7">General reasoning</td></tr>
    <tr><td class="model">GPQA-Diamond</td><td>88.28%</td><td class="swift15"><strong>88.59%</strong></td><td>15,014</td><td class="swift15">8,717</td><td class="change">&#8595; 41.9%</td><td class="change">&#8595; 58.5%</td></tr>
    <tr><td class="model">C-Eval</td><td>90.00%</td><td class="swift15"><strong>90.92%</strong></td><td>1,492</td><td class="swift15">819</td><td class="change">&#8595; 45.1%</td><td class="change">&#8595; 16.9%</td></tr>
    <tr><td class="model">IFBench</td><td><strong>73.53%</strong></td><td class="swift15">72.07%</td><td>8,052</td><td class="swift15">4,955</td><td class="change">&#8595; 38.5%</td><td class="change">&#8595; 47.3%</td></tr>
    <tr><td class="model">ERQA</td><td><strong>67.45%</strong></td><td class="swift15">65.40%</td><td>4,137</td><td class="swift15">1,906</td><td class="change">&#8595; 53.9%</td><td class="change">&#8595; 56.2%</td></tr>
    <tr><td class="section" colspan="7">Mathematics</td></tr>
    <tr><td class="model">AIME 2026</td><td><strong>98.67%</strong></td><td class="swift15">96.00%</td><td>22,014</td><td class="swift15">13,203</td><td class="change">&#8595; 40.0%</td><td class="change">&#8595; 48.5%</td></tr>
    <tr><td class="model">HMMT November 2025</td><td><strong>99.33%</strong></td><td class="swift15">97.33%</td><td>22,032</td><td class="swift15">14,957</td><td class="change">&#8595; 32.1%</td><td class="change">&#8595; 47.8%</td></tr>
    <tr><td class="section" colspan="7">Coding</td></tr>
    <tr><td class="model">LiveCodeBench v6</td><td>76.76%</td><td class="swift15"><strong>81.71%</strong></td><td>11,184</td><td class="swift15">8,448</td><td class="change">&#8595; 24.5%</td><td class="change">&#8595; 46.3%</td></tr>
    <tr><td class="section" colspan="7">Agent tasks</td></tr>
    <tr><td class="model">Terminal-Bench 2.1*</td><td>69.21%</td><td class="swift15"><strong>72.13%</strong></td><td>52,265</td><td class="swift15">43,733</td><td class="change">&#8595; 16.3%</td><td class="change">&#8595; 0.1%</td></tr>
  </tbody>
</table>

<p><strong>* Note:</strong> Terminal Bench 2.1 score of Swift1.5 27B is misleadingly low on token saving at first glance. It is not a bug, but a simple matter of the Swift models not falling into overthinking loops and failing the task, rather pursuing it until the end, leading to higher average token usage. The token reduction still falls in the -38.7% range when compared apples-to-apples on tasks both models succeed.</p>

<details>
<summary><strong>Benchmark methodology and reproduction settings</strong></summary>

<p style="font-size:13px;line-height:1.5;margin:8px 0;"><strong>Serving:</strong> BF16 · vLLM 0.27.1 · Qwen3 parser · context 262,144 · thinking xhigh.<br>
<strong>Sampling:</strong> temperature 1.0 · top_p 0.95 · top_k 20 · min_p 0 · presence_penalty 0 · repetition_penalty 1.<br>
<strong>Benchmarks:</strong> averages over five seeds (0–4) per model; five trials per task for Terminal-Bench, base and Swift 1.5 served at context 131,072 on the same Harbor build.</p>

<table style="display:table;width:100%;border-collapse:collapse;font-size:13px;line-height:1.3;margin:8px 0;">
  <thead><tr><th style="padding:4px 8px;text-align:left;">Benchmark</th><th style="padding:4px 8px;text-align:right;">Output cap</th></tr></thead>
  <tbody>
    <tr><td style="padding:3px 8px;">GPQA-Diamond</td><td style="padding:3px 8px;text-align:right;">100,000</td></tr>
    <tr><td style="padding:3px 8px;">C-Eval</td><td style="padding:3px 8px;text-align:right;">16,384</td></tr>
    <tr><td style="padding:3px 8px;">IFBench</td><td style="padding:3px 8px;text-align:right;">81,920</td></tr>
    <tr><td style="padding:3px 8px;">ERQA</td><td style="padding:3px 8px;text-align:right;">100,000</td></tr>
    <tr><td style="padding:3px 8px;">AIME 2026</td><td style="padding:3px 8px;text-align:right;">250,000</td></tr>
    <tr><td style="padding:3px 8px;">HMMT November 2025</td><td style="padding:3px 8px;text-align:right;">250,000</td></tr>
    <tr><td style="padding:3px 8px;">LiveCodeBench v6</td><td style="padding:3px 8px;text-align:right;">32,768</td></tr>
    <tr><td style="padding:3px 8px;">Terminal-Bench 2.1</td><td style="padding:3px 8px;text-align:right;">Agent/task limits</td></tr>
  </tbody>
</table>

</details>

## Efficiency across reasoning efforts

Qwen3.8's `reasoning_effort` setting lets users choose how much the model thinks.
For Swift 1.5 to be useful across these settings, it needs to reduce thinking while
keeping accuracy close to the base. We therefore tested `xhigh`, `medium`, and `low`:
thinking-token savings persist at every level.

<table class="swift15-table swift15-compact">
  <thead>
    <tr>
      <th class="benchmark-heading" style="width:34%;text-align:left;padding-left:18px;">Reasoning effort</th>
      <th class="score-heading" style="width:22%;">Qwen3.8</th>
      <th class="score-heading" style="width:22%;">Swift 1.5</th>
      <th class="tokens-heading" style="width:22%;">Mean thinking reduction</th>
    </tr>
  </thead>
  <tbody>
    <tr><td class="model">Xhigh</td><td>88.28%</td><td class="swift15"><strong>88.59%</strong></td><td class="change">&#8595; 41.9%</td></tr>
    <tr><td class="model">Medium</td><td><strong>84.14%</strong></td><td class="swift15">82.22%</td><td class="change">&#8595; 24.8%</td></tr>
    <tr><td class="model">Low</td><td>84.04%</td><td class="swift15"><strong>84.85%</strong></td><td class="change">&#8595; 28.7%</td></tr>
  </tbody>
</table>

At `low`, Swift 1.5 scores above the base while using about 29% fewer thinking tokens.

## Quantized Swift 1.5 models

| Format | Repository | Runtime |
| --- | --- | --- |
| GGUF | [Swift-1.5-Qwen3.8-27B-GGUF](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27B-GGUF) | llama.cpp |
| GSQ-RCO GGUF (compact 2–3 bit) | [Swift-1.5-Qwen3.8-27B-GSQ-RCO-GGUF](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27B-GSQ-RCO-GGUF) | llama.cpp |
| AWQ INT4 (W4A16) | [Swift-1.5-Qwen3.8-27b-W4A16-AWQ](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AWQ) | vLLM (`compressed-tensors`) |
| AutoRound INT4 (W4A16) | [Swift-1.5-Qwen3.8-27b-W4A16-AutoRound](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound) | vLLM (`auto-round`) |
| AWQ + GPTQ INT4 (W4A16) | [Swift-1.5-Qwen3.8-27b-INT4](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-INT4) | vLLM (`compressed-tensors`) |
| NVFP4 | [Swift-1.5-Qwen3.8-27b-NVFP4](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-NVFP4) | NVIDIA Blackwell |
| AMD Quark FP8 (W8A8) | [Swift-1.5-Qwen3.8-27b-Quark-FP8-dynamic-AMD](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-Quark-FP8-dynamic-AMD) | AMD Quark |
| MLX 5-bit | [Swift-1.5-5bit-MLX](https://huggingface.co/ukisai/Swift-1.5-5bit-MLX) | Apple MLX |
| MLX 4-bit | [Swift-1.5-4bit-MLX](https://huggingface.co/ukisai/Swift-1.5-4bit-MLX) | Apple MLX |
| MLX 3-bit (text only) | [Swift-1.5-3bit-MLX-TextOnly](https://huggingface.co/ukisai/Swift-1.5-3bit-MLX-TextOnly) | Apple MLX |

These results evaluate the merged Swift 1.5 checkpoint and three INT4 exports on
**GPQA-Diamond (198 questions), IFBench (300 prompts), and AIME 2026 (30 problems)**.
Each model completed the full datasets with **one sample per prompt, seed 0, and
zero request errors**. This is a single-seed evaluation, separate from the
five-repeat BF16 release results above.

The Qwen-base columns use the **saved seed/sample 0 runs**.
Quantization recipes and serving settings differ from the new Swift 1.5 runs,
so these are reference comparisons rather than a controlled measurement of
the Swift adaptation. Token reductions below are recomputed from those same
reference samples.

<table class="swift15-table" style="display:table;width:100%;table-layout:fixed;">
  <thead><tr>
    <th class="benchmark-heading" style="width:32%;text-align:left;padding-left:18px;">Benchmark / Swift 1.5 quantization</th>
    <th class="score-heading" style="width:16%;">Qwen base<br>accuracy</th>
    <th class="score-heading" style="width:16%;">Swift 1.5 quant<br>accuracy</th>
    <th class="tokens-heading" style="width:18%;">Mean token reduction</th>
    <th class="median-heading" style="width:18%;">Median token reduction</th>
  </tr></thead>
  <tbody>
    <tr><td class="model">GPQA-Diamond<br><span class="detail"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AWQ">AWQ INT4</a></span></td><td>86.36%</td><td class="swift15">88.38%</td><td class="change">&#8595; 51.5%</td><td class="change">&#8595; 64.4%</td></tr>
    <tr><td class="model">GPQA-Diamond<br><span class="detail"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound">AutoRound INT4</a></span></td><td>86.36%</td><td class="swift15">89.39%</td><td class="change">&#8595; 50.5%</td><td class="change">&#8595; 57.8%</td></tr>
    <tr><td class="model">GPQA-Diamond<br><span class="detail"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-INT4">AWQ + GPTQ INT4</a></span></td><td>86.36%</td><td class="swift15">90.91%</td><td class="change">&#8595; 45.8%</td><td class="change">&#8595; 64.4%</td></tr>
    <tr><td class="model">IFBench<br><span class="detail"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AWQ">AWQ INT4</a></span></td><td>72.00%</td><td class="swift15">72.00%</td><td class="change">&#8595; 36.9%</td><td class="change">&#8595; 49.3%</td></tr>
    <tr><td class="model">IFBench<br><span class="detail"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound">AutoRound INT4</a></span></td><td>72.00%</td><td class="swift15">69.33%</td><td class="change">&#8595; 29.3%</td><td class="change">&#8595; 39.2%</td></tr>
    <tr><td class="model">IFBench<br><span class="detail"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-INT4">AWQ + GPTQ INT4</a></span></td><td>72.00%</td><td class="swift15">70.00%</td><td class="change">&#8595; 31.8%</td><td class="change">&#8595; 52.7%</td></tr>
    <tr><td class="model">AIME 2026<br><span class="detail"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AWQ">AWQ INT4</a></span></td><td>70.00%</td><td class="swift15">86.67%</td><td class="change">&#8595; 29.2%</td><td class="change">&#8595; 36.2%</td></tr>
    <tr><td class="model">AIME 2026<br><span class="detail"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound">AutoRound INT4</a></span></td><td>76.67%</td><td class="swift15">83.33%</td><td class="change">&#8595; 17.7%</td><td class="change">&#8595; 32.4%</td></tr>
    <tr><td class="model">AIME 2026<br><span class="detail"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-INT4">AWQ + GPTQ INT4</a></span></td><td>76.67%</td><td class="swift15">83.33%</td><td class="change">&#8595; 22.4%</td><td class="change">&#8595; 34.0%</td></tr>
  </tbody>
</table>

**AIME scoring:** truncated responses count as incorrect for both columns.

The AMD Quark INT4 and FP8 exports have separate sanity evaluations; completed
results on these three reasoning benchmarks are not available for them.

<details>
<summary><strong>Quantized evaluation settings and BF16 reference</strong></summary>

**Serving:** vLLM 0.29.0, tensor parallelism 1, eager execution, BF16 activations,
context 131,072, template-default thinking without an effort override. The
AWQ + GPTQ export uses FP8 KV cache; BF16, AWQ, and AutoRound use auto KV dtype.
**Sampling:** temperature 1, top-p 0.95, top-k 20, min-p 0, presence penalty 0,
repetition penalty 1, seed 0. Output caps: GPQA 100,000, IFBench 81,920,
AIME 32,768. IFBench uses official strict prompt-level scoring.

GPQA token counts cover re-tokenized reasoning; IFBench and AIME count the
full generated response. Statistics include all responses, including truncations; medians
use the midpoint of the two central values when the sample count is even.

Saved Qwen references: W4A16 for GPQA and IFBench; Qwen AWQ for the
AWQ AIME row; Qwen W4A16 for the AutoRound and AWQ + GPTQ AIME rows. The
latter is a W4A16 reference for AutoRound, not an AutoRound base run.
The new runs do not reproduce the original software stack.

The fresh Swift 1.5 BF16 reference and all quantized exports scored as follows
under this single-seed protocol:

| Model | GPQA-Diamond | IFBench strict | AIME 2026 |
| --- | ---: | ---: | ---: |
| Swift 1.5 BF16 | 91.41% | 72.00% | 86.67% |
| AWQ INT4 | 88.38% | 72.00% | 86.67% |
| AutoRound INT4 | 89.39% | 69.33% | 83.33% |
| AWQ + GPTQ INT4 | 90.91% | 70.00% | 83.33% |

Truncation counts are recorded in the linked evaluation data.
These single-seed results do not establish
quality parity or replace the broader multi-seed evaluation.

[Verified counts, token statistics, settings, and evidence hashes](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b/blob/main/benchmarks/quantization-20260921.json).

</details>

## How to use

### GGUF download

The **[GGUF version](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27B-GGUF)** is
available for compatible llama.cpp-based runtimes. For the smallest files, use the
**[GSQ-RCO GGUF version](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27B-GSQ-RCO-GGUF)**: 8–12 GB mixed-precision quants refined for Swift 1.5.

### UkisAI API

Swift is served through an OpenAI-compatible API at
`https://ukisai.com/api/swift/v1`. It is **free for research purposes** and needs no
API key. The model id is `swift`.

~~~python
from openai import OpenAI

client = OpenAI(base_url="https://ukisai.com/api/swift/v1", api_key="none")
response = client.chat.completions.create(
    model="swift",
    messages=[{"role": "user", "content": "Explain speculative decoding in two sentences."}],
)
print(response.choices[0].message.content)
~~~

~~~bash
curl https://ukisai.com/api/swift/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "swift", "messages": [{"role": "user", "content": "Hello, Swift."}]}'
~~~

### Transformers

~~~python
import torch
from transformers import AutoModelForImageTextToText, AutoProcessor

model_id = "ukisai/Swift-1.5-Qwen3.8-27b"
processor = AutoProcessor.from_pretrained(model_id)
model = AutoModelForImageTextToText.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)
~~~

### vLLM

~~~bash
vllm serve ukisai/Swift-1.5-Qwen3.8-27b \
  --dtype bfloat16 \
  --tensor-parallel-size 1 \
  --max-model-len 262144 \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --port 8000
~~~

### SGLang

Alternatively, use a current SGLang build with Qwen3.8 support:

~~~bash
python -m sglang.launch_server \
  --model-path ukisai/Swift-1.5-Qwen3.8-27b \
  --dtype bfloat16 \
  --tp-size 1 \
  --context-length 262144 \
  --reasoning-parser qwen3 \
  --tool-call-parser qwen3_coder \
  --port 8000
~~~

Adjust tensor parallelism and context length to your GPU memory. See the base model's
[vLLM recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-27B) and
[SGLang recipe](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B)
for installation and hardware-specific settings.

### Optional MTP decoding

The published weights include the base model's MTP head. To enable self-speculative
decoding, append the corresponding flags to the server command above:

~~~bash
# vLLM
--speculative-config '{"method":"mtp","num_speculative_tokens":3}'

# SGLang
--speculative-algorithm EAGLE --speculative-num-steps 3 \
  --speculative-eagle-topk 1 --speculative-num-draft-tokens 4
~~~

## License and access

Swift 1.5 is a derivative of [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B)
(Copyright 2026 Alibaba Cloud, [Apache License 2.0](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b/blob/main/LICENSE-APACHE-2.0)). UkisAI's contribution, including the adapted
weights, is licensed under the **[Swift Open License v1.0](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b/blob/main/LICENSE)**. See [NOTICE](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b/blob/main/NOTICE) for the change notice and attribution details.

Personal, research, educational, evaluation, and commercial use are free for individuals
and organizations with gross annual revenue, including affiliates, of up to US$1,000,000.
Above that threshold, commercial use requires a separate Swift Enterprise License.
Contact [UkisAI](https://ukisai.com/contact) for terms.

Nothing in the Swift Open License limits rights in Qwen3.8-27B itself under Apache 2.0.

## Citation

~~~bibtex
@misc{swift-1.5-qwen3.8-27b,
  title  = {Swift 1.5 Qwen3.8-27B},
  author = {UkisAI},
  year   = {2026},
  url    = {https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b}
}
~~~

## Acknowledgements

We acknowledge the [NVIDIA Innovation Lab](https://www.nvidia.com/en-us/data-center/innovation-lab/),
[Amazon Web Services](https://aws.amazon.com/), and
[Google Cloud](https://cloud.google.com/) for providing the
compute for Swift's development, training, and evaluation.
