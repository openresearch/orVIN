"""Build a shared, exact-label identity catalogue from retained source records."""
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
import nhtsa

ROOT = nhtsa.ROOT
VERSION = "2026.09.26.1"
SOURCE_KEYS = ("id", "publisher", "title", "url", "edition", "section", "retrievedOn", "reuseBasis", "license", "termsUrl", "modifications", "archiveSha256", "inspectedSha256", "evidencePath")
DISPLAY = {"VOLKSWAGEN": ("vw", "VW"), "SKODA": ("skoda", "Škoda"), "BMW": ("bmw", "BMW"),
           "MERCEDES-BENZ": ("mercedes-benz", "Mercedes-Benz"), "TESLA": ("tesla", "Tesla"),
           "HONDA": ("honda", "Honda"), "TOYOTA": ("toyota", "Toyota"), "FORD": ("ford", "Ford"),
           "AUDI": ("audi", "Audi"), "SEAT": ("seat", "SEAT"), "CUPRA": ("cupra", "CUPRA"),
           "RENAULT": ("renault", "Renault"), "PEUGEOT": ("peugeot", "Peugeot"),
           "CITROEN": ("citroen", "Citroën"), "FIAT": ("fiat", "Fiat"), "OPEL": ("opel", "Opel"),
           "VAUXHALL": ("vauxhall", "Vauxhall"), "VOLVO": ("volvo", "Volvo"), "HYUNDAI": ("hyundai", "Hyundai"),
           "KIA": ("kia", "Kia"), "NISSAN": ("nissan", "Nissan"), "MAZDA": ("mazda", "Mazda"),
           "SUZUKI": ("suzuki", "Suzuki"), "MITSUBISHI": ("mitsubishi", "Mitsubishi"), "MINI": ("mini", "MINI"),
           "PORSCHE": ("porsche", "Porsche"), "DACIA": ("dacia", "Dacia"), "LEXUS": ("lexus", "Lexus"),
           "JEEP": ("jeep", "Jeep"), "LAND ROVER": ("land-rover", "Land Rover"), "JAGUAR": ("jaguar", "Jaguar"),
           "CHEVROLET": ("chevrolet", "Chevrolet"), "SUBARU": ("subaru", "Subaru"), "RENAULT TRUCKS": ("renault-trucks", "Renault Trucks")}


def key(value):
    return value.strip().translate(str.maketrans("abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"))


def b64(value):
    return base64.b64encode(str(value or "").encode()).decode()


def slug(value):
    # Encode every non-ASCII-alphanumeric byte, so punctuation cannot collapse identities.
    return "".join(chr(b).lower() if 65 <= b <= 90 or 97 <= b <= 122 or 48 <= b <= 57 else f"~{b:02x}" for b in value.encode())


def build():
    with zipfile.ZipFile(ROOT / "data/nhtsa" / nhtsa.FILENAME) as archive:
        with archive.open(archive.namelist()[0]) as stream:
            tables, _ = nhtsa.read_tables(io.TextIOWrapper(stream, encoding="utf-8-sig"), {"make", "model", "make_model"})
    sources = {s["id"]: dict(s) for s in json.loads((ROOT / "data/decoding/sources.json").read_text())}
    astra = json.loads((ROOT / "data/astra/metadata.json").read_text())
    sources[astra["source"]["id"]] = dict(astra["source"])
    kba = json.loads((ROOT / "data/kba/metadata.json").read_text())
    kba_id = "kba-fz-types-2026-01-01"
    sources[kba_id] = {**kba, "id": kba_id, "edition": kba["referenceDate"],
        "section": "FeatureServer layer 0; sourceObjectId", "reuseBasis": kba["license"], "termsUrl": kba["licenseUrl"],
        "archiveSha256": kba["snapshotSha256"], "evidencePath": "kba/metadata.json",
        "modifications": kba["modifications"] + " Normalized output labels by ORvin; original labels retained in long evidence."}
    for sid, source in sources.items():
        if sid == nhtsa.SOURCE_ID:
            source.update(license="LicenseRef-NHTSA-Public-Information", termsUrl="https://www.nhtsa.gov/about-nhtsa/terms-use",
                          modifications="Selected and normalized factual associations from the retained vPIC snapshot.")
        elif sid == astra["source"]["id"]:
            source.update(termsUrl="https://www.fedlex.admin.ch/eli/cc/2023/682/de",
                          modifications="Passenger approvals filtered; VIN masks interpreted conservatively; labels normalized by ORvin.")
        elif sid != kba_id:
            source["modifications"] = "Selected factual associations structured and combined as scoped ORvin rules; labels normalized. Original documents not redistributed."
    makes, models, make_ids = {}, {}, {}
    for row in sorted(tables["make"], key=lambda r: int(r["id"])):
        label = key(row["name"])
        if not label:
            continue
        mid, name = DISPLAY.get(label, (slug(label), row["name"].strip()))
        makes.setdefault(label, (mid, name, nhtsa.SOURCE_ID, "vpic.make id=" + row["id"]))
        make_ids[row["id"]] = makes[label][0]
    # Exact ASTRA marque labels add coverage; never split multi-brand labels or corporate groups.
    definitions = [l.split("\t")[1] for l in (ROOT / "data/astra/index.tsv").read_text().splitlines() if l.startswith("F\t")]
    for line in (ROOT / "data/astra/index.tsv").read_text().splitlines():
        c = line.split("\t")
        if c[0] != "W":
            continue
        for row in gzip.decompress((ROOT / "data/astra" / c[2]).read_bytes()).decode().splitlines():
            cells = row.split("\t")
            # Field order is taken from the index, not assumed below.
            label = key(base64.b64decode(cells[4 + definitions.index("make")]).decode())
            if label and label not in makes:
                mid, name = DISPLAY.get(label, (slug(label), label))
                makes[label] = (mid, name, astra["source"]["id"], "TG-Automobil.txt row=" + cells[1] + "; approval=" + cells[0] + "; 04 Marke")
    # Explicit aliases supported by the retained OEM/KBA marque labels. Display casing is ORvin policy.
    for alias, target, sid, locator in [
        ("VW", "VOLKSWAGEN", "vw-golf-v-profile", "Golf V profile / Volkswagen marque; display preference VW"),
        ("VOLKSWAGEN-VW", "VOLKSWAGEN", kba_id, "sourceObjectId=196017; manufacturer=VOLKSWAGEN-VW"),
        ("BAYER.MOT.WERKE-BMW", "BMW", kba_id, "sourceObjectId=186388; manufacturer=BAYER.MOT.WERKE-BMW"),
    ]:
        mid, name, _, _ = makes[target]
        makes[alias] = (mid, name, sid, locator)
    names = {r["id"]: r["name"].strip() for r in tables["model"] if r["name"]}
    for row in sorted(tables["make_model"], key=lambda r: (int(r["makeid"]), int(r["modelid"]))):
        mid, name = make_ids.get(row["makeid"]), names.get(row["modelid"])
        if mid and name:
            models.setdefault((mid, key(name)), (mid + ":" + slug(key(name)), name, nhtsa.SOURCE_ID,
                "vpic.model id=" + row["modelid"] + "; vpic.make_model makeid=" + row["makeid"]))
    models[("vw", "GOLF")] = ("vw:golf", "Golf", "vw-golf-v-profile", "Golf V profile; model family Golf, factory type 1K")
    models[("tesla", "MODEL Y")] = ("tesla:model-y", "Model Y", "tesla-model-y-2025-service-manual", "Model Y 2025+ service manual / VIN decoding")
    models[("vw", "GOLF SPORTSVAN")] = ("vw:golf-sportsvan", "Golf Sportsvan", kba_id, "sourceObjectId=196017; tradeName=GOLF SPORTSVAN; case-only display normalization")
    rows = [["V", VERSION]]
    for source in sorted(sources.values(), key=lambda s: s["id"]):
        rows.append(["S", *[b64(source.get(k)) for k in SOURCE_KEYS]])
    for alias, (mid, name, sid, locator) in sorted(makes.items()):
        rows.append(["M", b64(alias), mid, b64(name), sid, b64(locator)])
    for (mid, alias), (model_id, name, sid, locator) in sorted(models.items()):
        rows.append(["D", mid, b64(alias), model_id, b64(name), sid, b64(locator)])
    return ("\n".join("\t".join(row) for row in rows) + "\n").encode()


def validate():
    directory = ROOT / "data/identity"
    metadata = json.loads((directory / "metadata.json").read_text())
    content = (directory / "index.tsv").read_bytes()
    if hashlib.sha256(content).hexdigest() != metadata["sha256"] or content != build():
        raise ValueError("Identity catalogue differs from reviewed source projection")
    fixture_bytes = (directory / "fixtures.json").read_bytes()
    if hashlib.sha256(fixture_bytes).hexdigest() != metadata["fixturesSha256"]:
        raise ValueError("Changed identity fixture permission/attribution")
    for fixture in json.loads(fixture_bytes):
        source = fixture["source"]
        if source["kind"] != "USER_CONTRIBUTION" or not source["permission"] or not source["attribution"] or not fixture["expectationBasis"]:
            raise ValueError("Real VIN fixture requires explicit permission and separated ground truth")
    return metadata


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args()
    if args.generate:
        directory = ROOT / "data/identity"
        directory.mkdir(exist_ok=True)
        content = build()
        (directory / "index.tsv").write_bytes(content)
        (directory / "metadata.json").write_text(json.dumps({"version": VERSION, "sha256": hashlib.sha256(content).hexdigest(),
            "policy": "Exact make-scoped labels only; ASCII case comparison and explicit sourced aliases. No fuzzy model-family inference. Canonical display names are ORvin policy.",
            "reviewedOn": "2026-09-26", "generator": "tools/identity.py",
            "fixturesSha256": hashlib.sha256((directory / "fixtures.json").read_bytes()).hexdigest()}, indent=2) + "\n")
    else:
        print(validate())
