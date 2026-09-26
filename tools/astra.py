"""Reproducible ASTRA passenger-car type-approval candidate projection (offline)."""
import argparse
import base64
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data/astra"
SOURCE_URL = "https://opendata.astra.admin.ch/ivzod/2000-Typengenehmigungen_TG_TARGA/2200-Basisdaten_TG_ab_1995/TG-Automobil.txt"
FIELDS = (
    ("make", "Make", "04 Marke", ""),
    ("type", "Approval type (original name)", "04 Typ", ""),
    ("variant", "Type / variant / version", "05 Typ; Variante/Version", ""),
    ("vehicleCategory", "Vehicle category", "03 Fahrzeugklasse", ""),
    ("body", "Body style", "07 Karosserieform", ""),
    ("euApproval", "EU type approval", "09 EU-Gesamtgenehmigung", ""),
    ("drive", "Drive (source code)", "17 Achsantrieb", ""),
    ("engineMake", "Engine manufacturer", "25 Motor Marke", ""),
    ("engineCode", "Engine type", "25 Motor Typ", ""),
    ("fuelCode", "Fuel (source code)", "26 Bauart Treibstoff", ""),
    ("displacementCc", "Displacement", "27 Hubraum", "cm3"),
    ("powerKw", "Engine power", "28 Leistung kW", "kW"),
    ("seatsMin", "Seats minimum", "37 Anzahl Plätze Total von", ""),
    ("seatsMax", "Seats maximum", "37 Anzahl Plätze Total bis", ""),
    ("doors", "Doors (source notation)", "38 Anzahl Türen", ""),
    ("remarks", "Approval remarks", "Bemerkungen Z1–Z24", ""),
)


def digest(content):
    return hashlib.sha256(content).hexdigest()


def b64(text):
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def compressed(content):
    # GzipFile keeps the OS header stable across Python versions and platforms.
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", filename="", mtime=0) as stream:
        stream.write(content)
    return buffer.getvalue()


def templates(value):
    """Reject the complete row if any alternative is outside the reviewed grammar.

    Dots are unspecified positions, never literal characters. No repair of O/0,
    shortened/overlong templates, wildcard WMIs or prose is attempted.
    """
    parts = [part.strip() for part in value.split(" / ")]
    if not all(re.fullmatch(r"[A-HJ-NPR-Z0-9]{3}[A-HJ-NPR-Z0-9.]{14}", p)
               and sum(c != "." for c in p) >= 4 for p in parts):
        return ()
    return tuple(sorted(set(parts)))


def compile_snapshot(snapshot, output, source):
    output.mkdir(parents=True, exist_ok=True)
    buckets = defaultdict(list)
    counts = Counter()
    makes = set()
    ids = set()
    with gzip.open(snapshot, "rt", encoding="cp1252", newline="") as stream:
        reader = csv.reader(stream, delimiter="\t")
        header = next(reader)
        positions = [([header.index(f"Bemerkungen Z{i}") for i in range(1, 25)] if field[0] == "remarks"
                      else [header.index(field[2])]) for field in FIELDS]
        category = header.index("03 Fahrzeugklasse")
        pattern_column = header.index("06 Vorziffer")
        for line, row in enumerate(reader, 2):
            counts["sourceRows"] += 1
            if len(row) != len(header) - 1 or header[-1] != "":
                raise ValueError(f"ASTRA row {line}: inconsistent column count")
            if row[category] not in ("M1", "M1G"):
                counts["excludedNonPassengerRows"] += 1
                continue
            counts["passengerRows"] += 1
            patterns = templates(row[pattern_column])
            if not patterns:
                counts["excludedPatternRows"] += 1
                continue
            if row[0] in ids or not re.fullmatch(r"[A-Z0-9]+", row[0]):
                raise ValueError(f"Invalid/duplicate approval ID: {row[0]}")
            ids.add(row[0])
            counts["approvalRows"] += 1
            counts["patterns"] += len(patterns)
            makes.add(row[positions[0][0]])
            cells = [row[0], str(line), b64(row[pattern_column]), ",".join(patterns)]
            cells += [b64("\n".join(row[i] for i in group if row[i])) for group in positions]
            for wmi in sorted({p[:3] for p in patterns}):
                buckets[wmi].append("\t".join(cells) + "\n")
    index = [["V", "astra-targa-2026-07-30-v1"]]
    source_keys = ("id", "title", "publisher", "url", "edition", "section", "retrievedOn", "reuseBasis",
                   "archivePath", "archiveSha256", "inspectedSha256", "evidencePath")
    index.append(["D", *[b64(source[k]) for k in source_keys]])
    index.extend(["F", key, b64(label), b64(column), b64(unit)] for key, label, column, unit in FIELDS)
    # Intentional regeneration may remove a formerly accepted WMI. Only prune
    # generated shard names; unrelated files remain visible to inventory checks.
    for old in (output / "patterns").glob("*.tsv.gz"):
        wmi = old.name.removesuffix(".tsv.gz")
        if re.fullmatch(r"[A-HJ-NPR-Z0-9]{3}", wmi) and wmi not in buckets:
            old.unlink()
    for wmi, rows in sorted(buckets.items()):
        content = compressed("".join(sorted(rows)).encode("utf-8"))
        filename = f"patterns/{wmi}.tsv.gz"
        (output / "patterns").mkdir(exist_ok=True)
        (output / filename).write_bytes(content)
        index.append(["W", wmi, filename, digest(content)])
    content = "".join("\t".join(row) + "\n" for row in index).encode("utf-8")
    (output / "index.tsv").write_bytes(content)
    return {"version": index[0][1], "indexSha256": digest(content), "source": source,
            "counts": {**dict(counts), "wmis": len(buckets), "makes": len(makes)},
            "scope": "Swiss M1/M1G type-approval candidates; not proof of an individual vehicle's configuration or market",
            "patternPolicy": "Exactly 17 positions, literal WMI, at least one further fixed position; dots are unknown positions; slash alternatives all must pass. No inferred model year or build date.",
            "fields": [{"key": k, "label": label, "sourceColumn": column, "unit": unit} for k, label, column, unit in FIELDS]}


def validate(directory=DIRECTORY):
    metadata = json.loads((directory / "metadata.json").read_text())
    source = metadata["source"]
    archive = directory.parent / source["archivePath"]
    if digest(archive.read_bytes()) != source["archiveSha256"]:
        raise ValueError("ASTRA archive digest mismatch")
    with gzip.open(archive, "rb") as stream:
        original = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            original.update(chunk)
        if original.hexdigest() != source["inspectedSha256"]:
            raise ValueError("ASTRA original byte digest mismatch")
    with tempfile.TemporaryDirectory() as tmp:
        generated = Path(tmp)
        rebuilt = compile_snapshot(archive, generated, source)
        if rebuilt != metadata:
            raise ValueError("ASTRA projection metadata is stale")
        expected = {"metadata.json", "review.json", archive.name}
        for path in generated.rglob("*"):
            if path.is_file():
                relative = path.relative_to(generated)
                expected.add(relative.as_posix())
                if not (directory / relative).is_file() or path.read_bytes() != (directory / relative).read_bytes():
                    raise ValueError(f"ASTRA projection mismatch: {relative}")
        actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
        if actual != expected:
            raise ValueError("ASTRA projection contains missing/unaccounted files")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compile", action="store_true")
    args = parser.parse_args()
    if args.compile:
        metadata = json.loads((DIRECTORY / "metadata.json").read_text())
        metadata = compile_snapshot(DIRECTORY.parent / metadata["source"]["archivePath"], DIRECTORY, metadata["source"])
        (DIRECTORY / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    else:
        metadata = validate()
    print(json.dumps(metadata["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
