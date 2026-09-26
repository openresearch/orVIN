# Source traceability audit

Audit updated 2026-09-26 for the compiled-runtime development version after v0.2.1. The underlying
source review and retrieval dates are preserved individually; the audit does not
change earlier retrieval dates. ASTRA expansion and the normalized-answer projection were reviewed on 2026-09-26.
Contributor requirements are in [AGENTS.md](../AGENTS.md).

## Scope and results

| Data/rules | Coverage | Traceability and check |
| --- | ---: | --- |
| NHTSA WMI projection | 14,169 associations, 11,604 manufacturer entities, 12,998 WMIs | Every source reference resolves; exact reconstruction from the pinned complete ZIP |
| NHTSA native patterns | 1,343,387 exported from 1,678,690 source patterns | Source pattern/schema/element IDs retained; all exported bytes reconstructed; excluded rows accounted for |
| NHTSA associated and derived facts | Model/make, engine-model, year selection, displacement conversion | Original tables/functions retained; evidence identifies derivation kind and parent rule/schema IDs |
| KBA HSN/TSN | 63,260 rows | Source object IDs, complete source snapshot, edition/date, attribution and license; full table reconstruction |
| ASTRA passenger approvals | 122,273 rows, 125,065 full-length templates, 247 WMIs, 154 original make labels | Exact original bytes retained in gzip, complete reconstruction, row IDs and physical source rows, correlated specifications and remarks |
| ASTRA parser/reuse and BYD cross-check | 4 reviewed documents | Exact locators and inspected-byte hashes; documents not redistributed; independent BYD evidence limited to partial prefix/model/approval relationship |
| European priority worklist | 100 model targets, 93 with approval label-query hits | Selection-source metadata, explicit text queries, source projection hashes, counts and 279 approval examples validated offline |
| Separate WA observational corpus | 18,376 masked-prefix groups | Query and compressed-byte hashes, ODbL attribution, retained per-prefix results and report consistency; excluded from production packages |
| Historical seed | 6 WMI API snapshots | Individual endpoint, retrieval date, role, locator and verified SHA-256 added |
| Behavioral comparison sources | 4 public partial-VIN API responses | Original response bytes retained and hashed; fixtures link to the source records |
| Tesla Model Y | 2 factory layouts, 9 attribute rules and 3 production-year codes | One reviewed manual source, scope, edition, table locator and inspection hash |
| Volkswagen Golf | 2 bounded model-year-2005 factory rules | Three source documents; field-specific references and explicit explanation of the combined evidence |
| Research reports | 119 distinct cited URLs | Citation inventory records report/section locations; research leads are not automatically runtime evidence |
| Shared identity catalog | 12,447 make-label bindings, 32,010 model-label bindings | Exact reconstruction from pinned source labels, stable identities, source IDs and row locators; these are label bindings, not VIN coverage counts |
| Owner-contributed Golf 5 fixture | 1 expressly authorized VIN from Austria | Owner permission and attribution recorded; owner-reported model/country separated from the rule-derived model year |
| Contributed BMW X1 and Subaru Legacy fixtures | 2 expressly authorized test VINs | User reports and permission retained; ownership/year not assumed; current decoding gaps recorded |
| Shared runtime bundle | 523 files | Format/capability version, compiler/input hashes and per-file SHA-256; exact bytes checked in each language package |
| Entire shared data tree | 1,064 files | Includes reviewed inputs, policy/schema and compiled output; undeclared new files or missing files fail validation |

There are **21 bundled upstream source records** across the WMI, KBA, OEM, ASTRA and
snapshot/review manifests, plus the three separately recorded user contributions and
the separately licensed WA validation source.
A source record may cover many rows when
each row retains its original identity and the source projection is reproducible.
No missing runtime source reference was left unresolved.

## Gaps corrected

- Added a manifest for all six original WMI snapshots and retained/hash-pinned the
  four source-correlated public descriptor responses used for richer-decoding fixtures.
- Added precise edition/locator/inspection metadata to the OEM sources and linked
  Volkswagen fields to the documents that actually support them.
- Preserved the complete used-source catalog in the raw decoding APIs. All libraries
  expose normalized short results with self-contained credits; long results extend
  those results with field decisions, rule locators, complete evidence and any additional
  source credits. The CLI delegates these projections to the Python library.
- Added mandatory offline provenance validation to `tools/dataset.py`, which already
  runs in Maven and GitHub Actions. Failure tests cover absent/unknown references,
  missing locators, unexplained missing hashes, changed snapshots and unaccounted files.
- Python, Java and .NET package only the 523-file compiled bundle, with source
  metadata and notices. Original archives and fixtures remain in the repository.
  The [redistribution review](research/data-redistribution/README.md) records the
  basis for retaining the reviewed structured originals; transformed data retains
  upstream obligations.

## Explicit limitations

The Volkswagen maintenance manual was read through indexed PDF text. Its direct
download returned HTTP 403, so **no exact-byte hash is available**. The source record
preserves its URL, edition 11.2009, section 3.5.4, printed page 35 / PDF page 39,
third-party hosting status and the reason for the missing hash. It must not be
described as a retained, hash-verified original. The separate 2005 chart is also
hosted on a third-party mirror; its inspected-byte digest is recorded.

OEM manuals and web pages are not redistributed. Inspection hashes identify bytes
seen during review; without retaining those bytes they do not guarantee that a
future download will reproduce them. The package retains the selected factual
associations, exact citations, scope and reuse assessments.

The 119 research citations are an inventory of leads and supporting references.
Their regional report sections preserve the document assessments, applicability
and remaining gaps. Inventory validation checks citation continuity, not the
current availability or accuracy of every linked document. Each newly implemented
rule still requires a reviewed runtime source record.

These checks establish integrity, referential completeness and reproducibility of
the implemented projections. They do not prove that an upstream assertion is true,
that a rule covers every market/year, or that every public document may be copied.
The owner-authorized Golf 5 VIN is retained in `data/identity/fixtures.json` with
the attribution “User-contributed Golf 5 from Austria.” Its 2005 model year is a
rule-derived expectation, not an owner-confirmed fact. These checks run locally
and do not send customer VINs to external services.

ASTRA catalogue presence is not unique VIN identification. The production import
rejects short, malformed and otherwise unreviewed templates and never derives
model year from approval dates. The 100-model audit verifies text-query counts,
not decoding accuracy. WA labels were themselves VIN-decoded; the recorded 100%
known-label agreement must not be presented as independent real-world accuracy.
See [European scope and gaps](european-coverage.md).

## Verified artifacts

Local validation of the compiled-runtime migration passed: 43 Python library tests,
50 Java tests, 44 tooling tests and .NET behavioral checks. Complete parity passed
for 4,866 Java/Python results and 3,244 .NET/Python normalized results, including
source credits and detailed evidence. The 120-query pre-migration comparison has
no regressions in previously resolved primary fields; twenty AT/DE answers change
to include the explicitly requested labeled foreign-market suggestions.

The fresh JAR (34,660,352 bytes) and wheel (about 34.6 MB) contain all 523 runtime
files byte-for-byte. The wheel is built from the sdist and exercised after installation outside the checkout.
The installed NuGet consumer
checks every embedded byte against the same bundle. Repeating runtime generation
and the main JAR build produced identical bytes. Maven `verify` passed with complete
offline source reconstruction. These measurements record local verification, not
hosted CI, a published release or new factual coverage.

## Re-run

From an environment with `tools/requirements.txt` installed:

```sh
python tools/provenance.py
python tools/dataset.py
python -m unittest discover -s tools
PYTHONPATH=libs/python python -m unittest discover -s libs/python/tests
```

The first command performs the quick provenance audit. The second additionally
reconstructs all source projections offline. After intentional research edits,
review the citations and refresh their location inventory with
`python tools/provenance.py --update-research`.

Java validation runs via `cd libs/java && ./mvnw verify`. After fresh Java/Python/.NET
builds, run `tools/check_parity.py` and `tools/check_packages.py` as described in
[rich decoding](rich-decoding.md) and [NHTSA packaging](nhtsa-data.md).

## Automatic-update work, 2026-09-26

Added attributed BMW/Subaru fixtures and a sourced all-family BMW research report.
The report is research only; no BMW/Subaru decoding rules have been promoted.
Structured-source refreshes preserve the manually reviewed rule and fixture boundary;
see [automatic updates](automatic-updates.md). The initial live comparison found no
new NHTSA, KBA or ASTRA source content. The artifact measurements above describe
the subsequent compiled-runtime migration.
