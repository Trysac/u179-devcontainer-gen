"""CLI entry point for devcontainer-gen."""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from devcontainer_gen import (
    DEFAULT_TABLE,
    MAX_FILE_BYTES,
    DevcontainerError,
    detect_stacks,
    generate,
    render,
)

MARKER_NAMES = (
    "pyproject.toml",
    "setup.py",
    "requirements.txt",
    ".python-version",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    ".nvmrc",
    "go.mod",
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run devcontainer-gen CLI."""
    parser = argparse.ArgumentParser(
        prog="devcontainer-gen",
        description="Generate devcontainer.json for Python, Node, and Go projects",
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--name",
        default="dev",
        help="Container name (default: dev)",
    )
    parser.add_argument(
        "--port",
        dest="ports",
        type=int,
        action="append",
        default=[],
        help="Port to forward (repeatable)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing .devcontainer/devcontainer.json",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print rendered configuration to stdout instead of writing file",
    )

    args = parser.parse_args(argv)
    root_path = Path(args.root).resolve()

    # Collect marker files
    files: dict[str, str] = {}
    for marker in MARKER_NAMES:
        marker_file = root_path / marker
        if marker_file.is_file():
            try:
                raw = marker_file.read_bytes()
            except OSError as err:
                sys.stderr.write(f"error: failed to read {marker}: {err}\n")
                return 1
            if len(raw) > MAX_FILE_BYTES:
                sys.stderr.write(f"error: {marker} exceeds size limit of {MAX_FILE_BYTES} bytes\n")
                return 1
            files[marker] = raw.decode("utf-8", errors="replace")

    try:
        detection = detect_stacks(files)
        for warning in detection.warnings:
            sys.stderr.write(f"warning: {warning}\n")

        config = generate(
            detection.stacks,
            name=args.name,
            forward_ports=args.ports,
            table=DEFAULT_TABLE,
        )
        output_text = render(config)
    except DevcontainerError as err:
        sys.stderr.write(f"error: {err.message}\n")
        return 1

    if args.stdout:
        sys.stdout.write(output_text)
        return 0

    target_dir = root_path / ".devcontainer"
    target_file = target_dir / "devcontainer.json"

    if target_file.exists() and not args.force:
        sys.stderr.write("error: .devcontainer/devcontainer.json exists (use --force)\n")
        return 2

    target_dir.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path_str = tempfile.mkstemp(dir=target_dir, prefix=".devcontainer_", suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(output_text)
        os.replace(tmp_path_str, target_file)
    except Exception as exc:
        with contextlib.suppress(OSError):
            os.remove(tmp_path_str)
        sys.stderr.write(f"error: failed to write target file: {exc}\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
