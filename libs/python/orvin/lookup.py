"""Standard-library-only implementation; no network access or Java subprocesses."""
import copy
import csv
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import io
import json
from pathlib import Path
import re


def _data_directory():
    packaged = Path(__file__).parent / "_data"
    if packaged.is_dir():
        return packaged
    # A source checkout uses the one canonical data directory shared with Java.
    root = Path(__file__).resolve().parents[3]
    if (root / "libs/python/orvin/lookup.py").is_file() and (root / "data/generated/manifest.tsv").is_file():
        return root / "data/generated"
    raise RuntimeError("Bundled Orvin data is missing; reinstall the package")


def _normalize(value):
    if not isinstance(value, str):
        raise TypeError("Identifiers must be strings (including leading zeroes)")
    return value.strip(" ").translate(str.maketrans("abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"))


@dataclass(frozen=True)
class Context:
    """Independently supplied context; rich decoding may separately infer scoped year candidates."""
    model_year: int | None = None
    market: str | None = None

    def __post_init__(self):
        if self.model_year is not None and (type(self.model_year) is not int or not 1886 <= self.model_year <= 9999):
            raise ValueError("Model year must be between 1886 and 9999")
        if self.market is not None and (not isinstance(self.market, str) or not re.fullmatch("[A-Z]{2}", self.market)):
            raise ValueError("Market must use an uppercase two-letter country code")


def _may_apply(constraints, context):
    return ((context.market is None or not constraints["markets"] or context.market in constraints["markets"])
            and (context.model_year is None or
                 (constraints["fromModelYear"] or 1886) <= context.model_year <= (constraints["toModelYear"] or 9999)))


def _established(constraints, context):
    return ((not constraints["markets"] or context.market is not None)
            and ((constraints["fromModelYear"] is None and constraints["toModelYear"] is None)
                 or context.model_year is not None))


def _resolve(candidates, field, context):
    values = []
    missing = not candidates
    for candidate in candidates:
        value = field(candidate)
        if value is None:
            missing = True
        elif value not in values:
            values.append(value)
    status = ("AMBIGUOUS" if len(values) > 1 else "UNKNOWN" if missing else
              "NEEDS_CONTEXT" if any(not _established(a["constraints"], context) for a in candidates) else "KNOWN")
    return {"status": status, "possibilities": values, "value": values[0] if status == "KNOWN" else None}


class VinDecoder:
    """Manufacturer lookup with independent length/alphabet assessment; not VIN authentication."""

    def __init__(self, data, sha256):
        self._rich = None
        self._approvals = None
        data = copy.deepcopy(data)
        self._dataset = {"version": data["version"], "sha256": sha256}
        sources = {}
        for s in data["sources"]:
            sources[s["id"]] = {**{k: s[k] for k in ("id", "title", "url", "publisher", "retrievedOn",
                                                    "publicationVersion", "section")},
                "license": s["reuse"]["license"], "reuseUrl": s["reuse"]["url"], "reuseBasis": s["reuse"]["basis"],
                "snapshot": s.get("snapshot"), "snapshotSha256": s.get("sha256")}
        manufacturers = {m["id"]: {"id": m["id"], "name": m["name"], "country": m.get("country"),
                                      "sources": [sources[s] for s in m["sourceRefs"]]} for m in data["manufacturers"]}
        self._by_wmi = {}
        self._extended_prefixes = set()
        for a in sorted(data["assignments"], key=lambda row: row["id"]):
            c = a["constraints"]
            entry = {"id": a["id"], "wmi": a["wmi"], "manufacturer": manufacturers[a["manufacturerId"]],
                     "brand": a.get("brand"), "category": a.get("category"),
                     "constraints": {"markets": sorted(c.get("markets", [])), "fromModelYear": c.get("fromModelYear"),
                                     "toModelYear": c.get("toModelYear")},
                     "sources": [sources[s] for s in a["sourceRefs"]], "notes": a["notes"],
                     "ambiguityGroup": a.get("ambiguityGroup"), "ambiguityReason": a.get("ambiguityReason")}
            self._by_wmi.setdefault(a["wmi"], []).append(entry)
            if len(a["wmi"]) == 6:
                self._extended_prefixes.add(a["wmi"][:3])

    @classmethod
    @lru_cache(maxsize=1)
    def bundled(cls):
        from .program import read
        rows = [line.split("\t") for line in read(_data_directory(), "dataset.tsv").decode().splitlines()]
        data = {"version": rows[0][1], "sources": [], "manufacturers": [], "assignments": []}
        for c in rows[1:]:
            if c[0] == "S":
                data["sources"].append(dict(zip(("id", "title", "url", "publisher", "retrievedOn", "publicationVersion", "section"), c[1:8]),
                    reuse={"license": c[8], "url": c[9], "basis": c[10]}, snapshot=c[11] or None, sha256=c[12] or None))
            elif c[0] == "M":
                data["manufacturers"].append({"id": c[1], "name": c[2], "country": c[3] or None, "sourceRefs": c[4].split(",")})
            elif c[0] == "A":
                data["assignments"].append({"id": c[1], "wmi": c[2], "manufacturerId": c[3], "brand": c[4] or None,
                    "category": c[5] or None, "sourceRefs": c[6].split(","), "constraints": {
                        "markets": c[7].split(",") if c[7] else [], "fromModelYear": int(c[8]) if c[8] else None,
                        "toModelYear": int(c[9]) if c[9] else None}, "notes": c[10],
                    "ambiguityGroup": c[11] or None, "ambiguityReason": c[12] or None})
            else:
                raise RuntimeError("Unsupported assignment operation")
        decoder = cls(data, rows[0][2])
        from .details import RichDecoder
        decoder._rich = RichDecoder(_data_directory() / "decoding")
        from .approvals import ApprovalDecoder
        decoder._approvals = ApprovalDecoder(_data_directory() / "astra")
        return decoder

    @property
    def dataset(self):
        return copy.deepcopy(self._dataset)

    def decode_vehicle(self, supplied, context=None):
        """Return one normalized answer with short() and long() JSON projections."""
        from .answer import vin_answer
        return vin_answer(self.decode(supplied, context))

    def decode(self, supplied, context=None):
        context = Context() if context is None else context
        if not isinstance(context, Context):
            raise TypeError("context must be an Orvin Context")
        normalized = _normalize(supplied)
        # Java String.length counts UTF-16 code units; use the same boundary for unusual input.
        length = len(normalized.encode("utf-16-le", errors="surrogatepass")) // 2
        structure = ("UNSUPPORTED_LENGTH" if length != 17 else
                     "MODERN_FORMAT" if re.fullmatch("[A-HJ-NPR-Z0-9]{17}", normalized) else "INVALID_CHARACTERS")
        candidates = []
        if structure == "UNSUPPORTED_LENGTH":
            status = "UNSUPPORTED_FORMAT"
        else:
            # Slicing code units also matches Java for invalid, non-BMP input.
            units = normalized.encode("utf-16-le", errors="surrogatepass")
            prefix = units[:6].decode("utf-16-le", errors="surrogatepass")
            key = prefix + units[22:28].decode("utf-16-le", errors="surrogatepass") if prefix in self._extended_prefixes else prefix
            candidates = [a for a in self._by_wmi.get(key, []) if _may_apply(a["constraints"], context)]
            status = ("UNKNOWN" if not candidates else "AMBIGUOUS" if len(candidates) > 1 else
                      "NEEDS_CONTEXT" if not _established(candidates[0]["constraints"], context) else "RECOGNIZED")
        result = {"supplied": supplied, "normalized": normalized, "structure": structure, "status": status,
                  "candidates": candidates, "dataset": self._dataset,
                  "context": {"modelYear": context.model_year, "market": context.market}}
        for name in ("manufacturer", "brand", "category"):
            result[name] = _resolve(candidates, lambda a, key=name: a[key], context)
        result["manufacturerCountry"] = _resolve(candidates, lambda a: a["manufacturer"]["country"], context)
        from .details import resolution, unavailable
        result["details"] = self._rich.decode(normalized, structure, context) if self._rich else unavailable()
        from .approvals import unavailable as approvals_unavailable
        result["typeApprovals"] = (self._approvals.decode(normalized, structure) if self._approvals
                                   else approvals_unavailable())
        result["model"] = resolution(result["details"], "Model")
        result["modelYear"] = resolution(result["details"], "ModelYear")
        result["assemblyCountry"] = resolution(result["details"], "PlantCountry")
        decoded_make = resolution(result["details"], "Make")
        if decoded_make["status"] == "KNOWN":
            result["brand"] = decoded_make
        return copy.deepcopy(result)


class HsnTsnLookup:
    """Lookup supplied HSN/TSN against a fixed KBA reference date; never infer them from VIN."""

    def __init__(self, dataset, entries):
        self._dataset = copy.deepcopy(dataset)
        self._by_code = {}
        for entry in copy.deepcopy(entries):
            self._by_code.setdefault(entry["hsn"] + entry["tsn"], []).append(entry)

    @classmethod
    @lru_cache(maxsize=1)
    def bundled(cls):
        directory = _data_directory() / "kba"
        from .program import read
        metadata = json.loads(read(directory.parent, "kba/metadata.json"))
        content = (directory / "types.tsv").read_bytes()
        if hashlib.sha256(content).hexdigest() != metadata["sha256"]:
            raise RuntimeError("Bundled KBA table does not match its recorded SHA-256")
        entries = []
        for row in csv.DictReader(io.StringIO(content.decode("utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE):
            entry = {key: None if value == "\\N" else value for key, value in row.items()}
            if entry["registeredCount"] is not None:
                entry["registeredCount"] = int(entry["registeredCount"])
            entry["sourceObjectId"] = int(entry["sourceObjectId"])
            entries.append(entry)
        if len(entries) != metadata["recordCount"]:
            raise RuntimeError("Bundled KBA table is incomplete")
        dataset = {k: metadata[k] for k in ("version", "sha256", "referenceDate", "recordCount")}
        dataset["source"] = {k: metadata[k] for k in ("title", "publisher", "url", "serviceUrl", "retrievedOn",
                                                       "license", "licenseUrl", "modifications", "snapshotSha256")}
        return cls(dataset, entries)

    @property
    def dataset(self):
        return copy.deepcopy(self._dataset)

    def lookup_vehicle(self, hsn, tsn):
        """Return the normalized, sourced answer for independently supplied codes."""
        from .answer import hsntsn_answer
        return hsntsn_answer(self.lookup(hsn, tsn))

    def lookup(self, hsn, tsn):
        normalized_hsn, normalized_tsn = _normalize(hsn), _normalize(tsn)
        valid_hsn = re.fullmatch("[0-9]{4}", normalized_hsn) is not None
        valid_tsn = re.fullmatch("[A-Z0-9]{3}", normalized_tsn) is not None
        input_status = (("VALID" if valid_tsn else "INVALID_TSN") if valid_hsn else
                        ("INVALID_HSN" if valid_tsn else "INVALID_HSN_AND_TSN"))
        candidates = self._by_code.get(normalized_hsn + normalized_tsn, []) if input_status == "VALID" else []
        status = ("INVALID_INPUT" if input_status != "VALID" else "UNKNOWN" if not candidates else
                  "RECOGNIZED" if len(candidates) == 1 else "AMBIGUOUS")
        return copy.deepcopy({"suppliedHsn": hsn, "suppliedTsn": tsn, "normalizedHsn": normalized_hsn,
                              "normalizedTsn": normalized_tsn, "inputStatus": input_status, "status": status,
                              "candidates": candidates, "dataset": self._dataset,
                              "value": candidates[0] if status == "RECOGNIZED" else None})
