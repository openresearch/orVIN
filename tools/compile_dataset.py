"""Compile the offline, manifest-backed runtime bundle from reviewed projections.

Acquisition and upstream syntax belong to the source adapters. This compiler is
deterministic and never downloads data or modifies curated rules/policy.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAT = "orvin-runtime-1"
CAPABILITIES = "patterns,conditional-literals,year-cycles,relations,decimal-scaling,catalogue-consensus,cross-market"


def b64(value):
    return base64.b64encode(str(value).encode()).decode()


def digest(content):
    return hashlib.sha256(content).hexdigest()


def policy_rows(value, prefix=""):
    if isinstance(value, dict):
        for key, child in sorted(value.items()):
            yield from policy_rows(child, prefix + "." + key if prefix else key)
    elif isinstance(value, list):
        yield prefix + ".length\tI\t" + str(len(value))
        for i, child in enumerate(value):
            yield from policy_rows(child, prefix + "." + str(i))
    else:
        kind = "B" if isinstance(value, bool) else "I" if isinstance(value, int) else "S"
        yield "\t".join((prefix, kind, b64(value) if kind == "S" else str(value).lower()))


def literal_rules(data):
    """Translate the two reviewed historical authoring formats once at build time."""
    golf = json.loads((data / "europe/vw-golf-1k-2005.json").read_bytes())
    for rule in golf["rules"]:
        yield {"id": rule["id"], "pattern": rule["pattern"], "marketScope": "EUROPEAN_LAYOUT", "markets": [],
               "modelYear": rule["modelYear"], "stage": "vw-europe-golf-1k-2005",
               "warning": "Golf family only; filler characters do not identify engine or trim. Model year is not exact build date.",
               "conflictWarning": "Supplied model year conflicts with this documented European VIN layout.",
               "claims": [{"code": code, "value": value, "sourceId": source, "kind": "OEM_RULE_COMBINATION",
                           "ruleId": rule["id"], "keys": rule["pattern"]}
                          for code, value in sorted(rule["fields"].items()) for source in golf["fieldSources"][code]]}
    item = json.loads((data / "europe/tesla-model-y.json").read_bytes())
    for layout in item["layouts"]:
        tokens = ["."] * 17
        tokens[:3] = layout["wmi"]
        for position, chars in item["requirements"].items():
            tokens[int(position) - 1] = "[" + chars + "]"
        tokens[10] = layout["plant"]
        tokens[11:] = ["[0-9]"] * 6
        claims = [{"code": code, "value": value, "ruleId": "layout:" + layout["wmi"] + layout["plant"]}
                  for code, value in sorted(layout["fields"].items())]
        for attribute in item["attributes"]:
            for char in attribute["characters"]:
                for code, value in sorted(attribute["fields"].items()):
                    claims.append({"code": code, "value": value, "position": attribute["position"] - 1,
                                   "characters": char, "ruleId": f"position:{attribute['position']}:{char}"})
        for char, year in sorted(item["years"].items()):
            claims.append({"code": "ProductionYear", "value": str(year), "position": 9,
                           "characters": char, "ruleId": "position:10:" + char})
        for claim in claims:
            claim.update(sourceId=item["source"]["id"], kind="OEM_RULE", keys="")
        yield {"id": "layout-" + layout["wmi"] + layout["plant"], "pattern": "".join(tokens),
               "exclude": ".{11}000000", "marketScope": "GLOBAL", "markets": [],
               "stage": "tesla-model-y-2025-oem-rules", "claims": claims,
               "warning": "Production year is a calendar year, not model year or exact build date."}


def rule_rows(rules, source_ids, codes):
    seen = set()
    for rule in sorted(rules, key=lambda r: r["id"]):
        if rule["id"] in seen:
            raise ValueError("Duplicate rule " + rule["id"])
        seen.add(rule["id"])
        # Restrict patterns to the portable bounded VIN grammar; no arbitrary regex code.
        import re
        grammar = r"(?:[A-HJ-NPR-Z0-9.]|\[[A-HJ-NPR-Z0-9-]+\])(?:\{[0-9]{1,2}\})?"
        for pattern in (rule["pattern"], rule.get("exclude", "")):
            if pattern and "".join(re.findall(grammar, pattern)) != pattern:
                raise ValueError("Unsupported VIN pattern: " + pattern)
        values = [rule["id"], rule["pattern"], rule.get("exclude", ""), rule["marketScope"],
                  ",".join(sorted(rule["markets"])), str(rule.get("modelYear", "")), rule["stage"],
                  rule.get("warning", ""), rule.get("conflictWarning", "Supplied year conflicts with this rule.")]
        yield "R\t" + "\t".join(map(b64, values))
        for claim in rule["claims"]:
            if claim["sourceId"] not in source_ids or claim["code"] not in codes:
                raise ValueError("Unknown claim source/field: " + str(claim))
            position = claim.get("position", -1)
            if not -1 <= position < 17:
                raise ValueError("Claim position outside VIN")
            values = [rule["id"], str(position), claim.get("characters", ""), claim["code"], claim["value"],
                      claim["sourceId"], claim["kind"], claim["ruleId"], claim.get("keys", "")]
            yield "F\t" + "\t".join(map(b64, values))


def compile_bundle(root=ROOT):
    import dataset
    import kba
    from jsonschema import Draft202012Validator
    data = root / "data"
    inputs, files = {}, {}

    def read(name):
        content = (data / name).read_bytes()
        inputs[name] = digest(content)
        return content

    def copy(name):
        files[name] = read(name)

    wmi = read("dataset.json")
    files["dataset.tsv"] = dataset.render(json.loads(wmi), digest(wmi)).encode()
    for area in ("decoding", "astra", "identity", "kba"):
        copy(area + "/metadata.json")
    for area in ("astra", "identity"):
        copy(area + "/index.tsv")
    copy("kba/types.tsv")
    for area in ("decoding", "astra"):
        for path in sorted((data / area).rglob("*.tsv.gz")):
            copy(path.relative_to(data).as_posix())
    raw_index = read("decoding/index.tsv").decode().splitlines()
    index = "\n".join(line for line in raw_index if line.split("\t")[0] not in {"T", "R", "Y", "L", "A", "O", "F"}) + "\n"
    files["decoding/index.tsv"] = index.encode()
    meta = json.loads(files["decoding/metadata.json"])
    meta["indexSha256"] = digest(files["decoding/index.tsv"])
    files["decoding/metadata.json"] = (json.dumps(meta, ensure_ascii=False, indent=2) + "\n").encode()
    policy = json.loads(read("policy/decoder.json"))
    policy["patternProfile"]["referenceYear"] = int(raw_index[0].split("\t")[2])
    read("policy/identity.json")
    files["policy.tsv"] = ("\n".join(policy_rows(policy)) + "\n").encode()
    source_ids = {base64.b64decode(line.split("\t")[1]).decode() for line in raw_index if line.startswith("D\t")}
    codes = {line.split("\t")[2] for line in raw_index if line.startswith("E\t")}
    for name in ("europe/tesla-model-y.json", "europe/vw-golf-1k-2005.json"):
        read(name)
    rules = list(literal_rules(data))
    schema = json.loads(read("rules.schema.json"))
    validator = Draft202012Validator(schema)
    for path in sorted((data / "rules").glob("*.json")):
        document = json.loads(read(path.relative_to(data).as_posix()))
        validator.validate(document)
        rules.extend(document["rules"])
    validator.validate({"format": "orvin-literals-1", "rules": rules})
    files["rules.tsv"] = ("\n".join(rule_rows(rules, source_ids, codes)) + "\n").encode()
    for area, key in (("decoding", "indexSha256"), ("astra", "indexSha256"), ("identity", "sha256")):
        meta = json.loads(files[area + "/metadata.json"])
        files[area + "-metadata.tsv"] = (meta["version"] + "\t" + meta[key] + "\n").encode()
    meta = json.loads(files["kba/metadata.json"])
    files["kba-metadata.tsv"] = (kba.render_metadata(meta).rstrip("\n") + "\t" + digest(files["kba/metadata.json"]) + "\n").encode()
    for name in ("LICENSE.md", "CC0-1.0.txt"):
        copy(name)
    # Notices are part of the common bundle, including when building a wheel from an sdist.
    for name in ("LICENSE", "NOTICE"):
        files["CODE-" + name] = (root / name).read_bytes()
    lines = ["\t".join(("V", FORMAT, CAPABILITIES)), "P\t" + policy["version"],
             "C\ttools/compile_dataset.py\t" + digest(Path(__file__).read_bytes())]
    lines += ["I\t" + name + "\t" + sha for name, sha in sorted(inputs.items())]
    lines += ["F\t" + name + "\t" + digest(content) for name, content in sorted(files.items())]
    files["manifest.tsv"] = ("\n".join(lines) + "\n").encode()
    return files


def validate(root=ROOT, write=False):
    files = compile_bundle(root)
    directory = root / "data/generated"
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
    if write:
        for name in actual - files.keys():
            (directory / name).unlink()
        for name, content in files.items():
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists() or path.read_bytes() != content:
                path.write_bytes(content)
    elif actual != files.keys() or any((directory / name).read_bytes() != content for name, content in files.items()):
        raise ValueError("Stale runtime bundle; run tools/compile_dataset.py --generate and review the diff")
    return files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args()
    print(f"Validated {len(validate(write=args.generate))} compiled runtime files")
