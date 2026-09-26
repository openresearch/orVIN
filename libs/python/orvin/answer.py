"""Normalized vehicle answers; short and long are projections of one decision."""
import base64
import copy
from functools import lru_cache
import hashlib
import json

SOURCE_KEYS = ("id", "publisher", "title", "url", "edition", "section", "retrievedOn", "reuseBasis", "license", "termsUrl", "modifications", "archiveSha256", "inspectedSha256", "evidencePath")
PRIMARY = {"make": "Make", "model": "Model", "modelYear": "ModelYear", "productionYear": "ProductionYear"}


def _key(value):
    return value.strip().translate(str.maketrans("abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")) if value else ""


def _decode(value):
    return base64.b64decode(value).decode()


def _id(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()[:24]


class _Catalogue:
    def __init__(self, directory):
        self.metadata = json.loads((directory / "metadata.json").read_bytes())
        content = (directory / "index.tsv").read_bytes()
        if hashlib.sha256(content).hexdigest() != self.metadata["sha256"]:
            raise RuntimeError("Bundled identity catalogue does not match its SHA-256")
        self.makes, self.models, self.sources = {}, {}, {}
        for line in content.decode().splitlines():
            c = line.split("\t")
            if c[0] == "S":
                source = {key: _decode(v) or None for key, v in zip(SOURCE_KEYS, c[1:])}
                self.sources[source["id"]] = source
            elif c[0] in ("M", "D"):
                offset = 1 if c[0] == "M" else 2
                alias = _decode(c[offset])
                row = {"id": c[offset + 1], "name": _decode(c[offset + 2]), "sourceId": c[offset + 3],
                       "locator": _decode(c[offset + 4]), "original": alias}
                row["ruleId"] = "identity:" + _id([c[0], c[1] if c[0] == "D" else "", alias])
                if c[0] == "M":
                    self.makes[alias] = row
                else:
                    self.models[(c[1], alias)] = row

    def make(self, value):
        return self.makes.get(_key(value))

    def model(self, make_id, value):
        return self.models.get((make_id, _key(value)))


@lru_cache(maxsize=1)
def _catalogue():
    from .lookup import _data_directory
    return _Catalogue(_data_directory() / "identity")


class VehicleAnswer:
    """A resolved answer. Each projection returns an independent JSON-compatible dict."""
    def __init__(self, short, details):
        self._short, self._details = copy.deepcopy(short), copy.deepcopy(details)

    @property
    def vehicle(self):
        return copy.deepcopy(self._short["vehicle"])

    def short(self):
        return copy.deepcopy(self._short)

    def long(self):
        return {**self.short(), "details": copy.deepcopy(self._details)}


class _Builder:
    def __init__(self, raw, is_vin):
        self.raw, self.is_vin, self.catalogue = raw, is_vin, _catalogue()
        self.sources = dict(self.catalogue.sources)
        self.evidence, self.alternatives, self.normalizations = {}, [], {}
        self.decisions, self.status, self.vehicle, self.assumptions = {}, {}, {}, []
        for name in PRIMARY:
            if name in ("make", "model"):
                self.vehicle[name + "Id"] = None
            self.vehicle[name] = None
            self.status[name] = "UNKNOWN"
            self.decisions[name] = {"reason": "NO_EVIDENCE", "evidenceIds": [], "normalizationRuleIds": [], "alternativeIds": []}
        self.wmi_ids, self.approval_ids, self.rich_ids = [], [], {}
        self._collect()

    def _add_source(self, source):
        sid = source["id"]
        # The reviewed common catalogue supplies licensing fields absent from legacy DTOs.
        self.sources[sid] = {**source, **{k: v for k, v in self.sources.get(sid, {}).items() if v is not None}}

    def _fact(self, fact):
        eid = "fact:" + _id(fact)
        record = dict(fact)
        if record.get("sourceUrl") == self.sources.get(fact["sourceId"], {}).get("url"):
            record.pop("sourceUrl", None)
        self.evidence[eid] = {"kind": "VIN_FACT", "sourceIds": [fact["sourceId"]], "record": record}
        return eid

    def _collect(self):
        if not self.is_vin:
            source = self.raw["dataset"]["source"]
            sid = "kba-fz-types-" + self.raw["dataset"]["referenceDate"]
            self._add_source({**source, "id": sid, "edition": self.raw["dataset"]["referenceDate"]})
            for row in self.raw["candidates"]:
                eid = "kba:" + str(row["sourceObjectId"])
                self.evidence[eid] = {"kind": "KBA_TYPE", "sourceIds": [sid], "record": row}
                self.approval_ids.append(eid)
            if self.raw["inputStatus"] == "VALID" and not self.approval_ids:
                self.evidence["kba:lookup"] = {"kind": "LOOKUP_CHECK", "sourceIds": [sid], "record": {
                    "hsn": self.raw["normalizedHsn"], "tsn": self.raw["normalizedTsn"],
                    "referenceDate": self.raw["dataset"]["referenceDate"], "result": "NO_MATCH"}}
                for name in ("make", "model"):
                    self.decisions[name].update(reason="NO_TYPE_CODE_MATCH", evidenceIds=["kba:lookup"])
            return
        for candidate in self.raw["candidates"]:
            row = copy.deepcopy(candidate)
            source_ids = set()
            for source in row.pop("sources") + row["manufacturer"].pop("sources"):
                self._add_source(source)
                source_ids.add(source["id"])
            eid = "wmi:" + row["id"]
            self.evidence[eid] = {"kind": "WMI_ASSIGNMENT", "sourceIds": sorted(source_ids), "record": row}
            self.wmi_ids.append(eid)
        for source in self.raw["details"]["sources"] + self.raw["typeApprovals"]["sources"]:
            self._add_source(source)
        for code, field in self.raw["details"]["fields"].items():
            self.rich_ids[code] = sorted({self._fact(f) for f in field["evidence"]})
        for alternative in self.raw["details"]["alternatives"]:
            fields = {code: sorted({self._fact(f) for f in facts}) for code, facts in sorted(alternative["fields"].items())}
            self.alternatives.append({"id": "configuration:" + _id(alternative), "kind": "VIN_CONFIGURATION",
                "modelYear": alternative["modelYear"], "market": alternative["market"], "fields": fields})
        for row in self.raw["typeApprovals"]["candidates"]:
            eid = "approval:" + row["sourceId"] + ":" + str(row["sourceRow"])
            self.evidence[eid] = {"kind": "TYPE_APPROVAL", "sourceIds": [row["sourceId"]], "record": row}
            self.approval_ids.append(eid)

    def _select(self, name, values, knowledge, evidence_ids, reason, make_id=None):
        mappings, mapped, missing = [], [], not values
        for value in values:
            mapping = (self.catalogue.make(value) if name == "make" else
                       self.catalogue.model(make_id, value) if name == "model" else None)
            if name in ("make", "model"):
                missing |= mapping is None
                if mapping:
                    mappings.append(mapping)
                    mapped.append((mapping["id"], mapping["name"]))
            else:
                try:
                    mapped.append((None, int(value)))
                except (TypeError, ValueError):
                    missing = True
        unique = sorted(set(mapped), key=lambda v: str(v))
        status = ("AMBIGUOUS" if len(unique) > 1 else "UNKNOWN" if missing or knowledge == "UNKNOWN" else
                  "SUGGESTED" if knowledge == "NEEDS_CONTEXT" else "RESOLVED")
        self.status[name] = status
        self.vehicle[name] = unique[0][1] if status in ("RESOLVED", "SUGGESTED") else None
        if name in ("make", "model"):
            self.vehicle[name + "Id"] = unique[0][0] if self.vehicle[name] is not None else None
        for mapping in mappings:
            self.normalizations[mapping["ruleId"]] = mapping
        self.decisions[name] = {"reason": "UNMAPPED_IDENTITY" if missing and values and name in ("make", "model") else
                                "COMPETING_IDENTITIES" if status == "AMBIGUOUS" else reason,
            "evidenceIds": sorted(set(evidence_ids)), "normalizationRuleIds": sorted({m["ruleId"] for m in mappings}),
            "alternativeIds": sorted(a["id"] for a in self.alternatives if any(set(ids) & set(evidence_ids) for ids in a["fields"].values()))}

    def _assume(self, code, fields):
        if fields:
            self.assumptions.append({"code": code, "fields": fields})

    def resolve(self):
        if self.is_vin:
            if self.raw["structure"] != "MODERN_FORMAT":
                return self.finish()
            rich = self.raw["details"]
            for name, code in PRIMARY.items():
                field = rich["fields"].get(code)
                if field:
                    self._select(name, field["possibilities"], field["status"], self.rich_ids[code], "SCOPED_VIN_RULE", self.vehicle["makeId"])
            # A unique WMI assignment can establish the marque when no direct make is established.
            if self.status["make"] != "RESOLVED" and self.wmi_ids and not rich["fields"].get("Make"):
                self._select("make", [r.get("brand") for r in self.raw["candidates"]], self.raw["brand"]["status"],
                             self.wmi_ids, "WMI_ASSIGNMENT")
            if self.status["make"] == "SUGGESTED" and self.raw["brand"]["status"] == "KNOWN":
                mapped = [self.catalogue.make(r.get("brand")) for r in self.raw["candidates"]]
                if mapped and all(m and m["id"] == self.vehicle["makeId"] for m in mapped):
                    self._select("make", [r["brand"] for r in self.raw["candidates"]], "KNOWN", self.wmi_ids, "WMI_ASSIGNMENT")
            conditional = [name for name in PRIMARY if self.status[name] == "SUGGESTED" and PRIMARY[name] in rich["fields"]]
            self._assume("US_MARKET_ASSUMED", conditional if rich["marketScope"] == "US" else [])
            if self.status["make"] == "SUGGESTED" and not conditional:
                self._assume("MATCH_CONSTRAINTS_UNCONFIRMED", ["make"])
            # A conflict is never replaced by a weaker catalogue guess.
            conflict = rich["status"] == "CONTEXT_CONFLICT" and (rich["marketScope"] != "US" or self.raw["context"]["market"] == "US")
            supplied_year = self.raw["context"]["modelYear"]
            if supplied_year is not None:
                self.evidence["context:modelYear"] = {"kind": "CALLER_CONTEXT", "sourceIds": [], "record": self.raw["context"]}
            if conflict:
                for name in ("model", "modelYear"):
                    self.vehicle[name] = None
                    self.status[name] = "CONFLICT"
                    self.decisions[name]["reason"] = "CALLER_CONTEXT_CONFLICT"
                    self.decisions[name]["evidenceIds"] = sorted({"context:modelYear", *[eid for a in self.alternatives for eid in a["fields"].get(PRIMARY[name], [])]})
                    self.decisions[name]["alternativeIds"] = sorted(a["id"] for a in self.alternatives)
                self.vehicle["modelId"] = None
            if self.approval_ids:
                rows = [self.evidence[eid]["record"]["fields"] for eid in self.approval_ids]
                # Only exact reviewed label mappings; never turn arbitrary type prefixes into model families.
                for name, key in (("make", "make"), ("model", "type")):
                    if self.status[name] not in ("UNKNOWN", "SUGGESTED") or (name == "model" and conflict):
                        continue
                    if name == "model" and (not self.vehicle["makeId"] or any(
                            not self.catalogue.make(r.get("make")) or self.catalogue.make(r.get("make"))["id"] != self.vehicle["makeId"] for r in rows)):
                        continue
                    if self.status[name] == "SUGGESTED":
                        mapped = [self.catalogue.make(r.get(key)) if name == "make" else self.catalogue.model(self.vehicle["makeId"], r.get(key)) for r in rows]
                        if mapped and all(mapped) and {m["id"] for m in mapped} != {self.vehicle[name + "Id"]}:
                            self.vehicle[name] = self.vehicle[name + "Id"] = None
                            self.status[name] = "AMBIGUOUS"
                            self.decisions[name]["reason"] = "COMPETING_CONDITIONAL_SOURCES"
                            self.decisions[name]["evidenceIds"] = sorted(set(self.decisions[name]["evidenceIds"] + self.approval_ids))
                            for mapping in mapped:
                                self.normalizations[mapping["ruleId"]] = mapping
                            self.decisions[name]["normalizationRuleIds"] = sorted(set(self.decisions[name]["normalizationRuleIds"] + [m["ruleId"] for m in mapped]))
                        continue
                    self._select(name, [r.get(key) for r in rows], "NEEDS_CONTEXT", self.approval_ids,
                                 "CATALOGUE_CONSENSUS", self.vehicle["makeId"])
                    if self.status[name] == "SUGGESTED":
                        self._assume("CATALOGUE_MEMBERSHIP_UNCONFIRMED", [name])
            if self.vehicle["makeId"] is None and self.vehicle["modelId"] is not None:
                self.vehicle["model"] = self.vehicle["modelId"] = None
                self.status["model"] = "AMBIGUOUS"
                self.decisions["model"]["reason"] = "PRIMARY_MAKE_UNRESOLVED"
                self.decisions["model"]["evidenceIds"] = sorted(set(self.decisions["model"]["evidenceIds"] + self.decisions["make"]["evidenceIds"]))
            if self.decisions["model"]["reason"] in ("COMPETING_CONDITIONAL_SOURCES", "PRIMARY_MAKE_UNRESOLVED") and self.status["modelYear"] == "SUGGESTED":
                self.vehicle["modelYear"] = None
                self.status["modelYear"] = "UNKNOWN"
                self.decisions["modelYear"]["reason"] = "IDENTITY_APPLICABILITY_UNRESOLVED"
            year = self.raw["context"]["modelYear"]
            if year is not None and not conflict:
                if self.vehicle["modelYear"] is not None and self.vehicle["modelYear"] != year:
                    self.vehicle["modelYear"], self.status["modelYear"] = None, "CONFLICT"
                    self.decisions["modelYear"]["reason"] = "CALLER_CONTEXT_CONFLICT"
                else:
                    self.vehicle["modelYear"], self.status["modelYear"] = year, "PROVIDED"
                    self.decisions["modelYear"]["reason"] = "CALLER_CONTEXT"
                self.decisions["modelYear"]["evidenceIds"] = sorted(set(self.decisions["modelYear"]["evidenceIds"] + ["context:modelYear"]))
            for assumption in self.assumptions:
                assumption["fields"] = [name for name in assumption["fields"] if self.status[name] != "PROVIDED"]
            self.assumptions = [a for a in self.assumptions if a["fields"]]
        elif self.raw["inputStatus"] == "VALID" and self.approval_ids:
            rows = self.raw["candidates"]
            self._select("make", [r["manufacturer"] for r in rows], "KNOWN", self.approval_ids, "TYPE_CODE_LOOKUP")
            if self.vehicle["makeId"]:
                self._select("model", [r["tradeName"] for r in rows], "KNOWN", self.approval_ids, "TYPE_CODE_LOOKUP", self.vehicle["makeId"])
        return self.finish()

    def _credit(self, sid, fields):
        source = self.sources[sid]
        terms = source.get("termsUrl") or source.get("licenseUrl") or source.get("reuseUrl")
        return {"id": sid, "publisher": source.get("publisher"), "title": source.get("title"), "url": source.get("url"),
            "edition": source.get("edition") or source.get("publicationVersion"), "license": source.get("license"),
            "termsUrl": terms, "reuseBasis": source.get("reuseBasis"),
            "attribution": str(source.get("publisher", "")) + " — " + str(source.get("title", "")),
            "modifications": source.get("modifications") or "Source labels normalized by ORvin; original facts retained in evidence.",
            "fields": sorted(fields)}

    def finish(self):
        common, all_sources = {}, {m["sourceId"] for m in self.normalizations.values()}
        for evidence in self.evidence.values():
            all_sources.update(evidence["sourceIds"])
        for name, decision in self.decisions.items():
            used = {sid for eid in decision["evidenceIds"] for sid in self.evidence[eid]["sourceIds"]}
            used.update(self.normalizations[rid]["sourceId"] for rid in decision["normalizationRuleIds"])
            paths = ["/vehicle/" + name, "/vehicle/" + name + "Id"] if name in ("make", "model") else ["/vehicle/" + name]
            if self.vehicle[name] is None:
                paths = ["/fieldStatus/" + name]
            for sid in used:
                common.setdefault(sid, set()).update(paths)
            all_sources.update(used)
        short = {"schemaVersion": 1}
        if self.is_vin:
            short.update(vin=self.raw["normalized"], inputStatus="SUPPORTED_FORMAT" if self.raw["structure"] == "MODERN_FORMAT" else self.raw["structure"])
        else:
            short.update(hsn=self.raw["normalizedHsn"], tsn=self.raw["normalizedTsn"],
                         inputStatus="SUPPORTED_FORMAT" if self.raw["inputStatus"] == "VALID" else self.raw["inputStatus"])
        short.update(vehicle=self.vehicle, fieldStatus=self.status, assumptions=self.assumptions,
                     sources=[self._credit(sid, fields) for sid, fields in sorted(common.items())])
        source_details = {sid: {k: v for k, v in self.sources[sid].items() if k not in
            ("id", "publisher", "title", "url", "edition", "license", "termsUrl", "reuseBasis", "modifications")}
                          for sid in sorted(all_sources)}
        diagnostics = []
        datasets = {"lookup": self.raw["dataset"], "identity": {k: self.catalogue.metadata[k] for k in ("version", "sha256")}}
        specifications, variables = {}, {}
        if self.is_vin:
            datasets.update(decoding=self.raw["details"]["dataset"], typeApprovals=self.raw["typeApprovals"]["dataset"])
            for name in ("details", "typeApprovals"):
                section = self.raw[name]
                diagnostics.append({"source": name, "status": section["status"], "marketScope": section["marketScope"], "warnings": section["warnings"]})
                if name == "details":
                    diagnostics[-1].update(referenceYear=section["referenceYear"], stages=section["stages"])
            diagnostics.append({"source": "typeApprovals", "candidateCount": len(self.approval_ids)})
            variables = {"decoding": {code: {k: f[k] for k in ("label", "dataType", "status")} for code, f in sorted(self.raw["details"]["fields"].items())},
                         "typeApprovals": {code: {k: f[k] for k in ("label", "sourceColumn", "unit")} for code, f in sorted(self.raw["typeApprovals"]["fields"].items())}}
            for code, field in sorted(self.raw["details"]["fields"].items()):
                if code not in PRIMARY.values() and field["status"] == "KNOWN":
                    specifications[code] = {"value": field["value"], "status": "RESOLVED", "dataType": field["dataType"],
                                            "evidenceIds": self.rich_ids[code]}
            input_data = {"supplied": self.raw["supplied"], "context": self.raw["context"], "structure": self.raw["structure"]}
        else:
            datasets["lookup"] = {k: v for k, v in self.raw["dataset"].items() if k != "source"}
            input_data = {k: self.raw[k] for k in ("suppliedHsn", "suppliedTsn", "inputStatus")}
            diagnostics.append({"source": "kba", "status": self.raw["status"], "candidateCount": len(self.approval_ids)})
        rules = {}
        for item in self.evidence.values():
            if item["kind"] == "VIN_FACT":
                record = item["record"]
                rule = {key: record[key] for key in ("sourceId", "ruleId", "schemaId", "keys", "kind")}
                rules["rule:" + _id(rule)] = rule
        details = {"meta": {"library": "ORvin", "policyVersion": "vehicle-identity-v1", "datasets": datasets}, "input": input_data,
            "decisions": self.decisions, "specifications": specifications, "alternatives": self.alternatives,
            "evidence": dict(sorted(self.evidence.items())), "provenance": {"rules": dict(sorted(rules.items())), "variables": variables, "normalizationRules": dict(sorted(self.normalizations.items())),
                "sourceDetails": source_details,
                "additionalSources": [self._credit(sid, ["/details/evidence"]) for sid in sorted(all_sources - common.keys())]},
            "diagnostics": diagnostics}
        return VehicleAnswer(short, details)


def vin_answer(result):
    return _Builder(result, True).resolve()


def hsntsn_answer(result):
    return _Builder(result, False).resolve()
