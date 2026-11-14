"""Executa pytest, grava evidências e preserva o código de saída dos testes."""

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "current")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "pytest_cov",
        "--color=no",
        "--tb=short",
        "--cov=devops_lab",
        "--cov-report=term-missing",
        f"--cov-report=xml:{output / 'coverage.xml'}",
        f"--junitxml={output / 'junit.xml'}",
    ]
    environment = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    }
    result = subprocess.run(
        command, cwd=ROOT, env=environment, capture_output=True, text=True, encoding="utf-8"
    )
    log = result.stdout + result.stderr
    (output / "pytest.log").write_text(log, encoding="utf-8")
    (output / "run.json").write_text(
        json.dumps(
            {
                "timestamp_utc": datetime.now(UTC).isoformat(),
                "exit_code": result.returncode,
                "commit": os.getenv("GITHUB_SHA", "local"),
                "python": sys.version,
                "command": command,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(log)
    print(f"Evidências: {output}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
