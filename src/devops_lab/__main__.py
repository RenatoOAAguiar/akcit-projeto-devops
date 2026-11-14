"""Interface de linha de comando da aplicação de descontos."""

import argparse
import json

from devops_lab.pricing import calculate_total


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calcula o total de uma compra com desconto.")
    parser.add_argument("--subtotal", required=True, help="Valor antes do desconto; ex.: 100.00")
    parser.add_argument("--discount", required=True, help="Percentual de desconto; ex.: 10")
    args = parser.parse_args(argv)
    try:
        total = calculate_total(args.subtotal, args.discount)
    except ValueError as exc:
        parser.error(str(exc))
    print(
        json.dumps(
            {"subtotal": args.subtotal, "discount_percent": args.discount, "total": str(total)}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
