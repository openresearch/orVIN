# Dataset rights and upstream notices

The Apache code license does not license the embedded data.

## Swiss ASTRA type-approval factual data

`astra/` contains **Swiss Federal Roads Office (ASTRA), Basisdaten TG ab 1995,
TG-Automobil**, snapshot last modified 2026-07-30, retrieved 2026-09-26.
[Original data](https://opendata.astra.admin.ch/ivzod/2000-Typengenehmigungen_TG_TARGA/2200-Basisdaten_TG_ab_1995/TG-Automobil.txt).
ASTRA [explicitly publishes these factual data as Open Government Data](https://www.astra.admin.ch/de/news-homologation).
[Swiss EMBAG, Article 10(4)](https://www.fedlex.admin.ch/eli/cc/2023/682/de)
permits unrestricted OGD reuse subject to statutory attribution requirements.
This is a statutory OGD reuse basis, not a Creative Commons license or a claim
that all documents on the ASTRA website have the same terms. Preserve ASTRA
attribution, source URI and this notice. No endorsement is implied.

The retained gzip archive decompresses to the exact original bytes. Modifications
in the separate projection: M1/M1G selection, conservative template filtering,
selected original columns, base64/UTF-8 encoding and WMI partitioning. Remarks
remain associated with each approval. ASTRA requires careful, professional use
and provides data without warranty. These are possible approved types, not proof
of a vehicle's make/model, configuration, market, model year or build date.
See `astra/metadata.json` and the repository's `docs/research/astra-review.md` for
the source locators, original-byte hashes and reviewed scope.

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

## Scoped OEM factual associations

`europe/tesla-model-y.json` records selected factual associations from Tesla's
2025+ Model Y service manual. `europe/vw-golf-1k-2005.json` records a bounded synthesis
of Volkswagen's maintenance manual, 2005 year/plant chart and historical Golf V
profile. Each records exact URLs, editions, locators, review dates, hosting status
and inspected-byte hashes where available. No OEM manual/PDF or illustrations
are redistributed, and no open license for those documents is asserted.
Upstream rights are retained. These selected facts are independently structured
for interoperability; the files record that reuse assessment and its scope.

The native NHTSA projection in `decoding/` also preserves source pattern/schema
IDs and derivation kinds. Its matching semantics were implemented from the pinned
standalone source; NHTSA's published-information reuse statement and the limitations
above apply. `decoding/sources.json` and the runtime source catalog retain attribution.
The complete archive, projected files and historical/reference API snapshots are
checked by the offline provenance and source-reconstruction validators.

## Normalization and contributed regression fixture

The identity catalogue is a derived exact-label projection of the NHTSA, ASTRA and
selected OEM/KBA facts above. Each binding records its source and locator; display
names are ORvin policy. These transformations do not replace upstream reuse terms.

`identity/fixtures.json` contains a **User-contributed Golf 5 from Austria**, whose
owner explicitly permitted the VIN in repository tests on 2026-09-26. The fixture
records that permission and distinguishes owner-reported facts from rule-derived
expectations. No separate standardized license from the owner is asserted.
