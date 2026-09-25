# Orvin for Python

Offline VIN manufacturer and German HSN/TSN lookup. Python 3.10+, no runtime dependencies.
The wheel includes the same canonical datasets used by Java: 12,998 usable NHTSA WMIs and
63,260 KBA HSN/TSN records, plus the complete 76.2 MB NHTSA source ZIP and KBA snapshot.
The detailed VIN-pattern tables are archived; model/year/engine/trim decoding is not yet
implemented. Normal lookup loads only the normalized indexes and never executes SQL.

```python
from orvin import HsnTsnLookup, VinDecoder

vin = VinDecoder.bundled().decode("1HGAAAAAAAAAAAAAA")  # synthetic example
print(vin["manufacturer"]["value"]["name"])

german_type = HsnTsnLookup.bundled().lookup("0005", "AMQ")
print(german_type["value"]["tradeName"])
print(german_type["dataset"]["referenceDate"])
```

Results are fresh JSON-compatible dictionaries with explicit status values, candidates,
unknown values (`None`) and source/license metadata. Mutating a returned dictionary does not
change subsequent lookups. Use `Context(model_year=2005, market="US")` as the second argument
to `decode` only when that context is independently known. `dataset` is a read-only property
returning a fresh dictionary. `bundled()` caches parsed data per process.

HSN must contain four digits, including leading zeroes; TSN must contain three ASCII letters
or digits. Normalization only trims ASCII spaces and uppercases ASCII letters. Longer field
2.2 codes are not silently truncated. An absent type remains unknown: the KBA snapshot records
the stock at one reference date, not every type ever assigned. VIN cannot determine HSN/TSN.

Install the [0.1.0 release](https://github.com/openresearch/orvin/releases/tag/v0.1.0) wheel:

```sh
python3 -m pip install https://github.com/openresearch/orvin/releases/download/v0.1.0/orvin-0.1.0-py3-none-any.whl
```

The wheel/sdist are GitHub Release assets; the package is not published on PyPI.
From a checkout, install with `python3 -m pip install ./libs/python` for the development version.
The repository's `vin.sh` and `hsntsn.sh` need no installation. After installation, use
`orvin vin <vin>` / `orvin hsntsn <hsn> <tsn>` or `python3 -m orvin` with the same arguments.
Commands show a readable summary by default. Append `--json` for the complete library result;
the dictionary-based library APIs are unchanged.

Code: Apache-2.0. Bundled KBA data: dl-de/by-2-0. NHTSA data retains its source notice;
Orvin-owned data contributions alone are CC0. Preserve the bundled `_data/LICENSE.md`,
`_data/CODE-NOTICE`, source records and license links when redistributing data.
