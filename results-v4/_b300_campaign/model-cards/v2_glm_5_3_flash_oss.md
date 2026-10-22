---
language:
- en
- zh
library_name: transformers
pipeline_tag: image-text-to-text
tags:
- nvfp4
- fp4
- vllm
- llm-compressor
- compressed-tensors
- glm5_next
base_model: zai-org/GLM-5.3-Flash
license: mit
---

# GLM-5.3-Flash-NVFP4

## Model Overview
- **Model Architecture:** Glm5NextForConditionalGeneration
  - **Input:** Text / Image
  - **Output:** Text
- **Model Optimizations:**
  - **Weight quantization:** FP4
  - **Activation quantization:** FP4
- **Release Date:** 2026-08-27
- **Version:** 1.0
- **Model Developers:** RedHatAI

This model is a quantized version of [zai-org/GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash).
It was evaluated on several tasks to assess its quality.

### Model Optimizations

This model was obtained by quantizing the MoE expert weights and activations of [zai-org/GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash) to FP4 (NVFP4) data type, ready for inference with vLLM. The MTP layers are kept in FP8, matching the source checkpoint.

This optimization reduces the number of bits per parameter in the quantized layers from 8 to 4, reducing the disk size and GPU memory requirements by approximately 50% of the quantized weights.

Only the weights and activations of the MoE expert linear operators are quantized using [LLM Compressor](https://github.com/vllm-project/llm-compressor).

## Deployment

### vLLM Serving

```bash
docker run --gpus all \
  --privileged --ipc=host -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -e VLLM_ENGINE_READY_TIMEOUT_S=3600 \
  vllm/vllm-openai:glm53-flash RedHatAI/GLM-5.3-Flash-NVFP4 \
  --tensor-parallel-size 4 \
  --no-enable-flashinfer-autotune \
  --tool-call-parser glm47 \
  --enable-auto-tool-choice \
  --reasoning-parser glm45
```

### Enable Speculative Decoding

```
docker run --gpus all \
  --privileged --ipc=host -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -e VLLM_ENGINE_READY_TIMEOUT_S=3600 \
  -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
  vllm/vllm-openai:glm53-flash RedHatAI/GLM-5.3-Flash-NVFP4 \
  --tensor-parallel-size 4 \
  --no-enable-flashinfer-autotune \
  --tool-call-parser glm47 \
  --enable-auto-tool-choice \
  --reasoning-parser glm45 \
  --gpu-memory-utilization 0.85 \
  --disable-custom-all-reduce \
  --speculative-config '{"method":"mtp","num_speculative_tokens":5}'
```

## Creation

This model was created by applying [LLM Compressor](https://github.com/vllm-project/llm-compressor) with the NVFP4 scheme, exported in compressed-tensors format.

## Evaluation

This model was evaluated on GSM8K Platinum, MATH-500, AIME 2025, and GPQA Diamond using [lm-evaluation-harness](https://github.com/neuralmagic/lm-evaluation-harness) and [lighteval](https://github.com/neuralmagic/lighteval), all served with vLLM (OpenAI-compatible API). Each benchmark was run with 3 seeds (8 seeds for AIME 2025) and the results averaged.

### Accuracy

<table>
  <thead>
    <tr>
      <th>Category</th>
      <th>Benchmark</th>
      <th>RedHatAI/GLM-5.3-Flash-NVFP4</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="4"><b>Reasoning</b></td>
      <td>GSM8K Platinum (strict-match)</td>
      <td>97.74%</td>
    </tr>
    <tr>
      <td>MATH-500 (pass@1)</td>
      <td>94.87%</td>
    </tr>
    <tr>
      <td>AIME 2025 (pass@1)</td>
      <td>86.67%</td>
    </tr>
    <tr>
      <td>GPQA Diamond (pass@1)</td>
      <td>90.57%</td>
    </tr>
  </tbody>
</table>