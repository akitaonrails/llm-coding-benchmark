#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_KEY="${QWEN36_API_KEY:-}"
API_BASE="${LOCAL_API_BASE:-http://localhost:8000}"
MODEL="${LOCAL_MODEL:-qwen3_6_35b_a3b_q8_ik_llamacpp}"
RESULTS_DIR="${LOCAL_RESULTS_DIR:-results-local-qwen36}"
REPORT="${LOCAL_REPORT:-docs/report.local_qwen36.md}"
OPENCODE_CONFIG="${LOCAL_OPENCODE_CONFIG:-config/opencode.benchmark.local_qwen36.json}"

if [[ -z "$API_KEY" ]]; then
  echo "Error: QWEN36_API_KEY is not set." >&2
  exit 1
fi

if ! command -v opencode >/dev/null 2>&1; then
  echo "Error: opencode is not installed or not on PATH." >&2
  exit 1
fi

mkdir -p "${REPO_ROOT}/$(dirname "$OPENCODE_CONFIG")"

python3 - "$API_BASE" "$API_KEY" "$REPO_ROOT/$OPENCODE_CONFIG" <<'PYEOF'
import json, os, sys
api_base, api_key, out_path = sys.argv[1:4]
config = {
    "$schema": "https://opencode.ai/config.json",
    "provider": {
        "llamacpp": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "ik_llama.cpp (localhost)",
            "options": {
                "baseURL": api_base.rstrip("/") + "/v1",
                "apiKey": api_key,
            },
            "models": {
                "Qwen3.6-35B-A3B": {
                    "name": "Qwen3.6-35B-A3B (ik_llama.cpp)",
                    "limit": {"context": 131072, "output": 8192},
                }
            }
        }
    }
}
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(config, f, indent=2)
    f.write("\n")
print(f"Wrote {out_path}")
PYEOF

echo "Running benchmark for $MODEL against ik_llama.cpp at $API_BASE"

OPENCODE_CONFIG="${REPO_ROOT}/${OPENCODE_CONFIG}" \
python3 "${REPO_ROOT}/scripts/run_benchmark.py" \
  --config "${REPO_ROOT}/config/models.local_ik_llamacpp.json" \
  --opencode-config "${REPO_ROOT}/${OPENCODE_CONFIG}" \
  --results-dir "${REPO_ROOT}/${RESULTS_DIR}" \
  --report "${REPO_ROOT}/${REPORT}" \
  --model "$MODEL" \
  --timeout-minutes 120
