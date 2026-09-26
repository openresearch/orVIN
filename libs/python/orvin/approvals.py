"""Swiss approval candidates. These are not decoded facts about an individual car."""
import base64
from functools import lru_cache
import gzip
import hashlib
import json

WARNINGS = [
    "Matching Swiss type-approval templates identify possible approved types, not this vehicle's actual configuration or market.",
    "Keep each approval's specifications together; remarks may further restrict variants. Approval dates are not model years or build dates.",
]
SOURCE_KEYS = ("id", "title", "publisher", "url", "edition", "section", "retrievedOn", "reuseBasis",
               "archivePath", "archiveSha256", "inspectedSha256", "evidencePath")


def _unb64(value):
    return base64.b64decode(value).decode("utf-8")


def unavailable():
    return {"status": "UNAVAILABLE", "dataset": None, "marketScope": "CH", "warnings": [],
            "fields": {}, "candidates": [], "sources": []}


class ApprovalDecoder:
    def __init__(self, directory):
        self.directory = directory
        metadata = json.loads((directory / "metadata.json").read_bytes())
        content = (directory / "index.tsv").read_bytes()
        self._verify(content, metadata["indexSha256"])
        self.dataset = {"version": metadata["version"], "sha256": metadata["indexSha256"]}
        self.fields, self.shards = {}, {}
        for line in content.decode("utf-8").splitlines():
            c = line.split("\t")
            if c[0] == "D":
                self.source = dict(zip(SOURCE_KEYS, map(_unb64, c[1:])))
            elif c[0] == "F":
                self.fields[c[1]] = {"label": _unb64(c[2]), "sourceColumn": _unb64(c[3]), "unit": _unb64(c[4])}
            elif c[0] == "W":
                self.shards[c[1]] = (c[2], c[3])

    @staticmethod
    def _verify(content, expected):
        if hashlib.sha256(content).hexdigest() != expected:
            raise RuntimeError("Bundled ASTRA data does not match its recorded SHA-256")

    @lru_cache(maxsize=8)
    def _rows(self, wmi):
        if wmi not in self.shards:
            return ()
        filename, sha = self.shards[wmi]
        content = (self.directory / filename).read_bytes()
        self._verify(content, sha)
        rows = []
        for line in gzip.decompress(content).decode("utf-8").splitlines():
            c = line.split("\t")
            rows.append((c[0], int(c[1]), _unb64(c[2]), tuple(c[3].split(",")),
                         {key: _unb64(value) for key, value in zip(self.fields, c[4:]) if value}))
        return tuple(rows)

    def decode(self, vin, structure):
        candidates = []
        if structure == "MODERN_FORMAT":
            for approval, row, original, patterns, fields in self._rows(vin[:3]):
                matched = [p for p in patterns if all(c == "." or c == v for c, v in zip(p, vin))]
                if matched:
                    candidates.append({"approvalId": approval, "sourceId": self.source["id"], "sourceRow": row,
                                       "vinPattern": original, "matchedPatterns": matched, "fields": dict(fields)})
        fields = {}
        for key, definition in self.fields.items():
            if key == "remarks":
                continue  # Conditions belong to each configuration, never a merged list.
            values = sorted({c["fields"][key] for c in candidates if key in c["fields"]})
            if values:
                fields[key] = {**definition, "possibilities": values}
        return {"status": "INVALID_INPUT" if structure != "MODERN_FORMAT" else "CANDIDATES" if candidates else "NO_MATCH",
                "dataset": dict(self.dataset), "marketScope": "CH", "warnings": list(WARNINGS) if candidates else [],
                "fields": fields, "candidates": candidates, "sources": [dict(self.source)] if candidates else []}
