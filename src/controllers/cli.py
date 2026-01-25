#!/usr/bin/env python3
"""Herramienta de línea de comandos para consultar la base de datos."""

import argparse
from src.models.gastos import calcular_total_gastos
from src.models.ingresos import calcular_total_ingresos


def main():
    parser = argparse.ArgumentParser(description="Consultas rápidas de finanzas")
    parser.add_argument(
        "--totales",
        action="store_true",
        help="Mostrar el total de ingresos y gastos registrados",
    )
    args = parser.parse_args()

    if args.totales:
        print(f"Total gastos: {calcular_total_gastos()}")
        print(f"Total ingresos: {calcular_total_ingresos()}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
