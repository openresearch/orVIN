# KBA and NHTSA WMI comparison

Reviewed 2026-09-26 against the retained editions below. There are real-looking
assignment disagreements as well as many differences in names and scope. We
must not treat every differing label as a conflict, or silently merge the two
catalogues into one authoritative manufacturer/make/HSN answer.

## Reproducible scope

- KBA [SV 3.1, 15 January 2026](https://www.kba.de/SharedDocs/Downloads/DE/SV/sv31_pdf.pdf?__blob=publicationFile&v=3),
  source `kba-sv31-2026-01-15`, PDF SHA-256
  `d4a7daa14f46571fbcbe1e242567f0c1b79dd49793ea916e57b740c0495440f8`.
  The pinned factual extraction is `data/kba-wmi/rows.json.gz`; no original PDF is bundled.
- NHTSA [vPIC standalone database, September 2026](https://vpic.nhtsa.dot.gov/downloads/vPICList_lite_2026_09.plain.zip),
  source `nhtsa-vpic-2026-09`, original ZIP SHA-256
  `1ee4a1e22526a606b492ce4ab301894465afbf43dc00946df6d503c3102d5911`.
  The reconstructed WMI projection is `data/dataset.json`, version `2026.09.25.2`.

The complete machine-readable comparison is
[`data/kba-wmi/comparison.json`](../../../data/kba-wmi/comparison.json), regenerated
with `python tools/kba_wmi.py compare` and validated offline by the provenance audit.
Identifiers are compared at their full three- or six-character length. Manufacturer
name sets are compared after case/whitespace normalization only; no corporate
entity matching, abbreviation expansion or fuzzy name merging is attempted.

| Measurement | Count |
| --- | ---: |
| Distinct valid KBA WMIs | 3,827 |
| Also found in NHTSA | 773 |
| Additional to NHTSA | 3,054 |
| Overlap with identical normalized full-name sets | 59 |
| Overlap with differing full-name sets | 714 |
| KBA identifiers with more than one HSN | 671 |
| KBA identifiers with more than one nonempty full manufacturer name | 671 |

**714 is a review queue, not a count of proven incorrect assignments.** The two
sets of 671 identifiers are independent counts; they do not imply the same rows
or causes. This review examines representative discrepancies below, not a manual
adjudication of all 714 identifiers.

## Reviewed examples

Names in this table are shortened for readability. The linked snapshot retains
the original wording and each KBA row's stable ID, such as `sv31-p034-r078`.
All page numbers refer to PDF pages; rows count top to bottom within the table.

| WMI | KBA statement and locator | NHTSA statement and locator | Assessment |
| --- | --- | --- | --- |
| `WBA` | Bayerische Motorenwerke AG (Personenwagen); page 17, row 25 | BMW AG; WMI row 2012, make 452 (BMW) | Abbreviation and vehicle-class qualifier; no evidence here of a brand conflict. |
| `WP0` | Dr. Ing. h.c. F. Porsche AG (Personenwagen); page 109, row 16 | Dr. Ing. h.c. F. Porsche AG; WMI row 5486, make 584 (PORSCHE) | Formatting and class qualifier. |
| `W0V` | Opel Automobile GmbH; page 105, row 11 | General Motors LLC; WMI row 8984, make 471 (OPEL) | Different legal-manufacturer labels, but NHTSA still supplies the Opel retail make. Group/entity history is a possible explanation, not established by this comparison. |
| `WVW` | Volkswagen AG, Volkswagen do Brasil and Volkswagen of America; page 140, rows 4, 21, 34, 62; HSNs 0600, 0603, 1166, 1913 | Volkswagen AG; WMI row 2360, make 482 (VOLKSWAGEN) | Multiple directory associations versus one NHTSA entity. WMI alone cannot choose a vehicle HSN or legal company from these rows. |
| `JTD` | Toyota entities plus Fuji Heavy Industries/Subaru; page 51 row 42, page 128 row 47, page 134 rows 23, 42, 63 | Toyota Motor Corporation; WMI row 2258, make 448 (TOYOTA) | Cross-brand directory associations. They do not justify changing the VIN's retail make to Subaru. The retained rows do not resolve why each association exists. |
| `1CA` | DaimlerChrysler Corp (Dodge/Bus), HSN 1004; **page 34, row 78** | **Cobra Industries, Incorporated**, trailer; **WMI row 4873**, make 4657 (COBRA INDUSTRIES) | Apparent manufacturer-assignment disagreement, not just punctuation or an abbreviation. The KBA value was checked against the rendered original page, so this is not an observed extraction error. |

Neither retained source establishes the time interval needed to reconcile `1CA`.
Possible explanations include historical reassignment or a source error; this
comparison cannot determine which, or which assignment fits an actual vehicle.
There is no independently identified real vehicle fixture resolving this case.

Follow-up research on 2026-09-26 found a historical manufacturing connection:
[Chrysler Corp. v. Schuenemann, 618 S.W.2d 799 (30 April 1981)](https://openjurist.org/618/sw2d/799/chrysler-corp-v-schuenemann),
paragraphs 2–3 and 6, describes Cobra constructing a 1977 motorhome body on a Dodge
chassis purchased from Chrysler. This is the court opinion reproduced by the
third-party OpenJurist mirror, inspected as extracted web text without a byte hash.
It establishes a chassis/body-builder relationship in that case, not Chrysler
ownership of Cobra, corporate continuity or an assignment of `1CA`. It does not
resolve this WMI discrepancy and is not promoted to a runtime rule.

A local check with synthetic `1CAAAAAAAAAAAAAAA` returned primary make
`Cobra Industries` for AT, DE and US alike, with KBA's DaimlerChrysler name in
the separate directory field. There is no EU-versus-US switch for this conflict.

The manually reviewed preference `kba-sv31-1ca-prefer-nhtsa` now makes that choice
explicit. It is stored in `data/kba-wmi/metadata.json` under `identityPreferences`
and compiled into a separate `Make` rule, with evidence kind `SOURCE_PREFERENCE`.
Its make-decision evidence cites the selected NHTSA assignment, the conflicting
KBA source and PDF row, review date and rationale. The long result also includes
the warning that this preference does not prove KBA wrong or establish corporate
ownership. The original directory fields remain unmodified in their own alternative;
KBA HSN 1004 is not attached to the preferred Cobra make as a vehicle configuration.

The compiler checks the exact KBA row and the preferred NHTSA assignment's name,
make, identifier, category, constraints and locator. Changed or competing records
stop the build for review. An unchanged assignment may move to a new NHTSA source
edition; its runtime evidence cites that edition while metadata retains the
original review reference. This does not add a global DaimlerChrysler/Cobra alias
or adjudicate other directory discrepancies automatically.

## Consequences for orVIN

- Keep KBA's name, label, location and HSN as explicitly named
  `ManufacturerDirectory*` fields with their own source and row lineage.
- Keep NHTSA legal-manufacturer/marque records separate. KBA directory evidence
  does not automatically adjudicate or override a conflicting NHTSA assignment.
  Explicit reviewed preferences, such as `1CA`, identify the chosen source and
  scope. A primary result must not be presented as agreement between the datasets.
- Preserve correlated alternatives. For the Golf's `WVW`, four HSN associations
  remain available in long output; none is selected as the actual vehicle HSN.
- Preserve unknown dates and locations. A manufacturer's address is not a factory,
  and this edition's publication date is not an assignment-validity start date.
- Before using KBA labels as primary manufacturer/make mappings, separately review
  the exceptional identifiers, historical scope and mapping from legal entity to
  retail make. Do not automatically promote these 3,054 additional directory
  identifiers into 3,054 newly resolved vehicle makes.

One printed identifier, `WBI` (page 16, row 13), contains forbidden VIN letter `I`.
It is retained as an explicit exclusion rather than corrected by guesswork. A
further 2,497 rows have no WMI. Neither group produces a VIN-matching rule.

The comparison refreshes when NHTSA's reviewed structured snapshot changes. The
underlying KBA PDF and its extracted rules remain a manually reviewed source;
see [the import guide](../../kba-wmi-data.md) and
[automatic maintenance](../../automatic-updates.md).
