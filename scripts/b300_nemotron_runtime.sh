#!/bin/bash
set -euo pipefail
umask 077
if test ! -x /usr/local/cuda-13.0/bin/nvcc; then
  curl -fL --retry 2 --max-time 180 -o /root/cuda130.run https://developer.download.nvidia.com/compute/cuda/13.0.0/local_installers/cuda_13.0.0_580.65.06_linux.run
  sh /root/cuda130.run --silent --toolkit --override --no-man-page
fi
if test ! -x /root/venv-nemotron032/bin/vllm; then
  uv venv /root/venv-nemotron032
  uv pip install --python /root/venv-nemotron032/bin/python 'https://wheels.vllm.ai/3f1bcfd82bb2e93fcd364fc7a5491718453a77e2/vllm-0.32.0rc1.dev190%2Bg3f1bcfd82-cp38-abi3-manylinux_2_28_x86_64.whl' cohere-melody==0.15.2
fi
uv pip freeze --python /root/venv-nemotron032/bin/python > /root/logs/nemotron032-packages.txt
