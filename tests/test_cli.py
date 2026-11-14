import json

import pytest

from devops_lab.__main__ import main


def test_cli_outputs_total(capsys):
    assert main(["--subtotal", "100", "--discount", "10"]) == 0
    assert json.loads(capsys.readouterr().out)["total"] == "90.00"


def test_cli_rejects_invalid_amount(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--subtotal", "-1", "--discount", "10"])
    assert exc.value.code == 2
    assert "subtotal deve estar" in capsys.readouterr().err


def test_cli_requires_arguments():
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2
