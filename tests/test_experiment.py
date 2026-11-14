"""Valida que o experimento modifica somente o marcador conhecido."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "lab_script", Path(__file__).resolve().parents[1] / "scripts/lab.py"
)
lab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lab)


def test_break_fix_cycle_is_idempotent(tmp_path):
    path = tmp_path / "pricing.py"
    original = f"# keep this comment\n{lab.CORRECT}\n"
    path.write_text(original, encoding="utf-8")
    assert lab.change(path, "status") == "correct"
    assert lab.change(path, "break") == "broken"
    assert lab.change(path, "break") == "broken"
    assert lab.BROKEN in path.read_text()
    assert lab.change(path, "fix") == "correct"
    assert path.read_text() == original


def test_modified_marker_is_not_overwritten(tmp_path):
    path = tmp_path / "pricing.py"
    path.write_text("custom implementation", encoding="utf-8")
    with pytest.raises(ValueError, match="alterada"):
        lab.change(path, "break")
    assert path.read_text() == "custom implementation"
