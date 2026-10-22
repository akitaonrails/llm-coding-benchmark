#!/usr/bin/env bash
# v4.2 mode (b): synthetic saturation ramp via `vllm bench serve`.
# RUN ON THE POD against http://localhost:8000 (so the cloudflared tunnel is not the bottleneck).
# Usage: run_bench_ramp.sh <model_tag> [served_model_name] [venv]
#   model_tag         = output label, e.g. deepseek_v4_1_flash | glm_5_3_flash
#   served_model_name = the --served-model-name vLLM is answering as (default: $model_tag)
#   venv              = python venv whose `vllm` CLI to use (default: /root/vllm-next-venv)
# Reads the API key from /root/.llmkey into ENV (never echoed, never in argv of a key-dumping cmd).
# Coding-shaped load: long-ish input (growing v4 context), medium output. Tune via env below.
set -uo pipefail

MODEL_TAG="${1:?model_tag required}"
SERVED="${2:-$MODEL_TAG}"
VENV="${3:-/root/vllm-next-venv}"
# tokenizer source: the served name is NOT an HF repo, so bench must load the local
# tokenizer to synthesize/count random prompts. Pass the local model dir as 4th arg.
TOKENIZER="${4:-$SERVED}"
export HF_HUB_OFFLINE=1
BENCH="$VENV/bin/vllm"
BASE="http://localhost:8000"
OUT="/root/v4.2_results/$MODEL_TAG"
mkdir -p "$OUT"

# coding-shaped length profile (override via env). Input big to mimic accumulated v4 context.
IN_LEN="${IN_LEN:-8000}"
OUT_LEN="${OUT_LEN:-800}"
RANGE="${RANGE:-0.6}"            # +/- spread so prompts vary like real turns
# SLO: TTFT 2s, TPOT 20ms/token
GOODPUT="${GOODPUT:-ttft:2000 tpot:20}"
# concurrency ramp; extend until goodput collapses
LEVELS="${LEVELS:-1 2 4 8 16 24 32 48}"
# prompts per level: ~6x concurrency so the steady state dominates warmup
PPC="${PPC:-6}"

export VLLM_API_KEY="$(cat /root/.llmkey)"   # key stays in env only
export OPENAI_API_KEY="$VLLM_API_KEY"

echo "[ramp] model=$SERVED venv=$VENV in=$IN_LEN out=$OUT_LEN goodput='$GOODPUT' -> $OUT"
"$BENCH" bench serve --help >/dev/null 2>&1 || { echo "ERROR: '$BENCH bench serve' unavailable — check venv/version"; exit 2; }

for N in $LEVELS; do
  NUM=$(( N * PPC ))
  echo "=== concurrency $N  (num_prompts $NUM)  $(date -u +%H:%M:%S) ==="
  # NOTE: verify flag names against `$BENCH bench serve --help` first (versions drift).
  "$BENCH" bench serve \
    --backend openai-chat \
    --base-url "$BASE" \
    --endpoint /v1/chat/completions \
    --model "$SERVED" \
    --tokenizer "$TOKENIZER" \
    --dataset-name random \
    --random-input-len "$IN_LEN" \
    --random-output-len "$OUT_LEN" \
    --random-range-ratio "$RANGE" \
    --num-prompts "$NUM" \
    --max-concurrency "$N" \
    --goodput $GOODPUT \
    --percentile-metrics ttft,tpot,itl,e2el \
    --metric-percentiles 50,95,99 \
    --save-result --result-dir "$OUT" --result-filename "bench_c${N}.json" \
    2>&1 | tee "$OUT/bench_c${N}.log"
  echo "--- done c$N ---"
done
echo "[ramp] complete -> $OUT"
