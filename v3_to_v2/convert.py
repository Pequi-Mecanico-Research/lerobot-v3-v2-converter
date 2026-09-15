"""Convert a LeRobot dataset from codebase v3.0 to v2.1.

Wraps the upstream NVIDIA Isaac-GR00T converter (vendored as ``_nvidia_convert``)
with three additions:

- A compatibility shim for ``lerobot`` 0.5.x. The upstream code imports
  several symbols from ``lerobot.datasets.utils`` that were moved to
  ``lerobot.datasets.io_utils`` in 0.5.x. The shim mirrors any missing
  symbols from ``io_utils`` back onto ``utils`` before the upstream
  module is imported, so the same code runs on both 0.4.x and 0.5.x.
- Preservation of ``meta/modality.json`` (an extra metadata file used by
  GR00T) across the conversion. The upstream converter does not copy it.
- Explicit ``--input`` / ``--output`` arguments. When ``--output`` is given,
  the input directory is left untouched.
- Optional ``--push-to-hub REPO_ID``. When given, the converted v2.1 dataset
  is uploaded to the Hugging Face Hub after conversion, using raw
  ``HfApi`` calls (not ``LeRobotDataset.push_to_hub``). Every ``lerobot``
  release on PyPI (0.4.0 through at least 0.6.1) hardcodes
  ``CODEBASE_VERSION = "v3.0"`` and refuses to even load a v2.1 local
  dataset (``BackwardCompatibilityError``), so ``LeRobotDataset.push_to_hub``
  cannot be used here regardless of which ``lerobot`` version is installed.
  Uploading the folder directly and creating the ``v2.1`` tag ourselves
  sidesteps that check.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from huggingface_hub import HfApi

import lerobot.datasets.utils as _utils

try:
    import lerobot.datasets.io_utils as _io_utils

    for _sym in dir(_io_utils):
        if not _sym.startswith("_") and not hasattr(_utils, _sym):
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
    parser.add_argument(
        "--push-to-hub",
        dest="push_to_hub",
        default=None,
        metavar="REPO_ID",
        help=(
            "If set, upload the converted v2.1 dataset to this Hugging Face Hub "
            "dataset repo id (e.g. 'username/my-dataset') after conversion."
        ),
    )
    return parser.parse_args()


def push_dataset_to_hub(root: Path, repo_id: str) -> None:
    """Upload the converted v2.1 dataset at ``root`` to the Hub and tag it.

    Deliberately does not use ``LeRobotDataset.push_to_hub``: that method
    first instantiates a ``LeRobotDataset``, which raises
    ``BackwardCompatibilityError`` for a v2.1 local dataset on every
    ``lerobot`` release currently on PyPI (their ``CODEBASE_VERSION`` is
    already ``v3.0``). Uploading the folder and creating the version tag
    directly via ``HfApi`` avoids that check and works regardless of the
    installed ``lerobot`` version.
    """
    version_tag = json.loads((root / "meta" / "info.json").read_text())["codebase_version"]

    api = HfApi()
    api.create_repo(repo_id=repo_id, repo_type="dataset", exist_ok=True)
    api.upload_folder(repo_id=repo_id, repo_type="dataset", folder_path=str(root))
    api.create_tag(repo_id, tag=version_tag, repo_type="dataset")


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

    if args.push_to_hub is not None:
        print()
        print(f"Uploading dataset to the Hugging Face Hub: {args.push_to_hub}")
        push_dataset_to_hub(target, args.push_to_hub)


if __name__ == "__main__":
    main()
