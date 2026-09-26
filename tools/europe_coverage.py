"""Audit the 100 research targets against shipped approval rows, not decoder accuracy."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def validate(root=ROOT, refresh=False):
    worklist = json.loads((root / "docs/research/europe-priority/models-100.json").read_text())
    models = worklist["models"]
    if len(models) != 100 or len({m["id"] for m in models}) != 100:
        raise ValueError("European worklist must have exactly 100 distinct targets")
    sources = {s["id"]: s for s in worklist["sources"]}
    for source in sources.values():
        for key in ("publisher", "title", "url", "locator", "reviewed_date", "reuse_basis"):
            if not source.get(key):
                raise ValueError(f"Missing selection source {key}")
        digests = [file["sha256"] for file in source.get("files", [])]
        if source.get("inspected_sha256"):
            digests.append(source["inspected_sha256"])
        if not digests:
            raise ValueError("Selection source has no inspected-byte digest")
        for digest in digests:
            if not re.fullmatch(r"[a-f0-9]{64}", digest):
                raise ValueError("Invalid inspected selection-source digest")
    directory = root / "data/astra"
    metadata = json.loads((directory / "metadata.json").read_text())
    current = metadata["source"]
    if refresh:
        old = next(s for s in sources.values() if "projection_version" in s)
        astra = {**old, "id": current["id"], "edition": current["edition"],
                 "inspected_sha256": current["inspectedSha256"],
                 "projection_version": metadata["version"],
                 "projection_metadata_sha256": hashlib.sha256((directory / "metadata.json").read_bytes()).hexdigest(),
                 "projection_index_sha256": metadata["indexSha256"], "snapshot_updated_on": current["retrievedOn"]}
        # Keep historical selection citations, while regenerating only query output.
        cited = {e["source_id"] for m in models for e in m["evidence"]}
        worklist["sources"] = [s for s in sources.values() if "projection_version" not in s or s["id"] in cited]
        worklist["sources"].append(astra)
        sources[astra["id"]] = astra
    else:
        astra = sources[current["id"]]
    for filename, key in (("metadata.json", "projection_metadata_sha256"), ("index.tsv", "projection_index_sha256")):
        if hashlib.sha256((directory / filename).read_bytes()).hexdigest() != astra[key]:
            raise ValueError("European worklist refers to a different approval projection")
    records, keys = {}, []
    for line in (directory / "index.tsv").read_text().splitlines():
        c = line.split("\t")
        if c[0] == "F":
            keys.append(c[1])
        elif c[0] == "W":
            content = (directory / c[2]).read_bytes()
            if hashlib.sha256(content).hexdigest() != c[3]:
                raise ValueError("Coverage input shard changed")
            for row in gzip.decompress(content).decode().splitlines():
                cells = row.split("\t")
                fields = {k: base64.b64decode(v).decode() for k, v in zip(keys, cells[4:])}
                records[cells[0]] = {"approval_id": cells[0], "source_row": int(cells[1]),
                                     "vin_template": base64.b64decode(cells[2]).decode(), **fields}
    counts = {}
    for model in models:
        for evidence in model["evidence"]:
            if evidence["source_id"] not in sources or not evidence["locator"]:
                raise ValueError("Unresolved European selection evidence")
        query = model["astra_label_query"]
        regex = re.compile(query["type_regex"], 0 if query["case_sensitive"] else re.IGNORECASE)
        exclude = re.compile(query["type_exclude_regex"], re.IGNORECASE) if query["type_exclude_regex"] else None
        matches = {key: r for key, r in records.items() if r["make"] in query["make_equals"]
                   and regex.search(r["type"]) and not (exclude and exclude.search(r["type"]))}
        result = model["astra_text_query_result"]
        if refresh:
            result["source_id"] = current["id"]
            result["matching_distinct_approval_rows"] = len(matches)
            fields = ("approval_id", "source_row", "make", "type", "vin_template")
            result["examples"] = [{k: record[k] for k in fields}
                                  for _, record in sorted(matches.items())[:3]]
        if len(matches) != result["matching_distinct_approval_rows"]:
            raise ValueError(f"Stale approval count for {model['id']}: {len(matches)}")
        for example in result["examples"]:
            record = matches.get(example["approval_id"], {})
            if any(record.get(k) != v for k, v in example.items()):
                raise ValueError(f"Untraceable approval example: {model['id']}")
        counts[model["id"]] = len(matches)
    if refresh:
        (root / "docs/research/europe-priority/models-100.json").write_text(
            json.dumps(worklist, ensure_ascii=False, indent=2) + "\n")
    return {"targets": len(models), "targetsWithApprovalLabelMatches": sum(v > 0 for v in counts.values()),
            "noApprovalLabelMatch": [key for key, value in counts.items() if not value]}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Re-run unchanged research queries against new source data")
    print(json.dumps(validate(refresh=parser.parse_args().refresh), sort_keys=True))
