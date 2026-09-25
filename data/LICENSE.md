# Dataset rights and upstream notices

The Apache code license does not license the embedded data.

## Orvin's original work

Orvin contributors dedicate their original dataset selection, arrangement, annotations and
synthetic fixtures under [CC0-1.0](CC0-1.0.txt), **only to the extent they own the relevant rights**.
This does not relicense imported content, trademarks, manufacturer documents or third-party rights.
The schema and validation software are covered by the repository's Apache-2.0 code license.

## NHTSA bulk database and historical API snapshots

The runtime WMI mappings derive from the complete September 2026 NHTSA vPIC standalone database,
published 2026-09-19 and retrieved 2026-09-25. Its original ZIP, including source SQL and all tables,
is retained unchanged under `nhtsa/`. The six historical JSON snapshots are from vPIC DecodeWMI.
Their source-specific identifier is `LicenseRef-NHTSA-Public-Information`, a local descriptive
reference, **not an SPDX-listed license or a claim that NHTSA chose CC0**.

The [NHTSA Terms of Use, Ownership section](https://www.nhtsa.gov/about-nhtsa/terms-use) states that
published information may be distributed or copied. The [vPIC About page](https://vpic.nhtsa.dot.gov/About)
describes the public reuse of its data. Orvin relies on those statements for the factual API
records and published standalone database retained here. This is not a separate license grant
over third-party material or an Apache license for the archived SQL. NHTSA also disclaims accuracy
and completeness. Sources were reviewed on
2026-09-25; each mapping records the precise URL, retrieval date, section and reuse basis.
Modifications to the runtime projection: join WMI/make associations, normalize label whitespace,
uppercase brand labels, preserve ambiguity, and record three exclusions. The full source archive
is unmodified. See `nhtsa/metadata.json` and `docs/nhtsa-data.md` in the repository.

This is deliberately narrower than treating everything linked from a government website as public
domain. No underlying manufacturer PDFs, illustrations or manuals have been copied into Orvin.
The [NHTSA linking policy](https://www.nhtsa.gov/privacy-policy/linking-policy) does not authorize
reuse of externally linked copyrighted materials.

Preserve this notice and the individual source records when redistributing the dataset. If a
future source imposes different terms, document and assess them before importing it; never
silently extend the CC0 dedication to material a contributor does not own.

## KBA manufacturer and trade-name data

`kba/types.tsv`, the lossless attribute snapshot `kba/source.json.gz`, and factual KBA fixtures
derive from **Kraftfahrt-Bundesamt (KBA), FZ Hersteller Handelsnamen Kfz**:
[dataset](https://data.gov.de/suche/daten/fz-hersteller-handelsnamen-kfz?ids=c1e3a0b6-0d34-4e99-8181-91bdfb639208),
[source table](https://services-eu1.arcgis.com/U09msXRZoxesNntH/arcgis/rest/services/SP_HSN_TSN_92a1e/FeatureServer/0).
Reference date: 2026-01-01. Retrieved: 2026-09-25.

License: **Datenlizenz Deutschland – Namensnennung – Version 2.0 (dl-de/by-2-0)**,
[license text](https://www.govdata.de/dl-de/by-2-0). Preserve provider attribution, dataset URI
and license link with redistributed data, and identify modifications. These imported data are
not covered by Orvin's CC0 dedication.

Modifications: selected one reference date, renamed columns, sorted rows, represented nulls as
`\N`, and packaged the data for lookup. Source labels, counts and statistical markers are unchanged.
The JSON gzip snapshot retains the source attributes and complete object-ID set, with normalized
JSON serialization; it is not a byte-for-byte archive of HTTP response envelopes.
