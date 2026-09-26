"""Validate canonical JSON and compile a deterministic, internal TSV resource."""
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator, FormatChecker
import kba
import nhtsa
import decoding
import provenance
import astra

ROOT = Path(__file__).resolve().parents[1]


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def indexed(items, kind):
    result = {}
    for item in items:
        if item["id"] in result:
            raise ValueError(f"Duplicate {kind} id: {item['id']}")
        result[item["id"]] = item
    return result


def overlap(a, b):
    left, right = a["constraints"], b["constraints"]
    if max(left.get("fromModelYear", 1886), right.get("fromModelYear", 1886)) > min(
        left.get("toModelYear", 9999), right.get("toModelYear", 9999)
    ):
        return False
    return not (left.get("markets") and right.get("markets") and
                set(left["markets"]).isdisjoint(right["markets"]))


def validate(data, data_dir=ROOT / "data"):
    schema = read_json(ROOT / "data/schema.json")
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(data)
    sources = indexed(data["sources"], "source")
    manufacturers = indexed(data["manufacturers"], "manufacturer")
    indexed(data["assignments"], "assignment")
    for item in data["manufacturers"] + data["assignments"]:
        for source in item["sourceRefs"]:
            if source not in sources:
                raise ValueError(f"{item['id']}: unknown source {source}")
    for source in sources.values():
        if "snapshot" in source:
            path = data_dir / source["snapshot"]
            if not path.is_file() or nhtsa.sha256(path) != source["sha256"]:
                raise ValueError(f"{source['id']}: missing or changed snapshot")
    for assignment in data["assignments"]:
        if assignment["manufacturerId"] not in manufacturers:
            raise ValueError(f"{assignment['id']}: unknown manufacturer")
        constraints = assignment["constraints"]
        if constraints.get("fromModelYear", 1886) > constraints.get("toModelYear", 9999):
            raise ValueError(f"{assignment['id']}: reversed model-year interval")
    by_wmi, prefix_lengths = defaultdict(list), defaultdict(set)
    for assignment in data["assignments"]:
        wmi = assignment["wmi"]
        by_wmi[wmi].append(assignment)
        prefix_lengths[wmi[:3]].add(len(wmi))
    for prefix, lengths in prefix_lengths.items():
        if len(lengths) > 1:
            raise ValueError(f"Ordinary/extended prefix collision: {prefix}")
    for assignments in by_wmi.values():
        for a, b in itertools.combinations(assignments, 2):
            if not overlap(a, b):
                continue
            if all(a.get(key) == b.get(key) for key in ("manufacturerId", "brand", "category")):
                raise ValueError(f"Duplicate overlapping assignment: {a['id']}, {b['id']}")
            if not a.get("ambiguityGroup") or a.get("ambiguityGroup") != b.get("ambiguityGroup"):
                raise ValueError(f"Unexplained conflicting assignments: {a['id']}, {b['id']}")


def validate_fixtures(fixtures, data, *, exhaustive=True):
    assignments = {a["id"] for a in data["assignments"]}
    covered = set()
    required = {"assignmentId", "vin", "manufacturerId", "wmi", "brand", "category"}
    if not isinstance(fixtures, list) or not fixtures:
        raise ValueError("Behavior fixtures must be a non-empty array")
    for fixture in fixtures:
        if not isinstance(fixture, dict) or set(fixture) != required:
            raise ValueError("Unexpected fixture fields")
        if not all(isinstance(v, str) and v and not re.search(r"[\x00-\x1f\x7f]", v)
                   for v in fixture.values()):
            raise ValueError("Invalid fixture value")
        if not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", fixture["vin"]):
            raise ValueError("Assignment fixture must use a synthetic 17-character identifier")
        if fixture["assignmentId"] not in assignments:
            raise ValueError("Fixture references an unknown assignment")
        covered.add(fixture["assignmentId"])
    if exhaustive and covered != assignments:
        raise ValueError(f"Assignments without behavior fixtures: {sorted(assignments - covered)}")


def render(data, digest):
    rows = [["V", data["version"], digest]]
    for s in sorted(data["sources"], key=lambda x: x["id"]):
        rows.append(["S", s["id"], s["title"], s["url"], s["publisher"], s["retrievedOn"],
                     s["publicationVersion"], s["section"], s["reuse"]["license"],
                     s["reuse"]["url"], s["reuse"]["basis"], s.get("snapshot", ""), s.get("sha256", "")])
    for m in sorted(data["manufacturers"], key=lambda x: x["id"]):
        rows.append(["M", m["id"], m["name"], m.get("country", ""), ",".join(m["sourceRefs"])])
    for a in sorted(data["assignments"], key=lambda x: x["id"]):
        c = a["constraints"]
        rows.append(["A", a["id"], a["wmi"], a["manufacturerId"], a.get("brand", ""),
                     a.get("category", ""), ",".join(a["sourceRefs"]),
                     ",".join(sorted(c.get("markets", []))), str(c.get("fromModelYear", "")),
                     str(c.get("toModelYear", "")), a["notes"], a.get("ambiguityGroup", ""),
                     a.get("ambiguityReason", "")])
    return "".join("\t".join(row) + "\n" for row in rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--update-runtime", action="store_true",
                        help="Refresh checked-in Java resources after an intentional data edit")
    args = parser.parse_args()
    path = ROOT / "data/dataset.json"
    data = read_json(path)
    validate(data)
    # Full source reconstruction covers every imported row. Behavioral fixtures
    # remain independently reviewed examples, not generated copies of the data.
    nhtsa_metadata = nhtsa.validate()
    decoding_metadata = decoding.validate()
    astra_metadata = astra.validate()
    fixtures = read_json(ROOT / "data/fixtures.json")
    validate_fixtures(fixtures, data, exhaustive=False)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    kba_metadata = kba.validate()
    provenance_counts = provenance.validate()
    identity_metadata = read_json(ROOT / "data/identity/metadata.json")
    metadata_hash = hashlib.sha256((ROOT / "data/kba/metadata.json").read_bytes()).hexdigest()
    resources = {"dataset.tsv": render(data, digest),
                 "identity-metadata.tsv": identity_metadata["version"] + "\t" + identity_metadata["sha256"] + "\n",
                 "astra-metadata.tsv": astra_metadata["version"] + "\t" + astra_metadata["indexSha256"] + "\n",
                 "decoding-metadata.tsv": decoding_metadata["version"] + "\t" + decoding_metadata["indexSha256"] + "\n",
                 "kba-metadata.tsv": kba.render_metadata(kba_metadata).rstrip("\n") + "\t" + metadata_hash + "\n"}
    for name, content in resources.items():
        resource = ROOT / "libs/java/src/main/resources/com/openresearch/orvin" / name
        if args.update_runtime:
            resource.parent.mkdir(parents=True, exist_ok=True)
            resource.write_text(content, encoding="utf-8", newline="\n")
        if not resource.exists() or resource.read_bytes() != content.encode("utf-8"):
            raise ValueError(f"Stale {name}; run tools/dataset.py --update-runtime and review the diff")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render(data, digest), encoding="utf-8", newline="\n")
        fixture_file = ROOT / "libs/java/target/generated-test-resources/fixtures.tsv"
        fixture_file.parent.mkdir(parents=True, exist_ok=True)
        fixture_file.write_text("".join("\t".join(f[key] for key in (
            "assignmentId", "vin", "manufacturerId", "wmi", "brand", "category"
        )) + "\n" for f in fixtures), encoding="utf-8", newline="\n")
        kba_fixtures = read_json(ROOT / "data/kba/fixtures.json")
        keys = ("hsn", "tsn", "manufacturer", "tradeName", "registeredCount", "countMarker", "sourceObjectId")
        if not kba_fixtures or any(set(f) != set(keys) for f in kba_fixtures):
            raise ValueError("Unexpected KBA fixture fields")
        fixture_file.with_name("kba-fixtures.tsv").write_text("".join(
            "\t".join(kba.cell(f[k]) for k in keys) + "\n" for f in kba_fixtures), encoding="utf-8", newline="\n")
        vehicle_fixtures = read_json(ROOT / "data/vehicle-fixtures.json")
        fixture_file.with_name("vehicle-fixtures.tsv").write_text("".join(
            "\t".join((f["id"], f["vin"], f["market"], code, decoding.b64(value))) + "\n"
            for f in vehicle_fixtures for code, value in f["expected"].items()), encoding="utf-8", newline="\n")
    print(f"Validated {len(data['assignments'])} assignments; dataset {data['version']}; SHA-256 {digest}")
    print(f"Validated {kba_metadata['recordCount']} KBA entries for {kba_metadata['referenceDate']}")
    print(f"Validated complete NHTSA archive: {len(nhtsa_metadata['tables'])} tables; {nhtsa_metadata['runtimeWmiCount']} usable WMIs")
    print("Validated provenance: " + json.dumps(provenance_counts, sort_keys=True))
    print(f"Validated ASTRA: {astra_metadata['counts']['approvalRows']} passenger-car approval candidates")


if __name__ == "__main__":
    main()
