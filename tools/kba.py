"""Import (explicitly, online) or validate (offline) the pinned KBA Kfz snapshot."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import gzip
import hashlib
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data/kba"
SERVICE = "https://services-eu1.arcgis.com/U09msXRZoxesNntH/arcgis/rest/services/SP_HSN_TSN_92a1e/FeatureServer/0"
CATALOG = "https://data.gov.de/suche/daten/fz-hersteller-handelsnamen-kfz?ids=c1e3a0b6-0d34-4e99-8181-91bdfb639208"
HEADER = "hsn\ttsn\tmanufacturer\ttradeName\tregisteredCount\tcountMarker\tsourceObjectId\n"
FIELDS = {"Berichtszeitpunkt", "Herstellerschluessel", "Herstellertext", "Typschluessel",
          "Handelsname", "Anzahl", "ZS_Anzahl", "ObjectId"}


def digest(content):
    return hashlib.sha256(content).hexdigest()


def cell(value):
    if value is None:
        return "\\N"
    value = str(value)
    if value == "\\N" or re.search(r"[\x00-\x1f\x7f]", value):
        raise ValueError("Unsupported control character or null sentinel in KBA text")
    return value


def normalize(rows, reference_date):
    """Preserve every source row, including duplicate type keys and statistical markers."""
    expected_date = date.fromisoformat(reference_date).strftime("%d.%m.%Y")
    ids = set()
    normalized = []
    for row in rows:
        if set(row) != FIELDS or row["Berichtszeitpunkt"] != expected_date:
            raise ValueError("Unexpected KBA fields or reference date")
        oid = row["ObjectId"]
        if type(oid) is not int or oid <= 0 or oid in ids:
            raise ValueError("Missing/duplicate KBA object ID")
        ids.add(oid)
        hsn, tsn = row["Herstellerschluessel"], row["Typschluessel"]
        if not isinstance(hsn, str) or not re.fullmatch(r"[0-9]{4}", hsn):
            raise ValueError(f"Invalid source HSN: {hsn!r}")
        if not isinstance(tsn, str) or not re.fullmatch(r"[A-Z0-9]{3}", tsn):
            raise ValueError(f"Invalid source TSN: {tsn!r}")
        for name in ("Herstellertext", "Handelsname", "ZS_Anzahl"):
            if row[name] is not None and not isinstance(row[name], str):
                raise ValueError(f"Invalid source text: {name}")
        count = row["Anzahl"]
        if count is not None and (type(count) is not int or count < 0):
            raise ValueError("Invalid registered count")
        normalized.append([hsn, tsn, row["Herstellertext"], row["Handelsname"], count,
                           row["ZS_Anzahl"], oid])
    normalized.sort(key=lambda r: (r[0], r[1], r[6]))
    return (HEADER + "".join("\t".join(map(cell, r)) + "\n" for r in normalized)).encode("utf-8")


def check_completeness(rows, expected_ids, expected_count):
    actual = [r["ObjectId"] for r in rows]
    if (not expected_count or len(expected_ids) != expected_count
            or len(set(expected_ids)) != expected_count or len(actual) != expected_count
            or len(set(actual)) != expected_count or set(actual) != set(expected_ids)):
        raise ValueError("Incomplete KBA download: counts or object IDs do not match")


def query(**params):
    url = SERVICE + "/query?" + urllib.parse.urlencode({"f": "json", **params})
    with urllib.request.urlopen(url, timeout=90) as response:
        result = json.load(response)
    if "error" in result:
        raise ValueError(f"KBA service error: {result['error']}")
    return result


def download(reference_date, version, directory=DIRECTORY):
    source_date = date.fromisoformat(reference_date).strftime("%d.%m.%Y")
    where = f"Berichtszeitpunkt = '{source_date}'"
    count = query(where=where, returnCountOnly="true")["count"]
    ids = sorted(query(where=where, returnIdsOnly="true")["objectIds"])

    def batch(selected):
        response = query(where=f"{where} AND ObjectId >= {selected[0]} AND ObjectId <= {selected[-1]}", outFields="*",
                         returnGeometry="false", orderByFields="ObjectId ASC")
        if response.get("exceededTransferLimit"):
            raise ValueError("KBA batch exceeded transfer limit; decrease batch size")
        rows = [f["attributes"] for f in response["features"]]
        check_completeness(rows, selected, len(selected))
        return rows

    # Fixed object-ID batches avoid offset pagination skipping rows during a refresh.
    with ThreadPoolExecutor(max_workers=4) as pool:
        pages = pool.map(batch, (ids[i:i + 500] for i in range(0, len(ids), 500)))
        rows = sorted((r for page in pages for r in page), key=lambda r: r["ObjectId"])
    check_completeness(rows, ids, count)
    final_ids = query(where=where, returnIdsOnly="true")["objectIds"]
    check_completeness(rows, final_ids, query(where=where, returnCountOnly="true")["count"])
    table = normalize(rows, reference_date)
    # Lossless attribute snapshot, not a byte-for-byte HTTP response archive.
    snapshot = gzip.compress((json.dumps({"objectIds": ids, "rows": rows}, ensure_ascii=False,
                                        separators=(",", ":")) + "\n").encode("utf-8"), mtime=0)
    metadata = {
        "schemaVersion": 1, "version": version, "referenceDate": reference_date,
        "retrievedOn": date.today().isoformat(), "recordCount": count,
        "title": "FZ Hersteller Handelsnamen Kfz", "publisher": "Kraftfahrt-Bundesamt (KBA)",
        "url": CATALOG, "serviceUrl": SERVICE, "license": "dl-de/by-2-0",
        "licenseUrl": "https://www.govdata.de/dl-de/by-2-0",
        "modifications": "Selected one reference date; renamed columns, sorted rows and represented null as \\N. Source labels, counts and statistical markers unchanged.",
        "snapshot": "source.json.gz", "snapshotSha256": digest(snapshot),
        "table": "types.tsv", "sha256": digest(table),
    }
    directory.mkdir(parents=True, exist_ok=True)
    (directory / metadata["snapshot"]).write_bytes(snapshot)
    (directory / metadata["table"]).write_bytes(table)
    (directory / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                                               encoding="utf-8", newline="\n")
    print(f"Imported {count} source records for {reference_date}")


def validate(directory=DIRECTORY):
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    required = {"schemaVersion", "version", "referenceDate", "retrievedOn", "recordCount", "title",
                "publisher", "url", "serviceUrl", "license", "licenseUrl", "modifications",
                "snapshot", "snapshotSha256", "table", "sha256"}
    if set(metadata) != required or metadata["schemaVersion"] != 1:
        raise ValueError("Unexpected KBA metadata schema")
    if (metadata["snapshot"] != "source.json.gz" or metadata["table"] != "types.tsv"
            or metadata["license"] != "dl-de/by-2-0"
            or metadata["licenseUrl"] != "https://www.govdata.de/dl-de/by-2-0"
            or metadata["url"] != CATALOG or metadata["serviceUrl"] != SERVICE):
        raise ValueError("KBA provenance/terms changed; review the importer first")
    for key in required - {"schemaVersion", "recordCount"}:
        if not isinstance(metadata[key], str) or not metadata[key]:
            raise ValueError(f"Missing KBA metadata: {key}")
        cell(metadata[key])
    date.fromisoformat(metadata["retrievedOn"])
    if not re.fullmatch(r"\d{4}\.\d{2}\.\d{2}\.\d+", metadata["version"]):
        raise ValueError("Invalid KBA dataset version")
    snapshot = (directory / metadata["snapshot"]).read_bytes()
    table = (directory / metadata["table"]).read_bytes()
    if digest(snapshot) != metadata["snapshotSha256"] or digest(table) != metadata["sha256"]:
        raise ValueError("Missing or changed KBA snapshot/table")
    source = json.loads(gzip.decompress(snapshot))
    check_completeness(source["rows"], source["objectIds"], metadata["recordCount"])
    if normalize(source["rows"], metadata["referenceDate"]) != table:
        raise ValueError("KBA table differs from its source snapshot")
    return metadata


def render_metadata(metadata):
    keys = ("version", "sha256", "referenceDate", "recordCount", "title", "publisher", "url",
            "serviceUrl", "retrievedOn", "license", "licenseUrl", "modifications", "snapshotSha256")
    return "\t".join(cell(metadata[k]) for k in keys) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--import-date", help="Explicitly download YYYY-MM-DD; never used by builds")
    parser.add_argument("--version", help="Dataset version required for imports, e.g. 2026.09.25.1")
    args = parser.parse_args()
    if args.import_date:
        if not args.version or not re.fullmatch(r"\d{4}\.\d{2}\.\d{2}\.\d+", args.version):
            parser.error("--import-date requires --version YYYY.MM.DD.N")
        download(args.import_date, args.version)
    result = validate()
    print(f"Validated {result['recordCount']} KBA rows; SHA-256 {result['sha256']}")
