#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v ffmpeg >/dev/null; then
  echo "ffmpeg not found on PATH. Install it with: sudo apt install ffmpeg" >&2
  exit 1
fi

uv pip install -r requirements.txt

uv run v3_to_v2/convert.py \
  --input  /home/guilherme/Documents/GitHub/PequiMecanico/VLA_stack/modules/lerobot-v3-v2-converter/dataset/wxai_organize_table_inf_base \
  --output /home/guilherme/Documents/GitHub/PequiMecanico/VLA_stack/modules/lerobot-v3-v2-converter/dataset/wxai_organize_table_inf_base_output \
  --push-to-hub Guilhermefrazao/wxai_organize_table_inf_base "$@"
