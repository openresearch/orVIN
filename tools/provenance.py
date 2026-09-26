"""Offline provenance checks; full source-to-projection reconstruction is in dataset.py."""
import argparse
import gzip
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

import decoding
import nhtsa
import europe_coverage
import benchmark_wa
import identity

ROOT = nhtsa.ROOT
RESEARCH_FILES = ("README.md", "framework.md", "nhtsa-bulk.md", "europe.md", "asia.md", "americas-uk.md",
                  "../astra-review.md", "../europe-priority/README.md", "bmw-subaru-followup.md",
                  "../data-redistribution/README.md")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def source_record(source):
    for field in ("id", "publisher", "title", "url", "edition", "section", "retrievedOn", "reuseBasis"):
        require(isinstance(source.get(field), str) and source[field].strip(),
                f"Source {source.get('id')}: missing {field}")
    url = urlsplit(source["url"])
    require(url.scheme in ("https", "http") and url.netloc, f"Invalid source URL: {source['id']}")
    date.fromisoformat(source["retrievedOn"])
    for field in ("sha256", "archiveSha256", "inspectedSha256"):
        if source.get(field) is not None:
            require(re.fullmatch("[0-9a-f]{64}", source[field]), f"Invalid {field}: {source['id']}")


def snapshot(data_dir, relative, digest):
    path = data_dir / relative
    require(path.resolve().is_relative_to(data_dir.resolve()), "Snapshot escapes data directory")
    require(path.is_file() and nhtsa.sha256(path) == digest, f"Missing or changed source file: {relative}")


def references(refs, sources, label):
    require(isinstance(refs, list) and refs and all(isinstance(s, str) for s in refs),
            f"Missing source references: {label}")
    require(len(refs) == len(set(refs)) and set(refs) <= set(sources), f"Unknown/duplicate source reference: {label}")


def oem_sources(tesla, volkswagen):
    sources = [tesla["source"], *volkswagen["sources"]]
    ids = [s["id"] for s in sources]
    require(len(ids) == len(set(ids)), "Duplicate OEM source ID")
    for source in sources:
        source_record({**source, "reuseBasis": source.get("reuseBasis", volkswagen["reuseBasis"])})
        require(source.get("archiveStatus"), f"Missing archive status: {source['id']}")
        if not source.get("inspectedSha256"):
            require(source.get("hashUnavailableReason"), f"Missing inspected hash explanation: {source['id']}")
    require(tesla["source"].get("scope") and volkswagen.get("scope") and volkswagen.get("assessment"),
            "OEM rules must document their scope and synthesis")
    fields = {code for rule in volkswagen["rules"] for code in rule["fields"]}
    require(fields == set(volkswagen["fieldSources"]), "Missing/unused OEM field source mapping")
    for field, refs in volkswagen["fieldSources"].items():
        references(refs, {s["id"] for s in volkswagen["sources"]}, field)
    rule_ids = [r["id"] for r in volkswagen["rules"]]
    require(len(rule_ids) == len(set(rule_ids)), "Duplicate OEM rule ID")
    for rule in volkswagen["rules"]:
        require(rule["fields"], f"Empty rule: {rule['id']}")
        re.compile(rule["pattern"])
    return sources


def research_inventory(root=ROOT):
    """Index citation locations; this does not promote or independently verify a lead."""
    sources = {}
    directory = root / "docs/research/vin-rules"
    for name in RESEARCH_FILES:
        section = "Document introduction"
        for line in (directory / name).read_text().splitlines():
            if line.startswith("#"):
                section = line.lstrip("# ")
            for url in re.findall(r"https?://[^\s<>\]\)\"`]+", line):
                url = url.rstrip(".,;:")
                record = sources.setdefault(url, {"id": "research-" + hashlib.sha256(url.encode()).hexdigest()[:16],
                                                  "url": url, "role": "research-citation", "locations": []})
                location = {"document": name, "section": section}
                if location not in record["locations"]:
                    record["locations"].append(location)
    return sorted(sources.values(), key=lambda s: s["url"])


def inventory(data_dir, expected):
    actual = {p.relative_to(data_dir).as_posix() for p in data_dir.rglob("*") if p.is_file()}
    require(actual == expected, f"Unaccounted/missing data files: {sorted(actual ^ expected)}")


def validation_corpus(root):
    """Check the separate ODbL corpus and recorded report without decoding again."""
    directory = root / "validation/wa-ev"
    source = read(directory / "source.json")
    source_record({"id": source["sourceId"], "publisher": source["publisher"], "title": source["title"],
                   "url": source["sourceUrl"], "edition": source["temporal"]["Period of Time"],
                   "section": source["queryUrl"], "retrievedOn": source["retrievedOn"][:10],
                   "reuseBasis": source["reuse"]["attribution"] + " " + source["reuse"]["url"]})
    snapshot(directory, source["snapshot"], source["snapshotSha256"])
    raw = gzip.decompress((directory / source["snapshot"]).read_bytes())
    require(hashlib.sha256(raw).hexdigest() == source["sha256"], "Changed WA query bytes")
    groups = benchmark_wa.group_rows(json.loads(raw))
    require(len(groups) == source["prefixCount"], "Changed WA prefix inventory")
    report = read(directory / "benchmark.json")
    require(report["sourceSha256"] == source["sha256"], "WA report belongs to a different source")
    snapshot(directory, "aliases.json", report["aliasesSha256"])
    snapshot(directory, report["prefixResults"], report["prefixResultsSha256"])
    results = json.loads(gzip.decompress((directory / report["prefixResults"]).read_bytes()))
    require(len(results) == report["evaluatedPrefixes"], "Incomplete recorded WA results")
    require(benchmark_wa.summarize(results) == report["byPrefix"] and
            benchmark_wa.summarize(results, weighted=True) == report["byRegistrationCount"],
            "WA report metrics do not match retained results")
    inventory(directory, {"source.json", "groups.json.gz", "aliases.json", "benchmark.json",
                          "benchmark-prefixes.json.gz", "LICENSE.md", "README.md"})
    return len(groups)


def validate(root=ROOT):
    data_dir = root / "data"
    data = read(data_dir / "dataset.json")
    sources = {}
    expected = {"dataset.json", "schema.json", "fixtures.json", "vehicle-fixtures.json", "LICENSE.md", "CC0-1.0.txt",
                "nhtsa/metadata.json", "kba/metadata.json", "kba/fixtures.json", "snapshots/metadata.json",
                "europe/tesla-model-y.json", "europe/vw-golf-1k-2005.json",
                "decoding/metadata.json", "decoding/index.tsv", "decoding/sources.json"}
    for s in data["sources"]:
        source = {**s, "edition": s["publicationVersion"], "reuseBasis": s["reuse"]["basis"]}
        source_record(source)
        snapshot(data_dir, source["snapshot"], source["sha256"])
        sources[source["id"]] = source
        expected.add(source["snapshot"])
    for item in data["manufacturers"] + data["assignments"]:
        references(item["sourceRefs"], sources, item["id"])
    kba = read(data_dir / "kba/metadata.json")
    source_record({"id": "kba-fz-types-" + kba["referenceDate"], "publisher": kba["publisher"], "title": kba["title"],
                   "url": kba["serviceUrl"], "edition": kba["referenceDate"], "retrievedOn": kba["retrievedOn"],
                   "section": "Complete FeatureServer layer 0; sourceObjectId identifies each retained row",
                   "reuseBasis": kba["license"] + " " + kba["licenseUrl"] + "; " + kba["modifications"]})
    for file, digest in ((kba["snapshot"], kba["snapshotSha256"]), (kba["table"], kba["sha256"])):
        snapshot(data_dir, "kba/" + file, digest)
        expected.add("kba/" + file)
    historical = read(data_dir / "snapshots/metadata.json")
    for source in historical:
        source_record(source)
        require(source["id"] not in sources, "Duplicate historical source ID")
        snapshot(data_dir, source["snapshot"], source["sha256"])
        sources[source["id"]] = source
        expected.add(source["snapshot"])
    astra = read(data_dir / "astra/metadata.json")
    source = astra["source"]
    source_record(source)
    require(source["id"] not in sources, "Duplicate ASTRA source ID")
    sources[source["id"]] = source
    snapshot(data_dir, source["archivePath"], source["archiveSha256"])
    snapshot(data_dir, "astra/index.tsv", astra["indexSha256"])
    expected.update({"astra/metadata.json", "astra/index.tsv", "astra/review.json", source["archivePath"]})
    review = read(data_dir / "astra/review.json")
    for document in review["sources"]:
        source_record(document)
        require(document["id"] not in sources and document.get("inspectedSha256") and document.get("archiveStatus"),
                "Missing/duplicate ASTRA review evidence")
        sources[document["id"]] = document
    references(review["parserSourceRefs"], sources, "ASTRA parser")
    for fixture in review["fixtures"]:
        references(fixture["sourceRefs"], sources, fixture["vin"])
        require(re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", fixture["vin"]) and fixture["locator"],
                "Invalid/untraceable ASTRA specimen")
    for line in (data_dir / "astra/index.tsv").read_text().splitlines():
        cells = line.split("\t")
        if cells[0] == "W":
            snapshot(data_dir, "astra/" + cells[2], cells[3])
            expected.add("astra/" + cells[2])
        elif cells[0] == "D":
            import base64
            keys = ("id", "title", "publisher", "url", "edition", "section", "retrievedOn", "reuseBasis",
                    "archivePath", "archiveSha256", "inspectedSha256", "evidencePath")
            require([base64.b64decode(v).decode("utf-8") for v in cells[1:]] == [source[k] for k in keys],
                    "Stale ASTRA source catalog")
    tesla = read(data_dir / "europe/tesla-model-y.json")
    volkswagen = read(data_dir / "europe/vw-golf-1k-2005.json")
    for source in oem_sources(tesla, volkswagen):
        require(source["id"] not in sources, "Duplicate source ID")
        sources[source["id"]] = source
    documents = read(data_dir / "decoding/sources.json")
    require(documents == decoding.source_documents(tesla, volkswagen), "Stale decoding source catalog")
    for source in documents:
        source_record(source)
        require((data_dir / source["evidencePath"]).is_file(), "Missing source evidence")
    metadata = read(data_dir / "decoding/metadata.json")
    snapshot(data_dir, "decoding/index.tsv", metadata["indexSha256"])
    snapshot(data_dir, "decoding/sources.json", metadata["sourcesSha256"])
    for line in (data_dir / "decoding/index.tsv").read_text().splitlines():
        cells = line.split("\t")
        if cells[0] == "H":
            snapshot(data_dir, "decoding/" + cells[1], cells[2])
            expected.add("decoding/" + cells[1])
        elif cells[0] == "F":
            require(cells[4] in sources and cells[5] == sources[cells[4]]["url"], "Unresolved OEM evidence")
    for fixture in read(data_dir / "vehicle-fixtures.json"):
        references(fixture["sourceRefs"], sources, fixture["id"])
        require(fixture["source"] in {sources[s]["url"] for s in fixture["sourceRefs"]}, "Untraceable fixture URL")
    identity_metadata = identity.validate()
    expected.update({"identity/metadata.json", "identity/index.tsv", "identity/fixtures.json"})
    for fixture in read(data_dir / "identity/fixtures.json"):
        references(fixture["ruleSourceRefs"], sources, fixture["id"])
    import compile_dataset
    generated = compile_dataset.validate(root)
    expected.update("generated/" + name for name in generated)
    expected.update({"policy/identity.json", "policy/decoder.json", "rules.schema.json"})
    expected.update(p.relative_to(data_dir).as_posix() for p in (data_dir / "rules").glob("*.json"))
    inventory(data_dir, expected)
    research = research_inventory(root)
    require(read(root / "docs/research/vin-rules/sources.json") == research,
            "Research citations changed; review and run tools/provenance.py --update-research")
    european = europe_coverage.validate(root)
    validation_prefixes = validation_corpus(root)
    return {"dataFiles": len(expected), "sourceRecords": len(sources) + 1,
            "researchCitations": len(research), "assignments": len(data["assignments"]),
            "manufacturers": len(data["manufacturers"]), "kbaRows": kba["recordCount"],
            "identityVersion": identity_metadata["version"],
            "nativePatterns": metadata["counts"]["exportedPatterns"], "volkswagenRules": len(volkswagen["rules"]),
            "astraApprovals": astra["counts"]["approvalRows"],
            "europeanPriorityModels": european["targets"],
            "priorityModelsWithApprovalLabelMatches": european["targetsWithApprovalLabelMatches"],
            "observationalValidationPrefixes": validation_prefixes,
            "teslaLayouts": len(tesla["layouts"]), "teslaAttributeRules": len(tesla["attributes"])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update-research", action="store_true", help="Refresh citation inventory after reviewing report edits")
    args = parser.parse_args()
    if args.update_research:
        (ROOT / "docs/research/vin-rules/sources.json").write_text(nhtsa.json_text(research_inventory()), encoding="utf-8")
    else:
        print(json.dumps(validate(), sort_keys=True))
