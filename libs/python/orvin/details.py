"""Portable, bounded rich decoding. No SQL, network, defaults or VIN repair."""
import base64
import copy
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from functools import lru_cache
import gzip
import hashlib
import json
import re

YEAR_CODES = "ABCDEFGHJKLMNPRSTVWXY123456789"
MULTIPLE = {121, 129, 150, 154, 155, 114, 169}
STAGES = ["public-patterns", "model-make", "engine-model", "displacement-conversion"]


def _decode(value):
    return base64.b64decode(value).decode("utf-8")


def _verified(path, digest):
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != digest:
        raise RuntimeError("Bundled decoding resource does not match its SHA-256: " + path.name)
    return content


def unknown():
    return {"status": "UNKNOWN", "possibilities": [], "value": None}


def resolution(details, code):
    field = details["fields"].get(code)
    return {k: field[k] for k in ("status", "possibilities", "value")} if field else unknown()


def unavailable():
    return {"status": "UNAVAILABLE", "dataset": None, "marketScope": "US", "referenceYear": 2026,
            "stages": [], "warnings": [], "fields": {}, "alternatives": [], "sources": []}


class RichDecoder:
    def __init__(self, directory):
        self.directory = directory
        metadata = json.loads((directory / "metadata.json").read_bytes())
        index = _verified(directory / "index.tsv", metadata["indexSha256"]).decode("utf-8")
        self.dataset = {"version": metadata["version"], "sha256": metadata["indexSha256"]}
        self.elements, self.wmis, self.models, self.hashes = {}, {}, {}, {}
        self.schemas, self.engines = defaultdict(list), defaultdict(list)
        self.conversions = []
        self.europe_requirements, self.europe_years = {}, {}
        self.europe_layouts, self.europe_attributes = defaultdict(dict), []
        self.oem_rules = {}
        self.sources = {}
        for line in index.splitlines():
            c = line.split("\t")
            if c[0] == "V":
                self.reference_year, self.source = int(c[2]), c[3]
            elif c[0] == "D":
                keys = ("id", "title", "publisher", "url", "edition", "section", "retrievedOn", "reuseBasis",
                        "archivePath", "archiveSha256", "inspectedSha256", "evidencePath")
                source = dict(zip(keys, (_decode(v) or None for v in c[1:])))
                self.sources[source["id"]] = source
            elif c[0] == "E":
                self.elements[int(c[1])] = (c[2], _decode(c[3]), c[4])
            elif c[0] == "W":
                self.wmis[c[1]] = (c[2], int(c[3]), c[4])
            elif c[0] == "S":
                self.schemas[c[1]].append(tuple(map(int, c[2:])))
            elif c[0] == "M":
                self.models[c[1]] = (c[2], _decode(c[3]))
            elif c[0] == "G":
                self.engines[_decode(c[1])].append((c[2], int(c[3]), _decode(c[4]), _decode(c[5]), c[6]))
            elif c[0] == "C":
                self.conversions.append((c[1], int(c[2]), int(c[3]), c[4], Decimal(c[5])))
            elif c[0] == "H":
                self.hashes[c[1]] = c[2]
            elif c[0] == "T":
                self.europe_source, self.europe_url = c[1:]
            elif c[0] == "R":
                self.europe_requirements[int(c[1]) - 1] = c[2]
            elif c[0] == "Y":
                self.europe_years[c[1]] = int(c[2])
            elif c[0] == "L":
                self.europe_layouts[c[1] + c[2]][c[3]] = _decode(c[4])
            elif c[0] == "A":
                self.europe_attributes.append((int(c[1]) - 1, c[2], c[3], _decode(c[4])))
            elif c[0] == "O":
                self.oem_rules[c[1]] = (re.compile(_decode(c[2])), int(c[3]), defaultdict(list))
            elif c[0] == "F":
                self.oem_rules[c[1]][2][c[2]].append((_decode(c[3]), c[4], c[5]))
            else:
                raise RuntimeError("Unknown decoding index row")

    @lru_cache(maxsize=8)
    def _bucket(self, bucket):
        name = f"patterns-{bucket:03d}.tsv.gz"
        content = gzip.decompress(_verified(self.directory / name, self.hashes[name])).decode("utf-8")
        schemas = defaultdict(list)
        for line in content.splitlines():
            c = line.split("\t")
            schema = int(c[0])
            schemas[schema].append((int(c[1]), int(c[2]), _decode(c[3]), _decode(c[4]), _decode(c[5]),
                                    c[6], _decode(c[7]), int(c[8]), int(c[9])))
        return schemas

    @lru_cache(maxsize=32)
    def _patterns(self, schema):
        return tuple((*p[:6], re.compile(p[6]), *p[7:]) for p in self._bucket(schema % 256).get(schema, ()))

    def _fact(self, element, value, attribute, kind, rule, schema=None, key=""):
        return {"elementId": element, "value": value, "attributeId": attribute, "sourceId": self.source,
                "sourceUrl": self.sources[self.source]["url"],
                "kind": kind, "ruleId": rule, "schemaId": schema, "keys": key}

    def _europe(self, vin):
        layout = self.europe_layouts.get(vin[:3] + vin[10])
        if not layout or any(vin[p] not in chars for p, chars in self.europe_requirements.items()):
            return None
        # The reviewed manual defines a numeric production sequence, not a date.
        if not re.fullmatch("[0-9]{6}", vin[11:]) or vin[11:] == "000000":
            return None
        values = {code: (value, "layout:" + vin[:3] + vin[10]) for code, value in layout.items()}
        for position, chars, code, value in self.europe_attributes:
            if vin[position] in chars:
                values[code] = (value, f"position:{position + 1}:{vin[position]}")
        values["ProductionYear"] = (str(self.europe_years[vin[9]]), "position:10:" + vin[9])
        codes = {e[0]: (eid, e[1], e[2]) for eid, e in self.elements.items()}
        fields, facts = {}, {}
        for code, (value, rule) in sorted(values.items()):
            eid, label, datatype = codes[code]
            fact = {"elementId": eid, "value": value, "attributeId": value, "sourceId": self.europe_source,
                    "sourceUrl": self.europe_url, "kind": "OEM_RULE", "ruleId": rule, "schemaId": None, "keys": ""}
            fields[code] = {"label": label, "dataType": datatype, "status": "KNOWN", "possibilities": [value],
                            "value": value, "evidence": [fact]}
            facts[code] = [fact]
        return {"status": "DECODED", "dataset": self.dataset, "marketScope": "GLOBAL", "referenceYear": self.reference_year,
                "stages": ["tesla-model-y-2025-oem-rules"],
                "warnings": ["Production year is a calendar year, not model year or exact build date."],
                "fields": fields, "alternatives": [{"modelYear": None, "market": "GLOBAL", "fields": facts}]}

    def _oem(self, vin, context):
        for rule, (pattern, year, values) in self.oem_rules.items():
            if not pattern.fullmatch(vin):
                continue
            conflict = context.model_year is not None and context.model_year != year
            codes = {e[0]: (eid, e[1], e[2]) for eid, e in self.elements.items()}
            fields, facts = {}, {}
            for code, associations in sorted(values.items()):
                eid, label, datatype = codes[code]
                facts[code] = [{"elementId": eid, "value": value, "attributeId": value, "sourceId": source,
                                "sourceUrl": url, "kind": "OEM_RULE_COMBINATION", "ruleId": rule,
                                "schemaId": None, "keys": pattern.pattern} for value, source, url in associations]
                value = associations[0][0]
                fields[code] = {"label": label, "dataType": datatype, "status": "KNOWN", "possibilities": [value],
                                "value": value, "evidence": facts[code]}
            return {"status": "CONTEXT_CONFLICT" if conflict else "DECODED", "dataset": self.dataset, "marketScope": "EUROPEAN_LAYOUT",
                    "referenceYear": self.reference_year, "stages": ["vw-europe-golf-1k-2005"],
                    "warnings": ["Supplied model year conflicts with this documented European VIN layout."] if conflict else
                                ["Golf family only; filler characters do not identify engine or trim. Model year is not exact build date."],
                    "fields": {} if conflict else fields, "alternatives": [{"modelYear": year, "market": "EUROPEAN_LAYOUT", "fields": facts}]}
        return None

    def _years(self, vin, context, wmi):
        if vin[9] not in YEAR_CODES:
            return []
        base = 1980 + YEAR_CODES.index(vin[9])
        if context.model_year is not None:
            return [context.model_year] if context.model_year >= 1980 and (context.model_year - base) % 30 == 0 else []
        years = list(range(base, self.reference_year + 3, 30))
        _, vehicle_type, truck_type = self.wmis[wmi]
        # This discriminator is used only within the explicitly labelled US scheme.
        if vehicle_type in (2, 7) or (vehicle_type == 3 and truck_type == "1"):
            years = [y for y in years if (y < 2010) == vin[6].isdigit()]
        return years

    def _pass(self, vin, wmi, year, context):
        key = vin[3:8] + "|" + vin[9:]
        matches = defaultdict(list)
        for schema, start, end in self.schemas.get(wmi, ()):
            if not start <= year <= end:
                continue
            for pid, element, pattern, attr, value, changed, regex, capture, length in self._patterns(schema):
                if regex.match(key) is None:
                    continue
                formula = capture >= 0
                if formula:
                    value = key[capture:capture + length]
                    attr = value
                fact = self._fact(element, value, attr, "NUMERIC_PATTERN" if formula else "PATTERN",
                                  str(pid), schema, pattern)
                # Reverse only the descending keys; stable sorts express PostgreSQL
                # NULLS FIRST, then shortest non-star key, key text and insertion ID.
                matches[element].append((100 if formula else start, changed, pattern, pid, fact))
        engine = matches.get(18, [])
        if engine:
            parent = sorted(engine, key=lambda p: (p[0], not p[1], p[1], p[3]), reverse=True)[0][4]
            for pid, element, attr, value, changed in self.engines.get(parent["attributeId"].strip().lower(), ()):
                fact = self._fact(element, value, attr, "ENGINE_MODEL", parent["ruleId"] + "/engine:" + pid,
                                  parent["schemaId"], parent["keys"])
                matches[element].append((50, changed, parent["keys"], int(pid), fact))
        facts = {}
        for element, items in matches.items():
            items.sort(key=lambda p: (len(p[2].replace("*", "")), p[2].replace("[", "").replace("]", ""), p[3]))
            items.sort(key=lambda p: (not p[1], p[1]), reverse=True)
            items.sort(key=lambda p: p[0], reverse=True)
            selected = items if element in MULTIPLE else items[:1]
            facts[element] = list({json.dumps(p[4], sort_keys=True): p[4] for p in selected}.values())
        if 28 in facts:
            parent = facts[28][0]
            model = self.models.get(parent["attributeId"])
            if model:
                facts[26] = [self._fact(26, model[1], model[0], "MODEL_MAKE", parent["ruleId"] + "/make:" + model[0],
                                       parent["schemaId"], parent["keys"])]
        # Enrich only from original facts, never chain rounded conversions.
        for cid, source, target, operator, factor in self.conversions:
            if source not in matches or target in facts or len(facts.get(source, [])) != 1:
                continue
            parent = facts[source][0]
            try:
                original = Decimal(parent["value"])
                number = original * factor if operator == "*" else original / factor
                text = format(number.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP), "f").rstrip("0").rstrip(".")
            except InvalidOperation:
                continue
            facts[target] = [self._fact(target, text or "0", text or "0", "UNIT_CONVERSION",
                                        parent["ruleId"] + "/conversion:" + cid, parent["schemaId"], parent["keys"])]
        # A year code alone is not evidence that these vehicle-description rules matched.
        if facts:
            facts[29] = [self._fact(29, str(year), str(year), "CALLER_CONTEXT" if context.model_year else "VIN_YEAR",
                                    "model-year", key=vin[9])]
        return {"modelYear": year, "market": "US", "fields": {self.elements[e][0]: f for e, f in sorted(facts.items())}}

    def decode(self, vin, structure, context):
        result = self._decode(vin, structure, context)
        used = {e["sourceId"] for field in result["fields"].values() for e in field["evidence"]}
        used.update(e["sourceId"] for a in result["alternatives"] for facts in a["fields"].values() for e in facts)
        result["sources"] = [copy.deepcopy(self.sources[sid]) for sid in sorted(used)]
        return result

    def _decode(self, vin, structure, context):
        result = {"status": "UNKNOWN", "dataset": self.dataset, "marketScope": "US", "referenceYear": self.reference_year,
                  "stages": STAGES, "warnings": [], "fields": {}, "alternatives": [], "sources": []}
        if structure != "MODERN_FORMAT":
            result["status"] = "INVALID_INPUT"
            return result
        oem = self._oem(vin, context)
        if oem is not None:
            return oem
        european = self._europe(vin)
        if european is not None:
            return european
        if context.market not in (None, "US"):
            result["status"] = "OUT_OF_SCOPE"
            result["warnings"].append("NHTSA rules are scoped to US reporting; no applicable non-US rule is bundled for this VIN.")
            return result
        wmi = vin[:3] + vin[11:14] if vin[2] == "9" else vin[:3]
        if wmi not in self.wmis:
            return result
        years = self._years(vin, context, wmi)
        if not years:
            result["status"] = "CONTEXT_CONFLICT" if context.model_year is not None else "UNKNOWN"
            result["warnings"].append("VIN year code does not resolve within this US scheme and supplied context.")
            return result
        alternatives = [self._pass(vin, wmi, year, context) for year in years]
        result["alternatives"] = alternatives
        codes = sorted({code for a in alternatives for code in a["fields"]})
        for code in codes:
            evidence, values = [], []
            missing = False
            for alternative in alternatives:
                facts = alternative["fields"].get(code, [])
                missing |= not facts
                for fact in facts:
                    if fact not in evidence:
                        evidence.append(fact)
                    if fact["value"] not in values:
                        values.append(fact["value"])
            element = evidence[0]["elementId"]
            status = ("AMBIGUOUS" if len(values) > 1 else "UNKNOWN" if missing else
                      "NEEDS_CONTEXT" if context.market is None else "KNOWN")
            result["fields"][code] = {"label": self.elements[element][1], "dataType": self.elements[element][2],
                                      "status": status, "possibilities": values,
                                      "value": values[0] if status == "KNOWN" else None, "evidence": evidence}
        if codes:
            result["status"] = "NEEDS_CONTEXT" if context.market is None else "DECODED"
        if context.market is None and codes:
            result["warnings"].append("These possibilities assume US reporting scope; supply market US only when independently known.")
        if len(years) > 1:
            result["warnings"].append("The VIN year code has multiple possible cycles; alternatives retain each year's associated facts.")
        return result
