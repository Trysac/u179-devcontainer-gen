# Testing

## Running

```sh
uv run pytest --cov=devcontainer_gen   # tests with coverage report
uv run python scripts/check.py      # every gate, as CI and the factory run it
```

## Policy

- Branch coverage of `src/devcontainer_gen` must stay at or above 80 %.
- Tests exercise the public API and assert return values, raised exceptions, and file-system effects.
- Tests are deterministic; they do not access the network, clock, or external system state.

## Test Coverage

- `tests/test_devcontainer_gen.py` covers:
  - Acceptance tests for Python detection, defaults, and version parsing.
  - Integration tests for generation and rendering.
  - Polyglot repository detection (Python + Node).
  - Stack-specific logic (Go modules, Node versioning/NVM).
  - Error scenarios (`no_stack`, `file_too_large`, `invalid_option`).
  - CLI operational workflow (writing, forcing, stdout, error handling).
  - Image table override mechanics.
