"""devcontainer-gen: deterministic devcontainer.json generator for Python, Node, and Go."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

__all__ = [
    "DEFAULT_TABLE",
    "Detection",
    "DevcontainerError",
    "ImageSpec",
    "Stack",
    "__version__",
    "detect_stacks",
    "generate",
    "render",
]

__version__ = "0.1.0"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

ErrorCode = Literal["no_stack", "file_too_large", "invalid_option", "exists"]
StackName = Literal["python", "node", "go"]

MAX_FILE_BYTES = 65_536


class DevcontainerError(Exception):
    """Base exception raised by devcontainer_gen."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code: ErrorCode = code
        self.message: str = message


@dataclass(frozen=True)
class Stack:
    """Detected runtime stack."""

    name: StackName
    version: str
    lockfile: str | None


@dataclass(frozen=True)
class Detection:
    """Result of detecting stacks from marker and version files."""

    stacks: list[Stack]
    warnings: list[str]


@dataclass(frozen=True)
class ImageSpec:
    """Image, feature, extension, and command template for a language runtime."""

    image: str
    feature: str
    default_version: str
    extension: str
    install: Mapping[str | None, str]


DEFAULT_TABLE: Mapping[str, ImageSpec] = {
    "python": ImageSpec(
        image="mcr.microsoft.com/devcontainers/python:1-{version}-bookworm",
        feature="ghcr.io/devcontainers/features/python:1",
        default_version="3.12",
        extension="ms-python.python",
        install={
            "pyproject.toml": "python -m pip install -e .",
            "setup.py": "python -m pip install -e .",
            "requirements.txt": "python -m pip install -r requirements.txt",
            None: "python -m pip install -e .",
        },
    ),
    "node": ImageSpec(
        image="mcr.microsoft.com/devcontainers/typescript-node:1-{version}-bookworm",
        feature="ghcr.io/devcontainers/features/node:1",
        default_version="20",
        extension="dbaeumer.vscode-eslint",
        install={
            "package-lock.json": "npm ci",
            "pnpm-lock.yaml": "corepack enable && pnpm install --frozen-lockfile",
            None: "npm install",
        },
    ),
    "go": ImageSpec(
        image="mcr.microsoft.com/devcontainers/go:1-{version}-bookworm",
        feature="ghcr.io/devcontainers/features/go:1",
        default_version="1.22",
        extension="golang.go",
        install={
            "go.mod": "go mod download",
            None: "go mod download",
        },
    ),
}


_GO_VERSION_PATTERN = re.compile(r"^\s*go\s+(\d+\.\d+)(?:\.\d+)?", re.MULTILINE)
_NODE_VERSION_PATTERN = re.compile(r"^v?(\d+)(?:\.\d+)?(?:\.\d+)?")
_PY_VERSION_PATTERN = re.compile(r"^(\d+\.\d+)(?:\.\d+)?")


def _clean_text(text: str) -> str:
    if text.startswith("\ufeff"):
        text = text[1:]
    return text.replace("\r\n", "\n").replace("\r", "\n")


def detect_stacks(files: Mapping[str, str]) -> Detection:
    """Detect runtime stacks from root-level file contents."""
    for name, content in files.items():
        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
            raise DevcontainerError(
                "file_too_large",
                f"File '{name}' exceeds size limit of {MAX_FILE_BYTES} bytes",
            )

    cleaned_files: dict[str, str] = {k: _clean_text(v) for k, v in files.items()}
    warnings: list[str] = []
    stacks: list[Stack] = []

    # Python detection
    has_pyproject = "pyproject.toml" in cleaned_files
    has_setup_py = "setup.py" in cleaned_files
    has_reqs = "requirements.txt" in cleaned_files
    if has_pyproject or has_setup_py or has_reqs:
        py_lock: str | None = None
        if has_pyproject:
            py_lock = "pyproject.toml"
        elif has_setup_py:
            py_lock = "setup.py"
        elif has_reqs:
            py_lock = "requirements.txt"

        py_version = DEFAULT_TABLE["python"].default_version
        if ".python-version" in cleaned_files:
            lines = [line.strip() for line in cleaned_files[".python-version"].split("\n")]
            non_empty = [ln for ln in lines if ln]
            if non_empty:
                m = _PY_VERSION_PATTERN.match(non_empty[0])
                if m:
                    py_version = m.group(1)
                else:
                    warnings.append(".python-version: unsupported value, using " + py_version)

        stacks.append(Stack(name="python", version=py_version, lockfile=py_lock))

    # Node detection
    if "package.json" in cleaned_files:
        has_npm_lock = "package-lock.json" in cleaned_files
        has_pnpm_lock = "pnpm-lock.yaml" in cleaned_files
        node_lock: str | None = None
        if has_pnpm_lock and has_npm_lock:
            warnings.append("both package-lock.json and pnpm-lock.yaml found; using pnpm")
            node_lock = "pnpm-lock.yaml"
        elif has_pnpm_lock:
            node_lock = "pnpm-lock.yaml"
        elif has_npm_lock:
            node_lock = "package-lock.json"

        node_version = DEFAULT_TABLE["node"].default_version
        if ".nvmrc" in cleaned_files:
            first_line = cleaned_files[".nvmrc"].strip().split("\n")[0].strip()
            m = _NODE_VERSION_PATTERN.match(first_line)
            if m:
                node_version = m.group(1)
            else:
                warnings.append(".nvmrc: unsupported value, using " + node_version)

        stacks.append(Stack(name="node", version=node_version, lockfile=node_lock))

    # Go detection
    if "go.mod" in cleaned_files:
        go_content = cleaned_files["go.mod"]
        go_version = DEFAULT_TABLE["go"].default_version
        m = _GO_VERSION_PATTERN.search(go_content)
        if m:
            go_version = m.group(1)
        stacks.append(Stack(name="go", version=go_version, lockfile=None))

    return Detection(stacks=stacks, warnings=warnings)


def generate(
    stacks: Sequence[Stack],
    *,
    name: str = "dev",
    forward_ports: Sequence[int] = (),
    table: Mapping[str, ImageSpec] = DEFAULT_TABLE,
) -> dict[str, Any]:
    """Generate a devcontainer.json configuration dictionary from detected stacks."""
    if not stacks:
        raise DevcontainerError("no_stack", "No stacks provided for devcontainer generation")

    if not (1 <= len(name) <= 64 and all(c.isprintable() for c in name)):
        raise DevcontainerError(
            "invalid_option",
            f"Container name '{name}' must be 1-64 printable characters",
        )

    ports_list: list[int] = []
    for p in forward_ports:
        if not isinstance(p, int) or p < 1 or p > 65535:
            raise DevcontainerError(
                "invalid_option",
                f"Port {p} is invalid; must be an integer between 1 and 65535",
            )
        ports_list.append(p)

    primary_stack = stacks[0]
    if primary_stack.name not in table:
        raise DevcontainerError(
            "invalid_option",
            f"Unknown stack name '{primary_stack.name}' in table",
        )
    primary_spec = table[primary_stack.name]
    image_url = primary_spec.image.format(version=primary_stack.version)

    features: dict[str, dict[str, str]] = {}
    for secondary in stacks[1:]:
        if secondary.name not in table:
            raise DevcontainerError(
                "invalid_option",
                f"Unknown stack name '{secondary.name}' in table",
            )
        sec_spec = table[secondary.name]
        features[sec_spec.feature] = {"version": secondary.version}

    commands: list[str] = []
    extensions: list[str] = []

    for s in stacks:
        spec = table[s.name]
        if spec.extension and spec.extension not in extensions:
            extensions.append(spec.extension)

        # Resolve install command
        cmd = spec.install.get(s.lockfile)
        if cmd is None:
            cmd = spec.install.get(None)
        if cmd:
            commands.append(cmd)

    post_create_command = " && ".join(commands)

    result: dict[str, Any] = {
        "name": name,
        "image": image_url,
        "features": features,
        "postCreateCommand": post_create_command,
        "customizations": {"vscode": {"extensions": extensions}},
    }

    if ports_list:
        result["forwardPorts"] = ports_list

    return result


def render(config: dict[str, Any]) -> str:
    """Render devcontainer configuration dictionary as indented JSON text."""
    # Key order: name, image, features, postCreateCommand, customizations, forwardPorts
    ordered: dict[str, Any] = {}
    preferred_keys = ["name", "image", "features", "postCreateCommand", "customizations"]
    for key in preferred_keys:
        if key in config:
            ordered[key] = config[key]

    if config.get("forwardPorts"):
        ordered["forwardPorts"] = config["forwardPorts"]

    for k, v in config.items():
        if k not in ordered:
            ordered[k] = v

    return json.dumps(ordered, indent=2, ensure_ascii=False) + "\n"
