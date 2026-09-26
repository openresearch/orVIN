"""Import the pinned NHTSA bulk snapshot as data, without executing SQL.

Normal validation/builds are offline. Only the explicit download command uses
the network; a source update requires reviewing the pin and generated diff.
"""
import argparse
from collections import defaultdict
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import tempfile
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PINS = json.loads((ROOT / "tools/source-pins.json").read_text())
PIN = PINS["nhtsa"]
EDITION = PIN["edition"]
VERSION = PIN["version"]
RETRIEVED_ON = PIN["retrievedOn"]
PUBLISHED_ON = PIN["publishedOn"]
FILENAME = f"vPICList_lite_{EDITION}.plain.zip"
URL = "https://vpic.nhtsa.dot.gov/downloads/" + FILENAME
SHA256 = PIN["sha256"]
SOURCE_ID = PIN["sourceId"]
TABLES = {"wmi", "manufacturer", "make", "wmi_make", "vehicletype"}
ALIASES = {"988": "american-honda", "1057": "toyota-motor", "966": "bmw-ag",
           "1148": "volkswagen-ag", "976": "ford-motor", "971": "hombilt-trailers"}
CATEGORIES = {"Motorcycle": "MOTORCYCLE", "Passenger Car": "PASSENGER_CAR", "Truck": "TRUCK",
              "Bus": "BUS", "Trailer": "TRAILER", "Multipurpose Passenger Vehicle (MPV)": "MULTIPURPOSE_PASSENGER_VEHICLE",
              "Low Speed Vehicle (LSV)": "LOW_SPEED_VEHICLE", "Incomplete Vehicle": "INCOMPLETE_VEHICLE",
              "Off-Road Vehicle": "OFF_ROAD_VEHICLE"}
COPY = re.compile(r"COPY vpic\.([a-z0-9_]+) \(([^)]+)\) FROM stdin;\n?$")
ESCAPE = re.compile(r"\\([0-7]{1,3}|x[0-9a-fA-F]{1,2}|.)")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_value(value):
    """PostgreSQL text COPY NULL and backslash escaping (not CSV or SQL literals)."""
    if value == r"\N":
        return None
    result, position = bytearray(), 0
    for match in ESCAPE.finditer(value):
        result.extend(value[position:match.start()].encode("utf-8"))
        code = match[1]
        if code[0] in "01234567":
            result.append(int(code, 8))
        elif code[0] == "x" and len(code) > 1:
            result.append(int(code[1:], 16))
        else:
            result.extend({"b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v"}.get(code, code).encode("utf-8"))
        position = match.end()
    result.extend(value[position:].encode("utf-8"))
    return result.decode("utf-8")


def read_tables(stream, selected=None):
    """Keep only lookup tables in memory, while counting every source table."""
    selected = TABLES if selected is None else selected
    tables, inventory = {}, {}
    for line in stream:
        header = COPY.fullmatch(line)
        if not header:
            continue
        name, columns = header[1], header[2].split(", ")
        if name in inventory:
            raise ValueError(f"Duplicate COPY table: {name}")
        count, rows = 0, []
        for line in stream:
            if line.rstrip("\r\n") == r"\.":
                break
            count += 1
            if name in selected:
                values = line.rstrip("\r\n").split("\t")
                if len(values) != len(columns):
                    raise ValueError(f"Invalid COPY row in {name}")
                rows.append(dict(zip(columns, map(copy_value, values))))
        else:
            raise ValueError(f"Unterminated COPY table: {name}")
        inventory[name] = {"columns": columns, "rowCount": count}
        if name in selected:
            tables[name] = rows
    if selected - tables.keys():
        raise ValueError(f"Missing COPY tables: {sorted(selected - tables.keys())}")
    return tables, dict(sorted(inventory.items()))


def unique_index(rows, field="id"):
    index = {}
    for row in rows:
        if row[field] is None or row[field] in index:
            raise ValueError(f"Missing or duplicate {field}: {row[field]}")
        index[row[field]] = row
    return index


def text_cell(value):
    if value is None or not value.strip():
        raise ValueError("Missing source label")
    # The original spelling/spacing remains byte-for-byte in the source ZIP.
    result = " ".join(value.split())
    if re.search(r"[\x00-\x1f\x7f]", result):
        raise ValueError("Unsupported control character in source label")
    return result


def project(tables):
    """Generate all public usable WMI/make associations; retain genuine ambiguity."""
    wmis = unique_index(tables["wmi"])
    unique_index(tables["wmi"], "wmi")
    manufacturers = unique_index(tables["manufacturer"])
    makes = unique_index(tables["make"])
    types = unique_index(tables["vehicletype"])
    links = defaultdict(set)
    for link in tables["wmi_make"]:
        wmi_id, make_id = link["wmiid"], link["makeid"]
        if wmi_id not in wmis or make_id not in makes:
            raise ValueError("Unresolved wmi_make reference")
        if make_id in links[wmi_id]:
            raise ValueError("Duplicate wmi_make association")
        links[wmi_id].add(make_id)
    assignments, used, exclusions = [], set(), []
    for row in sorted(wmis.values(), key=lambda r: r["wmi"]):
        wmi, row_id = row["wmi"], row["id"]
        mfr_id = row["manufacturerid"]
        if mfr_id not in manufacturers or row["vehicletypeid"] not in types or not links[row_id]:
            raise ValueError(f"Unresolved WMI reference: {row_id}")
        reasons = []
        if not re.fullmatch(r"[A-HJ-NPR-Z0-9]{3}([A-HJ-NPR-Z0-9]{3})?", wmi):
            reasons.append("Invalid VIN alphabet or WMI length; not silently corrected")
        available = row["publicavailabilitydate"]
        if available is None:
            reasons.append("No public-availability date")
        elif date.fromisoformat(available.split(" ")[0]) > date.fromisoformat(RETRIEVED_ON):
            reasons.append("Public-availability date after snapshot retrieval")
        if reasons:
            exclusions.append({"wmiId": row_id, "wmi": wmi, "reasons": reasons})
            continue
        category = CATEGORIES[types[row["vehicletypeid"]]["name"]]
        used.add(mfr_id)
        brands = sorted(links[row_id], key=int)
        notes = f"NHTSA WMI row {row_id}. Historical validity and market exclusivity are not established."
        if row["noncompliant"] == "t":
            notes += " Source marks this WMI noncompliant; identification is not evidence of compliance."
        for make_id in brands:
            assignment = {"id": "wmi-" + wmi.lower() + (f"-make-{make_id}" if len(brands) > 1 else ""),
                          "wmi": wmi, "manufacturerId": ALIASES.get(mfr_id, "nhtsa-manufacturer-" + mfr_id),
                          "brand": text_cell(makes[make_id]["name"]).upper(), "category": category,
                          "sourceRefs": [SOURCE_ID], "constraints": {}, "notes": notes + f" Make row {make_id}."}
            if len(brands) > 1:
                assignment.update(ambiguityGroup="nhtsa-wmi-" + wmi.lower(),
                                  ambiguityReason="The source associates multiple makes with this WMI; the WMI alone cannot select one.")
            assignments.append(assignment)
    mfrs = [{"id": ALIASES.get(key, "nhtsa-manufacturer-" + key), "name": text_cell(manufacturers[key]["name"]),
             "sourceRefs": [SOURCE_ID]} for key in used]
    return sorted(mfrs, key=lambda r: r["id"]), sorted(assignments, key=lambda r: r["id"]), exclusions


def derive(archive):
    if sha256(archive) != SHA256:
        raise ValueError("NHTSA archive does not match the reviewed SHA-256 pin")
    with zipfile.ZipFile(archive) as zipped:
        members = zipped.namelist()
        if members != [f"vPICList_lite_{EDITION}.sql"]:
            raise ValueError("Unexpected NHTSA archive members")
        with zipped.open(members[0]) as stream:
            tables, inventory = read_tables(io.TextIOWrapper(stream, encoding="utf-8-sig"))
    manufacturers, assignments, exclusions = project(tables)
    source = {"id": SOURCE_ID, "title": PIN["title"],
              "url": URL, "publisher": "NHTSA", "retrievedOn": RETRIEVED_ON,
              "publicationVersion": EDITION.replace("_", "-") + "; published " + PUBLISHED_ON,
              "section": "WMI, manufacturer, wmi_make, make and vehicletype tables; full original database retained in snapshot.",
              "reuse": {"license": "LicenseRef-NHTSA-Public-Information",
                        "url": "https://www.nhtsa.gov/about-nhtsa/terms-use",
                        "basis": "NHTSA Ownership section permits copying and distribution of published information; upstream and third-party rights remain applicable."},
              "snapshot": "nhtsa/" + FILENAME, "sha256": SHA256}
    data = {"schemaVersion": 1, "version": VERSION, "sources": [source],
            "manufacturers": manufacturers, "assignments": assignments}
    metadata = {"version": VERSION, "source": source, "publicationDate": PUBLISHED_ON,
                "archiveBytes": archive.stat().st_size, "tables": inventory,
                "runtimeWmiCount": len({a["wmi"] for a in assignments}),
                "runtimeManufacturerCount": len(manufacturers), "runtimeAssignmentCount": len(assignments),
                "excludedWmis": exclusions,
                "transformations": ["Join WMI to makes via wmi_make; preserve all associated makes as candidates.",
                                    "Normalize label whitespace and uppercase brand labels; preserve manufacturer spelling.",
                                    "Keep manufacturer and assembly countries unknown; WMI country is not either fact.",
                                    "Do not interpret administrative dates as model-year constraints.",
                                    "Retain noncompliant flags as assignment notes; never silently correct malformed WMIs."],
                "implementedDecoding": ["WMI manufacturer, brand candidates and vehicle category",
                                        "Public VIN patterns, model-year alternatives, model/make, engine-model associations and displacement conversion"],
                "archivedOnly": "Vehicle-spec enrichment, defaults, VIN repair and vPIC error scoring remain unimplemented. SQL is retained as source data, never executed by either library."}
    return data, metadata


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def validate(data_dir=ROOT / "data"):
    expected, metadata = derive(data_dir / "nhtsa" / FILENAME)
    for path, content in [(data_dir / "dataset.json", expected), (data_dir / "nhtsa/metadata.json", metadata)]:
        if path.read_text(encoding="utf-8") != json_text(content):
            raise ValueError(f"Stale or incomplete NHTSA projection: {path.name}; rerun tools/nhtsa.py import")
    return metadata


def import_archive(archive):
    data, metadata = derive(archive)
    directory = ROOT / "data/nhtsa"
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / FILENAME
    if archive.resolve() != destination.resolve():
        shutil.copyfile(archive, destination)
    (directory / "metadata.json").write_text(json_text(metadata), encoding="utf-8", newline="\n")
    (ROOT / "data/dataset.json").write_text(json_text(data), encoding="utf-8", newline="\n")
    print(f"Imported {metadata['runtimeWmiCount']} WMIs, {len(data['assignments'])} associations; {len(metadata['excludedWmis'])} exclusions recorded")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="Offline source hash, completeness and projection check")
    importer = commands.add_parser("import", help="Regenerate from a local pinned ZIP, without network")
    importer.add_argument("--archive", type=Path, default=ROOT / "data/nhtsa" / FILENAME)
    commands.add_parser("download", help="Explicitly download, verify and import the pinned official ZIP")
    args = parser.parse_args()
    if args.command == "download":
        with tempfile.TemporaryDirectory(prefix="orvin-nhtsa-") as directory:
            archive = Path(directory) / FILENAME
            with urlopen(URL, timeout=120) as response, archive.open("wb") as stream:
                shutil.copyfileobj(response, stream)
            import_archive(archive)
    elif args.command == "import":
        import_archive(args.archive)
    else:
        metadata = validate()
        print(f"Validated full NHTSA snapshot and {metadata['runtimeWmiCount']} usable WMIs")


if __name__ == "__main__":
    main()
