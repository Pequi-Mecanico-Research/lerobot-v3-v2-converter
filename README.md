# lerobot-v3-v2-converter

Two-way LeRobot dataset format converter between codebase **v2.1** and
**v3.0**. Targets the gap where downstream tools and frameworks
(e.g. NVIDIA GR00T) still consume v2.1, while `lerobot record` on
recent releases writes v3.0.

## Install

```bash
pip install -r requirements.txt
```

`ffmpeg` must be available on `PATH`. Both converters call it to
re-segment videos.

Compatible with `lerobot` 0.4.x and 0.5.x.

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

## Features

- **Both directions** in a single repo: `v3_to_v2/` and `v2_to_v3/`.
- **`lerobot` 0.4.x and 0.5.x compatibility, both directions**. Both
  upstream converters import `load_info` / `load_tasks` / `write_info`
  from `lerobot.datasets.utils`. In 0.5.x those symbols moved to
  `lerobot.datasets.io_utils`, breaking import. Each wrapper applies a
  small module-level shim that mirrors any missing symbol from
  `io_utils` back onto `utils`, so the same upstream code runs on both
  versions unchanged.
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

## Verified

Round-trip (`v3.0 → v2.1 → v3.0`) on a 30-episode / ~15k-frame
single-camera SO-ARM101 dataset, run on **`lerobot` 0.4.1 and 0.5.2**.
The final v3.0 dataset matches the original v3.0 input on every
checked property:

| check                                  | result      |
|----------------------------------------|-------------|
| `info.json` codebase / counts / config | identical   |
| `data/*.parquet` total rows            | identical   |
| video total frame count (`ffprobe`)    | identical   |
| `meta/episodes/*.parquet` total rows   | identical   |
| `meta/tasks.parquet`                   | byte-equal  |
| `meta/modality.json`                   | byte-equal  |

A public 90-episode SO-ARM101 wrist-only dataset shipped in LeRobot v3.0
format (and convertible to v2.1 with this tool) is available at
[`dongyoonkim/so101-eraser-90ep-wrist`](https://huggingface.co/datasets/dongyoonkim/so101-eraser-90ep-wrist).

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
