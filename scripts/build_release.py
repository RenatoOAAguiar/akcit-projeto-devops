"""Gera uma aplicação .pyz executável, sem ferramentas externas de empacotamento."""

import zipapp
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    output = ROOT / "dist" / "devops-lab.pyz"
    output.parent.mkdir(parents=True, exist_ok=True)
    zipapp.create_archive(
        ROOT / "src",
        target=output,
        main="devops_lab.__main__:main",
        compressed=True,
        filter=lambda path: "__pycache__" not in path.parts and path.suffix != ".pyc",
    )
    print(f"Aplicação gerada: {output}")


if __name__ == "__main__":
    main()
