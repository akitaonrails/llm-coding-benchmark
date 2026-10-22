---
pipeline_tag: image-text-to-text
base_model:
- Qwen/Qwen3.8-Flash-Next
license: other
license_name: nvidia-open-model-license
library_name: Model Optimizer
tags:
- nvidia
- ModelOpt
- Qwen3.8
- quantized
- FP4
- fp4
---

# Model Overview

## Description:
The NVIDIA Qwen3.8-Flash-Next NVFP4 model is the quantized version of Alibaba's Qwen3.8-Flash-Next model, which is an auto-regressive language model that uses an optimized transformer architecture. Qwen3.8-Flash-Next is a causal language model with a vision encoder, hybrid attention (Gated DeltaNet and Qwen Sparse Attention), Mixture-of-Experts, gated residual streams, and n-gram embeddings. For more information, please check [here](https://huggingface.co/Qwen/Qwen3.8-Flash-Next). The NVIDIA Qwen3.8-Flash-Next NVFP4 model is quantized with [Model Optimizer](https://github.com/NVIDIA/Model-Optimizer).

This model is ready for commercial or non-commercial use.  <br>

## Third-Party Community Consideration
This model is not owned or developed by NVIDIA. This model has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA [(Qwen3.8-Flash-Next) Model Card](https://huggingface.co/Qwen/Qwen3.8-Flash-Next) from Qwen.

### License/Terms of Use:
Governing Terms: Use of this model is governed by the [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/).

**ADDITIONAL INFORMATION** : [Qwen Community License 1.0](https://huggingface.co/Qwen/Qwen3.8-Flash-Next/blob/main/LICENSE). **Qwen3.8-Flash-Next** .

### Deployment Geography:
Global <br>

### Use Case: <br>
Developers looking to take off-the-shelf, pre-quantized models for deployment in AI Agent systems, chatbots, RAG systems, and other AI-powered applications. <br>

### Release Date:  <br>
Hugging Face 08/31/2026 via https://huggingface.co/nvidia/Qwen3.8-Flash-Next-NVFP4 <br>

## Evaluation
The accuracy benchmark results are presented in the table below:
<table>
  <tr>
   <td><strong>Precision</strong>
   </td>
   <td><strong>GPQA Diamond</strong>
   </td>
   <td><strong>HLE</strong>
   </td>
   <td><strong>τ²-Bench Telecom</strong>
   </td>
   <td><strong>MMMU Pro</strong>
   </td>
   <td><strong>SciCode</strong>
   </td>
   <td><strong>AA-LCR</strong>
   </td>
   <td><strong>IFBench</strong>
   </td>
   <td><strong>Omniscience</strong>
   </td>
   <td><strong>Terminal-Bench 2.1</strong>
   </td>
  </tr>
  <tr>
   <td>FP8
   </td>
   <td><strong>92.0</strong>
   </td>
   <td><strong>34.7</strong>
   </td>
   <td><strong>90.8</strong>
   </td>
   <td><strong>77.1</strong>
   </td>
   <td><strong>16.3</strong>
   </td>
   <td><strong>71.9</strong>
   </td>
   <td><strong>80.5</strong>
   </td>
   <td><strong>28.1</strong>
   </td>
   <td><strong>83.3</strong>
   </td>
  </tr>
  <tr>
   <td>NVFP4
   </td>
   <td><strong>91.5</strong>
   </td>
   <td><strong>35.4</strong>
   </td>
   <td><strong>90.1</strong>
   </td>
   <td><strong>78.3</strong>
   </td>
   <td><strong>18.8</strong>
   </td>
   <td><strong>74.1</strong>
   </td>
   <td><strong>81.0</strong>
   </td>
   <td><strong>27.6</strong>
   </td>
   <td><strong>82.9</strong>
   </td>
  </tr>
</table>


> Baseline: [Qwen3.8-Flash-Next-FP8](https://huggingface.co/Qwen/Qwen3.8-Flash-Next-FP8). Benchmarked with temperature=1.0, top_p=0.95, max_new_tokens=131072, and reasoning_effort=xhigh.

## References
NVIDIA Model Optimizer: https://github.com/NVIDIA/Model-Optimizer

## Model Architecture:
**Architecture Type:** Transformers  <br>
**Network Architecture:** Hybrid Attention (Gated DeltaNet and Qwen Sparse Attention) with Mixture-of-Experts (`Qwen4ExpForConditionalGeneration`) <br>
**Number of Model Parameters:** 125B in total and 6B activated, plus 51B n-gram embedding and 4B MTP <br>
**This model was developed based on [Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)** <br>

## Input:
**Input Type(s):** Text, Image, Video <br>
**Input Format(s):** String, Red, Green, Blue (RGB), Video (MP4/WebM) <br>
**Input Parameters:** One-Dimensional (1D), Two-Dimensional (2D), Three-Dimensional (3D) <br>
**Other Properties Related to Input:** Context length up to 262K natively and extensible up to 1,000,000 tokens. <br>

## Output:
**Output Type(s):** Text <br>
**Output Format:** String <br>
**Output Parameters:** One-Dimensional (1D): Sequences <br>
**Other Properties Related to Output:** None <br>

Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions. <br>

## Software Integration:
**Supported Runtime Engine(s):** <br>
* **vLLM** <br>

**Post-Training Quantization Toolkit:** <br>
* [NVIDIA Model Optimizer](https://github.com/NVIDIA/Model-Optimizer) v0.46.0 with [Transformers v5.16.0](https://github.com/huggingface/transformers/releases/tag/v5.16.0) or later for upstream Qwen4-Exp support <br>

**Supported Hardware Microarchitecture Compatibility:** <br>
* NVIDIA Blackwell B200 <br>
* NVIDIA Blackwell B300 <br>

**Preferred Operating System(s):** <br>
* Linux <br>

The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.

## Model Version(s):
The model version is NVFP4 1.0 and was produced with nvidia-modelopt **v0.46.0**. <br>

## Training and Evaluation Datasets:

## Calibration Dataset:
**Link:** [cnn_dailymail](https://huggingface.co/datasets/abisee/cnn_dailymail), [Nemotron-Post-Training-Dataset-v2](https://huggingface.co/datasets/nvidia/Nemotron-Post-Training-Dataset-v2) <br>
**Data Modality:** Text <br>
**Data Collection Method by dataset:** Automated. <br>
**Labeling Method by dataset:** Automated. <br>
**Properties:** The cnn_dailymail dataset is an English-language dataset containing just over 300k unique news articles as written by journalists at CNN and the Daily Mail. The Nemotron-Post-Training-Dataset-v2 is a post-training dataset curated by NVIDIA containing multi-turn conversations across diverse topics. <br>

## Training Dataset:
**Data Modality:** Undisclosed <br>
**Data Collection Method by dataset:** Undisclosed <br>
**Labeling Method by dataset:** Undisclosed <br>
**Properties:** Undisclosed<br>
**Image Training Data Size:** Undisclosed<br>
**Text Training Data Size:** Undisclosed<br>
**Video Training Data Size:** Undisclosed<br>

## Evaluation Dataset:
**Datasets:** GPQA Diamond, HLE, τ²-Bench Telecom, MMMU Pro, SciCode, AA-LCR, IFBench, Omniscience, Terminal-Bench 2.1 <br>
**Data Collection Method by dataset:** Hybrid: Automated, Manually-Collected <br>
**Labeling Method by dataset:** Hybrid: Manually-Labeled, Automated <br>
**Properties:** We evaluated the model on text-based reasoning, coding, agentic tool-use, and multimodal benchmarks: GPQA Diamond contains 448 graduate-level multiple-choice questions written by domain experts in biology, physics, and chemistry. HLE (Humanity's Last Exam) is an expert-level academic benchmark with 2158 text-only questions across mathematics, humanities and the natural sciences. τ²-Bench Telecom evaluates agentic tool-use and policy-adherence capabilities in dual-control telecom customer-service scenarios where the model interacts with a simulated user and external tools to resolve account issues. MMMU Pro is the more challenging version of the Massive Multi-discipline Multimodal Understanding benchmark, measuring college-level multimodal reasoning across diverse disciplines with expanded answer choices and a vision-only input setting. SciCode evaluates scientific coding capabilities. AA-LCR (Artificial Analysis Long Context Recall) evaluates a model's ability to accurately retrieve and recall information from long input contexts. IFBench evaluates instruction-following capabilities across diverse and structured task constraints. Omniscience evaluates broad factual knowledge and reasoning. Terminal-Bench 2.1 evaluates agentic coding performance in realistic terminal environments. <br>

## Inference:
**Acceleration Engine:** **vLLM** <br>
**Test Hardware:** **NVIDIA Blackwell B200 and B300** <br>

## Post Training Quantization
This is a mixed-precision checkpoint. The routed MoE expert linear layers in the main language model use W4A4 NVFP4 with MSE-calibrated weight scales. Attention layers, shared experts, and other main-model layers remain in BF16. The MTP routed experts use 128x128 block-scaled FP8, and the PLE n-gram embedding uses per-tensor FP8. The resulting checkpoint is approximately 2.7x smaller than the BF16 source checkpoint (about a 63% reduction in disk size).

The main language model's routed experts were quantized directly from [Qwen/Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next). The complete MTP module and PLE n-gram embedding match [Qwen/Qwen3.8-Flash-Next-FP8](https://huggingface.co/Qwen/Qwen3.8-Flash-Next-FP8) byte-for-byte. The FP8 MTP routed-expert tensors and PLE tensors were copied from that checkpoint; the remaining BF16 MTP tensors were already identical between the BF16 and FP8 sources and did not require replacement. No fine-tuning was performed.

## Usage

The checkpoint combines NVFP4 routed experts with an FP8 PLE n-gram embedding. Serving without MTP requires [vLLM commit `d4d703caf908786416585ceb1f369e2e0363358b`](https://github.com/vllm-project/vllm/commit/d4d703caf908786416585ceb1f369e2e0363358b) or a later upstream commit. MTP speculative decoding additionally requires [vLLM PR #55513](https://github.com/vllm-project/vllm/pull/55513) until that fix is merged upstream.

Run the sample command below from a compatible vLLM environment or container:

```sh
vllm serve nvidia/Qwen3.8-Flash-Next-NVFP4 \
    --tensor-parallel-size 8 \
    --quantization modelopt \
    --max-model-len 262144 \
    --reasoning-parser qwen3 \
    --trust-remote-code
```

To enable MTP speculative decoding on eight GPUs, use expert parallelism so the MTP expert width remains compatible with its 128x128 FP8 blocks:

```sh
vllm serve nvidia/Qwen3.8-Flash-Next-NVFP4 \
    --tensor-parallel-size 8 \
    --enable-expert-parallel \
    --quantization modelopt \
    --max-model-len 262144 \
    --speculative-config '{"method":"mtp","num_speculative_tokens":1}' \
    --reasoning-parser qwen3 \
    --trust-remote-code \
    --no-enable-flashinfer-autotune
```

## Model Limitations:
The base model was trained on data that contains toxic language and societal biases originally crawled from the internet. Therefore, the model may amplify those biases and return toxic responses especially when prompted with toxic prompts. The model may generate answers that may be inaccurate, omit key information, or include irrelevant or redundant text producing socially unacceptable or undesirable text, even if the prompt itself does not include anything explicitly offensive.

## Ethical Considerations

NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. Developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

Please make sure you have proper rights and permissions for all input image and video content; if image or video includes people, personal health information, or intellectual property, the image or video generated will not blur or maintain proportions of image subjects included.

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).
