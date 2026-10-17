"""The command line: parse arguments, run one operation, print the result."""

import argparse
import sys

from calc.format import format_result
from calc.ops import OPERATIONS, CalcError


def main(argv: list[str] | None = None) -> int:
    """Run the calculator and return its exit status."""
    args = build_parser().parse_args(argv)
    try:
        a = float(args.a)
        b = float(args.b)
    except ValueError as e:
        print(f"calc: not a number: {e}", file=sys.stderr)
        return 1
    try:
        result = OPERATIONS[args.op](a, b)
    except CalcError as e:
        print(f"calc: {e}", file=sys.stderr)
        return 1
    print(format_result(result, args.precision))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="calc", description="A tiny calculator.")
    parser.add_argument("--precision", type=int, default=None, help="round the result to this many decimal places")
    sub = parser.add_subparsers(dest="op", required=True)
    for name in OPERATIONS:
        op = sub.add_parser(name)
        op.add_argument("a")
        op.add_argument("b")
    return parser
