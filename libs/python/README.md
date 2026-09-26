# orVIN for Python

`VinDecoder.bundled().decode(vin)["typeApprovals"]` provides sourced Swiss
type-approval candidates, including original type names, engine/power alternatives
and per-approval remarks. These are catalogue possibilities; they do not overwrite
the separately decoded `model`, `modelYear` or plant facts. All required runtime data and source credits are
bundled for offline use.

Offline VIN manufacturer and German HSN/TSN lookup. Python 3.10+, no runtime dependencies.
The wheel includes the same compiled dataset used by Java and .NET:
12,998 usable NHTSA WMIs, 63,260 KBA HSN/TSN records and 122,273 Swiss approval rows.
Original source archives and test fixtures stay in the repository. orVIN uses 1,343,387 public patterns to decode model, year,
factory and other vehicle fields with explicit scope/provenance. Selected European Tesla
Model Y rules distinguish production year from model year. Runtime loads required compressed
shards through bounded caches and never executes SQL or uses a database server.

```python
from orvin import Context, HsnTsnLookup, VinDecoder

answer = VinDecoder.bundled().decode_vehicle("WVWZZZ1KZ5P000001")
print(answer.vehicle)  # VW / Golf / 2005; productionYear is None
short_values = answer.short()
long_values = answer.long()  # same root values, plus details

# Original source-level API remains available:
vin = VinDecoder.bundled().decode("1HGAAAAAAAAAAAAAA")  # synthetic example
print(vin["manufacturer"]["value"]["name"])

# Scoped US-market decoding:
vehicle = VinDecoder.bundled().decode("1HGCM82603A000000", Context(market="US"))
print(vehicle["model"]["value"])  # Accord
print(vehicle["details"]["fields"]["PlantCity"]["value"])  # MARYSVILLE

german_type = HsnTsnLookup.bundled().lookup("0005", "AMQ")
print(german_type["value"]["tradeName"])
print(german_type["dataset"]["referenceDate"])
```

Results are fresh JSON-compatible dictionaries with explicit status values, candidates,
unknown values (`None`) and source/license metadata. Mutating a returned dictionary does not
change subsequent lookups. Use `Context(model_year=2005, market="US")` as the second argument
to `decode` only when that context is independently known. `dataset` is a read-only property
returning a fresh dictionary. `bundled()` caches parsed data per process.

NHTSA rich fields are conditional (`NEEDS_CONTEXT`) unless US market scope is independently
known. A foreign-market match may supply a labeled
`SUGGESTED` identity when no applicable claim exists. It does not establish technical facts. `details.alternatives` keeps uncertain year cycles
separate. All attribute values, including numbers, are strings; `None` means no established value.
Field evidence includes source URLs, rule/schema IDs and derivation kind. Exact build dates,
full option lists and vehicle histories are not decoded. WMI `status` remains independent of
`details.status`; a model can resolve the brand while original WMI candidates remain available.

HSN must contain four digits, including leading zeroes; TSN must contain three ASCII letters
or digits. Normalization only trims ASCII spaces and uppercases ASCII letters. Longer field
2.2 codes are not silently truncated. An absent type remains unknown: the KBA snapshot records
the stock at one reference date, not every type ever assigned. VIN cannot determine HSN/TSN.

Install the [0.3.1 release](https://github.com/openresearch/orvin/releases/tag/v0.3.1) wheel,
including normalized answers, rich decoding and the bundled dataset:

```sh
python3 -m pip install https://github.com/openresearch/orvin/releases/download/v0.3.1/orvin-0.3.1-py3-none-any.whl
```

The wheel/sdist are GitHub Release assets; the package is not published on PyPI.
From a checkout, install with `python3 -m pip install ./libs/python` for the development version.
The repository's `vin.sh` and `hsntsn.sh` need no installation. After installation, use
`orvin vin <vin>` / `orvin hsntsn <hsn> <tsn>` or `python3 -m orvin` with the same arguments.
Commands now return normalized short JSON by default; `--json` selects the same
view. Add `--long` or `--json --long` for the exact short object plus `details`,
including all evidence and additional source credits. `--json=short` and
`--json=long` are equivalent selectors. This intentionally replaces the old CLI
JSON shape; raw `decode`/`lookup` dictionary APIs remain available. Both views retain
attribution and assumptions. Unknown/unreviewed model-family mappings stay null;
source-specific candidate configurations and remarks remain in the long evidence.

Code: Apache-2.0. Bundled KBA data: dl-de/by-2-0. NHTSA data retains its source notice;
orVIN-owned data contributions alone are CC0. Preserve the bundled `_data/LICENSE.md`,
`_data/CODE-NOTICE`, source records and license links when redistributing data.
