# Rich offline VIN decoding

Implement model, model year, assembly plant and the other public attributes encoded
by the pinned September 2026 NHTSA patterns in both native libraries. Keep the
original source archive embedded, and add deterministic, language-neutral runtime
tables. No database, network call or Java installation for the Python CLI.

## Contract and boundaries

- Keep the existing manufacturer lookup API. Add sourced vehicle details and
  convenience resolutions for model, model year and assembly country.
- NHTSA patterns describe US reporting scope. Unknown market produces conditional
  possibilities; an explicit non-US market must not silently use US rules.
- Model-year cycles use the snapshot year as a deterministic horizon. Retain
  possible years and their associated facts together; never blend configurations.
- Implement public patterns, scoped schema selection, dictionary values, numeric
  captures, published precedence, engine-model facts and displacement conversions.
  Do not claim full vPIC equivalence: vehicle-spec enrichment, defaults, VIN repair
  and error-scoring passes are outside this increment.
- Exact build dates and complete option lists remain unknown. Add separately
  documented European rules only where applicability is established.

## Work

- [x] Deterministic exporter and source/completeness validation.
- [x] Python decoder, public result and readable CLI.
- [x] Equivalent Java decoder and immutable public results.
- [x] Scoped European extension where independently documented.
- [x] Independent expected examples, failure boundaries, complete cross-language
      parity and installed artifact checks.
- [x] Update capabilities, source provenance and user examples.

## Validation completed 2026-09-26

- 26 Python library tests, 41 Java tests and 30 tooling tests pass.
- Full offline source reconstruction and provenance validation pass: 284 shared data
  files, 16 source records, 78 research citations and all source rows accounted for.
- 1,586 complete Python/Java results match using production classes/resources in the
  JAR, including source catalogs, conditional values and null fields.
- Every shared data file matches byte-for-byte in the JAR and the wheel built from
  the sdist. An installed wheel outside the checkout resolves Golf, Accord, Model Y
  and KBA examples with source evidence.
- Local Java build uses JDK 26 with Java 17 release targeting. The GitHub Actions
  17/21/25 matrix remains the check for those runtime versions; it has not run for
  these uncommitted changes.
- Development versions are 0.2.0-SNAPSHOT / 0.2.0.dev0. Nothing has been published
  or integrated into Tourfold during this increment.

The Golf extension is intentionally limited to European WVWZZZ1KZ5[PW] layouts;
its combined evidence and missing maintenance-PDF byte hash are documented in
`docs/provenance-audit.md`. Vehicle-spec enrichment, defaults, repair/scoring and
exact build date remain outside this increment.
