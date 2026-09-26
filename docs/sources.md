# Initial source assessment — 2026-09-25

## Selected: NHTSA vPIC bulk database

The current dataset is generated from the complete official September 2026
[standalone database](https://vpic.nhtsa.dot.gov/downloads/vPICList_lite_2026_09.plain.zip),
published 2026-09-19. Both library distributions retain that ZIP unchanged, including all
97 tables and the stored functions. The importer extracts all public usable WMI/manufacturer/
make/type associations: 12,998 WMIs, 11,604 manufacturer entities and 14,169 associations.
See [import, exclusions and field coverage](nhtsa-data.md).

The archive retains NHTSA's published-information reuse statement and source attribution;
it is not relabeled CC0 or Apache-2.0. The native libraries now execute a bounded projection of the public patterns,
model/make and engine associations, displacement conversion and scoped model-year rules.
See [rich decoding](rich-decoding.md) for stages and limits. The [50-make research](research/vin-rules/README.md) identifies
potential scoped additions and European gaps.

## Historical seed: NHTSA vPIC API

The [API documentation](https://vpic.nhtsa.dot.gov/api/) describes DecodeWMI and its six-character
form (VIN positions 1–3 plus 12–14). [About vPIC](https://vpic.nhtsa.dot.gov/About) describes data
derived from manufacturer submissions. Its [FAQ](https://vpic.nhtsa.dot.gov/api/Home/Index/FAQ)
explains that foreign vehicle coverage depends on manufacturers reporting vehicles intended for
US use, import or sale. Thus this is a source of specific assignments, not proof of global coverage.

Original seed scope: factual manufacturer name, make and vehicle type for six exact WMI queries.
The original JSON snapshots remain in `data/snapshots/`, retrieved 2026-09-25, with per-file URLs and hashes in `data/snapshots/metadata.json`. They supported `Results[0]` and
the fields used. The dataset preserves NHTSA's manufacturer identity separately from make/brand.
It makes no assertions about manufacturer headquarters or assembly location.

The [NHTSA Terms of Use](https://www.nhtsa.gov/about-nhtsa/terms-use) permits copying and distributing
published information. Our assessment is that this supports redistribution of these API records;
we retain that source-specific notice rather than assign an invented permissive license to them.
This assessment does not establish rights in arbitrary manufacturer submissions.

`CreatedOn`, `UpdatedOn` and `DateAvailableToPublic` describe source database records. They are
not model-year bounds or historical assignment dates. The current records do not establish
market exclusivity or all-time validity, so those constraints are absent and the limitation is explicit.

During research, the API documentation's `1T9131` example returned no records. It was not imported.
The real extended seed `1H9333` was found through `GetWMIsForManufacturer/trailer` and then
verified through its exact DecodeWMI endpoint. Documentation examples are not accepted as facts.

## KBA: HSN/TSN data available; manufacturer directories still deferred

Follow-up research established reusable official **FZ 6** and **FZ Hersteller Handelsnamen Kfz**
datasets for HSN/TSN, manufacturer labels, trade names and stock counts under dl-de/by-2-0.
The 2026 workbook and KBA's published machine-readable table were inspected. See
[the KBA assessment](kba-data.md) for exact sources, fields, licensing and VIN integration limits.
The Kfz table's 63,260 entries for 2026-01-01 are bundled in both the Python and Java libraries,
with exact source attributes, object-ID completeness checks and dl-de/by-2-0 attribution.

The [KBA WMI portal](https://www.kba-online.de/wmi_prod/webapp-nezo/) identifies KBA as the German
assignment authority, describes extended identifiers and refers to the annual manufacturer
directory. An authoritative current copy of that directory and its edition-specific reuse notice
were not established in this pass. Third-party mirrors were not imported or treated as permission.

Before adding KBA WMI-directory data, obtain the official edition, publication date, relevant rows/pages, exact
reuse conditions and a review of how the entries distinguish manufacturer identities, HSNs and WMIs.

## Deferred: manufacturer VIN guides

Ford's [2022 VIN guide](https://content.fordpro.com/content/dam/fordpro/us/en-us/pdf/fleet-vehicles/vin-lookup-and-guides/2022-vin-guide.pdf)
illustrates model-year-specific mappings and the distinction between WMI, vehicle characteristics
and assembly plant. It is a research reference only. No guide content, rules or PDF are embedded:
redistribution permission for this particular document has not been established. A public download
alone is not a data license. Apply the same edition-by-edition review to other manufacturers.

## Review boundaries

Machine checks verify schema, referential integrity, snapshot digests, identifier shape,
overlapping assignments and tested behavior. They do not establish truth, authority, source
completeness, ownership or sufficient reuse rights. Those are human review responsibilities.

One owner-authorized Golf 5 VIN from Austria is retained in `data/identity/fixtures.json`,
with attribution, explicit permission and separate owner-reported versus rule-derived facts.
It is never sent to external services. No owner address or private document is included. Other full-length
test identifiers are synthetic; the WMI facts are public. Synthetic identifiers need not have
a valid checksum and should never be described as actual vehicles.
