# ORvin contributor instructions

ORvin is a standalone project. Keep the language-neutral dataset in `data/`, Python
in `libs/python/`, and Java (including Maven configuration) in `libs/java/`.
Both libraries must consume the same versioned data and preserve equivalent results.

The project/library display name is **ORvin** (exact casing). Keep package names,
Maven artifact IDs, CLI commands and repository paths lowercase `orvin`.

## Mandatory source traceability

- Every imported record and decoding rule must resolve to an identifiable source.
  Record a stable source ID, publisher, document title, exact URL, edition or snapshot
  version, retrieval/review date, and a precise page, section, table, row or API locator.
  Retain upstream row IDs and schema IDs in generated data and decoded evidence.
- Record the reuse basis and required attribution. Public availability alone is not
  permission to redistribute a document. Preserve upstream notices in both packages.
- Pin each retained upstream file with SHA-256. For documents not redistributed,
  record the inspected-byte digest when available and explicitly explain any missing
  digest. Never invent a hash, retrieval date, license or stronger authority.
- Bind rules to their reviewed market, manufacturer/WMI, model/year and layout scope.
  Cite the actual source of each field; do not attach an unrelated source to every field.
  Derived facts must identify their derivation and parent rule/source lineage. Distinguish
  a source's explicit assertion from a combination of sources or an inference.
- Do not infer assembly location from manufacturer identity, model year from production
  year, or exact build date/engine/trim from filler characters. Preserve unknown values
  and correlated alternatives when the sources do not resolve them.
- Keep source metadata and evidence available in installed Python and Java artifacts,
  including CLI JSON. Both short and long JSON views must carry self-contained
  credits for their sourced content, including applicable license/terms links and
  modification notices; compact output must not strip required attribution.
  Readable CLI output must list all sources used by its result.
- Research citations are leads, not implemented rules. Preserve their source links,
  document locators, limits and review notes. Promoting a lead requires a full runtime
  source record and a scoped rule with independent behavioral examples.
- Prefer synthetic VINs in fixtures. A real customer VIN may be committed only with
  explicit permission recorded next to its attribution and owner-reported facts.
  `data/identity/fixtures.json` contains an expressly authorized Golf 5 from Austria.
  Distinguish owner-reported facts from decoder-derived expectations. Never send
  customer VINs to external services without separate explicit authorization.
- Keep type-approval catalogue candidates separate from established vehicle facts.
  Preserve each row's remarks and correlated specifications; a catalogue label hit
  is not full model coverage. Never infer model year from an approval date.
- Describe validation-label origins. A public dataset whose labels were VIN-decoded
  is a correlated benchmark, not independent OEM ground truth. Keep separately
  licensed validation corpora outside the packaged production dataset.

## Validation and changes

`tools/provenance.py` checks source records, hashes, field references, fixture provenance,
research-citation inventory and the complete `data/` file inventory. Add new source/data
files to its explicit inventory and manifests; never bypass a failing check.

After data or rule changes, run `python tools/dataset.py` in the repository's development
environment. It performs offline reconstruction of the complete NHTSA, KBA and native
decoding projections, plus provenance validation. Intentional regeneration commands are
documented in `docs/nhtsa-data.md` and `docs/rich-decoding.md`; review regenerated diffs.
Use `--update-runtime` only to refresh the checked-in Java metadata after a reviewed change.

Run the relevant Python, Java and tooling tests for behavior changes. Before handing off
a change to the shared decoder or dataset, run `tools/check_parity.py` and
`tools/check_packages.py` on fresh artifacts. These verify equivalent results and that
both distributions embed every shared data file unchanged. Documentation-only changes
need a diff/link review, not new behavioral tests.

Keep `docs/provenance-audit.md` and capability documentation accurate. Automated integrity
checks do not prove factual accuracy, global coverage or reuse rights; report limitations
honestly. Do not silently broaden a rule because one example happens to match it.

## Automatic maintenance boundary

The daily structured-data workflow may update the reviewed NHTSA, KBA and ASTRA
snapshots, generated projections and provenance only after full validation. Read
`docs/automatic-updates.md` before changing its source contracts, publication allowlist
or thresholds. PDF/forum-derived rules, curated normalization and independent fixture
expectations require manual review; never adjust them automatically to pass a refresh.
User-contributed VINs include the Golf, BMW X1 and Subaru Legacy in identity fixtures;
keep their explicit permission, attribution, reported facts and current gaps separate.
