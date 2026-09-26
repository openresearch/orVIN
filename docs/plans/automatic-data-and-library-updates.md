# Automatic data updates, API releases and additional VIN coverage

Status: steps 1, 2, 3 and 5 delivered and verified, 2026-09-26. Step 4 research is complete; decoding implementation remains deferred for review after this checkpoint.

## Requested outcome

1. Automatically detect and adopt changes to the existing NHTSA, KBA and Swiss ASTRA
   structured datasets, then release both libraries when validation succeeds.
2. Keep PDF- and forum-derived rules under manual research and review. They are never
   automatically rewritten or expanded by the dataset updater.
3. Detect new stable ORvin library releases from a GitLab schedule, update the API's
   pinned library, test it, publish a new container and deploy through existing Flux automation.
4. Add the two newly contributed vehicles as attributed regression fixtures, then
   research better European BMW model-family and year coverage.

## Baseline at the planning checkpoint

- ORvin source, library releases and Maven packages currently live in
  https://github.com/openresearch/orvin. Python release wheels include SHA256SUMS.
  The latest published release inspected for this plan is v0.2.0.
- The API lives in https://gitlab.openresearch.com/dispoxyz/code/orvin-api. GitLab
  already tests main and builds AMD64/ARM64 images, pushing to its own registry.
- Flux is already configured in `flux-internal/tourfold/orvin`: Harbor proxies image
  pulls, image scanning runs every minute, and image-update automation runs every
  five minutes. The highest successful main image tag by pipeline IID is selected.
- No library-update pipeline schedule exists yet. The API currently pins v0.2.0
  and its SHA-256 explicitly in requirements.txt.
- Existing library importers are deliberately pinned/offline by default. NHTSA has
  explicit download/import commands; KBA can import an explicit reference date;
  ASTRA compiles an already retained source snapshot. Automated discovery and
  version-independent refresh orchestration still need implementation.
- Before this planning checkpoint, only the local API branch
  `codex/automatic-library-updates` was created. No updater code, schedule, access
  settings, fixture changes or new releases have been introduced for this work.

Use each repository's existing CI host: GitHub Actions for library refresh/release,
GitLab schedules for API upgrades, and the existing Flux configuration for deployment.

## 1. Add contributed fixtures and establish a baseline

Files: ORvin `data/identity/fixtures.json`, relevant Python/Java tests, provenance
validation and documentation where needed.

- BMW VIN ending `VR72507`: user reports BMW, Austrian context, and the registration
  trade designation **X1 xDrive18d E84 N47**. Record model family X1, variant,
  generation and engine-family statements separately from decoder-derived facts.
- Subaru VIN ending `G068909`: preserve the exact user report **Legacy Kombi C22**.
  The meaning of C22, country and year are not independently established by that
  statement; do not silently reinterpret them.
- Preserve the complete VINs in the expressly requested test fixtures, with
  attribution to the user, contribution date, permission to use them in tests,
  and an explanation that the source is this conversation rather than a public URL.
  Do not assume the user owns either vehicle.
- Run both examples through the existing offline decoder and record current
  behavior and gaps. Keep reported truth separate from current decoder assertions;
  do not encode an incorrect current answer as the expected vehicle identity.
- Neither contribution supplies a confirmed model year or production date. Keep
  those ground-truth labels absent until independently supported.
- Keep these VINs local to repository tests; use synthetic identifiers or generic
  model/type-code queries for internet research and API demonstrations.

Acceptance: provenance checks accept both contributions, tests retain independent
reported facts, and Java/Python results agree without inventing missing information.

## 2. Research and improve BMW model-family decoding

- Review current NHTSA and ASTRA matches first, then find documented European BMW
  type-code/VDS mappings. Cover all BMW model families, including numbered Series, X, Z, i and M models,
  with explicit generation/market/year coverage and gaps.
- Prefer OEM/service/type-approval material. Existing BMW US MY2026 research is
  not evidence that the same mappings apply to older European vehicles.
- Distinguish model family, generation, body, variant and engine. For the contributed
  example the intended normalized family is X1; the long answer may carry supported
  E84/xDrive18d/N47 details without turning every catalogue alternative into a fact.
- Investigate model-year encoding separately from production-year/date lookup.
  Do not apply the US tenth-character year convention to every European BMW VIN.
  A type's production interval is not an individual vehicle's model year.
- Check historical Subaru Legacy BG-series material relevant to the new fixture
  while preserving the original C22 report; add only independently supported rules.
- Every implemented rule needs exact source URL, edition, locator, retrieval date,
  inspected-byte digest where available, reuse basis and applicability limits.
  Forum pages are research leads requiring manual assessment, not automatic rules.
- Add positive and near-miss examples for new mappings, with separate provenance
  for user reports and published encoding rules. Preserve ambiguity and unknowns.

Acceptance: publish an evidence-backed coverage assessment; implement only mappings
that pass source/reuse review and independent behavioral checks in both libraries.

## 3. Automate the three structured upstream datasets

Proposed schedule: one daily library check. No changed source content means no
dataset commit, version increment or release.

| Source | Discovery/change detection | Required import controls |
| --- | --- | --- |
| NHTSA vPIC | Inspect the official download listing and release notes for the PostgreSQL archive; compare the downloaded archive SHA-256. | Verify edition, schema and required tables/columns; retain archive, source IDs, publication/retrieval dates and hashes; rebuild WMI and rich-decoding projections. |
| KBA Kfz | Query available reference dates and service metadata; detect additions and corrections by hashing a complete normalized snapshot. | Retain one coherent reference date; check schema, counts and exact object-ID completeness before/after download; preserve markers, leading zeroes, attribution and license metadata. |
| Swiss ASTRA | Check the existing official TG-Automobil file, using HTTP modification metadata as a hint and content SHA-256 as the definitive check. | Preserve original bytes and compressed snapshot; validate columns, passenger scope, VIN-template grammar, approval IDs, exclusions and regenerated shards. |

- Separate release discovery/download from deterministic offline compilation;
  ordinary builds must continue to work from committed snapshots without fetching data.
- Parameterize hard-coded snapshot editions, IDs and dataset versions where needed,
  preserving the old snapshot's provenance instead of relabeling it as newly fetched.
- Validate upstream schema and terms against the reviewed source contract. Missing
  fields, changed semantics/terms, unexpected source destinations or incomplete
  downloads stop the refresh for review.
- Add baseline comparisons for empty/truncated datasets, substantial row loss,
  changed exclusion rates and regressions in independently known vehicles. Choose
  thresholds from existing snapshots; do not invent a permissive threshold just to pass.
- Limit automatic changes to the three source snapshots, their generated projections,
  inventories and provenance/release metadata. Curated rules and manually reviewed
  normalization policy cannot be rewritten to make an automatic refresh pass.
- Generate a source-by-source diff summary, including upstream versions, digests,
  record counts, exclusions and affected fixtures. Preserve this in release evidence.
- Run offline reconstruction, provenance checks, Python/Java/tooling suites,
  cross-language parity, installed-wheel checks and embedded-data/package checks.
- If all gates pass, serialize updates, commit the verified snapshot and publish a
  new patch release of both libraries with complete attribution and checksums.
  Release numbering must avoid races with manual releases and support safe retries.
- Adapt the existing release workflow for explicit reuse by the updater: do not rely
  on a tag pushed with GitHub's workflow token automatically triggering another workflow.

Automatic release is appropriate for changes within these already reviewed data
contracts. A green test suite alone does not prove new source semantics or reuse rights.
Schema/terms changes require review; PDFs and forum-derived rules always require review.

Acceptance: dry-run unchanged, valid-change and rejected-change paths; prove that
failed checks leave main, release tags and published packages unchanged; exercise one
complete controlled refresh/release with matching Python and Java data.

## 4. Schedule API upgrades in GitLab

Proposed schedule: daily stable-release checks against the existing ORvin GitHub
release endpoint. Drafts/prereleases are excluded and versions are compared numerically.

- Confirm the wheel belongs to the expected project/version and verify its checksum
  against SHA256SUMS and the release asset digest when available. Fail on missing,
  conflicting or changed-in-place assets; never silently downgrade.
- Update the exact requirements.txt wheel URL and SHA-256. Install with hash
  verification and run lint plus API/real-Valkey tests before committing the pin.
- Serialize updater jobs and use a fast-forward push; a concurrent main change must
  be handled safely rather than overwritten. Use the project's short-lived CI job
  token with same-project push enabled and existing main protection preserved.
- Explicitly trigger the normal main build after the bot commit: GitLab job-token
  pushes do not themselves start a pipeline. Include failure/retry behavior for the
  boundary between committing the pin and starting the build.
- The normal main pipeline tests the exact pin again, publishes immutable main image
  tags to GitLab, and records library version/checksum with the image/build artifacts.
- Flux's existing Harbor-backed policy then updates its Git commit and deploys the
  new image. Verify the running /healthz version after a controlled end-to-end run.
- Unchanged releases should finish without a container rebuild. Support an explicit
  rebuild/recovery action and document how failed updates are retried.
- Document schedule ownership, failure visibility, pausing upgrades, disabling Flux
  image automation for rollback, and resuming after a corrected release.

Acceptance: tests cover new/same/older/prerelease versions, missing or mismatched
checksums, candidate test failure and safe commit/trigger retry. Run a real scheduled
no-change check and a controlled build-to-Flux rollout without inventing a public
library release solely for testing.

## Delivery order

1. Add the attributed fixtures and record the current decoding gaps.
2. Complete the GitLab API updater and verify the existing Flux deployment path.
3. Implement and validate the structured-data updater and reusable library release flow.
4. Complete all-BMW and relevant Subaru research in a subagent. Review proposed implementation only after step 5; do not add decoding rules during this delivery.
5. Release the verified library changes; use that real release to confirm the complete
   library-to-API automatic upgrade chain.

## Implementation progress (2026-09-26)

- Step 1: both attributed contributions are committed. Their independent reported
  identities and current decoding gaps remain separate. Python/Java parity passes
  for 4,866 full results, including the new examples.
- Step 2: API updater is on GitLab main. Active schedule 31 runs daily at 04:30
  Europe/Vienna. A real unchanged run skipped rebuilding; a controlled recovery run
  successfully triggered a normal main build. GitLab 18 requires the job token in
  the trigger form field. No personal access token is stored.
- Step 3: structured-data updater and reusable release workflow are implemented.
  Online comparison found all three pinned sources unchanged. A simulated change
  to all three sources in a disposable checkout passed complete offline regeneration
  and provenance checks, including retention of fixture-cited historical archives.
  No simulated source bytes are committed or published.
- Step 4: [all-BMW and Subaru research](../research/vin-rules/bmw-subaru-followup.md)
  is complete and its citations are registered. Implementation remains deferred.
- Step 5: [v0.2.1](https://github.com/openresearch/orvin/releases/tag/v0.2.1)
  is published and deployed. [Release run](https://github.com/openresearch/orvin/actions/runs/36231490657)
  passed all Java/Python, tooling, provenance, package equality, parity and installed-wheel checks.
  [Hosted source check](https://github.com/openresearch/orvin/actions/runs/36231473233)
  passed with all three sources unchanged and correctly skipped publishing.
  [GitLab scheduled upgrade](https://gitlab.openresearch.com/dispoxyz/code/orvin-api/-/pipelines/143154)
  verified and tested the wheel, committed the exact pin in `1baa60d`, and explicitly
  triggered [image pipeline 143155](https://gitlab.openresearch.com/dispoxyz/code/orvin-api/-/pipelines/143155).
  Flux selected `main-2026-09-26-09-09-43-14`, committed manifest update `46966da2`,
  and rolled out the healthy deployment. Reconciliation was requested to accelerate
  the configured timers; image selection and the manifest change used the existing automation.
  Public `/healthz` reports 0.2.1. Synthetic Golf VIN and HSN/TSN checks passed,
  including source credits, short/long equality and no-store responses.

No new upstream edition was available, so changed-source regeneration was verified
with simulated inputs locally; automatic publication of a future real upstream
change has not yet been observed. The release-to-API-to-Flux chain was exercised
with the real v0.2.1 release. No BMW/Subaru runtime decoding rule was added.

## Sources inspected for feasibility

- [NHTSA downloads](https://vpic.nhtsa.dot.gov/downloads/) and
  [release notes](https://vpic.nhtsa.dot.gov/Downloads/ReleaseNotes): versioned bulk
  archives and recent roughly monthly updates.
- [KBA Kfz service](https://services-eu1.arcgis.com/U09msXRZoxesNntH/arcgis/rest/services/SP_HSN_TSN_92a1e/FeatureServer/0)
  and existing ORvin KBA importer/source assessment: structured dated reference data.
- [ASTRA source directory](https://opendata.astra.admin.ch/ivzod/2000-Typengenehmigungen_TG_TARGA/2200-Basisdaten_TG_ab_1995/)
  and ORvin's retained metadata/importer: stable file source and pinned byte digests.
- [GitLab schedules](https://docs.gitlab.com/ci/pipelines/schedules/) and
  [job token permissions](https://docs.gitlab.com/ci/jobs/ci_job_token/): scheduled
  execution, same-project repository push and explicit downstream pipeline triggering.

Feasibility conclusion: yes for the three structured sources with the gates above;
yes for automatic API upgrades using the existing release and Flux infrastructure.
No automatic interpretation or promotion of PDF/forum-derived rules.
