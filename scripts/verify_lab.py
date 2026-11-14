"""Demonstra o ciclo local e restaura o código original mesmo se uma etapa falhar."""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRICING = ROOT / "src/devops_lab/pricing.py"
REPORTS = ROOT / "reports/validation"


def main() -> int:
    original = PRICING.read_bytes()
    if b"total = amount - discount  # LAB: discount operation" not in original:
        print("Comece com a versão correta: python scripts/lab.py fix", file=sys.stderr)
        return 2
    environment = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "src"),
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
    }
    steps = []

    def run(label: str, arguments: list[str], expected: int = 0):
        result = subprocess.run(
            [sys.executable, *arguments],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        steps.append({"step": label, "exit_code": result.returncode, "expected": expected})
        if result.returncode != expected:
            print(result.stdout + result.stderr)
            raise RuntimeError(f"{label}: esperava código {expected}, recebeu {result.returncode}")
        print(f"OK: {label} (código {result.returncode})")
        return result

    try:
        run("testes da base", ["scripts/run_checks.py", "--output", str(REPORTS / "baseline")])
        run("injetar falha", ["scripts/lab.py", "break"])
        run(
            "testes detectam regressão",
            ["scripts/run_checks.py", "--output", str(REPORTS / "broken")],
            1,
        )
        run(
            "Master bloqueia",
            [
                "-m",
                "devops_lab.pr_review",
                "--local",
                "--mode",
                "rules",
                "--output",
                str(REPORTS / "review-broken"),
            ],
            1,
        )
        run(
            "diagnóstico offline",
            [
                "-m",
                "devops_lab.diagnostics",
                "--mode",
                "offline",
                "--log",
                str(REPORTS / "broken/pytest.log"),
                "--output",
                str(REPORTS / "analysis"),
            ],
        )
        run("corrigir falha", ["scripts/lab.py", "fix"])
        run("testes da correção", ["scripts/run_checks.py", "--output", str(REPORTS / "fixed")])
        run(
            "Master aprova",
            [
                "-m",
                "devops_lab.pr_review",
                "--local",
                "--mode",
                "rules",
                "--output",
                str(REPORTS / "review-fixed"),
            ],
        )
        run("empacotamento", ["scripts/build_release.py"])
        application = run(
            "executável", ["dist/devops-lab.pyz", "--subtotal", "100", "--discount", "10"]
        )
        if json.loads(application.stdout)["total"] != "90.00":
            raise RuntimeError("Executável retornou um total inesperado")
    finally:
        PRICING.write_bytes(original)
    (REPORTS / "validation.json").write_text(
        json.dumps(
            {
                "scope": "local; sem chamada real de IA e sem operações GitHub",
                "timestamp_utc": datetime.now(UTC).isoformat(),
                "steps": steps,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Experimento local validado. Evidências: {REPORTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
