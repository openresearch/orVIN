"""Readable summaries by default; --json exposes the complete public library result."""
import argparse
import json
import sys
from . import Context, HsnTsnLookup, VinDecoder
from .summary import hsntsn_summary, vin_summary


def main():
    parser = argparse.ArgumentParser(description="Offline VIN and KBA HSN/TSN lookup")
    sub = parser.add_subparsers(dest="mode", required=True)
    vin = sub.add_parser("vin", help="Identify a VIN manufacturer")
    vin.add_argument("vin")
    vin.add_argument("--model-year", type=int, help="Independently known model year")
    vin.add_argument("--market", help="Independently known uppercase two-letter market")
    kba = sub.add_parser("hsntsn", help="Look up a supplied four-digit HSN and three-character TSN")
    kba.add_argument("hsn")
    kba.add_argument("tsn")
    for command in (vin, kba):
        command.add_argument("--json", action="store_true", help="Print the complete library result as JSON")
    args = parser.parse_args()
    try:
        context = Context(args.model_year, args.market) if args.mode == "vin" else None
    except ValueError as error:
        parser.error(str(error))
    try:
        result = (VinDecoder.bundled().decode(args.vin, context)
                  if args.mode == "vin" else HsnTsnLookup.bundled().lookup(args.hsn, args.tsn))
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        print(f"Orvin: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    else:
        print(vin_summary(result) if args.mode == "vin" else hsntsn_summary(result))
    return 2 if result["status"] in ("INVALID_INPUT", "UNSUPPORTED_FORMAT") else 0


if __name__ == "__main__":
    raise SystemExit(main())
