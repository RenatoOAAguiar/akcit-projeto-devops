"""Introduz ou corrige somente a linha conhecida do experimento, sem executar IA."""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRICING = ROOT / "src" / "devops_lab" / "pricing.py"
CORRECT = "total = amount - discount  # LAB: discount operation"
BROKEN = "total = amount + discount  # LAB: discount operation"


def change(path: Path, action: str) -> str:
    source = path.read_text(encoding="utf-8")
    if source.count(CORRECT) == 1 and BROKEN not in source:
        state = "correct"
    elif source.count(BROKEN) == 1 and CORRECT not in source:
        state = "broken"
    else:
        raise ValueError("Linha do laboratório alterada. Revise o arquivo antes de continuar.")
    if action == "status":
        return state
    target = "broken" if action == "break" else "correct"
    if state != target:
        old, new = (CORRECT, BROKEN) if target == "broken" else (BROKEN, CORRECT)
        path.write_text(source.replace(old, new, 1), encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["break", "fix", "status"])
    args = parser.parse_args()
    try:
        print(f"Estado do laboratório: {change(PRICING, args.action)}")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Erro: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
