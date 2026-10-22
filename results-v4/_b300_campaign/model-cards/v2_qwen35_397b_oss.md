---
pipeline_tag: text-generation
base_model:
- Qwen/Qwen3.5-397B-A17B
license: apache-2.0
library_name: Model Optimizer
tags:
- nvidia
- ModelOpt
- Qwen3.5
- quantized
- FP4
- fp4
---

# Model Overview

## Description:
The NVIDIA Qwen3.5-397B-A17B NVFP4 model is the quantized version of Alibaba's Qwen3.5-397B-A17B model, which is an auto-regressive language model that uses an optimized transformer architecture. For more information, please check [here](https://huggingface.co/Qwen/Qwen3.5-397B-A17B). The NVIDIA Qwen3.5-397B-A17B NVFP4 model is quantized with [Model Optimizer](https://github.com/NVIDIA/Model-Optimizer).

This model is ready for commercial/non-commercial use.  <br>

## Third-Party Community Consideration
This model is not owned or developed by NVIDIA. This model has been developed and built to a third-party’s requirements for this application and use case; see link to Non-NVIDIA [(Qwen3.5-397B-A17B) Model Card](https://huggingface.co/Qwen/Qwen3.5-397B-A17B).

### License/Terms of Use:
[Apache license 2.0](https://huggingface.co/datasets/choosealicense/licenses/blob/main/markdown/apache-2.0.md)

### Deployment Geography:
Global <br>

### Use Case: <br>
Developers looking to take off-the-shelf, pre-quantized models for deployment in AI Agent systems, chatbots, RAG systems, and other AI-powered applications. <br>

### Release Date:  <br>
Huggingface 02/17/2026 via https://huggingface.co/nvidia/Qwen3.5-397B-A17B-NVFP4 <br>

## Model Architecture:
**Architecture Type:** Transformers  <br>
**Network Architecture:** Qwen3.5-397B-A17B <br>
**Number of Model Parameters:** 397B in total and 17B activated <br>

## Input:
**Input Type(s):** Text, Image, Video <br>
**Input Format(s):** String, Red, Green, Blue (RGB), Video (MP4/WebM) <br>
**Input Parameters:** One-Dimensional (1D), Two-Dimensional (2D), Three-Dimensional (3D) <br>
**Other Properties Related to Input:** Context length up to 262K <br>

## Output:
**Output Type(s):** Text <br>
**Output Format:** String <br>
**Output Parameters:** 1D (One-Dimensional): Sequences <br>
**Other Properties Related to Output:** N/A <br>

Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA’s hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions. <br>

## Software Integration:
**Supported Runtime Engine(s):** <br>
* SGLang <br>
* vLLM <br>

**Supported Hardware Microarchitecture Compatibility:** <br>
* NVIDIA Blackwell <br>

**Preferred Operating System(s):** <br>
* Linux <br>

## Model Version(s):
The model is quantized with nvidia-modelopt **v0.42.0**  <br>

## Training, Testing, and Evaluation Datasets:

## Calibration Dataset:
** Link: [cnn_dailymail](https://huggingface.co/datasets/abisee/cnn_dailymail), [Nemotron-Post-Training-Dataset-v2](https://huggingface.co/datasets/nvidia/Nemotron-Post-Training-Dataset-v2) <br>
** Data Collection Method by dataset: Automated. <br>
** Labeling method: Automated. <br>
** Properties: The cnn_dailymail dataset is an English-language dataset containing just over 300k unique news articles as written by journalists at CNN and the Daily Mail. <br>

## Training Dataset:
** Data Modality: Undisclosed <br>
** Data Collection Method by dataset: Undisclosed <br>
** Labeling Method by dataset: Undisclosed<br>
** Properties: Undisclosed

## Testing Dataset:
** Data Collection Method by dataset: Undisclosed <br>
** Labeling Method by dataset: Undisclosed <br>
** Properties: Undisclosed <br>

## Evaluation Dataset:
** Data Collection Method by dataset: Hybrid: Human, Automated <br>
** Labeling Method by dataset: Hybrid: Human, Automated <br>
** Properties: We evaluated the model on benchmarks including GPQA, which is a dataset of 448 multiple-choice questions written by domain experts in biology, physics, and chemistry. <br>


## Inference:
**Engine:** SGLang <br>
**Test Hardware:** B200 <br>

## Post Training Quantization
This model was obtained by quantizing the weights and activations of Qwen3.5-397B-A17B to NVFP4 data type, ready for inference with SGLang. Only the weights and activations of the linear operators within transformer blocks in MoE are quantized.

## Usage

To serve this checkpoint with [SGLang](https://github.com/sgl-project/sglang), you can start the docker `lmsysorg/sglang:v0.5.9` and run the sample command below:

```sh
python3 -m sglang.launch_server --model nvidia/Qwen3.5-397B-A17B-NVFP4 --tensor-parallel-size 4 --quantization modelopt_fp4 --trust-remote-code
```

To serve this checkpoint with [vLLM](https://github.com/vllm-project/vllm), you can start the docker image `vllm/vllm-openai:latest` and run [the sample command (for GB200)](https://docs.vllm.ai/projects/recipes/en/latest/Qwen/Qwen3.5.html#gb200-deployment) below:

```sh
vllm serve nvidia/Qwen3.5-397B-A17B-NVFP4 \
  -dp 4 \
  --enable-expert-parallel \
  --language-model-only \
  --reasoning-parser qwen3 \
  --enable-prefix-caching
```

### Evaluation
The accuracy benchmark results are presented in the table below:
<table>
  <tr>
   <td><strong>Precision</strong>
   </td>
   <td><strong>MMLU Pro</strong>
   </td>
   <td><strong>GPQA Diamond</strong>
   </td>
   <td><strong>LiveCodeBench V6</strong>
   </td>
   <td><strong>SciCode</strong>
   </td>
   <td><strong>AIME 2025</strong>
   </td>
   <td><strong>AA-LCR</strong>
   </td>
   <td><strong>IFBench</strong>
   </td>
  </tr>
  <tr>
   <td>FP8
   </td>
   <td><strong>0.883</strong>
   </td>
   <td><strong>0.871</strong>
   </td>
   <td><strong>0.837</strong>
   </td>
   <td><strong>0.467</strong>
   </td>
   <td><strong>0.918</strong>
   </td>
   <td><strong>0.696</strong>
   </td>
   <td><strong>0.761</strong>
   </td>
  </tr>
  <tr>
   <td>NVFP4
   </td>
   <td><strong>0.880</strong>
   </td>
   <td><strong>0.871</strong>
   </td>
   <td><strong>0.843</strong>
   </td>
   <td><strong>0.479</strong>
   </td>
   <td><strong>0.922</strong>
   </td>
   <td><strong>0.701</strong>
   </td>
   <td><strong>0.756</strong>
   </td>
  </tr>
  <tr>
</table>

> Baseline: [Qwen3.5-397B-A17B-FP8](https://huggingface.co/Qwen/Qwen3.5-397B-A17B-FP8).
> Benchmarked with temperature=0.6, top_p=0.95, max num tokens 64000

## Model Limitations:
The base model was trained on data that contains toxic language and societal biases originally crawled from the internet. Therefore, the model may amplify those biases and return toxic responses especially when prompted with toxic prompts. The model may generate answers that may be inaccurate, omit key information, or include irrelevant or redundant text producing socially unacceptable or undesirable text, even if the prompt itself does not include anything explicitly offensive.

## Ethical Considerations

NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications.  When downloaded or used in accordance with our terms of service, developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://app.intigriti.com/programs/nvidia/nvidiavdp/detail).
