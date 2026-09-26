# Dataset redistribution review

Reviewed 2026-09-26 against tracked files at `bec8d73` and the official sources
below. This is a scoped source-terms assessment, not blanket legal clearance for
future imports. Outcome: retain the reviewed structured snapshots in the repository.
Compilation and packaging do not remove source-specific obligations.

## Structured production inputs

| Input retained in Git | Published basis and locator | Decision |
| --- | --- | --- |
| NHTSA standalone ZIP, historical API records and derived indices | [NHTSA Terms of Use](https://www.nhtsa.gov/about-nhtsa/terms-use), Ownership; [vPIC About](https://vpic.nhtsa.dot.gov/About), public reuse and Downloads | The publisher permits copying/distribution of published information and supplies a standalone database for local use. Retain the reviewed archive and notices; do not relicense its SQL or imported records as ORvin-owned Apache/CC0 work. |
| KBA attribute snapshot and HSN/TSN projection | [Exact Kfz catalogue record](https://data.gov.de/suche/daten/fz-hersteller-handelsnamen-kfz?ids=c1e3a0b6-0d34-4e99-8181-91bdfb639208), resource license; [dl-de/by-2-0](https://www.govdata.de/dl-de/by-2-0), clauses 1–3 | Copying, transformation, combination, commercial use and redistribution are permitted with provider credit, dataset URI, license link and modification notice. Keep them in source metadata, packages and applicable results. |
| ASTRA TG-Automobil snapshot and candidate projection | [ASTRA publication notice](https://www.astra.admin.ch/de/news-homologation), type-approval factual data; [TARGA documentation](https://www.astra.admin.ch/dam/de/sd-web/7fPLSFMqD6JR/informationsprodukte_typengenehmigungsdaten.pdf), version 1.0, section 1.3, page 3; [EMBAG Art. 10](https://www.fedlex.admin.ch/eli/cc/2023/682/de), paragraph 4 | ASTRA explicitly identifies this collection as OGD; the federal provision permits unrestricted reuse, subject to special statutory source-credit duties. This supports retention and transformed redistribution of these factual records. Preserve ASTRA credit and notices; do not invent a CC license. |

The official [EMBAG consolidated PDF, 2025-05-01](https://www.fedlex.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/2023/682/20250501/de/pdf-a/fedlex-data-admin-ch-eli-cc-2023-682-20250501-de-pdf-a.pdf)
was downloaded again and Art.10(2)/(4), pages 4–5, inspected. Its SHA-256 remains
`996b8d697fdfd9278e453b7fff832601a7739bcd914ba9a7c16e0d0d903b0149`.
The law and documentation are research references, not newly bundled source assets.
HTML terms were reviewed through the web tool; no exact-byte hashes are asserted.
See [the earlier ASTRA assessment](../astra-review.md) for dataset scope and limitations.

## Separately licensed validation data

Washington Department of Licensing's [dataset metadata](https://data.wa.gov/api/views/f6w7-q2d2.json)
was rechecked: `licenseId=ODBL`. [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/)
sections 3.1 and 4.2–4.6 permit redistribution and derivatives subject to notices,
applicable share-alike and derivative-database availability requirements. The grouped
snapshot and prefix-result database already have their own ODbL notice and are
available in machine-readable form under `validation/wa-ev/`. Keep them separate
from production rules and packages. See [their license](../../../validation/wa-ev/LICENSE.md).

## OEM rules and package boundary

The tracked data inventory contains no OEM PDF/manual collection. Existing Tesla
and Volkswagen rules contain selected factual associations and source-specific
assessments, not an open license to reproduce their documents. This structured-data
review does not broaden those assessments to complete tables, manuals or forum posts.
Any new extraction still requires the source and rights review in `AGENTS.md`.

Inspection of the current built JAR and wheel confirmed that both include the raw
NHTSA ZIP, KBA JSON snapshot and ASTRA text snapshot, as well as generated data.
The accepted migration changes that packaging boundary: originals stay in Git;
published packages contain generated runtime data, provenance and required notices.

Generated mappings are transformed work, but changing their representation does
not automatically remove upstream database, contractual or attribution obligations.
Fetching restricted data during a build would likewise not authorize shipping a
restricted source or derived database. No such download workaround is needed for
the three reviewed structured inputs above.
