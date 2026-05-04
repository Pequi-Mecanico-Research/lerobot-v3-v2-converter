# lerobot-v3-v2-converter

Two-way LeRobot dataset format converter between codebase **v2.1** and
**v3.0**. Targets the gap where downstream tools and frameworks
(e.g. NVIDIA GR00T) still consume v2.1, while `lerobot record` on
recent releases writes v3.0.

## Features

- **Both directions** in a single repo: `v3_to_v2/` and `v2_to_v3/`.
- **`lerobot` 0.5.x compatibility for v3 → v2**. The upstream NVIDIA
  Isaac-GR00T converter is written against `lerobot` 0.4.x. On 0.5.x
  it fails at import because `load_info` / `load_tasks` / `write_info`
  moved from `datasets/utils.py` to `datasets/io_utils.py`. This
  wrapper applies a small module-level shim that restores those names,
  so the upstream code works unchanged on both 0.4.x and 0.5.x.
- **`modality.json` is preserved**. GR00T datasets carry an extra
  `meta/modality.json` describing state / action / video keys. Neither
  upstream converter copies it through. This wrapper backs it up
  before and restores it after the conversion, in both directions.
- **Explicit `--input` / `--output`**. Upstream converters run in
  place. Here, when `--output` is given, the input directory is left
  untouched.
- **Vendored, no extra clone**. The actual conversion logic is
  vendored into this repo with the original Apache 2.0 headers
  preserved. You only need to clone this repo. See `NOTICE` for
  upstream sources, commits, and versions.

## Install

```bash
pip install -r requirements.txt
```

`ffmpeg` must be available on `PATH`. Both converters call it to
re-segment videos.

## Usage

### v3.0 → v2.1

```bash
python v3_to_v2/convert.py \
  --input  /path/to/dataset_v30 \
  --output /path/to/dataset_v21
```

In place (input becomes v2.1, `<name>_v3.0` backup is written next to it):

```bash
python v3_to_v2/convert.py --input /path/to/dataset
```

### v2.1 → v3.0

```bash
python v2_to_v3/convert.py \
  --input  /path/to/dataset_v21 \
  --output /path/to/dataset_v30
```

In place (input becomes v3.0, `<name>_old` backup is written next to it):

```bash
python v2_to_v3/convert.py --input /path/to/dataset
```

`--push-to-hub` is off by default in this wrapper; the upstream v2 → v3
default is the opposite. Pass `--push-to-hub` explicitly to upload the
converted dataset to the Hugging Face Hub (requires the input directory
name to match a Hub `repo_id` and an authenticated session).

## Layout

```
lerobot-v3-v2-converter/
├── v3_to_v2/
│   ├── convert.py            # CLI wrapper
│   └── _nvidia_convert.py    # vendored: NVIDIA Isaac-GR00T converter
├── v2_to_v3/
│   ├── convert.py            # CLI wrapper
│   └── _hf_convert.py        # vendored: Hugging Face LeRobot converter
├── README.md
├── LICENSE                    # Apache 2.0
├── NOTICE                     # third-party attributions
├── .gitignore
└── requirements.txt
```

## License

Apache License 2.0. See `LICENSE`. Vendored upstream files retain their
original Apache 2.0 headers; see `NOTICE` for source URLs and pinned
commit / version.
