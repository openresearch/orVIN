"""Compile portable public decoding rules from the pinned SQL-as-data archive.

No SQL is executed. Regeneration is deterministic and normal validation is offline.
The small index and compressed rule shards are shared by Python and Java.
"""
import argparse
import base64
from collections import Counter, defaultdict
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
import zipfile

import nhtsa

ROOT = nhtsa.ROOT
DIRECTORY = ROOT / "data/decoding"
VERSION = nhtsa.PINS["decodingVersion"]
REFERENCE_YEAR = nhtsa.PINS["referenceYear"]
SHARDS = 256
EXCLUDED = {26, 27, 29, 39}


def b64(value):
    return base64.b64encode(str(value).encode()).decode()


def rows_from(stream, wanted):
    """Stream selected COPY rows without retaining the 1.68M-row pattern table."""
    for line in stream:
        header = nhtsa.COPY.fullmatch(line)
        if not header:
            continue
        name, columns = header[1], header[2].split(", ")
        for line in stream:
            if line.rstrip("\r\n") == r"\.":
                break
            if name in wanted:
                values = line.rstrip("\r\n").split("\t")
                if len(values) != len(columns):
                    raise ValueError(f"Invalid COPY row in {name}")
                yield name, dict(zip(columns, map(nhtsa.copy_value, values)))
        else:
            raise ValueError(f"Unterminated COPY table: {name}")


def pattern_regex(key):
    """Published LIKE / sqlwild_to_regex semantics, in a common regex subset.

    Formula patterns match digits at # positions and return the first-to-last #
    substring. Bracket formulas do not participate in the SQL formula LIKE stage.
    """
    if key is None:
        raise ValueError("Null pattern key")
    bracket = "[" in key
    formula = "#" in key
    if bracket and formula:
        return None
    key_for_regex = key.replace("1-A", "1A") if bracket else key
    out, inside = [], False
    for ch in key_for_regex:
        if ch == "*" or (ch == "_" and not bracket):
            out.append(".")
        elif ch == "%" and not bracket:
            out.append(".*")
        elif ch == "#" and formula:
            out.append("[0-9]")
        elif ch == "[" and bracket:
            inside = True
            out.append(ch)
        elif ch == "]" and bracket:
            inside = False
            out.append(ch)
        elif ch == "-" and inside:
            out.append(ch)
        elif ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_":
            out.append(ch)
        elif ch in "|.\\^$+?{}()":
            out.append("\\" + ch)
        else:
            raise ValueError(f"Unsupported pattern character in {key!r}: {ch!r}")
    if inside:
        raise ValueError(f"Unterminated character class: {key}")
    regex = "^" + "".join(out)
    re.compile(regex)
    return regex


def read_small(archive):
    with archive.open(archive.namelist()[0]) as stream:
        # Catalog tables are small. Exclude result/validation/spec caches and the
        # large pattern table; the latter is streamed separately below.
        wanted = set(json.loads((ROOT / "data/nhtsa/metadata.json").read_text())["tables"])
        wanted -= {"pattern", "wmiyearvalidchars", "vehiclespecpattern", "decodingoutput"}
        return nhtsa.read_tables(io.TextIOWrapper(stream, encoding="utf-8-sig"), wanted)[0]


def compile_archive(destination):
    source = ROOT / "data/nhtsa" / nhtsa.FILENAME
    if nhtsa.sha256(source) != nhtsa.SHA256:
        raise ValueError("Unreviewed NHTSA source archive")
    destination.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    with zipfile.ZipFile(source) as archive:
        tables = read_small(archive)
        elements = {r["id"]: r for r in tables["element"]
                    if r["isprivate"] != "t" and r["decode"] is not None}
        schemas = {r["id"] for r in tables["vinschema"] if r["tobeqced"] != "t"}
        public_wmis = {a["wmi"] for a in json.loads((ROOT / "data/dataset.json").read_text())["assignments"]}
        wmis = {r["id"]: r for r in tables["wmi"] if r["wmi"] in public_wmis}
        dictionaries = {name: {r["id"]: r.get("name") for r in rows if "id" in r}
                        for name, rows in tables.items()}

        def value(element, attr):
            if attr is None or not attr.strip():
                return None
            if element["datatype"] == "lookup":
                result = dictionaries[element["lookuptable"].lower()].get(attr)
                if result is None:
                    return None
                return result.strip()
            return attr.strip()

        index = [["V", VERSION, str(REFERENCE_YEAR), nhtsa.SOURCE_ID, nhtsa.SHA256]]
        europe = json.loads((ROOT / "data/europe/tesla-model-y.json").read_text())
        index.append(["T", europe["source"]["id"], europe["source"]["url"]])
        for position, characters in europe["requirements"].items():
            index.append(["R", position, characters])
        for code, year in europe["years"].items():
            index.append(["Y", code, str(year)])
        for layout in europe["layouts"]:
            for code, val in layout["fields"].items():
                index.append(["L", layout["wmi"], layout["plant"], code, b64(val)])
        for attribute in europe["attributes"]:
            for code, val in attribute["fields"].items():
                index.append(["A", str(attribute["position"]), attribute["characters"], code, b64(val)])
        for eid, code, label, datatype in [(10001, "ProductionYear", "Production year", "int"),
                                           (10002, "BatteryChemistry", "Battery chemistry", "string"),
                                           (10003, "MotorConfiguration", "Motor configuration", "string")]:
            index.append(["E", str(eid), code, b64(label), datatype])
        volkswagen = json.loads((ROOT / "data/europe/vw-golf-1k-2005.json").read_text())
        for rule in volkswagen["rules"]:
            index.append(["O", rule["id"], b64(rule["pattern"]), str(rule["modelYear"])])
            for code, val in rule["fields"].items():
                for source in volkswagen["sources"]:
                    if source["id"] not in volkswagen["fieldSources"][code]:
                        continue
                    index.append(["F", rule["id"], code, b64(val), source["id"], source["url"]])
        documents = source_documents(europe, volkswagen)
        for source in documents:
            keys = ("id", "title", "publisher", "url", "edition", "section", "retrievedOn", "reuseBasis",
                    "archivePath", "archiveSha256", "inspectedSha256", "evidencePath")
            index.append(["D", *(b64(source.get(key) or "") for key in keys)])
        (destination / "sources.json").write_text(nhtsa.json_text(documents), encoding="utf-8", newline="\n")
        for r in sorted(elements.values(), key=lambda r: int(r["id"])):
            index.append(["E", r["id"], r["code"], b64(r["name"]), r["datatype"]])
        for r in sorted(wmis.values(), key=lambda r: r["wmi"]):
            index.append(["W", r["wmi"], r["id"], r["vehicletypeid"], r["trucktypeid"] or ""])
        for r in sorted(tables["wmi_vinschema"], key=lambda r: int(r["id"])):
            if r["wmiid"] in wmis and r["vinschemaid"] in schemas and r["yearfrom"] is not None:
                index.append(["S", wmis[r["wmiid"]]["wmi"], r["vinschemaid"], r["yearfrom"], r["yearto"] or "2999"])
        for r in sorted(tables["make_model"], key=lambda r: int(r["modelid"])):
            index.append(["M", r["modelid"], r["makeid"], b64(dictionaries["make"][r["makeid"]].strip().upper())])
        engine_names = {r["id"]: r["name"].strip().lower() for r in tables["enginemodel"]}
        for r in sorted(tables["enginemodelpattern"], key=lambda r: int(r["id"])):
            e = elements.get(r["elementid"])
            if e is not None and (v := value(e, r["attributeid"])) is not None:
                index.append(["G", b64(engine_names[r["enginemodelid"]]), r["id"], r["elementid"],
                              b64(r["attributeid"]), b64(v), r["updatedon"] or r["createdon"] or ""])
        for r in sorted(tables["conversion"], key=lambda r: int(r["id"])):
            formula = re.fullmatch(r"#x#\s*([*/])\s*([0-9.]+)\s*", r["formula"])
            if not formula:
                raise ValueError("Unsupported conversion formula")
            index.append(["C", r["id"], r["fromelementid"], r["toelementid"], formula[1], formula[2]])

        shards = defaultdict(list)
        with archive.open(archive.namelist()[0]) as stream:
            for _, p in rows_from(io.TextIOWrapper(stream, encoding="utf-8-sig"), {"pattern"}):
                counts["sourcePatterns"] += 1
                e = elements.get(p["elementid"])
                if e is None or int(p["elementid"]) in EXCLUDED or p["vinschemaid"] not in schemas:
                    counts["excludedPrivateUndecodedOrQc"] += 1
                    continue
                regex = pattern_regex(p["keys"])
                if regex is None:
                    counts["unsupportedBracketFormula"] += 1
                    continue
                formula = "#" in p["keys"]
                v = value(e, p["attributeid"])
                if v is None and not formula:
                    counts["missingValueOrDictionaryEntry"] += 1
                    continue
                key = p["keys"]
                start = key.index("#") if formula else -1
                length = key.rindex("#") - start + 1 if formula else 0
                row = [p["vinschemaid"], p["id"], p["elementid"], b64(key), b64(p["attributeid"] or ""),
                       b64(v or ""), p["updatedon"] or p["createdon"] or "", b64(regex), str(start), str(length)]
                shards[int(p["vinschemaid"]) % SHARDS].append((int(p["id"]), "\t".join(row)))
                counts["exportedPatterns"] += 1
        for bucket, rows in sorted(shards.items()):
            name = f"patterns-{bucket:03d}.tsv.gz"
            # GzipFile has a fixed mtime and no embedded filename across platforms.
            with (destination / name).open("wb") as output:
                with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0, compresslevel=9) as zipped:
                    zipped.write(("\n".join(row for _, row in sorted(rows)) + "\n").encode())
            index.append(["H", name, nhtsa.sha256(destination / name)])
        (destination / "index.tsv").write_text("".join("\t".join(row) + "\n" for row in index), encoding="utf-8", newline="\n")
    metadata = {"formatVersion": 1, "version": VERSION, "sourceId": nhtsa.SOURCE_ID,
                "sourceSha256": nhtsa.SHA256, "referenceYear": REFERENCE_YEAR,
                "indexSha256": nhtsa.sha256(destination / "index.tsv"),
                "sourcesSha256": nhtsa.sha256(destination / "sources.json"), "counts": dict(sorted(counts.items())),
                "stages": ["public-patterns", "model-make", "engine-model", "displacement-conversion"],
                "notImplemented": ["vehicle-spec-enrichment", "defaults", "vin-repair", "vpic-error-scoring"],
                "marketScope": "US", "numericValues": "Source strings; converted displacement rounded to six decimal places."}
    (destination / "metadata.json").write_text(nhtsa.json_text(metadata), encoding="utf-8", newline="\n")
    return metadata


def source_documents(tesla, volkswagen):
    """A stable source record travels with every rule and installed distribution."""
    base = json.loads((ROOT / "data/dataset.json").read_text())["sources"][0]
    nhtsa_source = {"id": base["id"], "title": base["title"], "publisher": base["publisher"], "url": base["url"],
                    "edition": base["publicationVersion"],
                    "section": "pattern, vinschema, wmi_vinschema, element dictionaries, make_model, engine-model and conversion tables; spvindecode_core and fvinmodelyear2 semantics",
                    "retrievedOn": base["retrievedOn"], "reuseBasis": base["reuse"]["basis"],
                    "archivePath": base["snapshot"], "archiveSha256": base["sha256"],
                    "inspectedSha256": base["sha256"], "evidencePath": "decoding/metadata.json"}
    documents = [nhtsa_source]
    for source, path, reuse in [(tesla["source"], "europe/tesla-model-y.json", tesla["source"]["reuseBasis"]),
                                *((s, "europe/vw-golf-1k-2005.json", volkswagen["reuseBasis"]) for s in volkswagen["sources"])]:
        documents.append({"id": source["id"], "title": source["title"], "publisher": source["publisher"],
                          "url": source["url"], "edition": source["edition"], "section": source["section"],
                          "retrievedOn": source["retrievedOn"], "reuseBasis": reuse, "archivePath": None,
                          "archiveSha256": None, "inspectedSha256": source.get("inspectedSha256"), "evidencePath": path})
    import kba_wmi
    _, metadata = kba_wmi.load()
    documents.append(metadata["source"])
    return sorted(documents, key=lambda s: s["id"])


def validate():
    with tempfile.TemporaryDirectory(prefix="orvin-decoding-") as temporary:
        directory = Path(temporary)
        metadata = compile_archive(directory)
        if {p.name for p in DIRECTORY.iterdir()} != {p.name for p in directory.iterdir()}:
            raise ValueError("Decoding file inventory mismatch; run tools/decoding.py import")
        for path in directory.iterdir():
            if nhtsa.sha256(path) != nhtsa.sha256(DIRECTORY / path.name):
                raise ValueError(f"Stale decoding projection: {path.name}; run tools/decoding.py import")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("import", "validate"))
    args = parser.parse_args()
    metadata = compile_archive(DIRECTORY) if args.command == "import" else validate()
    print(json.dumps(metadata["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
