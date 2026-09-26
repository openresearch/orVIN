"""Thin CLI: normalized short JSON by default, extended by --long."""
import argparse
import json
import sys
from . import Context, HsnTsnLookup, VinDecoder
from .answer import hsntsn_answer, vin_answer


def main():
    parser = argparse.ArgumentParser(description="Offline VIN and KBA HSN/TSN lookup")
    sub = parser.add_subparsers(dest="mode", required=True)
    vin = sub.add_parser("vin", help="Decode sourced VIN manufacturer and vehicle details")
    vin.add_argument("vin")
    vin.add_argument("--model-year", type=int, help="Independently known model year")
    vin.add_argument("--market", help="Independently known uppercase two-letter market")
    kba = sub.add_parser("hsntsn", help="Look up a supplied four-digit HSN and three-character TSN")
    kba.add_argument("hsn")
    kba.add_argument("tsn")
    for command in (vin, kba):
        command.add_argument("--json", action="store_true", help="Print JSON (the default); combine with --long for evidence")
        command.add_argument("--json=short", dest="short_explicit", action="store_true", help=argparse.SUPPRESS)
        command.add_argument("--long", "--json=long", dest="long", action="store_true", help="Extend short JSON with all evidence and explanations")
    args = parser.parse_args()
    if args.short_explicit and args.long:
        parser.error("--json=short conflicts with --long/--json=long")
    try:
        context = Context(args.model_year, args.market) if args.mode == "vin" else None
    except ValueError as error:
        parser.error(str(error))
    try:
        result = (VinDecoder.bundled().decode(args.vin, context)
                  if args.mode == "vin" else HsnTsnLookup.bundled().lookup(args.hsn, args.tsn))
        answer = vin_answer(result) if args.mode == "vin" else hsntsn_answer(result)
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        print(f"ORvin: {error}", file=sys.stderr)
        return 1
    print(json.dumps(answer.long() if args.long else answer.short(), indent=2, ensure_ascii=True, allow_nan=False))
    valid = result["structure"] == "MODERN_FORMAT" if args.mode == "vin" else result["inputStatus"] == "VALID"
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
