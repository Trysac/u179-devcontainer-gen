# devcontainer-gen

[![PyPI version](https://img.shields.io/pypi/v/trysac-devcontainer-gen)](https://pypi.org/project/trysac-devcontainer-gen/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-devcontainer-gen)](LICENSE)
[![CI](https://github.com/Trysac/u179-devcontainer-gen/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u179-devcontainer-gen/actions/workflows/ci.yml)

Generate devcontainer.json for Python, Node and Go projects from marker files, with versions from version files, an overridable image table and golden output

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-devcontainer-gen
# or
uv add trysac-devcontainer-gen
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import devcontainer_gen

# normalize() trims surrounding whitespace and lower-cases the text.
print(devcontainer_gen.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    devcontainer_gen.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
