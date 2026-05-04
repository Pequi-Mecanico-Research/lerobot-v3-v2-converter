"""Convert a LeRobot dataset from codebase v3.0 to v2.1.

Wraps the upstream NVIDIA Isaac-GR00T converter (vendored as ``_nvidia_convert``)
with three additions:

- A compatibility shim for ``lerobot`` >= 0.5.x, which moved
  ``load_info`` / ``load_tasks`` / ``write_info`` from ``datasets/utils`` to
  ``datasets/io_utils``. Without the shim, the upstream import fails on 0.5.x.
- Preservation of ``meta/modality.json`` (an extra metadata file used by
  GR00T) across the conversion. The upstream converter does not copy it.
- Explicit ``--input`` / ``--output`` arguments. When ``--output`` is given,
  the input directory is left untouched.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import lerobot.datasets.utils as _utils

try:
    import lerobot.datasets.io_utils as _io_utils

    for _sym in ("load_info", "load_tasks", "write_info"):
        if not hasattr(_utils, _sym) and hasattr(_io_utils, _sym):
            setattr(_utils, _sym, getattr(_io_utils, _sym))
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _nvidia_convert import convert_dataset  # noqa: E402

from lerobot.utils.utils import init_logging  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a LeRobot dataset directory from codebase v3.0 to v2.1.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the v3.0 dataset directory.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Path where the v2.1 dataset will be written. "
            "If omitted, the conversion runs in place and a v3.0 backup is "
            "written next to the input."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output directory if it already exists.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    init_logging()

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
        force_conversion=args.force,
    )

    if modality_backup is not None:
        restored = target / "meta" / "modality.json"
        restored.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(modality_backup, restored)
        modality_backup.unlink()

    backup = target.parent / f"{target.name}_v3.0"
    print()
    print("Conversion complete.")
    print(f"  v2.1 output : {target}")
    print(f"  v3.0 backup : {backup}")


if __name__ == "__main__":
    main()
