# Deterministic devcontainer.json generation from repository markers

Status: accepted (generated, pending human review)

## Context

Dev container setups often involve brittle copy-pasting across repositories. Polyglot repositories requiring multiple runtimes (e.g. Python backend with Node frontend) need deterministic prioritization of primary base images and secondary Dev Container features without requiring interactive CLIs or node-based tooling.

## Decision

Implement devcontainer-gen with deterministic stack priority (Python > Node > Go), where the primary stack sets the base image and subsequent stacks configure devcontainer features. Lockfiles and version files (.python-version, .nvmrc, go.mod) determine package manager install commands and version pins. The image and feature mapping is isolated in an overridable ImageSpec table.

## Consequences

Developers and automated scaffolding tools can generate standardized, valid devcontainer configurations purely through standard library Python. Supported languages are constrained to Python, Node, and Go, and non-numeric version strings emit non-fatal warnings with sensible defaults.
