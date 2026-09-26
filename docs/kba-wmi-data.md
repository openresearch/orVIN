# KBA manufacturer/WMI directory

The source checkout imports **SV 3.1, 15 January 2026**, retrieved 26 September
2026, as manufacturer-directory evidence for every market. This addition is not
part of the already published 0.3.0 artifacts.

| Coverage | Count |
| --- | ---: |
| Extracted table rows | 7,759 |
| Rows with valid identifiers, retaining repetitions | 5,261 |
| Distinct valid WMIs | 3,827 |
| Extended six-character WMIs | 1,661 |
| Additional identifiers compared with NHTSA September 2026 | 3,054 |
| Identifiers also present in NHTSA | 773 |
| Identifiers appearing on more than one KBA row | 681 |

The directory supplements NHTSA; it is not a complete world register. It includes
historical entries, reserved assignments, foreign manufacturers and repeated HSN
associations without model-year validity bounds. The comparison retains 714
overlapping identifiers whose full manufacturer labels differ after whitespace/case
comparison. Those are review signals, not proof of different legal companies.
No fuzzy entity merges are made. See the [conflict analysis](research/kba-wmi/comparison.md)
and `data/kba-wmi/comparison.json`.

## Returned information

The common compiler encodes each valid row as a generic matching rule. Ordinary
WMIs match VIN positions 1–3; extended WMIs also require positions 12–14. All three
libraries execute the same compiled rules without PDF software or network access.

| Detailed field | Meaning |
| --- | --- |
| `ManufacturerDirectoryName` | Full manufacturer name as printed |
| `ManufacturerDirectoryLabel` | KBA's abbreviated manufacturer label |
| `ManufacturerDirectoryLocation` | Listed manufacturer location, **not the vehicle's assembly plant** |
| `ManufacturerDirectoryHSN` | HSN associated with that directory row, **not a VIN-to-HSN determination** |

These catalogue facts do not establish retail make, model, model year, production
date, engine or TSN. Primary fields remain governed by the existing sourced
decoding/normalization rules. In particular, `dataset.tsv` and the legacy WMI
manufacturer/marque lookup remain the separate NHTSA projection; KBA's rows are
visible in rich decoding and normalized long output, not silently substituted
into NHTSA legal identities or retail makes.

One explicit source preference covers `1CA`: prefer NHTSA's Cobra Industries make
assignment while preserving KBA PDF page 34 row 78's DaimlerChrysler/Dodge wording.
This preference was reviewed on 2026-09-26 and is recorded in
`kba-wmi/metadata.json` under `identityPreferences`. It compiles to a separate
generic rule; long-output make-decision evidence has kind `SOURCE_PREFERENCE`,
the rule ID, both record locators and the explanation. It does not relabel other
Chrysler records, establish a corporate relationship, infer a vehicle HSN or
choose differently for EU/US callers. See the [comparison report](research/kba-wmi/comparison.md).

Known directory values appear in `details.specifications`. Competing values remain
ambiguous in raw `details.fields`; normalized long output retains every row in
`details.alternatives` and `details.evidence`, even when there is no unique value
to put in specifications. Each fact has its PDF page, top-to-bottom row ordinal,
HSN, WMI and column locator. Source credits appear in long output's
`details.provenance.additionalSources`; short output credits the fields it actually
returns and does not append unrelated directory facts.

For example, with a synthetic VIN:

```sh
./vin.sh WAKAAAAAAAAAAAAAA --market AT --json --long
```

The directory reports **ABT e-Line GmbH**, **Kempten**, HSN **1925** (PDF page 6,
row 12). It does not invent a retail make or model. `W09AAAAAAAAA53001` matches
the extended identifier `W09/A53` for **A+A HAHN GMBH** (page 6, row 1).
`WVWZZZ1KZ5P000001` still resolves to **VW / Golf / 2005** using the reviewed Golf
rules; its four KBA directory rows remain alternatives, including HSNs 0600,
0603, 1166 and 1913. No one of those HSNs is selected as the vehicle's code.

## Source, extraction and rights

The [official PDF](https://www.kba.de/SharedDocs/Downloads/DE/SV/sv31_pdf.pdf?__blob=publicationFile&v=3)
has 151 pages and SHA-256
`d4a7daa14f46571fbcbe1e242567f0c1b79dd49793ea916e57b740c0495440f8`.
`data/kba-wmi/rows.json.gz` is a hash-pinned factual extraction with empty cells
and original labels preserved. All 145 table pages' HSN and WMI columns were
independently compared with pdfplumber; rendered pages 6, 16, 17 and 140 were
reviewed for ordinary/extended identifiers, the invalid identifier and repeated
or missing manufacturer values. Regression fixtures record independent examples.
Page 34 was also reviewed to confirm the apparent `1CA` assignment disagreement.

The source includes **2,497 rows without a WMI**, retained in the authoring
snapshot but not compiled into VIN rules. **One row has `WBI`**, which contains
the forbidden VIN letter `I` (PDF page 16, row 13). It is retained as an explicit
exclusion, not corrected to another identifier. No name or location is copied
into a missing cell from an adjacent row.

Keep the [KBA notices](../data/LICENSE.md#kba-sv-31-manufacturerwmi-directory),
PDF page 151 copyright link and modification statement. The source-specific
identifier is `LicenseRef-KBA-SV31-Attribution`. The assessment is in the packaged
`kba-wmi/metadata.json` and [research note](research/kba-wmi/README.md).
The original PDF and authoring snapshot are not included in library packages;
the generated rules, assessment and notices are included.

## Reproduce and validate

Normal builds validate the pinned row snapshot and regenerate the runtime offline:

```sh
.venv/bin/python tools/kba_wmi.py validate
.venv/bin/python tools/dataset.py
```

To re-extract the reviewed PDF, install the optional development dependency and
supply the original file. Its digest must match before parsing; the extraction
must reproduce the reviewed row snapshot byte-for-byte:

```sh
.venv/bin/python -m pip install -r tools/requirements-pdf.txt
.venv/bin/python tools/kba_wmi.py extract --pdf /path/to/sv31_pdf.pdf
```

To regenerate after an intentional, reviewed change:

```sh
.venv/bin/python tools/kba_wmi.py compare
.venv/bin/python tools/decoding.py import
.venv/bin/python tools/identity.py --generate
.venv/bin/python tools/dataset.py --update-runtime
```

New PDF editions require manual review of source scope, layout, rights, pins,
row inventory, exclusions and fixtures. The daily updater does not download or
replace this PDF source. It only refreshes the diagnostic comparison when the
separately reviewed NHTSA snapshot changes. Preferences also require manual review:
their guards reject changed KBA rows, changed NHTSA identity/scope/locators or
new competing assignments, instead of silently carrying an override forward.
