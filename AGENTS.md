# ORvin contributor instructions

ORvin is a standalone project. Keep the language-neutral dataset in `data/`, Python
in `libs/python/`, Java (including Maven configuration) in `libs/java/`, and C#
in `libs/dotnet/`.
All libraries must consume the same versioned data and preserve equivalent results.

The project/library display name is **ORvin** (exact casing). Keep package names,
Maven artifact IDs, CLI commands and repository paths lowercase `orvin`.

This file is the canonical contributor policy for people and coding agents.
Read [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow and
[data/LICENSE.md](data/LICENSE.md) for existing source-specific rights and notices.
`CLAUDE.md` imports this file; maintain shared rules here rather than duplicating them.

## Plans, research and documentation

- Keep ORvin documentation in this repository's `docs/`. These conventions apply
  to standalone checkouts; do not depend on a parent repository's instructions or
  store ORvin plans and research in another project's documentation tree.
- Store new implementation plans and design notes under
  `docs/plans/<feature-or-initiative>/`. Keep cross-cutting plans together across
  the dataset, tooling, Python, Java, .NET and release workflows. Continue updating
  existing plans in place rather than creating competing copies.
- Keep plans current as work progresses: record status, decisions, completed and
  deferred work, validation results, open questions and implementation gotchas.
  Clearly distinguish proposals from implemented behavior and verified results.
- Store research reports, source investigations, coverage worklists and supporting
  research metadata under `docs/research/<topic>/`. Follow the source, licensing
  and attribution rules below, including precise citations and unresolved limits.
  Update the relevant research index and citation inventory when adding reports;
  VIN-rule research uses `docs/research/vin-rules/sources.json` and the explicit
  research-file inventory in `tools/provenance.py`.
- Keep architecture, API usage, source/import guides, coverage reports and
  operational documentation in `docs/`, with relative links between related
  documents. Keep the root README concise and link to those guides. Package-local
  READMEs may explain package-specific usage.
- Research documents do not replace runtime provenance. Reviewed production data,
  rules, fixtures, source records and notices remain in `data/`; generated API
  references belong with their owning library rather than in `docs/plans/`.

## Mandatory source traceability

- Every imported record and decoding rule must resolve to an identifiable source.
  Record a stable source ID, publisher, document title, exact URL, edition or snapshot
  version, retrieval/review date, and a precise page, section, table, row or API locator.
  Retain upstream row IDs and schema IDs in generated data and decoded evidence.
- Record the reuse basis and required attribution. Public availability alone is not
  permission to redistribute a document. Preserve upstream notices in every package.
- Prefer the original publisher's source. Identify mirrors, secondary sources and
  forum claims as such; do not present them as OEM assertions. Record corroboration,
  contradictions and unresolved limits. AI output, a search snippet, or another
  decoder's answer alone is not evidence for a new rule or independent ground truth.
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
- Keep source metadata and evidence available in installed Python, Java and .NET artifacts,
  including CLI JSON. Both short and long JSON views must carry self-contained
  credits for their sourced content, including applicable license/terms links and
  modification notices; compact output must not strip required attribution.
  Readable CLI output must list all sources used by its result.
- Research citations are leads, not implemented rules. Preserve their source links,
  document locators, limits and review notes. Promoting a lead requires a full runtime
  source record and a scoped rule with independent behavioral examples.
- Prefer synthetic VINs in fixtures. A real customer VIN may be committed only with
  explicit permission covering publication in repository tests and bundled artifacts,
  recorded next to its attribution and contributor-reported facts. Do not assume
  the contributor owns the vehicle. Keep private registration documents and personal
  details out of fixtures. Distinguish reported facts from decoder-derived expectations.
  Never send customer VINs to external services without separate explicit authorization.
- Keep type-approval catalogue candidates separate from established vehicle facts.
  Preserve each row's remarks and correlated specifications; a catalogue label hit
  is not full model coverage. Never infer model year from an approval date.
- Describe validation-label origins. A public dataset whose labels were VIN-decoded
  is a correlated benchmark, not independent OEM ground truth. Keep separately
  licensed validation corpora outside the packaged production dataset.

## Licenses, redistribution and attribution

- Separate ORvin's code/documentation license (Apache-2.0), the dedication of
  original dataset work (CC0-1.0 only to the extent the contributor owns the rights),
  and each upstream source's terms. Imported material keeps its own terms; neither
  repository license automatically applies to it. Preserve third-party notices.
- For every new source or changed reuse basis, record the exact license/terms URL,
  applicable edition or dated review, relevant clause, and a concrete assessment
  of the proposed use. Distinguish permission to inspect a source, extract selected
  facts, redistribute a transformed database, and bundle the original file. Assess
  applicable copyright, database and access terms for that use; attribution alone
  does not establish permission. Do not invent SPDX identifiers or call a source
  public domain merely because it is on a government website.
- Check obligations against distribution in the Java JAR, Python wheel/sdist and .NET NuGet package,
  and exposure of sourced results in the API/CLI. Record required credit wording,
  source URI, license/terms link, notices, modification statements and any other
  applicable conditions. Use an existing approved source assessment only within
  its reviewed scope; permission for one dataset is not permission for linked PDFs.
- Do not copy manuals, PDF tables, forum posts, illustrations, third-party decoder
  databases or other source assets into the repo unless that redistribution is
  supported by the recorded assessment. Reformatting or manually transcribing a
  source does not resolve its rights. Any permitted factual extraction needs its
  own source and scope assessment; it must not reproduce protected material by default.
- If authority, rights or license compatibility remains unresolved, keep a precise
  research citation and the unresolved question outside packaged production data.
  Do not import the material, implement the proposed rule, or claim approval to
  improve coverage. New sources, changed terms and manual rules need maintainer
  review before merging. Checks on already reviewed structured refreshes follow
  the automatic-maintenance boundary below.
- Store the assessment with the applicable source metadata and source documentation;
  a PR description or a link in a research report is not a runtime source record.
  Add applicable notices to `data/LICENSE.md` and the source catalogue, retain
  evidence locators through normalization, and preserve required credits in both
  short and long output. Do not imply publisher endorsement.
- Preserve older source editions and their notices while retained rules or fixtures
  cite them. Keep each retained edition associated with its actual bytes and hash;
  never label new bytes as an old verified snapshot or silently carry a reuse
  assessment over to changed terms.

## Pull request evidence and review

For changes to data, rules, normalization, source metadata or packaging, include:

1. A before/after example and the precise fields, markets, years and VIN layouts affected.
2. Source IDs mapped to fields, exact document/row locators, edition/retrieval dates,
   hashes (or explained unavailable hashes for unbundled documents), and derivation notes.
3. The reuse assessment, what will be redistributed, required attribution and where
   the notices appear in packages and output. State any unresolved source questions.
4. Independent expected facts, positive examples and relevant near-miss/conflict
   cases. Record permission for any real VIN; never update expectations merely to
   match new decoder output or treat a shared data error as proof from parity.
5. Validation commands and results, updated provenance/capability documentation,
   and a review of the generated diff. Change the canonical input/importer and
   regenerate; do not hand-edit generated projections or embedded copies.

Use the [data-change PR template](.github/PULL_REQUEST_TEMPLATE/data-change.md).
Maintainers must review factual support and reuse rights as well as CI. A green
build, a filled-in metadata field, or an agent's assurance cannot establish either.
Do not weaken provenance checks, drop attribution, hide conflicts, or broaden a
source's scope to make a contribution pass.

## Validation and changes

`tools/provenance.py` checks source records, hashes, field references, fixture provenance,
research-citation inventory and the complete `data/` file inventory. Add new source/data
files to its explicit inventory and manifests; never bypass a failing check.

After data or rule changes, run `python tools/dataset.py` in the repository's development
environment. It performs offline reconstruction of the complete NHTSA, KBA and native
decoding projections, plus provenance validation. Intentional regeneration commands are
documented in `docs/nhtsa-data.md` and `docs/rich-decoding.md`; review regenerated diffs.
Use `--update-runtime` to regenerate the common `data/generated/` bundle after a reviewed change.

Run the relevant Python, Java, .NET and tooling tests for behavior changes. Before handing off
a change to the shared decoder or dataset, run `tools/check_parity.py` and
`tools/check_packages.py` on fresh artifacts, plus the .NET installed-package checks
with `--bundle-dir data/generated`. These verify equivalent results and that
distributions embed exactly the common `data/generated/` bundle, byte-for-byte,
with required notices. Never package raw snapshots, private evidence or fixtures. Documentation-only changes
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
