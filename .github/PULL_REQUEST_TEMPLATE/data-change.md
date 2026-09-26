## Change and evidence

Describe the affected identifiers and observable before/after behavior.
Follow the shared [source and licensing policy](https://github.com/openresearch/orvin/blob/main/AGENTS.md).
State any fields, markets, years or VIN layouts deliberately left unsupported.

| Rule / field | Source ID and exact URL | Edition, date and locator | Hash or explained absence | Reuse basis and terms URL |
| --- | --- | --- | --- | --- |
| | | | | |

Explain which claims are explicit source facts and which are derived. Identify
secondary sources, conflicting evidence and any unresolved questions.

## Redistribution and attribution

List what this PR adds to the repository and published artifacts: selected facts,
transformed records, source archives, permitted extracts or fixtures. Explain why
the cited terms support those particular uses, including any applicable conditions.
An online source or an attribution alone is not redistribution permission.

Specify required credit wording, source/license links and modification notices,
and where they appear in metadata, `data/LICENSE.md`, Java/Python packages and
short/long results. Refer to an existing approved assessment when its scope is unchanged.

## Contributor checks

- [ ] Data changes, source records and behavioral fixtures are included together.
- [ ] Each factual field is supported; unknown fields have not been guessed.
- [ ] Historical, market and year restrictions or ambiguity are represented explicitly.
- [ ] The proposed reuse is supported; imported material is not relicensed Apache-2.0 or CC0.
- [ ] Bundled source material is permitted for redistribution, with required notices preserved.
- [ ] Fixtures are synthetic or have recorded publication permission; no private documents/personal details are included.
- [ ] Expected facts are independent of decoder output; relevant near-miss/conflict cases are covered.
- [ ] Canonical inputs and regenerated outputs agree; source IDs, locators, hashes and retained editions are traceable.
- [ ] Required credits survive packaging, normalization and short/long output in both languages.
- [ ] Dataset versions and provenance/capability documentation are updated where applicable.

## Validation

List commands and results, or explain why a check is not applicable:

- Offline reconstruction and provenance (`tools/dataset.py`).
- Relevant Python, Java and tooling tests.
- Full-result parity (`tools/check_parity.py`) and embedded-data equality on fresh
  JAR/wheel artifacts (`tools/check_packages.py`).

## Human review

Record why the source is authoritative, which fields it establishes, and why its terms permit
this contribution. New sources, changed terms and manual rules require maintainer review
before merging. Green CI checks consistency and regressions, not factual or legal correctness.
Unresolved rights remain research-only; do not fix a failed check by guessing facts,
changing fixture expectations to match output, or removing notices or validation.
