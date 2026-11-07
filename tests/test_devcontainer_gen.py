"""Tests for devcontainer_gen."""

from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from devcontainer_gen import (
    DEFAULT_TABLE,
    DevcontainerError,
    Stack,
    detect_stacks,
    generate,
    render,
)
from devcontainer_gen.__main__ import main


def test_acceptance_python_detection_and_default() -> None:
    res = detect_stacks(
        {
            "pyproject.toml": '[project]\nname = "x"\n',
            ".python-version": "3.12.4\n",
        }
    )
    assert res.stacks == [
        Stack("python", "3.12", "pyproject.toml") or Stack("python", "3.12", None)
    ]
    assert res.stacks[0].name == "python"
    assert res.stacks[0].version == "3.12"

    # Without .python-version
    res_default = detect_stacks({"pyproject.toml": '[project]\nname = "x"\n'})
    assert res_default.stacks[0].version == "3.12"


def test_acceptance_render_generate_python() -> None:
    cfg = generate([Stack("python", "3.12", None)])
    rendered = render(cfg)
    assert json.loads(rendered) == {
        "name": "dev",
        "image": "mcr.microsoft.com/devcontainers/python:1-3.12-bookworm",
        "features": {},
        "postCreateCommand": "python -m pip install -e .",
        "customizations": {"vscode": {"extensions": ["ms-python.python"]}},
    }
    assert rendered.endswith("}\n")
    assert '  "name": "dev"' in rendered


def test_acceptance_python_node_polyglot() -> None:
    det = detect_stacks(
        {
            "pyproject.toml": '[project]\nname = "x"\n',
            "package.json": '{"name": "frontend"}',
            "package-lock.json": "{}",
        }
    )
    cfg = generate(det.stacks)
    assert cfg["image"] == "mcr.microsoft.com/devcontainers/python:1-3.12-bookworm"
    assert cfg["features"] == {"ghcr.io/devcontainers/features/node:1": {"version": "20"}}
    assert cfg["postCreateCommand"] == "python -m pip install -e . && npm ci"
    assert cfg["customizations"]["vscode"]["extensions"] == [
        "ms-python.python",
        "dbaeumer.vscode-eslint",
    ]


def test_acceptance_go_and_node_alone() -> None:
    res_go = detect_stacks({"go.mod": "module x\n\ngo 1.22.3\n"})
    assert res_go.stacks == [Stack("go", "1.22", None)]
    cfg_go = generate(res_go.stacks)
    assert cfg_go["image"] == "mcr.microsoft.com/devcontainers/go:1-1.22-bookworm"
    assert cfg_go["postCreateCommand"] == "go mod download"

    res_node = detect_stacks({"package.json": '{"name": "pkg"}'})
    cfg_node = generate(res_node.stacks)
    assert cfg_node["image"] == "mcr.microsoft.com/devcontainers/typescript-node:1-20-bookworm"


def test_acceptance_nvmrc_and_pnpm() -> None:
    res_nvm = detect_stacks(
        {
            "package.json": "{}",
            ".nvmrc": "lts/iron\n",
        }
    )
    assert res_nvm.stacks[0].version == "20"
    assert res_nvm.warnings == [".nvmrc: unsupported value, using 20"]

    res_v18 = detect_stacks(
        {
            "package.json": "{}",
            ".nvmrc": "v18.19.0",
        }
    )
    assert res_v18.stacks[0].version == "18"

    res_pnpm = detect_stacks(
        {
            "package.json": "{}",
            "pnpm-lock.yaml": "lockfileVersion: 5.4",
        }
    )
    cfg_pnpm = generate(res_pnpm.stacks)
    assert cfg_pnpm["postCreateCommand"] == "corepack enable && pnpm install --frozen-lockfile"


def test_acceptance_error_and_ports() -> None:
    with pytest.raises(DevcontainerError) as exc_info:
        generate([])
    assert exc_info.value.code == "no_stack"

    large_content = "a" * 65_537
    with pytest.raises(DevcontainerError) as exc_large:
        detect_stacks({"pyproject.toml": large_content})
    assert exc_large.value.code == "file_too_large"

    ok_content = "a" * 65_536
    res_boundary = detect_stacks({"package.json": ok_content})
    assert len(res_boundary.stacks) == 1

    with pytest.raises(DevcontainerError) as exc_port:
        generate([Stack("python", "3.12", None)], forward_ports=(0,))
    assert exc_port.value.code == "invalid_option"

    with pytest.raises(DevcontainerError) as exc_port_high:
        generate([Stack("python", "3.12", None)], forward_ports=(65536,))
    assert exc_port_high.value.code == "invalid_option"

    with pytest.raises(DevcontainerError) as exc_name:
        generate([Stack("python", "3.12", None)], name="")
    assert exc_name.value.code == "invalid_option"

    with pytest.raises(DevcontainerError) as exc_name_unprintable:
        generate([Stack("python", "3.12", None)], name="dev\ncontainer")
    assert exc_name_unprintable.value.code == "invalid_option"

    cfg_port = generate([Stack("python", "3.12", None)], forward_ports=(3000,))
    assert cfg_port["forwardPorts"] == [3000]
    rendered = render(cfg_port)
    assert '"forwardPorts": [\n    3000\n  ]' in rendered


def test_acceptance_table_override() -> None:
    stacks = [Stack("python", "3.12", None)]
    custom_table = {
        **DEFAULT_TABLE,
        "python": replace(DEFAULT_TABLE["python"], image="example.com/py:{version}"),
    }
    cfg = generate(stacks, table=custom_table)
    assert cfg["image"] == "example.com/py:3.12"


def test_acceptance_cli_workflow(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Explicit acceptance check with literal 'ROOT'
    root_dir = tmp_path / "ROOT"
    root_dir.mkdir()
    (root_dir / "pyproject.toml").write_text('[project]\nname = "demo"\n', encoding="utf-8")
    cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        ret_root = main(["ROOT"])
        assert ret_root == 0
        target_root = root_dir / ".devcontainer" / "devcontainer.json"
        assert target_root.exists()
    finally:
        os.chdir(cwd)

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "demo"\n', encoding="utf-8")

    # Test --stdout
    ret_stdout = main([str(tmp_path), "--stdout"])
    assert ret_stdout == 0
    captured = capsys.readouterr()
    assert "mcr.microsoft.com/devcontainers/python" in captured.out
    assert not (tmp_path / ".devcontainer" / "devcontainer.json").exists()

    # Test normal write
    ret_write = main([str(tmp_path)])
    assert ret_write == 0
    target = tmp_path / ".devcontainer" / "devcontainer.json"
    assert target.exists()
    initial_content = target.read_text(encoding="utf-8")
    assert "python:1-3.12-bookworm" in initial_content

    # Re-run without --force -> returns 2
    ret_exists = main([str(tmp_path)])
    assert ret_exists == 2
    captured_err = capsys.readouterr()
    assert "error: .devcontainer/devcontainer.json exists (use --force)" in captured_err.err
    assert target.read_text(encoding="utf-8") == initial_content

    # Re-run with --force -> succeeds
    ret_force = main([str(tmp_path), "--force", "--name", "forced-dev"])
    assert ret_force == 0
    assert '"name": "forced-dev"' in target.read_text(encoding="utf-8")


def test_edge_cases_bom_and_crlf() -> None:
    res = detect_stacks(
        {
            "pyproject.toml": '\ufeff[project]\r\nname = "test"\r\n',
            ".python-version": "\ufeff3.11.2\r\n",
        }
    )
    assert res.stacks == [Stack("python", "3.11", "pyproject.toml")]
    assert res.warnings == []


def test_edge_cases_empty_python_version() -> None:
    res = detect_stacks(
        {
            "requirements.txt": "flask==3.0.0\n",
            ".python-version": "\n   \n",
        }
    )
    assert res.stacks == [Stack("python", "3.12", "requirements.txt")]
    assert res.warnings == []


def test_edge_cases_both_lockfiles() -> None:
    res = detect_stacks(
        {
            "package.json": "{}",
            "package-lock.json": "{}",
            "pnpm-lock.yaml": "{}",
        }
    )
    assert res.stacks[0].lockfile == "pnpm-lock.yaml"
    assert any("both package-lock.json and pnpm-lock.yaml found" in w for w in res.warnings)


def test_setup_py_detection() -> None:
    res = detect_stacks({"setup.py": "from setuptools import setup\nsetup()\n"})
    assert res.stacks[0].lockfile == "setup.py"
    cfg = generate(res.stacks)
    assert cfg["postCreateCommand"] == "python -m pip install -e ."


def test_node_lockfile_none() -> None:
    res = detect_stacks({"package.json": '{"version": "1.0.0"}'})
    assert res.stacks[0].lockfile is None
    cfg = generate(res.stacks)
    assert cfg["postCreateCommand"] == "npm install"


def test_invalid_table_stack_raises() -> None:
    with pytest.raises(DevcontainerError) as exc:
        generate([Stack("unknown", "1.0", None)])  # type: ignore
    assert exc.value.code == "invalid_option"

    with pytest.raises(DevcontainerError) as exc_sec:
        generate([Stack("python", "3.12", None), Stack("unknown", "1.0", None)])  # type: ignore
    assert exc_sec.value.code == "invalid_option"


def test_cli_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # No stack detected
    ret = main([str(tmp_path)])
    assert ret == 1
    err = capsys.readouterr().err
    assert "error: No stacks provided" in err

    # Marker file too large via CLI
    big_file = tmp_path / "package.json"
    big_file.write_bytes(b"x" * 65_537)
    ret_large = main([str(tmp_path)])
    assert ret_large == 1
    err_large = capsys.readouterr().err
    assert "exceeds size limit" in err_large


def test_render_preserves_extra_keys() -> None:
    cfg = {
        "name": "custom",
        "image": "img",
        "features": {},
        "postCreateCommand": "echo hi",
        "customizations": {"vscode": {"extensions": []}},
        "remoteUser": "vscode",
    }
    rendered = render(cfg)
    assert '"remoteUser": "vscode"' in rendered
