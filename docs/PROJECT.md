# Project record

## Objective

Generate `devcontainer.json` for Python, Node, and Go projects from existing marker files, using versions from project files, with an overridable image table and deterministic output.

## Scope

- Detection of Python (`pyproject.toml`, `setup.py`, `requirements.txt`), Node (`package.json`), and Go (`go.mod`) stacks.
- Version extraction from `.python-version`, `.nvmrc`, and `go.mod`.
- Configuration rendering to valid JSON.
- Atomic CLI file writing.

## Out of Scope

- Dockerfile parsing or generation.
- `docker-compose` configuration generation.
- Execution, building, or managing container runtimes.
- Detection of non-specified languages.
- Support for monorepo subfolder configurations.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | 572224 / 12697 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.1661 |

## Factory run u179 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | gemini-3.8-flash | yes | 4618 | 8829 | 0 | 0 | 0.0183 |
| fix-1 | gemini-3.8-flash | no | 68064 | 754 | 0 | 188788 | 0.0680 |
| fix-2 | gemini-3.8-flash | no | 20109 | 474 | 0 | 36950 | 0.0196 |
| audit | gemini-3.1-flash-lite | no | 37834 | 477 | 0 | 32216 | 0.0110 |
| docs | gemini-3.1-flash-lite | no | 183645 | 2163 | 0 | 0 | 0.0492 |

Total: $0.1661. Prices: Anthropic list prices.
