# Architecture

`devcontainer_gen` is a deterministic, pure-Python library for generating `devcontainer.json` from repository markers.

## Detection Pipeline

1.  **File Input**: Reads marker files with a hard limit of 65,536 bytes.
2.  **Stack Discovery**: Evaluates project root for:
    - Python (`pyproject.toml`, `requirements.txt`, `setup.py`, `.python-version`)
    - Node (`package.json`, `package-lock.json`, `pnpm-lock.yaml`, `.nvmrc`)
    - Go (`go.mod`)
3.  **Conflict Resolution**: The first detected stack serves as the base image. Subsequent stacks are added as Dev Container features.
4.  **Generation**: Combines `ImageSpec` definitions and detected versions to create the configuration dictionary.
5.  **Rendering**: Serializes the dictionary to indented JSON.

## Design Decisions

- **Zero Runtime Dependencies**: Ensures portability and eliminates supply chain risk.
- **Atomicity**: Uses tempfiles and `os.replace` to ensure `.devcontainer/devcontainer.json` is never corrupted during updates.
- **Extensibility**: The `ImageSpec` table is exposed to the `generate` function, allowing users to inject custom registries or configurations.
