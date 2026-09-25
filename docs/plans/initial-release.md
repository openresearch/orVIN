# Initial release work

- [x] Create `openresearch/orvin` and work in a separate local checkout.
- [x] Assess NHTSA API reuse and coverage; document KBA/manufacturer-guide limitations.
- [x] Define canonical JSON, provenance, constraints and explicit ambiguity.
- [x] Seed five ordinary WMIs and one extended assignment with reusable API snapshots.
- [x] Implement the immutable Java 17 offline API and independent structural assessment.
- [x] Add schema/semantic validation and behavior/validator regression tests.
- [x] Add contribution templates, CI configuration and publication preparation.
- [x] Complete the initial WMI verification: 21 Java and 10 validator tests passed. The later
  KBA/Python slice below supersedes the seed artifact size and verification totals.
- [x] Research German HSN/TSN enrichment: official FZ 6 and Kfz portal table have usable terms;
  record actual fields, annual coverage limits and lack of a VIN-to-TSN crosswalk in `docs/kba-data.md`.
- [x] Import 63,260 KBA Kfz rows at 2026-01-01, retaining source attributes, hashes and attribution.
- [x] Implement separate HSN/TSN lookup with invalid/unknown/recognized/ambiguous outcomes.
- [x] Organize shared data in `data`, independent implementations in `libs/python` and `libs/java`.
- [x] Keep all Maven files in `libs/java`, including wrappers and `.mvn`.
- [x] Add Python-only `vin.sh` and `hsntsn.sh`, readable default summaries and complete output with
  `--json`, without an install/compile step. Preserve unknown/ambiguous states and deduplicate sources.
- [x] Pass 30 Java, 17 Python/library/script and 14 data-validation tests; compare 246 complete
  Java/Python results, including source metadata and nulls.
- [x] Build the Python wheel from its sdist, install it in a fresh environment outside the checkout,
  and verify both lookups, the console entry point, byte-identical data and required notices.
- [x] Compare expanded clean JAR builds on local JDK 26.0.2.1 targeting Java 17: identical SHA-256
  `d7c1c09aff1a8a35e05021deb6d32142643e4c8d4dc45e393046b33164468ea2`; 1,586,215 bytes.
- [x] Research 50 makes with three research agents; index public evidence, applicability and
  reuse gaps in `docs/research/vin-rules/README.md`.
- [x] Replace the six-WMI seed with the full usable September 2026 NHTSA WMI projection:
  12,998 WMIs, 11,604 manufacturer entities and 14,169 associations; preserve multi-brand ambiguity.
- [x] Pin and embed the complete 76,201,016-byte NHTSA ZIP (97 tables and all source functions)
  in both distributions. Record three runtime exclusions while preserving the complete archive.
- [x] Implement explicit download/import, full offline source reconstruction, COPY parsing tests,
  scalable conflict validation and byte-for-byte artifact checks in CI.
- [x] Expanded verification: 32 Java, 18 Python/library/script and 19 data-tool tests passed;
  878 complete Java/Python results match, with Java production resources loaded from the JAR.
- [x] Verify all 17 shared data files byte-for-byte in the JAR and wheel; exercise both artifacts
  outside the checkout (fresh offline wheel install and a standalone copied JAR).
- [x] Compare the current main JAR against a clean rebuild: identical SHA-256
  `fd3fef7730a790d5ddce866117ceb2c4542985ce3551aac6852404a01fda5070`;
  74,414,998 bytes. Wheel built from sdist: 73,865,730 bytes. Same local JDK/toolchain as above.
- [ ] Implement detailed NHTSA pattern/year/enrichment/validation semantics in both libraries;
  full source archival does not mean these fields are decoded yet.
- [x] Add tag-triggered Java publishing to GitHub Packages and Java/Python GitHub Release assets,
  gated by reusable CI, with matching versions, checksums and manual dry-run support.
- [x] Document Maven and Gradle consumption/authentication without changing Tourfold.
- [x] Verify a disposable `v0.1.0` release build: 32 Java, 18 Python and 22 data/release-tool tests;
  878 parity results, complete embedded-data checks, strict wheel/sdist metadata, manifest/checksums,
  and Maven deployment to a temporary file registry passed. Both workflows pass actionlint 1.7.12.
- [x] Commit and push the library/release workflow branch. CI runs the Java/Python matrix on
  branch pushes; the current result is available in GitHub Actions rather than a static build claim.
- [x] Deploy the release candidate to a temporary Maven registry and resolve it from an independent
  consumer with an isolated dependency cache; both embedded dataset lookups passed.
- [ ] Configure verified repository protection where access permits.
- [ ] Obtain human source/licensing review before declaring a release ready.
- [ ] Publish a version tag when a release is requested; optional Maven Central/PyPI setup remains separate.

Decisions: Apache-2.0 code; CC0 only for Orvin-owned data contributions; NHTSA-derived facts retain
their source notice; KBA data retains dl-de/by-2-0. WMI JSON and KBA TSV with JSON metadata are
canonical and language-neutral. Java uses validated derived resources; Python reads canonical
data directly. Both implementations work offline without runtime dependencies. Country, year,
plant, engine and vehicle-history guesses remain out of scope. VIN coverage now includes the full
usable NHTSA WMI projection; detailed VIN fields remain future work. The earlier artifact hash/size
above describes the pre-bulk build and is historical only;
the KBA snapshot is complete for the queried reference date, not every type ever assigned.
