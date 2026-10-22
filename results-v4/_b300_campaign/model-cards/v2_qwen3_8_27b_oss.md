---
library_name: transformers
license: apache-2.0
pipeline_tag: image-text-to-text
---

# Qwen3.8-27B

> [!Note]
> This repository contains model weights and configuration files for the post-trained model in the Hugging Face Transformers format. 
>
> These artifacts are compatible with Hugging Face Transformers, vLLM, SGLang, TokenSpeed, etc.

> [!Tip]
> For users seeking managed, scalable inference without infrastructure maintenance, the official Qwen API service is provided by [Qwen Cloud](https://www.qwencloud.com).
> In particular, **Qwen3.8-27B** will be available as a hosted version with more production features, e.g., 1M context length by default, official built-in tools. For more information, please refer to the [Qwen3.8-27B Overview](https://www.qwencloud.com/models/qwen3.8-27b). The service is coming soon. Stay tuned for updates.

Following the widespread community adoption of the Qwen3.5 and Qwen3.6 series, we are pleased to introduce Qwen3.8, the most capable generation in the Qwen open-model family to date.

Built on the architectural foundation of Qwen3.5, Qwen3.8 delivers substantial gains across coding, professional work, research, and long-horizon agentic tasks. Qwen3.8-27B brings these advances to a compact, deployment-friendly dense model: a native vision-language model that understands images and videos, with flexible thinking control, designed to carry complex, multi-step tasks through to completion with greater reliability.

## Qwen3.8 Highlights

Qwen3.8-27B features the following enhancements:
- **Core Capabilities**: Comprehensive improvements across coding, professional work, research, and long-horizon agentic tasks.
- **Agent Execution**: Stronger autonomous planning and better handling of environment feedback, leading to more reliable end-to-end task completion.
- **Downstream Compatibility**: Broader support for popular harnesses and development tools, making it easier to integrate into your existing stack.
- **Flexible Thinking Control**: Thinking mode is on by default and can be disabled per request; reasoning depth can be tuned with `reasoning_effort`, and reasoning context from historical messages is retained via `preserve_thinking`.
- **Vision-Language Understanding**: Native support for image and video understanding, from STEM diagrams and documents to hour-scale videos.


## Model Overview

- Type: Causal Language Model with Vision Encoder
- Training Stage: Pre-training & Post-training
- Language Model
    - Number of Parameters: 27B
    - Hidden Dimension: 5120
    - Token Embedding: 248,320 (Padded)
    - Number of Layers: 64
    - Hidden Layout: 16 × (3 × (Gated DeltaNet → FFN) → 1 × (Gated Attention → FFN))
    - Gated DeltaNet:
        - Number of Linear Attention Heads: 48 for V and 16 for QK
        - Head Dimension: 128
    - Gated Attention:
        - Number of Attention Heads: 24 for Q and 4 for KV
        - Head Dimension: 256
        - Rotary Position Embedding Dimension: 64
    - Feed Forward Network:
        - Intermediate Dimension: 17,408
    - LM Output: 248,320 (Padded)
    - MTP (Multi-Token Prediction): trained with multiple steps
- Context Length: 262,144 natively and extensible up to 1,000,000 tokens.


## Benchmark Results

### Text Performance
<style>
.vl-table th{font-size:15px!important;line-height:1.2}
.vl-table td:not(.benchmark-cell):not([colspan]){font-size:15px;line-height:1.2;vertical-align:middle}
.vl-table .benchmark-cell{padding:12px 10px 12px 18px!important;vertical-align:middle}
.vl-table .benchmark-capability{font-size:15px;font-weight:600;line-height:1.22;color:#171717}
.vl-table .benchmark-name{margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B}
.vl-table .metric-stack{display:flex;flex-direction:column;gap:7px;padding:3px 0}
.vl-table .metric-label{font-size:10px;font-weight:400;line-height:1.1;color:#777}
.vl-table .metric-value{margin-top:2px;font-size:15px;line-height:1.15;color:#171717}
</style>
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1200px;margin:0 auto;padding:16px 0">
<table class="vl-table" style="width:100%;table-layout:fixed;border-collapse:collapse;font-size:13px">
<thead><tr>
<th style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0A2EFE;color:#0A2EFE"></th><th style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0A2EFE;color:#0A2EFE;font-size: 14px;width:14.00%;background:rgba(10, 46, 254, 0.08);">Qwen3.8-27B</th><th style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0A2EFE;color:#0A2EFE;font-size: 14px;width:14.00%;">Qwen3.6-27B</th><th style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0A2EFE;color:#0A2EFE;font-size: 14px;width:14.00%;">Qwen3.7-Plus</th><th style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0A2EFE;color:#0A2EFE;font-size: 14px;width:14.00%;">Muse Glimmer-30B</th><th style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0A2EFE;color:#0A2EFE;font-size: 14px;width:14.00%;">Opus4.6 Max</th></tr></thead>
<tbody>
<tr><td colspan="6" style="padding:8px 12px;font-weight:600;color:#0A2EFE;border-bottom:1px solid rgba(10, 46, 254, 0.2);background:#D6DAFC">Coding</td></tr>
<tr>
<td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Agentic terminal coding</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">Terminal Bench 2.1 (Terminus)</div></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;">73.0</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">63.4</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">64.0</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">51.7</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>78.2</strong></td>
</tr>
<tr>
<td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Agentic coding</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">SWE-bench Pro</div></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>61.7</strong></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">53.5</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">57.6</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">51.2</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">53.4</td>
</tr>
<tr>
<td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Repo-level code generation</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">NL2Repo-Bench</div></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;">42.3</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">36.2</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">41.1</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>47.6</strong></td>
</tr>
<tr>
<td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Agentic coding</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">DeepSWE 1.1</div></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>42.2</strong></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">13.3</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">14.2</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td>
</tr>
<tr>
<td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Software engineering</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">QwenSWEBench</div></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>79.0</strong></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">49.3</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">59.2</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">63.8</td>
</tr>
<tr><td colspan="6" style="padding:8px 12px;font-weight:600;color:#0A2EFE;border-bottom:1px solid rgba(10, 46, 254, 0.2);background:#D6DAFC">Agent</td></tr>
<tr>
<td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Long-horizon office work</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">CoWorkBench</div></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>70.7</strong></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">61.0</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">65.1</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">68.2</td>
</tr>
<tr>
<td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Professional job tasks</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">JobBench</div></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>33.4</strong></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">21.8</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">27.6</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td>
</tr>
<tr>
<td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Frontier agentic tasks</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">Agents' Last Exam</div></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Pass@1</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717"><strong>20.4</strong></div></div><div style="margin-top:7px"><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Score</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717"><strong>42.9</strong></div></div></div></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Pass@1</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">10.6</div></div><div style="margin-top:7px"><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Score</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">27.3</div></div></div></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Pass@1</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">13.2</div></div><div style="margin-top:7px"><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Score</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">33.6</div></div></div></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td>
</tr>
<tr><td colspan="6" style="padding:8px 12px;font-weight:600;color:#0A2EFE;border-bottom:1px solid rgba(10, 46, 254, 0.2);background:#D6DAFC">General</td></tr>
<tr>
<td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Instruction following</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">IFBench</div></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>79.5</strong></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">69.1</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">79.1</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">77.0</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">62.5</td>
</tr>
<tr>
<td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Scientific reasoning</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">GPQA Diamond</div></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;">89.2</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">87.8</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">90.3</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">83.5</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>91.3</strong></td>
</tr>
<tr>
<td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Multidisciplinary reasoning</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">HLE</div></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;">30.8</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">24.0</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">34.7</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">22.0</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>40.0</strong></td>
</tr>
<tr>
<td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Competitive coding</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">LiveCodeBench v6</div></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>90.3</strong></td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">83.9</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">89.6</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td>
<td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">88.8</td>
</tr>
</tbody>
</table>
<div style="margin-top:12px;font-size:11px;line-height:1.5;color:rgba(0,0,0,0.72)">
<ol style="margin:0;padding-left:20px">
<li>SWE-bench Pro: Except for Opus4.6 Max, which uses the officially reported score, all models are evaluated with the Claude Code harness at temp=1.0, top_p=0.95, and a 256K context window. Problematic tasks were corrected, and all baseline models were re-evaluated on the refined benchmark.</li>
<li>NL2Repo-Bench: Evaluated with the Claude Code harness. To prevent reward hacking, we disable Bash commands that attempt to access the specific repository, such as pip download, pip install, and git clone.</li>
<li>DeepSWE 1.1: Evaluated with the Claude Code harness at temp=1.0, top_p=0.95, and a 256K context window.</li>
<li>QwenSWEBench: In-house coding benchmark for evaluating models' software engineering capabilities. Evaluated with the Claude Code harness. Reporting avg@3 with an 8-hour timeout, max_tokens=32,768, temperature=1.0, and a 256K context window.</li>
<li>CoWorkBench: In-house cowork benchmark for evaluating long-horizon tasks across computer science, finance, law, medical, and other productivity domains.</li>
<li>HLE: Judged by GPT-4o.</li>
<li>The best result in each row is shown in bold.</li>
<li>Empty cells (--) indicate that results are not yet available or not applicable.</li>
</ol>
</div>
</div>

### VL Performance
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1200px;margin:0 auto;padding:16px 0">
<table class="vl-table" style="width:100%;table-layout:fixed;border-collapse:collapse;font-size:13px">
<thead><tr><th style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0A2EFE;color:#0A2EFE"></th><th style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0A2EFE;color:#0A2EFE;font-size: 14px;width:14.00%;background:rgba(10, 46, 254, 0.08);">Qwen3.8-27B</th><th style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0A2EFE;color:#0A2EFE;font-size: 14px;width:14.00%;">Qwen3.6-27B</th><th style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0A2EFE;color:#0A2EFE;font-size: 14px;width:14.00%;">Qwen3.7-Plus</th><th style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0A2EFE;color:#0A2EFE;font-size: 14px;width:14.00%;">Muse Glimmer-30B</th><th style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0A2EFE;color:#0A2EFE;font-size: 14px;width:14.00%;">Opus4.6 Max</th></tr></thead>
<tbody>
<tr><td colspan="6" style="padding:8px 12px;font-weight:600;color:#0A2EFE;border-bottom:1px solid rgba(10, 46, 254, 0.2);background:#D6DAFC">Agentic Multimodal Intelligence</td></tr>
<tr><td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Computer use</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">OSWorld-Verified</div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>84.3</strong></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">63.9</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">73.3</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">65.9</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">72.7</td></tr>
<tr><td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Browser use</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">WebArena-Verified</div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>64.8</strong></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">48.8</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">55.3</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td></tr>
<tr><td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Mobile use</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">AndroidWorld</div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>81.9</strong></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">70.3</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">81.0</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">62.0</td></tr>
<tr><td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Application recreation</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">RecreationBench</div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>47.1</strong></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">29.8</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">30.2</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td></tr>
<tr><td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Multimodal tool use</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">ClawEval-MM</div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Pass@3</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717"><strong>57.4</strong></div></div><div style="margin-top:7px"><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Average</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">56.9</div></div></div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Pass@3</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">42.6</div></div><div style="margin-top:7px"><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Average</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">50.4</div></div></div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Pass@3</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717"><strong>57.4</strong></div></div><div style="margin-top:7px"><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Average</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717"><strong>60.1</strong></div></div></div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Pass@3</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">52.5</div></div><div style="margin-top:7px"><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Average</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">54.7</div></div></div></td></tr>
<tr><td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Multimodal software engineering</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">SWE-MM</div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>38.6</strong></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">25.7</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">30.0</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">27.1</td></tr>
<tr><td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Visual web development</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">Vision2Web</div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>62.9</strong></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">45.0</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">42.1</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td></tr>
<tr><td colspan="6" style="padding:8px 12px;font-weight:600;color:#0A2EFE;border-bottom:1px solid rgba(10, 46, 254, 0.2);background:#D6DAFC">General Multimodal Intelligence</td></tr>
<tr><td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Visual math problem solving</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">MathVision</div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Without CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">90.0</div></div><div style="margin-top:7px"><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">With CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717"><strong>94.6</strong></div></div></div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Without CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">85.1</div></div></div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Without CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717"><strong>90.3</strong></div></div></div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Without CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">65.5</div></div></div></td></tr>
<tr><td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">General visual reasoning</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">BabyVision</div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Without CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717"><strong>65.7</strong></div></div><div style="margin-top:7px"><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">With CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717"><strong>85.6</strong></div></div></div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Without CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">28.9</div></div></div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Without CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">64.7</div></div><div style="margin-top:7px"><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">With CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">70.4</div></div></div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Without CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">12.6</div></div></div></td></tr>
<tr><td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Scientific chart analysis</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">CharXiv (RQ)</div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Without CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">83.7</div></div><div style="margin-top:7px"><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">With CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717"><strong>90.2</strong></div></div></div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Without CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">78.4</div></div></div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Without CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717"><strong>85.8</strong></div></div><div style="margin-top:7px"><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">With CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">85.9</div></div></div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">78.8</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><div class="metric-stack" style="padding:3px 0"><div><div class="metric-label" style="font-size:10px;font-weight:400;line-height:1.1;color:#777">Without CI</div><div class="metric-value" style="margin-top:2px;font-size:15px;line-height:1.15;color:#171717">66.0</div></div></div></td></tr>
<tr><td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Document intelligence</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">OmniDocBench 1.5</div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;">91.1</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">89.4</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>91.4</strong></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">75.8</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">86.6</td></tr>
<tr><td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Real-world perception</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">RealWorldQA</div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;">85.9</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">84.1</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>86.9</strong></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">73.9</td></tr>
<tr><td class="benchmark-cell" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15);"><div class="benchmark-capability" style="font-size:15px;font-weight:600;line-height:1.22;color:#171717">Embodied intelligence</div><div class="benchmark-name" style="margin-top:4px;font-size:11px;font-weight:400;line-height:1.2;color:#6B6B6B">ERQA</div></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);background:rgba(10, 46, 254, 0.08);vertical-align:middle;font-size:15px;line-height:1.2;">65.5</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">62.5</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;"><strong>69.8</strong></td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">--</td><td style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15);vertical-align:middle;font-size:15px;line-height:1.2;">40.8</td></tr>
</tbody>
</table>
<div style="margin-top:12px;font-size:11px;line-height:1.5;color:rgba(0,0,0,0.72)">
<ol style="margin:0;padding-left:20px">
<li>MathVision, BabyVision, and CharXiv (RQ): Where both settings are available, cells report “Without CI” and “With CI” separately; otherwise, only the available setting is shown. A small number of incorrect ground-truth annotations in MathVision and CharXiv (RQ) were corrected following manual verification, and all reported scores on those benchmarks were computed using the corrected annotations.</li>
<li>MathVision: Qwen3.8-27B is evaluated using the fixed prompt: “Please reason step by step, and put your final answer within <code>\boxed{}</code>.” For the remaining models, we report the higher score from two prompt variants—one with and one without the <code>\boxed{}</code> formatting requirement.</li>
<li>WebArena-Verified: Scores are computed with the official WebArena-Verified grader under the OSWorld scaffold.</li>
<li>RecreationBench: An in-house, long-horizon application-recreation benchmark designed to evaluate hybrid-agent capabilities across five platforms: desktop (Ubuntu, macOS, and Windows), mobile (Android), and the web.</li>
<li>ClawEval-MM: Scores are reported as “Pass@3 / average score.” Pass@3 is the percentage of tasks passed in at least one of three trials; the average score is the mean benchmark score across the three trials.</li>
<li>Vision2Web: Scores are averaged across the frontend, webpage, and website categories. Evaluations use the Claude Code harness and are judged by <code>gpt-5.4-2026-03-05</code>.</li>
<li>SWE-MM: Scores are evaluated on the Claude Code harness using the public dev split of SWE-bench Multimodal, with the modifications described in Appendix 8.3 of the Claude Opus 4.7 system card.</li>
<li>Empty cells (--) indicate that results are not yet available or not applicable.</li>
</ol></div>
</div>


## Quickstart

For streamlined integration, we recommend using Qwen3.8 via APIs.

### Serving Qwen3.8

> [!Important]
> Inference efficiency and throughput vary significantly across frameworks. 
> We recommend using the latest framework versions to ensure optimal performance and compatibility.
> For production workloads or high-throughput scenarios, dedicated serving engines such as SGLang, vLLM, or TokenSpeed are recommended.

Qwen3.8 can be deployed with popular inference frameworks, e.g.:

- [SGLang](https://www.sglang.io/): [Qwen3.8 Cookbook](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B)
- [vLLM](https://vllm.ai/): [Qwen3.8 Recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-27B)
- [TokenSpeed](https://lightseek.org/tokenspeed/): [Qwen3.8 Recipe](https://lightseek.org/tokenspeed/recipes/models#qwen3-8)


### API Usage

> [!Important]
> Qwen3.8 models operate in thinking mode by default, generating thinking content signified by `<think>\n...</think>\n\n` before producing the final response.
> To disable thinking content and obtain a direct response, refer to the examples [here](#instruct-or-non-thinking-mode).


> [!Tip]
> We recommend using the following sets of sampling parameters for generation:
> - Thinking Mode: `temperature=1.0`, `top_p=0.95`, `top_k=20`, `min_p=0.0`, `presence_penalty=0.0`, `repetition_penalty=1.0`
> - Instruct (or non-thinking) mode: `temperature=0.7`, `top_p=0.80`, `top_k=20`, `min_p=0.0`, `presence_penalty=1.5`, `repetition_penalty=1.0`
>
> Please note that the support for sampling parameters varies according to inference frameworks.


Qwen3.8 comes with official support for `reasoning_effort`, which can be used to adjust reasoning depth and control cost:  
  - `xhigh` (default): for complex tasks demanding thorough analysis
  - `medium`: balancing accuracy and speed
  - `low`: efficient reasoning optimizing for speed and cost


In addition, `preserve_thinking` is enabled by default for all workloads for the best out-of-the-box experience. To disable preserved thinking, refer to the examples [here](#disable-preserved-thinking).

> [!Tip]
> In multi-turn agentic tasks, lower reasoning effort does not always reduce overall task completion time. Although it may produce faster per-turn responses, it can also lead to insufficient analysis, more failures, and repeated retries, which may increase total latency and token consumption.


#### Chat Completions API

The Chat Completions API can be used with most inference frameworks, as well as [Qwen Cloud](https://www.qwencloud.com/).
Before starting, make sure the OpenAI Python SDK is installed and the API key and the API base URL are configured, e.g.:
```shell
pip install -U openai

# Set the following accordingly
export OPENAI_BASE_URL='your-base-url'
export OPENAI_API_KEY='your-api-key'
```

##### Text-Only Input

```python
from openai import OpenAI
# Configured by environment variables
client = OpenAI()

messages = [{"role": "user", "content": "Write a Python function to merge two sorted linked lists."}]

completion = client.chat.completions.create(
    model="Qwen/Qwen3.8-27B",
    messages=messages,
    extra_body={
        "chat_template_kwargs": {
            "enable_thinking": True,  # on by default
            "preserve_thinking": True, # on by default
        },
    },
    reasoning_effort="xhigh",  # xhigh by default; supported levels are xhigh, medium, and low
    stream=True,
    stream_options={"include_usage": True},
)

reasoning_content = ""
answer_content = ""
is_answering = False
print("\n" + "=" * 20 + "Reasoning" + "=" * 20 + "\n")

for chunk in completion:
    if not chunk.choices:
        print("\nUsage:")
        print(chunk.usage)
        continue

    delta = chunk.choices[0].delta

    if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
        if not is_answering:
            print(delta.reasoning_content, end="", flush=True)
        reasoning_content += delta.reasoning_content
    elif hasattr(delta, "reasoning") and delta.reasoning is not None:
        if not is_answering:
            print(delta.reasoning, end="", flush=True)
        reasoning_content += delta.reasoning

    if hasattr(delta, "content") and delta.content:
        if not is_answering:
            print("\n" + "=" * 20 + "Answer" + "=" * 20 + "\n")
            is_answering = True
        print(delta.content, end="", flush=True)
        answer_content += delta.content

messages.append({
    "role": "assistant",
    "content": answer_content,
    "reasoning_content": reasoning_content,
    "reasoning": reasoning_content,
})
```


##### Image Input

```python
from openai import OpenAI
# Configured by environment variables
client = OpenAI()

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://qianwen-res.oss-accelerate.aliyuncs.com/Qwen3.5/demo/CI_Demo/mathv-1327.jpg"
                }
            },
            {
                "type": "text",
                "text": "The centres of the four illustrated circles are in the corners of the square. The two big circles touch each other and also the two little circles. With which factor do you have to multiply the radii of the little circles to obtain the radius of the big circles?\nChoices:\n(A) $\\frac{2}{9}$\n(B) $\\sqrt{5}$\n(C) $0.8 \\cdot \\pi$\n(D) 2.5\n(E) $1+\\sqrt{2}$"
            }
        ]
    }
]

chat_response = client.chat.completions.create(
    model="Qwen/Qwen3.8-27B",
    messages=messages,
)
print("Chat response:", chat_response)
```

##### Video Input

```python
from openai import OpenAI
# Configured by environment variables
client = OpenAI()

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "video_url",
                "video_url": {
                    "url": "https://qianwen-res.oss-accelerate.aliyuncs.com/Qwen3.5/demo/video/N1cdUjctpG8.mp4"
                }
            },
            {
                "type": "text",
                "text": "How many porcelain jars were discovered in the niches located in the primary chamber of the tomb?"
            }
        ]
    }
]

chat_response = client.chat.completions.create(
    model="Qwen/Qwen3.8-27B",
    messages=messages,
)

# When vLLM is launched with `--media-io-kwargs '{"video": {"num_frames": -1}}'`,
# video frame sampling can be configured via `extra_body` (e.g., by setting `fps`).
# This feature is currently supported only in vLLM.
#
# By default, `fps=2` and `do_sample_frames=True`.
# With `do_sample_frames=True`, you can customize the `fps` value to set your desired video sampling rate.
# chat_response = client.chat.completions.create(
#     model="Qwen/Qwen3.8-27B",
#     messages=messages,
#     extra_body={
#         "mm_processor_kwargs": {"fps": 2, "do_sample_frames": True},
#     }, 
# )

print("Chat response:", chat_response)
```


##### Instruct (or Non-Thinking) Mode

Qwen3.8-27B will think by default before responding.
You can obtain a direct response from the model without thinking by configuring the API parameters. 
For example,
```python
from openai import OpenAI
# Configured by environment variables
client = OpenAI()

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://qianwen-res.oss-accelerate.aliyuncs.com/Qwen3.5/demo/RealWorld/RealWorld-04.png"
                }
            },
            {
                "type": "text",
                "text": "Where is this?"
            }
        ]
    }
]

chat_response = client.chat.completions.create(
    model="Qwen/Qwen3.8-27B",
    messages=messages,
    temperature=0.7,
    top_p=0.8,
    presence_penalty=1.5,
    extra_body={
        "top_k": 20,
        "chat_template_kwargs": {"enable_thinking": False},
    }, 
)
print("Chat response:", chat_response)
```

> [!Note]
> If you are using APIs from Qwen Cloud, in addition to changing `model`, please use `"enable_thinking": False` instead of `"chat_template_kwargs": {"enable_thinking": False}`.


##### Disable Preserved Thinking


By default, Qwen3.8 retains thinking blocks from all historical messages, maintaining a complete reasoning trace across the conversation. This behavior, known as preserved thinking, ensures full context continuity and is especially beneficial for agent scenarios where decision consistency and reduced redundant reasoning are critical. It also improves KV cache utilization, optimizing inference efficiency in both thinking and non-thinking modes.

If you prefer to retain only the thinking blocks from the latest user message, you can disable this behavior by setting `preserve_thinking` to `False`:

```python
from openai import OpenAI

# Configured by environment variables
client = OpenAI()
messages = [...]
chat_response = client.chat.completions.create(
    model="Qwen/Qwen3.8-27B",
    messages=messages,
    extra_body={
        "chat_template_kwargs": {"preserve_thinking": False},
    },
)
print("Chat response:", chat_response)
```

> [!Note]
> If you are using APIs from Qwen Cloud, in addition to changing `model`, please use `"preserve_thinking": False` directly instead of wrapping it in `chat_template_kwargs`.


## Best Practices

To achieve optimal performance, we recommend the following settings:

1. **Sampling Parameters**: We suggest using the following sets of sampling parameters:  
    
    - Thinking Mode: `temperature=1.0`, `top_p=0.95`, `top_k=20`, `min_p=0.0`, `presence_penalty=0.0`, `repetition_penalty=1.0`
    - Instruct (or non-thinking) mode: `temperature=0.7`, `top_p=0.80`, `top_k=20`, `min_p=0.0`, `presence_penalty=1.5`, `repetition_penalty=1.0`
    
    For supported frameworks, you can adjust the `presence_penalty` parameter between 0 and 2 to reduce endless repetition. However, using a higher value may occasionally result in language mixing and a slight decrease in model performance.

2. **Adequate Output Length**: To optimize performance on agentic tasks, we recommend allocating sufficient output length to allow the model to generate detailed and comprehensive responses. For frameworks that support separate token limits for internal reasoning and final outputs, we suggest the following configuration within the 1M context length:
    
    - Reasoning Content: Set the maximum output length to 262,144 tokens.
    - Final Response: Set the maximum output length to 131,072 tokens.

    These settings provide the necessary capacity for complex reasoning while ensuring ample space for high-quality final deliverables.

3. **Processing Ultra-Long Texts**: Qwen3.8-27B natively supports context lengths of up to 262,144 tokens. For long-horizon tasks where the total length (including both input and output) exceeds this limit, we recommend using RoPE scaling techniques to handle long texts effectively, e.g., YaRN.

    YaRN is currently supported by several inference frameworks, e.g., vLLM, SGLang, and TokenSpeed. 
    In general, there are two approaches to enabling YaRN for supported frameworks:

    - Modifying the model configuration file:
        
        In the `config.json` file, change the `rope_parameters` fields in `text_config` to:
        ```json
        {
            "mrope_interleaved": true,
            "mrope_section": [
                11,
                11,
                10
            ],
            "rope_type": "yarn",
            "rope_theta": 10000000,
            "partial_rotary_factor": 0.25,
            "factor": 4.0,
            "original_max_position_embeddings": 262144,
        }
        ```

    - Passing command line arguments:

        For vLLM, you can use
        ```shell
        VLLM_ALLOW_LONG_MAX_MODEL_LEN=1 vllm serve ... --hf-overrides '{"text_config": {"rope_parameters": {"mrope_interleaved": true, "mrope_section": [11, 11, 10], "rope_type": "yarn", "rope_theta": 10000000, "partial_rotary_factor": 0.25, "factor": 4.0, "original_max_position_embeddings": 262144}}}' --max-model-len 1000000  
        ```

        For SGLang, you can use
        ```shell
        SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1 python -m sglang.launch_server ... --json-model-override-args '{"text_config": {"rope_parameters": {"mrope_interleaved": true, "mrope_section": [11, 11, 10], "rope_type": "yarn", "rope_theta": 10000000, "partial_rotary_factor": 0.25, "factor": 4.0, "original_max_position_embeddings": 262144}}}' --context-length 1000000
        ```

        For TokenSpeed, you can use
        ```shell
        TOKENSPEED_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1 tokenspeed serve ... --hf-overrides '{"text_config": {"rope_parameters": {"mrope_interleaved": true, "mrope_section": [11, 11, 10], "rope_type": "yarn", "rope_theta": 10000000, "partial_rotary_factor": 0.25, "factor": 4.0, "original_max_position_embeddings": 262144}}}' --max-model-len 1000000  
        ```
    
    > [!NOTE]
    > All the notable open-source frameworks implement static YaRN, which means the scaling factor remains constant regardless of input length, **potentially impacting performance on shorter texts.**
    > We advise modifying the `rope_parameters` configuration only when processing long contexts is required. 
    > It is also recommended to modify the `factor` as needed. For example, if the typical context length for your application is 524,288 tokens, it would be better to set `factor` as 2.0. 


4. **Long Video Understanding**: To optimize inference efficiency for plain text and images, the `size` parameter in the released `video_preprocessor_config.json` is conservatively configured. It is recommended to set the `longest_edge` parameter in the video_preprocessor_config file to 469,762,048 (corresponding to 224k video tokens) to enable higher frame-rate sampling for hour-scale videos and thereby achieve superior performance. For example,
    ```json
    {"longest_edge": 469762048, "shortest_edge": 4096}
    ```

    Alternatively, override the default values via engine startup parameters. For implementation details, refer to: [vLLM](https://github.com/vllm-project/vllm/pull/34330) / [SGLang](https://github.com/sgl-project/sglang/pull/18467).


## Citation

If you find our work helpful, feel free to give us a cite.


```bibtex
@misc{qwen38,
    title = {{Qwen3.8-Max}: A New Bar for Coding and Cowork},
    url = {https://qwen.ai/blog?id=qwen3.8},
    author = {{Qwen Team}},
    month = {August},
    year = {2026}
}
```
