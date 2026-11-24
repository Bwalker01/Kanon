import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from kanon import __version__
from kanon.cli import main

ROOT = Path(__file__).resolve().parents[1]


def pyproject_version() -> str:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]


def test_version_matches_pyproject():
    assert __version__ == pyproject_version()


def test_version_flag_prints_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"kanon {pyproject_version()}"


def test_no_command_prints_help(capsys):
    assert main([]) == 0
    assert "usage: kanon" in capsys.readouterr().out


def test_module_entry_point():
    out = subprocess.run(
        [sys.executable, "-m", "kanon", "--version"], capture_output=True, text=True, check=True
    )
    assert out.stdout.strip() == f"kanon {pyproject_version()}"


def test_version_is_defined_in_one_place():
    """No source file may hard-code the package version; pyproject.toml is the only source."""
    pattern = re.compile(re.escape(pyproject_version()))
    offenders = [p for p in (ROOT / "src").rglob("*.py") if pattern.search(p.read_text(encoding="utf-8"))]
    assert offenders == []
