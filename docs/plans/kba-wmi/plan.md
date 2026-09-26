# KBA WMI directory import

Status: implementation and local package verification complete, 2026-09-26.
Prepared for release 0.3.1; publication and API deployment are pending.
The recorded reuse basis is the attribution notice on SV 3.1 PDF page 151;
see `docs/research/kba-wmi/README.md`.

## Design

- Parse the pinned SV 3.1 PDF (15 January 2026) into a factual row snapshot with
  PDF page and top-to-bottom row locators. Preserve empty cells, spelling, leading
  zeroes and all repeated rows. Do not redistribute the original PDF.
- Validate its original digest before extraction; pin the transformed snapshot
  and rebuild projections offline. Record invalid identifiers and missing WMIs
  explicitly rather than fixing or inventing them.
- Compile valid rows into the existing portable literal-rule format, with global
  applicability and six-character identifiers at VIN positions 1–3 plus 12–14.
  No language-specific PDF parser or new runtime dependency is needed.
- Use explicit manufacturer-directory fields for name, label, location and HSN.
  These are catalogue associations, not retail makes, actual vehicle HSN/TSN,
  model/year facts or assembly locations. Preserve each row as a correlated
  alternative and competing values as ambiguous. NHTSA WMI/marque assignments
  remain separately sourced, so a missing KBA brand does not erase an established
  marque or falsely support it.
- Embed source metadata, reuse assessment, license and modification notices in
  the common bundle. Existing long-output provenance carries credits for the
  additional directory evidence; short output attributes the facts it exposes.
- Keep this PDF source under manual review, outside automatic source refreshes.

## Validation

- [x] Inspect rendered sample rows and compare extraction against a second PDF reader.
- [x] Validate snapshot integrity, row completeness, identifier exclusions and NHTSA overlap.
- [x] Test global matching, extended identifiers, near misses, ambiguity and source credits.
- [x] Rebuild the dataset and run Python, Java, .NET, parity and installed-package checks.
- [x] Update coverage, source/import guides, provenance audit and this plan with results.

The second extraction compared all 145 table pages' HSN and WMI columns using
pdfplumber; rendered pages 6, 16, 17, 34 and 140 were reviewed. Six synthetic
fixtures cover independent source facts, including the apparent `1CA` disagreement.
See the [comparison report](../../research/kba-wmi/comparison.md): 773 overlapping
identifiers, 59 equal normalized manufacturer-name sets and 714 differing sets.
These are label comparisons, not 714 established assignment errors.

Validation passed: full offline reconstruction/provenance, 48 tooling tests,
46 Python tests, Maven `verify` with 51 Java tests, .NET installed-package behavior
and all 524 embedded resource bytes, 6,474 Java/Python complete results and 4,316
.NET/Python normalized results. Fresh JAR/wheel resource checks passed; the wheel
was built from its sdist and exercised outside the checkout, including the
contributed Golf, global/extended identifiers, attribution and conflicting names.

Maven used `-Dpython=/Users/schmidp/Development/or/tourfold/orvin/.venv/bin/python`
because the system Python lacks the development-only `jsonschema` dependency.
The .NET consumer restored the freshly packed version through an isolated NuGet
cache to avoid reusing the earlier `0.3.0-dev` package.

## Explicit 1CA source preference

Follow-up requested 2026-09-26: make the preference for NHTSA's Cobra Industries
assignment explicit and traceable, without rewriting KBA's source wording.

- [x] Record the reviewed KBA row, preferred NHTSA assignment, review date and
  rationale in the source metadata; retain original source hashes/locators.
- [x] Compile a separate `Make` rule with `SOURCE_PREFERENCE` evidence using the
  existing portable runtime; keep directory HSN/name in their own alternative.
- [x] Stop for review if the referenced identities, constraints or locators change,
  or a competing NHTSA assignment appears; permit unchanged records in new editions.
- [x] Verify importer guards, positive/near-miss outputs, all three libraries and
  fresh package/parity checks. Update the audit with the final measurements.

Preference validation passed: 49 tooling tests, 47 Python tests, Maven `verify`
with 52 Java tests and complete source reconstruction, fresh installed .NET checks,
6,474 Java/Python and 4,316 .NET/Python results, and all 524 common package files.
The installed wheel confirms explicit preference evidence in AT/DE/US/JP, preserved
KBA wording, no preference on the neighbouring `1C3` prefix, and unchanged Golf
identity. Derived decoding/identity versions are now `2026.09.26.3`; no library
release or deployment was performed for this follow-up.
