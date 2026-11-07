# devcontainer-gen

Deterministic `devcontainer.json` generator for Python, Node, and Go projects. Automatically detects runtime stacks from project marker files and generates valid container configurations.

## Installation

```bash
pip install devcontainer-gen
```

## Usage Example

```python
from devcontainer_gen import detect_stacks, generate, render

files = {"pyproject.toml": "[project]\nname = 'demo'\n", ".python-version": "3.12.4"}
detection = detect_stacks(files)
# Generate configuration, default stack uses Python image
config = generate(detection.stacks, forward_ports=[8000])
print(render(config))
```

## Public API Summary

- **Functions**:
  - `detect_stacks(files: Mapping[str, str]) -> Detection`: Analyzes file content to identify stacks.
  - `generate(stacks: Sequence[Stack], *, name: str = 'dev', forward_ports: Sequence[int] = (), table: Mapping[str, ImageSpec] = DEFAULT_TABLE) -> dict`: Creates configuration dictionary.
  - `render(config: dict) -> str`: Produces formatted JSON string.
- **Errors**: `DevcontainerError` with codes: `no_stack`, `file_too_large`, `invalid_option`, `exists`.
- **Limits**:
  - Input files: Max 65,536 bytes.
  - Container name: 1-64 printable characters.
  - Ports: 1-65535.

## Why not existing CLI templates?

Existing Dev Container CLI templates are interactive and manual. `devcontainer-gen` is a deterministic, programmatic library, ideal for automation, scaffolders, and headless CI integration.

## Security

See [docs/SECURITY.md](docs/SECURITY.md) for the threat model and mitigations.
