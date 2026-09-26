# European coverage expansion

Audience: Europe overall, prioritizing Germany and Austria (user clarification,
2026-09-26). New registrations guide priorities; they are not the same as the
installed fleet, and a family name does not establish coverage of every generation.

- [x] Locate a broad European source: ASTRA Swiss passenger-car type approvals.
- [x] Import a pinned snapshot and reconstruct a conservative VIN-template projection.
- [x] Expose correlated, sourced approval candidates in both libraries and the CLI.
- [x] Audit a sourced 100-model priority set and publish coverage/gaps.
- [x] Add a separately licensed public masked-prefix benchmark, with truthful limits
  on the independence and completeness of its labels.
- [x] Verify provenance, cross-language parity and installed artifact contents.

Approval candidates describe approved types, not the build record of an individual
car. They must not overwrite directly decoded model/year/plant facts. Keep the raw
type names and configuration rows together; do not combine an engine from one row
with the power or body of another. Approval dates are not model years or build dates.
Only reviewed 17-position templates enter the first projection; excluded syntax is
counted and retained in the original snapshot for later work.

Delivered 122,273 approval rows / 125,065 templates / 247 WMIs, with 93 of the
100 target text queries finding catalogue rows. This is candidate enrichment,
not a claim of full 93-model decoding. Seven query gaps and the lack of broad
independent European labelled VIN ground truth are documented in
[the coverage report](../european-coverage.md).

Local verification: 30 Python library tests, 46 Java tests and 39 tooling tests;
complete offline source reconstruction and provenance; 1,610 full Java/Python
result comparisons; all 535 shared data files verified byte-for-byte in the
fresh JAR and wheel. The wheel was built from the source distribution and tested
after installation outside the checkout. Changes are not yet published.

Community decoder tables and forum posts remain useful leads. The first broad
expansion prioritizes official approval facts; unsupported layouts remain unknown.
