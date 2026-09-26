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

from .program import policy, rules, read


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
        metadata = json.loads(read(directory.parent, "decoding/metadata.json"))
        index = _verified(directory / "index.tsv", metadata["indexSha256"]).decode("utf-8")
        self.dataset = {"version": metadata["version"], "sha256": metadata["indexSha256"]}
        self.elements, self.wmis, self.models, self.hashes = {}, {}, {}, {}
        self.schemas, self.engines = defaultdict(list), defaultdict(list)
        self.conversions = []
        self.policy = policy()
        self.literal_rules = rules(directory.parent)
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

    def _literals(self, vin, context):
        results = []
        for rule in self.literal_rules:
            if not rule["pattern"].fullmatch(vin) or (rule["exclude"] and rule["exclude"].fullmatch(vin)):
                continue
            foreign = bool(rule["markets"]) and context.market not in rule["markets"]
            conflict = rule["year"] is not None and context.model_year is not None and rule["year"] != context.model_year
            if conflict and foreign:
                continue
            facts = defaultdict(list)
            codes = {e[0]: (eid, e[1], e[2]) for eid, e in self.elements.items()}
            for position, chars, code, value, source, kind, rule_id, keys in rule["claims"]:
                if position >= 0 and vin[position] not in chars:
                    continue
                eid, _, _ = codes[code]
                fact = {"elementId": eid, "value": value, "attributeId": value, "sourceId": source,
                        "sourceUrl": self.sources[source]["url"], "kind": kind, "ruleId": rule_id,
                        "schemaId": None, "keys": keys}
                if fact not in facts[code]:
                    facts[code].append(fact)
            fields = {}
            for code, evidence in sorted(facts.items()):
                values = sorted({f["value"] for f in evidence})
                status = "AMBIGUOUS" if len(values) > 1 else "NEEDS_CONTEXT" if foreign else "KNOWN"
                fields[code] = {"label": codes[code][1], "dataType": codes[code][2], "status": status,
                                "possibilities": values, "value": values[0] if status == "KNOWN" else None, "evidence": evidence}
            results.append({"status": "CONTEXT_CONFLICT" if conflict else "NEEDS_CONTEXT" if foreign else "DECODED",
                "dataset": self.dataset, "marketScope": rule["scope"], "referenceYear": self.reference_year,
                "stages": [rule["stage"]], "warnings": [rule["conflictWarning"] if conflict else rule["warning"]],
                "fields": {} if conflict else fields,
                "alternatives": [{"modelYear": rule["year"], "market": rule["scope"], "fields": dict(sorted(facts.items()))}]})
        return results

    def _p(self, key):
        return self.policy.get("patternProfile." + key)

    def _years(self, vin, context, wmi):
        if vin[self._p("yearPosition")] not in self._p("yearCodes"):
            return []
        base = self._p("yearBase") + self._p("yearCodes").index(vin[self._p("yearPosition")])
        if context.model_year is not None:
            return [context.model_year] if context.model_year >= self._p("yearBase") and (context.model_year - base) % self._p("yearCycle") == 0 else []
        years = list(range(base, self.reference_year + self._p("yearHorizon") + 1, self._p("yearCycle")))
        _, vehicle_type, truck_type = self.wmis[wmi]
        # This discriminator is used only within the explicitly labelled US scheme.
        if vehicle_type in self.policy.array("patternProfile.cycleDiscriminator.vehicleTypes") or (vehicle_type == self._p("cycleDiscriminator.conditionalType") and truck_type == self._p("cycleDiscriminator.truckType")):
            years = [y for y in years if (y < self._p("cycleDiscriminator.beforeYear")) == vin[self._p("cycleDiscriminator.position")].isdigit()]
        return years

    def _pass(self, vin, wmi, year, context):
        key = self._p("keySeparator").join(vin[self._p(f"keySlices.{i}.0"):self._p(f"keySlices.{i}.1")] for i in range(self._p("keySlices.length")))
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
                matches[element].append((self._p("formulaPriority") if formula else start, changed, pattern, pid, fact))
        engine = matches.get(self._p("engineElement"), [])
        if engine:
            parent = sorted(engine, key=lambda p: (p[0], not p[1], p[1], p[3]), reverse=True)[0][4]
            for pid, element, attr, value, changed in self.engines.get(parent["attributeId"].strip().lower(), ()):
                fact = self._fact(element, value, attr, "ENGINE_MODEL", parent["ruleId"] + "/engine:" + pid,
                                  parent["schemaId"], parent["keys"])
                matches[element].append((self._p("enginePriority"), changed, parent["keys"], int(pid), fact))
        facts = {}
        for element, items in matches.items():
            items.sort(key=lambda p: (len(p[2].replace("*", "")), p[2].replace("[", "").replace("]", ""), p[3]))
            items.sort(key=lambda p: (not p[1], p[1]), reverse=True)
            items.sort(key=lambda p: p[0], reverse=True)
            selected = items if element in self.policy.array("patternProfile.multipleElements") else items[:1]
            facts[element] = list({json.dumps(p[4], sort_keys=True): p[4] for p in selected}.values())
        if self._p("modelElement") in facts:
            parent = facts[self._p("modelElement")][0]
            model = self.models.get(parent["attributeId"])
            if model:
                facts[self._p("makeElement")] = [self._fact(self._p("makeElement"), model[1], model[0], "MODEL_MAKE", parent["ruleId"] + "/make:" + model[0],
                                       parent["schemaId"], parent["keys"])]
        # Enrich only from original facts, never chain rounded conversions.
        for cid, source, target, operator, factor in self.conversions:
            if source not in matches or target in facts or len(facts.get(source, [])) != 1:
                continue
            parent = facts[source][0]
            try:
                original = Decimal(parent["value"])
                number = original * factor if operator == "*" else original / factor
                text = format(number.quantize(Decimal(1).scaleb(-self._p("conversionScale")), rounding=ROUND_HALF_UP), "f").rstrip("0").rstrip(".")
            except InvalidOperation:
                continue
            facts[target] = [self._fact(target, text or "0", text or "0", "UNIT_CONVERSION",
                                        parent["ruleId"] + "/conversion:" + cid, parent["schemaId"], parent["keys"])]
        # A year code alone is not evidence that these vehicle-description rules matched.
        if facts:
            facts[self._p("yearElement")] = [self._fact(self._p("yearElement"), str(year), str(year), "CALLER_CONTEXT" if context.model_year else "VIN_YEAR",
                                    "model-year", key=vin[self._p("yearPosition")])]
        return {"modelYear": year, "market": self._p("market"), "fields": {self.elements[e][0]: f for e, f in sorted(facts.items())}}

    def decode(self, vin, structure, context):
        result = self._decode(vin, structure, context)
        used = {e["sourceId"] for field in result["fields"].values() for e in field["evidence"]}
        used.update(e["sourceId"] for a in result["alternatives"] for facts in a["fields"].values() for e in facts)
        result["sources"] = [copy.deepcopy(self.sources[sid]) for sid in sorted(used)]
        return result

    def _patterns_result(self, vin, structure, context):
        result = {"status": "UNKNOWN", "dataset": self.dataset, "marketScope": self._p("market"), "referenceYear": self.reference_year,
                  "stages": self.policy.array("patternProfile.stages"), "warnings": [], "fields": {}, "alternatives": [], "sources": []}
        if structure != "MODERN_FORMAT":
            result["status"] = "INVALID_INPUT"
            return result
        extended = vin[self._p("extendedWmi.position")] == self._p("extendedWmi.character")
        wmi = vin[:3] + vin[self._p("extendedWmi.suffixStart"):self._p("extendedWmi.suffixEnd")] if extended else vin[:3]
        if wmi not in self.wmis:
            return result
        years = self._years(vin, context, wmi)
        if not years:
            result["status"] = "CONTEXT_CONFLICT" if context.model_year is not None else "UNKNOWN"
            result["warnings"].append(self._p("yearConflictWarning"))
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
                      "NEEDS_CONTEXT" if context.market != self._p("market") else "KNOWN")
            result["fields"][code] = {"label": self.elements[element][1], "dataType": self.elements[element][2],
                                      "status": status, "possibilities": values,
                                      "value": values[0] if status == "KNOWN" else None, "evidence": evidence}
        if codes:
            result["status"] = "NEEDS_CONTEXT" if context.market != self._p("market") else "DECODED"
        if context.market != self._p("market") and codes:
            result["warnings"].append(self._p("unknownMarketWarning") if context.market is None else
                                      self._p("fallbackMessage").replace("{sourceMarket}", self._p("market")).replace("{requestedMarket}", context.market))
        if len(years) > 1:
            result["warnings"].append(self._p("yearAlternativesWarning"))
        return result

    def _decode(self, vin, structure, context):
        patterns = self._patterns_result(vin, structure, context)
        if structure != "MODERN_FORMAT":
            return patterns
        results = self._literals(vin, context) + [patterns]
        meaningful = [r for r in results if r["fields"] or r["alternatives"]]
        applicable_conflicts = [r for r in results if r["status"] == "CONTEXT_CONFLICT" and
                                (r["marketScope"] != self._p("market") or context.market == self._p("market"))]
        if applicable_conflicts:
            merged = copy.deepcopy(applicable_conflicts[0])
            merged["fields"] = {}
            merged["alternatives"] = [a for r in meaningful for a in r["alternatives"]]
            return merged
        if not meaningful:
            return patterns
        if len(meaningful) == 1:
            return meaningful[0]
        merged = copy.deepcopy(meaningful[0])
        merged["fields"] = {}
        merged["alternatives"] = [a for r in meaningful for a in r["alternatives"]]
        merged["stages"] = list(dict.fromkeys(s for r in meaningful for s in r["stages"]))
        merged["warnings"] = list(dict.fromkeys(s for r in meaningful for s in r["warnings"] if s))
        scopes = sorted({r["marketScope"] for r in meaningful})
        merged["marketScope"] = scopes[0] if len(scopes) == 1 else "MULTIPLE"
        for code in sorted({code for r in meaningful for code in r["fields"]}):
            fields = [r["fields"][code] for r in meaningful if code in r["fields"]]
            # Applicable claims (including ambiguity) block foreign suggestions.
            applicable = [f for f in fields if f["status"] != "NEEDS_CONTEXT" and any(
                r["fields"].get(code) is f and r["status"] != "NEEDS_CONTEXT" for r in meaningful)]
            selected = applicable or fields
            values = sorted({v for f in selected for v in f["possibilities"]})
            evidence = []
            for f in selected:
                for fact in f["evidence"]:
                    if fact not in evidence:
                        evidence.append(fact)
            status = "AMBIGUOUS" if len(values) > 1 else "UNKNOWN" if any(f["status"] == "UNKNOWN" for f in selected) else "KNOWN" if applicable else "NEEDS_CONTEXT"
            merged["fields"][code] = {**selected[0], "status": status, "possibilities": values,
                                      "value": values[0] if status == "KNOWN" else None, "evidence": evidence}
        merged["status"] = "DECODED" if any(f["status"] == "KNOWN" for f in merged["fields"].values()) else "NEEDS_CONTEXT"
        return merged
