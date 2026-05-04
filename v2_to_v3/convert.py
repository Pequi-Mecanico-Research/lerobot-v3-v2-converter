"""Convert a LeRobot dataset from codebase v2.1 to v3.0.

Wraps the upstream Hugging Face LeRobot converter (vendored as
``_hf_convert``) with three additions:

- A compatibility shim for ``lerobot`` 0.5.x. The vendored upstream
  code imports several symbols from ``lerobot.datasets.utils`` that
  were moved to ``lerobot.datasets.io_utils`` in 0.5.x. The shim
  mirrors any missing symbols from ``io_utils`` back onto ``utils``
  before the upstream module is imported, so the same code runs on
  both 0.4.x and 0.5.x.
- Preservation of ``meta/modality.json`` (an extra metadata file used by
  GR00T) across the conversion. The upstream converter does not copy it.
- Explicit ``--input`` / ``--output`` arguments. When ``--output`` is given,
  the input directory is left untouched. ``--push-to-hub`` is disabled
  by default; the upstream default is the opposite.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import lerobot.datasets.utils as _utils

try:
    import lerobot.datasets.io_utils as _io_utils

    for _sym in dir(_io_utils):
        if not _sym.startswith("_") and not hasattr(_utils, _sym):
            setattr(_utils, _sym, getattr(_io_utils, _sym))
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _hf_convert import convert_dataset  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a LeRobot dataset directory from codebase v2.1 to v3.0.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the v2.1 dataset directory.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Path where the v3.0 dataset will be written. "
            "If omitted, the conversion runs in place and a v2.1 backup is "
            "written next to the input as ``<name>_old``."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output directory if it already exists.",
    )
    parser.add_argument(
        "--push-to-hub",
        action="store_true",
        help=(
            "Push the converted dataset to the Hugging Face Hub. "
            "Requires that the input directory name matches a Hub ``repo_id`` "
            "and that you are authenticated."
        ),
    )
    parser.add_argument(
        "--data-file-size-mb",
        type=int,
        default=None,
        help="Override the v3.0 data shard size (MB).",
    )
    parser.add_argument(
        "--video-file-size-mb",
        type=int,
        default=None,
        help="Override the v3.0 video shard size (MB).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_dir = Path(args.input).expanduser().resolve()
    if not input_dir.is_dir():
        sys.exit(f"Input directory does not exist: {input_dir}")

    if args.output is None:
        target = input_dir
    else:
        target = Path(args.output).expanduser().resolve()
        if target.exists():
            if not args.force:
                sys.exit(
                    f"Output directory already exists: {target} (use --force to overwrite)."
                )
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(input_dir, target)

    modality_src = target / "meta" / "modality.json"
    modality_backup: Path | None = None
    if modality_src.is_file():
        modality_backup = target.parent / f".{target.name}.modality.json.bak"
        shutil.copy(modality_src, modality_backup)

    convert_dataset(
        repo_id=target.name,
        root=str(target.parent),
        push_to_hub=args.push_to_hub,
        force_conversion=args.force,
        data_file_size_in_mb=args.data_file_size_mb,
        video_file_size_in_mb=args.video_file_size_mb,
    )

    if modality_backup is not None:
        restored = target / "meta" / "modality.json"
        restored.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(modality_backup, restored)
        modality_backup.unlink()

    backup = target.parent / f"{target.name}_old"
    print()
    print("Conversion complete.")
    print(f"  v3.0 output : {target}")
    print(f"  v2.1 backup : {backup}")


if __name__ == "__main__":
    main()
