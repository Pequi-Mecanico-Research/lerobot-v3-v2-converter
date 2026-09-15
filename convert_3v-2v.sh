#!/bin/bash

uv pip install -r requirements.txt

uv run v3_to_v2/convert.py \
  --input  /path/to/dataset_v30 \
  --output /path/to/dataset_v21 \
  --push-to-hub /path/to/repo_id