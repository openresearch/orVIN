"""The versioned runtime contract; no upstream formats or vehicle-specific logic."""
import base64
from functools import lru_cache
import hashlib

FORMAT = "orvin-runtime-1"
CAPABILITIES = {"patterns", "conditional-literals", "year-cycles", "relations", "decimal-scaling", "catalogue-consensus", "cross-market"}


@lru_cache(maxsize=1)
def manifest(directory):
    rows = [line.split("\t") for line in (directory / "manifest.tsv").read_text().splitlines()]
    if rows[0][1] != FORMAT or not set(rows[0][2].split(",")) <= CAPABILITIES:
        raise RuntimeError("Unsupported ORvin runtime format/capabilities")
    return {c[1]: c[2] for c in rows if c[0] == "F"}


def read(directory, name):
    expected = manifest(directory).get(name)
    content = (directory / name).read_bytes()
    if expected is None or hashlib.sha256(content).hexdigest() != expected:
        raise RuntimeError("Runtime bundle integrity failure: " + name)
    return content


class Policy:
    def __init__(self, content):
        self.values = {}
        for line in content.decode().splitlines():
            key, kind, value = line.split("\t")
            self.values[key] = (base64.b64decode(value).decode() if kind == "S" else
                                int(value) if kind == "I" else value == "true")

    def get(self, key):
        return self.values[key]

    def array(self, key):
        return [self.get(f"{key}.{i}") for i in range(self.get(key + ".length"))]


@lru_cache(maxsize=1)
def policy():
    from .lookup import _data_directory
    return Policy(read(_data_directory(), "policy.tsv"))


def rules(directory):
    import re
    result = {}
    for line in read(directory, "rules.tsv").decode().splitlines():
        tag, *cells = line.split("\t")
        c = [base64.b64decode(v).decode() for v in cells]
        if tag == "R":
            result[c[0]] = {"pattern": re.compile(c[1]), "exclude": re.compile(c[2]) if c[2] else None,
                "scope": c[3], "markets": c[4].split(",") if c[4] else [], "year": int(c[5]) if c[5] else None,
                "stage": c[6], "warning": c[7], "conflictWarning": c[8], "claims": []}
        elif tag == "F":
            result[c[0]]["claims"].append((int(c[1]), *c[2:]))
        else:
            raise RuntimeError("Unsupported literal-rule operation: " + tag)
    return list(result.values())
