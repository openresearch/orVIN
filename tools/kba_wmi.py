"""Manually reviewed KBA SV 3.1 adapter; offline builds use the pinned factual extract.

Only `extract --pdf ...` needs pypdf (see requirements-pdf.txt). No PDF is bundled.
This parser deliberately accepts only the inspected edition and table layout.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import io
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data/kba-wmi"
SOURCE_ID = "kba-sv31-2026-01-15"
PDF_SHA256 = "d4a7daa14f46571fbcbe1e242567f0c1b79dd49793ea916e57b740c0495440f8"
COLUMNS = ("label", "hsn", "part1", "part2", "name", "location")
FIELDS = (
    (100001, "ManufacturerDirectoryName", "Manufacturer name in WMI directory", "name"),
    (100002, "ManufacturerDirectoryLabel", "Manufacturer label in WMI directory", "label"),
    (100003, "ManufacturerDirectoryLocation", "Manufacturer location in WMI directory (not assembly plant)", "location"),
    (100004, "ManufacturerDirectoryHSN", "Associated HSN in WMI directory (not a VIN-to-HSN determination)", "hsn"),
)
WARNING = ("Manufacturer-directory associations, including historical entries; not proof of the vehicle's "
           "retail make, HSN/TSN, assembly location or production date. Repeated rows remain alternatives.")


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def sha(content):
    return hashlib.sha256(content).hexdigest()


def compressed(content):
    stream = io.BytesIO()
    with gzip.GzipFile(fileobj=stream, mode="wb", filename="", mtime=0, compresslevel=9) as archive:
        archive.write(content)
    return stream.getvalue()


def row_id(row):
    return f"sv31-p{row['page']:03d}-r{row['row']:03d}"


def identifier(row):
    if not row["part1"]:
        return None, "No WMI published in this row"
    wmi = row["part1"] + row["part2"]
    if not re.fullmatch(r"[A-HJ-NPR-Z0-9]{3}([A-HJ-NPR-Z0-9]{3})?", wmi):
        return None, "Invalid modern VIN alphabet or identifier length; source value not corrected"
    if (row["part1"][2] == "9") != bool(row["part2"]):
        return None, "Inconsistent ordinary/extended WMI layout; source value not corrected"
    return wmi, None


def validate_rows(rows):
    if not rows:
        raise ValueError("Empty KBA directory")
    previous = (5, 0)
    for row in rows:
        if set(row) != {"page", "row", *COLUMNS}:
            raise ValueError("Unexpected KBA row fields")
        current = (row["page"], row["row"])
        if (type(row["page"]) is not int or type(row["row"]) is not int or
                not 6 <= row["page"] <= 150 or current <= previous or
                row["row"] != (previous[1] + 1 if row["page"] == previous[0] else 1)):
            raise ValueError("Invalid or unordered KBA page/row locator")
        previous = current
        if not re.fullmatch(r"[0-9]{4}", row["hsn"]) or not row["label"]:
            raise ValueError("Missing KBA HSN or manufacturer label")
        if any(not isinstance(row[k], str) or re.search(r"[\x00-\x1f\x7f]", row[k]) for k in COLUMNS):
            raise ValueError("Invalid KBA cell")
        if row["part2"] and not row["part1"]:
            raise ValueError("KBA WMI suffix without prefix")


def extract_pdf(path):
    # Lazy dependency: normal builds are independent of PDF software/network.
    if sha(path.read_bytes()) != PDF_SHA256:
        raise ValueError("KBA PDF differs from the manually reviewed edition")
    from pypdf import PdfReader
    reader = PdfReader(path)
    if len(reader.pages) != 151:
        raise ValueError("Unexpected KBA page count")
    records = []
    for number, page in enumerate(reader.pages[5:150], 6):
        cells = defaultdict(str)
        def visitor(text, matrix, text_matrix, font, size):
            y, x = round(matrix[5], 3), round(matrix[4], 3)
            # Every page repeats its column header above the body bounds.
            if not 45 < y < 710 or not text:
                return
            if text.strip() and size != -6.0:
                raise ValueError(f"Unexpected table font on PDF page {number}")
            if size == -6.0:
                cells[(y, x)] += text.replace("\n", "")
        page.extract_text(visitor_text=visitor)
        rows = defaultdict(dict)
        bounds = ((29, 32), (133, 136), (153, 156), (175, 178), (197, 200), (426, 430))
        for (y, x), text in cells.items():
            column = next((name for name, (lo, hi) in zip(COLUMNS, bounds) if lo <= x <= hi), None)
            if column is None or column in rows[y]:
                raise ValueError(f"Unexpected/duplicate cell on PDF page {number}: {x}, {y}")
            rows[y][column] = text
        if not rows:
            raise ValueError(f"Empty KBA table page {number}")
        for ordinal, (_, values) in enumerate(sorted(rows.items(), reverse=True), 1):
            records.append({"page": number, "row": ordinal, **{k: values.get(k, "") for k in COLUMNS}})
    validate_rows(records)
    return records


def load(directory=DIRECTORY):
    metadata = json.loads((directory / "metadata.json").read_bytes())
    content = (directory / metadata["snapshot"]).read_bytes()
    if sha(content) != metadata["snapshotSha256"]:
        raise ValueError("KBA WMI snapshot digest mismatch")
    raw = gzip.decompress(content)
    if sha(raw) != metadata["extractedSha256"]:
        raise ValueError("KBA WMI extracted data digest mismatch")
    rows = json.loads(raw)
    validate_rows(rows)
    if dict(sorted(Counter(str(r["page"]) for r in rows).items())) != metadata["pageRowCounts"]:
        raise ValueError("KBA WMI page inventory mismatch")
    if metadata["source"]["inspectedSha256"] != PDF_SHA256:
        raise ValueError("KBA WMI original PDF pin mismatch")
    return rows, metadata


def rules(rows):
    for row in rows:
        wmi, _ = identifier(row)
        if wmi is None:
            continue
        pattern = wmi + ".{14}" if len(wmi) == 3 else wmi[:3] + ".{8}" + wmi[3:] + ".{3}"
        locator = f"PDF page {row['page']}, table row {row['row']} (top to bottom); HSN {row['hsn']}; WMI {wmi}"
        yield {"id": row_id(row), "pattern": pattern, "marketScope": "GLOBAL", "markets": [],
               "stage": "manufacturer-directory", "warning": WARNING,
               "claims": [{"code": code, "value": row[column], "sourceId": SOURCE_ID,
                           "kind": "MANUFACTURER_DIRECTORY", "ruleId": row_id(row),
                           "keys": locator + "; column " + column}
                          for _, code, _, column in FIELDS if row[column]]}


def preference_rules(rows, metadata, nhtsa_data):
    """Compile reviewed row-specific preferences without relabeling source rows.

    A refresh may move an unchanged NHTSA record to a new source edition, but
    changing either identity or its locator needs another manual review.
    """
    directory = {row_id(row): row for row in rows}
    manufacturers = {m["id"]: m["name"] for m in nhtsa_data["manufacturers"]}
    source_ids = {source["id"] for source in nhtsa_data["sources"]}
    for preference in metadata.get("identityPreferences", []):
        row = directory.get(preference["kbaRowId"])
        expected = preference["preferredAssignment"]
        if (preference["kind"] != "SOURCE_PREFERENCE" or not preference["reason"] or
                not re.fullmatch(r"\d{4}-\d{2}-\d{2}", preference["reviewedOn"]) or
                preference["kbaSourceId"] != metadata["source"]["id"] or
                row != preference["expectedKbaRow"] or identifier(row)[0] != expected["wmi"]):
            raise ValueError("KBA preference scope changed; manual review required")
        candidates = [a for a in nhtsa_data["assignments"] if a["wmi"] == expected["wmi"]]
        if len(candidates) != 1:
            raise ValueError("NHTSA preference assignment changed; manual review required")
        assignment = candidates[0]
        actual = {key: assignment.get(key) for key in expected if key != "manufacturerName"}
        actual["manufacturerName"] = manufacturers.get(assignment["manufacturerId"])
        if actual != expected or len(assignment["sourceRefs"]) != 1 or not set(assignment["sourceRefs"]) <= source_ids:
            raise ValueError("NHTSA preference assignment changed; manual review required")
        wmi = expected["wmi"]
        pattern = wmi + ".{14}" if len(wmi) == 3 else wmi[:3] + ".{8}" + wmi[3:] + ".{3}"
        locator = (f"Preference {preference['id']}, reviewed {preference['reviewedOn']}; "
                   f"preferred NHTSA assignment {assignment['id']}, manufacturer {assignment['manufacturerId']}; "
                   f"{assignment['notes']} Conflicting KBA source {preference['kbaSourceId']}, "
                   f"row {preference['kbaRowId']} (PDF page {row['page']}, table row {row['row']}). "
                   + preference["reason"])
        # Keep the preferred make in its own alternative: combining it with the
        # KBA row would falsely attach the conflicting directory HSN to Cobra.
        yield {"id": preference["id"], "pattern": pattern, "marketScope": "GLOBAL", "markets": [],
               "stage": "reviewed-source-preference", "warning": preference["reason"],
               "claims": [{"code": "Make", "value": assignment["brand"],
                           "sourceId": assignment["sourceRefs"][0], "kind": "SOURCE_PREFERENCE",
                           "ruleId": preference["id"], "keys": locator}]}


def comparison(rows, nhtsa_data):
    nhtsa = defaultdict(list)
    manufacturers = {m["id"]: m["name"] for m in nhtsa_data["manufacturers"]}
    for assignment in nhtsa_data["assignments"]:
        name = manufacturers[assignment["manufacturerId"]]
        if name not in nhtsa[assignment["wmi"]]:
            nhtsa[assignment["wmi"]].append(name)
    grouped, excluded, absent = defaultdict(list), [], []
    for row in rows:
        wmi, reason = identifier(row)
        if wmi:
            grouped[wmi].append(row)
        elif row["part1"]:
            excluded.append({"rowId": row_id(row), "printedIdentifier": row["part1"] + row["part2"], "reason": reason})
        else:
            absent.append(row_id(row))
    overlap = sorted(grouped.keys() & nhtsa.keys())
    def normalized(value):
        return " ".join(value.upper().split())
    differing = []
    for wmi in overlap:
        names = sorted({r["name"] for r in grouped[wmi] if r["name"]})
        if {normalized(n) for n in names} != {normalized(n) for n in nhtsa[wmi]}:
            differing.append({"wmi": wmi, "kbaNames": names, "nhtsaNames": sorted(nhtsa[wmi]),
                              "rowIds": [row_id(r) for r in grouped[wmi]]})
    return {"counts": {"sourceRows": len(rows), "matchingRows": sum(map(len, grouped.values())),
                       "uniqueWmis": len(grouped), "extendedWmis": sum(len(w) == 6 for w in grouped),
                       "additionalWmis": len(grouped.keys() - nhtsa.keys()), "overlappingWmis": len(overlap),
                       "repeatedWmis": sum(len(r) > 1 for r in grouped.values()),
                       "wmisWithMultipleHsns": sum(len({r['hsn'] for r in group}) > 1 for group in grouped.values()),
                       "wmisWithMultipleManufacturerNames": sum(len({r['name'] for r in group if r['name']}) > 1 for group in grouped.values()),
                       "differingManufacturerLabels": len(differing), "rowsWithoutWmi": len(absent),
                       "invalidIdentifierRows": len(excluded)},
            "sources": {"kbaSourceId": SOURCE_ID, "kbaPdfSha256": PDF_SHA256,
                        "nhtsaDatasetVersion": nhtsa_data.get("version"),
                        "nhtsaSourceIds": [s["id"] for s in nhtsa_data.get("sources", [])]},
            "assessment": "Exact label differences are review signals, not proof of different legal entities. No fuzzy entity merges or retail-make inferences are made.",
            "excludedRows": excluded, "rowsWithoutWmi": absent, "differingManufacturerLabels": differing}


def validate(root=ROOT):
    directory = root / "data/kba-wmi"
    rows, metadata = load(directory)
    nhtsa_data = json.loads((root / "data/dataset.json").read_bytes())
    list(preference_rules(rows, metadata, nhtsa_data))
    report = comparison(rows, nhtsa_data)
    if (directory / "comparison.json").read_bytes() != json_bytes(report):
        raise ValueError("Stale KBA/NHTSA comparison; run tools/kba_wmi.py compare")
    if report["counts"]["sourceRows"] != metadata["recordCount"]:
        raise ValueError("KBA WMI row count mismatch")
    return metadata, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract")
    extract.add_argument("--pdf", type=Path, required=True)
    commands.add_parser("compare")
    commands.add_parser("validate")
    args = parser.parse_args()
    if args.command == "extract":
        rows = extract_pdf(args.pdf)
        raw = json_bytes(rows)
        content = compressed(raw)
        # Extraction must reproduce the reviewed snapshot; changing pins is a separate manual review.
        metadata = json.loads((DIRECTORY / "metadata.json").read_bytes())
        if sha(raw) != metadata["extractedSha256"] or sha(content) != metadata["snapshotSha256"]:
            raise ValueError("Extracted rows differ from reviewed snapshot")
        (DIRECTORY / metadata["snapshot"]).write_bytes(content)
        print(f"Verified extraction of {len(rows)} rows from the pinned PDF")
    elif args.command == "compare":
        rows, _ = load()
        report = comparison(rows, json.loads((ROOT / "data/dataset.json").read_bytes()))
        (DIRECTORY / "comparison.json").write_bytes(json_bytes(report))
        print(json.dumps(report["counts"], sort_keys=True))
    else:
        _, report = validate()
        print(json.dumps(report["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
