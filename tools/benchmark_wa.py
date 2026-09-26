#!/usr/bin/env python3
"""Offline, observational WA EV prefix benchmark; never fetch individual vehicles."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT / "validation/wa-ev"
SOURCE = "https://data.wa.gov/resource/f6w7-q2d2.json"
METADATA = "https://data.wa.gov/api/views/f6w7-q2d2.json"
QUERY = {"$select": "vin_1_10,make,model,model_year,count(*) as vehicle_count",
         "$group": "vin_1_10,make,model,model_year",
         "$order": "vin_1_10,make,model,model_year", "$limit": "100000"}
FIELDS = {"make": "brand", "model": "model", "model_year": "modelYear"}
CONTINUATIONS = ("A000001", "F500000", "Z999999")
ROW_FIELDS = {"vin_1_10", "make", "model", "model_year", "vehicle_count"}


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def normalized(value):
    """Only case and repeated whitespace are insignificant; punctuation is retained."""
    return " ".join(str(value).upper().split())


def group_rows(rows):
    """Retain conflicting labels and weights instead of arbitrarily taking a row."""
    groups = {}
    for row in rows:
        if set(row) != ROW_FIELDS:
            raise ValueError("Corpus must contain only the four grouped labels and vehicle_count")
        prefix = row["vin_1_10"]
        if not isinstance(prefix, str) or not re.fullmatch("[A-Z0-9]{10}", prefix):
            raise ValueError("Expected a masked ten-character VIN prefix")
        if not all(isinstance(row[field], str) and row[field].strip() for field in FIELDS):
            raise ValueError("Expected nonempty source labels")
        count = row["vehicle_count"]
        if isinstance(count, bool) or not re.fullmatch("[1-9][0-9]*", str(count)):
            raise ValueError("Expected a positive aggregate count")
        group = groups.setdefault(prefix, {"prefix": prefix, "vehicleCount": 0,
                                           "labels": {field: set() for field in FIELDS}})
        group["vehicleCount"] += int(count)
        for field in FIELDS:
            group["labels"][field].add(normalized(row[field]))
    return [groups[prefix] for prefix in sorted(groups)]


def consensus(resolutions):
    """A known label must survive every declared continuation probe."""
    statuses = {row["status"] for row in resolutions}
    known = {normalized(row["value"]) for row in resolutions
             if row["status"] == "KNOWN" and row["value"] is not None}
    if statuses == {"KNOWN"} and len(known) == 1:
        return "KNOWN", next(iter(known))
    if len(known) > 1:
        return "PROBE_DISAGREEMENT", None
    if len(statuses) == 1 and "KNOWN" not in statuses:
        return next(iter(statuses)), None
    return "PROBE_INCOMPLETE", None


def accepted_alias(make, observed, predicted, aliases):
    return any(normalized(a["make"]) == make
               and normalized(a["observed"]) == observed
               and normalized(a["decoded"]) == predicted for a in aliases)


def evaluate_group(group, decode, aliases, continuations=CONTINUATIONS):
    prefix = group["prefix"]
    # Low-volume extended WMIs need positions 12-14, absent from this source.
    unsupported = prefix[2] == "9" or not re.fullmatch("[A-HJ-NPR-Z0-9]{10}", prefix)
    probes = [] if unsupported else [decode(prefix + tail) for tail in continuations]
    outcomes = {}
    for field, result_field in FIELDS.items():
        labels = group["labels"][field]
        result = {"observed": sorted(labels), "predicted": None}
        if len(labels) != 1:
            result["status"] = "SOURCE_CONFLICT"
        elif unsupported:
            result["status"] = "UNSUPPORTED_PREFIX"
        else:
            status, value = consensus([probe[result_field] for probe in probes])
            result.update(status=status, predicted=value)
            if status == "KNOWN":
                expected = next(iter(labels))
                result["exactMatch"] = value == expected
                make = next(iter(group["labels"]["make"])) if len(group["labels"]["make"]) == 1 else None
                result["aliasMatch"] = result["exactMatch"] or (
                    field == "model" and accepted_alias(make, expected, value, aliases))
        outcomes[field] = result
    return {"prefix": prefix, "vehicleCount": group["vehicleCount"], "fields": outcomes}


def summarize(evaluations, weighted=False):
    summary = {}
    for field in FIELDS:
        counts = Counter()
        for row in evaluations:
            weight = row["vehicleCount"] if weighted else 1
            outcome = row["fields"][field]
            counts["total"] += weight
            counts[outcome["status"]] += weight
            if outcome["status"] == "KNOWN":
                counts["exactMatches"] += weight * outcome["exactMatch"]
                counts["aliasMatches"] += weight * outcome["aliasMatch"]
        eligible = counts["total"] - counts["SOURCE_CONFLICT"] - counts["UNSUPPORTED_PREFIX"]
        known = counts["KNOWN"]
        summary[field] = {
            "total": counts["total"], "eligible": eligible, "known": known,
            "exactMatches": counts["exactMatches"], "aliasMatches": counts["aliasMatches"],
            "exactMismatches": known - counts["exactMatches"],
            "aliasMismatches": known - counts["aliasMatches"],
            "coverage": known / eligible if eligible else None,
            "exactPrecision": counts["exactMatches"] / known if known else None,
            "aliasPrecision": counts["aliasMatches"] / known if known else None,
            "sourceConflicts": counts["SOURCE_CONFLICT"],
            "unsupportedPrefixes": counts["UNSUPPORTED_PREFIX"],
            "abstentions": {key: counts[key] for key in sorted(counts)
                            if key not in {"total", "KNOWN", "exactMatches", "aliasMatches",
                                           "SOURCE_CONFLICT", "UNSUPPORTED_PREFIX"}}}
    return summary


def store_snapshot(directory, raw, metadata_raw, retrieved_on, query_url):
    rows = json.loads(raw)
    groups = group_rows(rows)
    if len(rows) >= int(QUERY["$limit"]):
        raise ValueError("Query reached its row limit; refusing a possibly truncated snapshot")
    metadata = json.loads(metadata_raw)
    if metadata.get("licenseId") != "ODBL":
        raise ValueError("Source license changed; review reuse terms before replacing the snapshot")
    directory.mkdir(parents=True, exist_ok=True)
    compressed = gzip.compress(raw, mtime=0)
    (directory / "groups.json.gz").write_bytes(compressed)
    fields = [{"fieldName": c["fieldName"], "name": c["name"], "description": c.get("description")}
              for c in metadata["columns"] if c["fieldName"] in ROW_FIELDS]
    manifest = {
        "sourceId": "washington-dol-ev-population-f6w7-q2d2",
        "title": metadata["name"], "publisher": "Washington State Department of Licensing",
        "sourceUrl": "https://data.wa.gov/Transportation/Electric-Vehicle-Population-Data/f6w7-q2d2",
        "queryUrl": query_url, "query": QUERY, "retrievedOn": retrieved_on,
        "sha256": sha256(raw), "snapshot": "groups.json.gz", "snapshotSha256": sha256(compressed),
        "uncompressedBytes": len(raw), "groupCount": len(rows), "prefixCount": len(groups),
        "vehicleCount": sum(g["vehicleCount"] for g in groups),
        "metadataUrl": METADATA, "metadataSha256": sha256(metadata_raw),
        "sourceRowsUpdatedAt": metadata.get("rowsUpdatedAt"),
        "temporal": metadata.get("metadata", {}).get("custom_fields", {}).get("Temporal", {}),
        "sourceFieldDescriptions": fields,
        "reuse": {"license": "ODbL-1.0", "url": "https://opendatacommons.org/licenses/odbl/1-0/",
                  "attribution": "Contains information from Washington State Department of Licensing's Electric Vehicle Population Data, available under the Open Database License (ODbL) 1.0.",
                  "modifications": "Grouped by VIN prefix, make, model, and model year; registration counts aggregated. No location or owner fields retained."},
        "limitations": [
            "Make, model, and model year source labels were themselves obtained by VIN decoding; this is correlated observational evidence, not independent OEM ground truth.",
            "Only the first ten VIN characters are published. Synthetic continuation probes cannot establish the actual plant, serial number, or validity of a complete VIN.",
            "Washington registrations are an EV/PHEV population sample, not a global or European vehicle sample; US decoding context is an explicit assumption."]}
    write_json(directory / "source.json", manifest)
    return manifest


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def implementation_hashes():
    return {
        "decoderSourceSha256": {p.name: sha256(p.read_bytes()) for p in sorted((ROOT / "libs/python/orvin").glob("*.py"))},
        "richDatasetMetadataSha256": sha256((ROOT / "data/decoding/metadata.json").read_bytes()),
        "approvalDatasetMetadataSha256": sha256((ROOT / "data/astra/metadata.json").read_bytes())
        if (ROOT / "data/astra/metadata.json").is_file() else None,
        "wmiDatasetSha256": sha256((ROOT / "data/dataset.json").read_bytes()),
        "toolSha256": sha256(Path(__file__).read_bytes())}


def refresh(directory):
    with urlopen(METADATA, timeout=120) as response:
        metadata_raw = response.read()
    query_url = SOURCE + "?" + urlencode(QUERY)
    with urlopen(query_url, timeout=120) as response:
        raw = response.read()
    with urlopen(METADATA, timeout=120) as response:
        after = json.load(response)
    if json.loads(metadata_raw).get("rowsUpdatedAt") != after.get("rowsUpdatedAt"):
        raise RuntimeError("Source changed during retrieval; retry for a consistent snapshot")
    return store_snapshot(directory, raw, metadata_raw,
                          datetime.now(timezone.utc).isoformat(), query_url)


def run(directory, output, limit=None):
    initial_hashes = implementation_hashes()
    sys.path.insert(0, str(ROOT / "libs/python"))
    from orvin import Context, VinDecoder
    manifest = json.loads((directory / "source.json").read_bytes())
    compressed = (directory / manifest["snapshot"]).read_bytes()
    raw = gzip.decompress(compressed)
    if sha256(raw) != manifest["sha256"] or sha256(compressed) != manifest["snapshotSha256"]:
        raise ValueError("Snapshot does not match its recorded hashes")
    groups = group_rows(json.loads(raw))
    if len(groups) != manifest["prefixCount"] or sum(g["vehicleCount"] for g in groups) != manifest["vehicleCount"]:
        raise ValueError("Snapshot counts do not match the manifest")
    alias_raw = (directory / "aliases.json").read_bytes()
    aliases = json.loads(alias_raw)["modelAliases"]
    decoder = VinDecoder.bundled()
    selected = groups[:limit] if limit else groups
    evaluations = []
    for index, group in enumerate(selected, 1):
        try:
            evaluations.append(evaluate_group(group, lambda vin: decoder.decode(vin, Context(market="US")), aliases))
        except Exception as error:
            raise RuntimeError(f"Decoder failed for public masked prefix {group['prefix']} at {index}/{len(selected)}") from error
        if index % 1000 == 0:
            print(f"Evaluated {index}/{len(selected)} prefixes", file=sys.stderr)
    by_make = defaultdict(list)
    for evaluation in evaluations:
        observed = evaluation["fields"]["make"]["observed"]
        by_make[observed[0] if len(observed) == 1 else "SOURCE_CONFLICT"].append(evaluation)
    mismatches = {}
    for field in FIELDS:
        mismatch_rows = [r for r in evaluations if r["fields"][field]["status"] == "KNOWN"
                         and not r["fields"][field]["aliasMatch"]]
        mismatches[field] = [{"prefix": r["prefix"], "vehicleCount": r["vehicleCount"],
                              **r["fields"][field]} for r in mismatch_rows[:25]]
    details = json.dumps(evaluations, separators=(",", ":"), ensure_ascii=False).encode()
    if implementation_hashes() != initial_hashes:
        raise RuntimeError("Library, benchmark, or dataset metadata changed during evaluation; rerun against a stable checkout")
    details_path = output.with_name(output.stem + "-prefixes.json.gz")
    details_path.write_bytes(gzip.compress(details, mtime=0))
    report = {
        "benchmark": "wa-ev-masked-prefix-observational-v1",
        "generatedOn": datetime.now(timezone.utc).isoformat(),
        "sourceSha256": manifest["sha256"], "aliasesSha256": sha256(alias_raw),
        "dataset": decoder.dataset,
        **initial_hashes,
        "configuration": {"market": "US", "modelYearContext": None,
                          "continuations": list(CONTINUATIONS), "suppliedVinIsSynthetic": True,
                          "normalization": "Uppercase and collapse whitespace only; preserve punctuation.",
                          "consensus": "Every synthetic continuation must return the same KNOWN label.",
                          "excluded": "Conflicting source labels and prefixes requiring unavailable extended WMI positions.",
                          "aliasesAppliedOnlyTo": "model", "aliasCount": len(aliases)},
        "completeSnapshotEvaluated": len(selected) == len(groups),
        "evaluatedPrefixes": len(evaluations), "sourcePrefixes": len(groups),
        "byPrefix": summarize(evaluations), "byRegistrationCount": summarize(evaluations, weighted=True),
        "byObservedMake": {make: summarize(rows) for make, rows in sorted(by_make.items())},
        "firstMismatchExamples": mismatches,
        "prefixResults": details_path.name, "prefixResultsSha256": sha256(details_path.read_bytes()),
        "attribution": manifest["reuse"]["attribution"], "limitations": manifest["limitations"] + [
            "Probe agreement is necessary for this benchmark's known predictions, but is not a proof that all possible hidden continuations agree.",
            "Registration-weighted metrics repeat one prefix prediction by its public aggregate count; they are not independent vehicle-level observations."]}
    write_json(output, report)
    print(json.dumps({"report": str(output), "prefixes": len(evaluations), "byPrefix": report["byPrefix"]}, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Download only the grouped four-label public query")
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--limit", type=int, help="Optional partial smoke run, explicitly marked in output")
    args = parser.parse_args()
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")
    if args.refresh:
        refresh(args.directory)
    run(args.directory, args.output or args.directory / "benchmark.json", args.limit)


if __name__ == "__main__":
    main()
