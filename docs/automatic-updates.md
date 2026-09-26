# Automatic structured-data releases

The library's GitHub Actions workflow `Refresh structured datasets` checks the three
existing structured sources daily at 00:17 UTC. GitLab checks for a stable library
release daily at 04:30 Europe/Vienna, tests an exact wheel/checksum upgrade, and builds
the API. Flux then deploys that image through the existing Harbor pull proxy.

## Source update boundary

Only NHTSA's PostgreSQL bulk archive, KBA's Kfz table, and ASTRA's TG-Automobil file
are refreshed. Downloads are explicit; normal builds remain deterministic and offline.
PDFs, forums, OEM documents, parser grammar, custom rules, contributed fixtures and
normalization policy are never rewritten automatically.

`tools/source-pins.json` records the currently selected NHTSA edition/hash and derived
dataset versions. Other source snapshots retain their existing metadata files. The
updater records source URLs, hashes, retrieval dates, publication/reference dates and
versioned byte snapshots, and regenerates the existing projections. Older NHTSA/ASTRA
bytes remain bundled when reviewed fixtures still cite them. Historical source notices
remain available in the provenance catalogue.

Changes must remain within the reviewed source contract:

- NHTSA archive layout, COPY table/column schemas and SQL function definitions must
  remain unchanged. SQL is inspected as data and is never executed.
- KBA must retain the reviewed fields/types and source notices; downloads verify the
  complete object-ID inventory and counts, and source editing metadata must remain
  stable throughout retrieval. Annual reference dates and in-place corrections are checked.
- ASTRA must retain the exact column header and the reviewed conservative template
  grammar. Invalid/ambiguous templates remain excluded.
- Empty data, more than 5% row loss, or more than 50% growth in checked counts stops
  the run. An increase of more than one percentage point in NHTSA decoding or ASTRA
  passenger-template exclusion rates also stops the run. These are conservative operational review thresholds, not statistical
  guarantees or a license to ignore smaller regressions.

Reuse assessments and legal-document interpretations remain manually reviewed. The
updater preserves their attribution and does not claim that schema/tests can detect
every upstream semantic or legal change. New source families or new reuse terms need
a separate review; it never assigns new rights automatically.

## Validation and publication

Source bytes are compared before changing the checkout. Identical content produces
no commit, tag, or release. For changed content, offline reconstruction/provenance,
both libraries, tooling tests, installed-wheel behavior, cross-language parity and
embedded-package equality must all pass before committing.

Publication checks a strict file allowlist, confirms main has not moved, and atomically
pushes the generated-data commit plus the next stable patch tag. A reused release
workflow validates the exact new commit on the supported language versions and publishes
both packages. Explicit workflow reuse is necessary because workflow-token tag pushes
do not trigger another GitHub workflow. Failed publication is visible in Actions;
retry the failed release jobs without creating a replacement version/tag.

The refresh report is uploaded as a workflow artifact; a published refresh also retains
it in `docs/data-refresh/latest.json`. The 100-model worklist keeps its manually chosen
models and queries; only the resulting ASTRA counts/examples are regenerated.

The contributed BMW X1 and Subaru Legacy are independent user-reported test evidence.
Current decoding gaps are recorded beside them. Unknown results are not treated as
proof of complete coverage; any future resolved identity must agree with the report.
KBA population counts and catalogue row IDs are snapshot facts, not permanent vehicle
identity fixtures. Their exact mapping is checked by full source reconstruction and
cross-language comparison; the independent HSN/TSN identity expectations remain fixed.

## Operations

Read-only online discovery/comparison:

```sh
.venv/bin/python tools/refresh_data.py
```

To regenerate, use `--apply` in a **clean disposable checkout**. A failed check can
leave uncommitted candidate files in that checkout; it cannot publish them. The daily
workflow performs the complete test/build checks before invoking `publish_refresh.py`.
Do not run the publisher manually on an unvalidated candidate.

Use the workflow's manual Run workflow action with `publish=false` for validation
without a release. `publish=true` permits publication only for changed source content.
Disable the schedule/workflow to stop automatic library releases; the GitLab API
schedule and Flux image automation are separately controlled. For rollback, pause
the API update schedule and Flux automation, then select a prior immutable image.

Existing source-assessment documents retain their original dated snapshot counts.
Current release counts and hashes are authoritative in the embedded source metadata
and refresh report, rather than in those historical research summaries.

References: [NHTSA downloads](https://vpic.nhtsa.dot.gov/downloads/),
[KBA source](https://services-eu1.arcgis.com/U09msXRZoxesNntH/arcgis/rest/services/SP_HSN_TSN_92a1e/FeatureServer/0),
[ASTRA directory](https://opendata.astra.admin.ch/ivzod/2000-Typengenehmigungen_TG_TARGA/2200-Basisdaten_TG_ab_1995/),
[GitHub workflow-token behavior](https://docs.github.com/en/actions/how-tos/writing-workflows/choosing-when-your-workflow-runs/triggering-a-workflow#triggering-a-workflow-from-a-workflow),
[GitLab job-token pushes](https://docs.gitlab.com/ci/jobs/ci_job_token/#allow-git-push-requests-to-your-project-repository).
