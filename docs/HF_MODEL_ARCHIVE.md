# Hugging Face model archive

The reusable local archive is `/mnt/gigachad/huggingface/archives/`. Future
downloads and serving trials must first check the pinned files there. Reuse a
verified checkpoint when model, revision and quantization match, without
downloading it again. Preserve the archive copy if a test needs a staged copy
elsewhere. When a newly tested model proves useful for future testing or
serving, keep its weights here and record its source, pinned revision,
quantization, verification status and test evidence. Never delete archive
weights, partial downloads, manifests or provenance from the NAS without the
user's explicit approval, including for cleanup or disk-space recovery. Each
subdirectory has a `manifest.json` with the exact upstream revision, selected
files, expected sizes and a per-model `verified` status. The `download.py` in
each subdirectory resumes incomplete files and verifies their sizes. Read the
manifest before treating a path as complete.

The long-running transfer supervisor writes
`/mnt/gigachad/huggingface/archives/download-status.json` and
`supervisor.log`. A stalled transfer is retried after ten minutes without
progress. Large files use `http_download.py`: pinned Hugging Face CDN byte
ranges are journaled so an interrupted transfer can resume, and each finished
file is checked against its upstream SHA-256. This replaced Xet for large
files after repeated stalls on SC117. The fallback was validated by
interrupting and resuming a 4.1 GB SC117 file, then checking its full hash;
the evidence is in `http-download-verification.json` in the archive root.
For a readable live snapshot, run `watch -n 10 python3
/mnt/gigachad/huggingface/archives/status.py` in a terminal.
If the machine restarts, resume the main batch with `python3
/mnt/gigachad/huggingface/archives/supervise_downloads.py`. Resume the
Experiential batch separately with `python3
/mnt/gigachad/huggingface/archives/supervise_downloads.py --only-stage
experiential-uncensored --status-path
/mnt/gigachad/huggingface/archives/experiential-uncensored/download-status.json`.
Check each status file before starting a supervisor so there is only one
supervisor per batch. The archive is preserved on the NAS; the current Strata
service is independent of these transfers.

## Uncensored Qwen3.8 Flash-Next variants

`/mnt/gigachad/huggingface/archives/uncensored-qwen-flash-next/` contains the
specific Strata options discussed on 2026-10-22: Alesha's IQ3_S plus switchable
refusal-direction vector, SC117 IQ3_S, RVN IQ3_S, OrcaRouter IQ3_XXS, and
DatKurai Coder IQ1_M. The manifest selects the relevant quantizations rather
than every quantization in those upstream repositories. Alesha's IQ3_S shards
are unchanged from the ISTA-DASLab vanilla quant; with the control vector off,
those files also serve as the vanilla Qwen3.8 Flash-Next IQ3_S archive.

## Official Flash and local models

`/mnt/gigachad/huggingface/archives/flash-and-local/` contains these pinned
checkpoints:

| Folder | Source | Why kept |
|---|---|---|
| `glm-5_3-flash/` | `zai-org/GLM-5.3-Flash` | Full official GLM Flash checkpoint |
| `deepseek-v4_1-flash/` | `deepseek-ai/DeepSeek-V4.1-Flash` | Original official V4.1 Flash checkpoint |
| `deepseek-v4_1-flash-1017/` | `deepseek-ai/DeepSeek-V4.1-Flash-1017` | Latest discussed V4.1 Flash revision, separate weights |
| `minimax-m3_1-flash/` | `MiniMaxAI/MiniMax-M3.1-Flash` | Full official M3.1 Flash checkpoint |
| `kimi-k3/` | `moonshotai/Kimi-K3` | Full official K3 checkpoint |
| `qwen3_8-flash-next-gyro-s/` | `agentionai/Qwen3.8-Flash-Next-Gyro-GGUF` | Discussed 5090 speed candidate, Gyro-S quant |
| `qwen3_8-27b-q8_0-strix/` | `unsloth/Qwen3.8-27B-GGUF` | Q8_0 quant used for the completed Strix Halo v4 run |
| `qwen3_6-35b-q3_k_m-5090/` | `bartowski/Qwen_Qwen3.6-35B-A3B-GGUF` | Q3_K_M GGUF named in the 5090 serving configuration for the best completed earlier local model |

As of 2026-10-23, no official downloadable **DeepSeek V4.1 Pro**, separate
**MiniMax M3.1 non-Flash**, or **Kimi K3 Flash** checkpoint was found. Those
names are recorded as unavailable in the archive manifest, rather than
silently substituting older or unrelated models. The archived official
checkpoints are sources for future serving; being downloaded does not mean
they fit a single 5090 or have passed a local benchmark.

The local-selection evidence is in [Strata serving](strata-serving.md), the
[v4 local campaign summary](../results-v4/_local_campaign/summary.json),
[v4 per-model report](success_report.v4.per_model.md), and the
[earlier 5090 subset](success_report.nvidia.md). We excluded locally completed
models with clearly poor benchmark results, such as GLM-4.7-Flash on the 5090.

## Uncensored DeepSeek V4.1 Flash

`/mnt/gigachad/huggingface/archives/uncensored-deepseek-v4_1/` queues the
full FP8 checkpoints from
[`dealignai/DeepSeek-V4.1-Flash-UNCENSORED-FP8`](https://huggingface.co/dealignai/DeepSeek-V4.1-Flash-UNCENSORED-FP8)
and its [1017 successor](https://huggingface.co/dealignai/DeepSeek-V4.1-Flash-1017-UNCENSORED-FP8).
Each is about 510 GB. Venice identifies dealignai as the maker of its
`deepseek-v4-1-flash-uncensored` API model; it does not publish the exact
Hugging Face commit used in production, so the archive records that provenance
limit. These are separate from the vanilla DeepSeek checkpoints above.

## Experiential uncensored model links

The [Experiential model catalog](https://platform.experientiallabs.ai/models)
lists four uncensored releases with public Hugging Face weights. Its
[DeepSeek V4.1 Flash 1017 Uncensored](https://platform.experientiallabs.ai/models/deepseek-v4.1-flash-uncensored)
links to the dealignai 1017 checkpoint queued above. The other three pinned
checkpoints are queued in
`/mnt/gigachad/huggingface/archives/experiential-uncensored/`:

| Model page | Hugging Face checkpoint | Approximate size |
|---|---|---:|
| [GLM-5.3 Uncensored](https://platform.experientiallabs.ai/models/glm-5.3-uncensored) | [`dealignai/GLM-5.3-UNCENSORED-FP8`](https://huggingface.co/dealignai/GLM-5.3-UNCENSORED-FP8) | 756 GB |
| [GLM-5.3 Flash Uncensored](https://platform.experientiallabs.ai/models/glm-5.3-flash-uncensored) | [`dealignai/GLM-5.3-Flash-UNCENSORED-FP8`](https://huggingface.co/dealignai/GLM-5.3-Flash-UNCENSORED-FP8) | 328 GB |
| [MiMo-V2.6 Flash Uncensored](https://platform.experientiallabs.ai/models/mimo-v2.6-flash-uncensored) | [`dealignai/MiMo-V2.6-Flash-RL-UNCENSORED`](https://huggingface.co/dealignai/MiMo-V2.6-Flash-RL-UNCENSORED) | 178 GB |

The Experiential batch runs concurrently with the main archive batch and has
its own `download-status.json` and `supervisor.log` in its directory. Both
statuses appear in the archive `status.py` summary.

These model pages identify the source repositories, but do not expose the
exact commit served by the API. The archive pins the Hugging Face revisions
observed on 2026-10-23. Check each batch manifest for `verified` before using
its weights.
