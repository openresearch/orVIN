# NHTSA bulk data

Both libraries use the same normalized WMI dataset and embed the **complete original source ZIP**.
Consumers need neither a database server nor network access. The source is NHTSA's
[September 2026 standalone vPIC database](https://vpic.nhtsa.dot.gov/downloads/vPICList_lite_2026_09.plain.zip),
listed on the [official download page](https://vpic.nhtsa.dot.gov/downloads/).

| Item | Pinned value |
| --- | --- |
| Publication / retrieval | 2026-09-19 / 2026-09-25 |
| Orvin WMI dataset version | `2026.09.25.2` |
| Source ZIP | 76,201,016 bytes |
| SHA-256 | `1ee4a1e22526a606b492ce4ab301894465afbf43dc00946df6d503c3102d5911` |
| Complete source | 97 tables, including 13,001 WMIs and 1,678,690 VIN patterns; 15 SQL functions |
| Runtime lookup | 12,998 WMIs; 11,604 manufacturer entities; 14,169 WMI/brand associations |

The full table/column inventory, row counts, transformations and exclusions are in
[`data/nhtsa/metadata.json`](../data/nhtsa/metadata.json). The source archive is stored beside it.

## What is used now

`tools/nhtsa.py` joins `wmi`, `manufacturer`, `wmi_make`, `make` and `vehicletype` into
`data/dataset.json`. The importer does not execute SQL. Python reads the resulting JSON;
Java reads a deterministic TSV compiled from exactly that JSON. Both build an in-memory index
and return manufacturer identity, possible brands, vehicle category and provenance.

The source has **526 WMIs with multiple makes**. Every association is retained; `1C4`, for example,
has Dodge, Chrysler, Volkswagen, Jeep, Fiat, Ram and Lancia candidates. A shared manufacturer
can remain known even when the brand is ambiguous. The mostly empty legacy `wmi.makeid` field
is not used in place of the authoritative `wmi_make` join.

Source categories cover 348 passenger-car WMIs, 314 truck, 241 multipurpose, 230 incomplete,
164 bus, 1,579 motorcycle, 482 low-speed, 19 off-road and 9,621 usable trailer WMIs.
These counts describe identifiers, not globally complete brand/model coverage.

Label whitespace is normalized and brand names are uppercased consistently with the original
API seeds. Original spelling and source fields remain unchanged in the ZIP. Numeric source IDs
are retained in manufacturer IDs and assignment notes. Six existing manufacturer aliases remain
stable. Database timestamps do not become model-year bounds; WMI geography does not become
manufacturer headquarters or assembly country. The source's two noncompliant flags remain visible
in assignment notes; recognizing an identifier is not a compliance assessment.

## Explicit exclusions

| Source WMI / row | Reason |
| --- | --- |
| `1OY` / 7647 | Contains forbidden VIN letter O |
| `4OG` / 8079 | Contains forbidden VIN letter O |
| `ABT` / 6700 | No public-availability date |

These records are excluded only from the normal runtime projection, not deleted from the
archived source. No letter is silently replaced with a similar digit. Future snapshots also
exclude WMIs whose public-availability date is later than the recorded retrieval date.

## What is archived but not decoded yet

The ZIP preserves every original table and function, including detailed model, engine, fuel,
body, restraint, plant, year, validation and enrichment data. Neither library currently executes
that procedural decoder or returns those detailed fields. Pattern matching, applicability,
precedence, year-cycle handling and enrichment still need native implementations and reviewed
behavioral tests. See the [bulk feasibility assessment](research/vin-rules/nhtsa-bulk.md).

NHTSA's [coverage explanation](https://vpic.nhtsa.dot.gov/api/Home/Index/FAQ) focuses on vehicles
reported for US sale, import or use. A complete download cannot fill missing European rules.
The separate [50-make research](research/vin-rules/README.md) records additional scoped evidence.
KBA HSN/TSN lookup remains separate; no VIN-to-HSN/TSN mapping is inferred.

## Rebuild, update and package

```sh
# Offline regeneration from the bundled source:
python3 tools/nhtsa.py import
.venv/bin/python tools/dataset.py --update-runtime

# Offline integrity and full projection check:
python3 tools/nhtsa.py validate

# Explicit network refresh of the reviewed, pinned edition:
python3 tools/nhtsa.py download

# Or import an already downloaded copy of that exact edition:
python3 tools/nhtsa.py import --archive /path/to/vPICList_lite_2026_09.plain.zip
```

The importer verifies the source hash before writing. Normal builds never refresh data.
To adopt a newer edition, review its publication date, archive hash, schema, exclusions and
reuse terms; update the pin/version in `tools/nhtsa.py`, regenerate, review the diff and run
both libraries' tests. Do not edit the derived WMI JSON directly: full-source validation rejects
drift. New source families require an explicit importer/schema change with provenance.

The Java main JAR embeds `data/` under `META-INF/orvin/`; the Python wheel embeds it under
`orvin/_data/`. The complete compressed archive stays on disk unless explicitly read; ordinary
lookup does not expand it. The verified main JAR is 74,414,998 bytes and the wheel is
73,865,730 bytes; outer archive compression also compresses the embedded source ZIP. Check artifacts:

```sh
python3 tools/check_packages.py --jar libs/java/target/orvin-0.1.0-SNAPSHOT.jar
python3 tools/check_packages.py --wheel libs/python/dist/orvin-0.1.0.dev0-py3-none-any.whl
python3 tools/check_parity.py
```

Checks compare every embedded shared data file byte-for-byte. Cross-language verification loads
Java classes/resources from the main JAR and tests samples across the WMI and KBA catalogs.
The wheel is also installed and exercised outside the checkout in CI.

Preserve [upstream notices](../data/LICENSE.md). NHTSA data, source SQL and manufacturer documents
are not covered by Orvin's CC0 dedication or Apache code license.
