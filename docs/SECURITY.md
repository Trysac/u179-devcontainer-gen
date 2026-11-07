# Security Policy

## Threat Model

`devcontainer_gen` parses marker files from potentially untrusted repositories to produce container configurations.

### Defended

- **Denial of Service**: Marker files exceeding 65,536 bytes are rejected to prevent memory exhaustion.
- **Injection/Validation**: Container names are strictly validated (1-64 printable characters) and forwarded ports are checked against the valid integer range (1-65535).
- **Filesystem Integrity**: The CLI writes to temporary files within `.devcontainer` and uses `os.replace` for atomic updates, preventing partial writes.
- **Supply Chain**: The library is zero-dependency, minimizing the attack surface from third-party code.

### Not Defended

- **Logic Integrity**: Parsing does not validate that the extracted versions or install commands are safe or appropriate for the intended infrastructure; this is left to the user to review.
