# Project naming

The project display name is **orVIN**, approved 2026-09-26. This supersedes the
previous casing throughout documentation, attribution notices, runtime metadata,
CLI diagnostics, release labels and the web interface.

Python/Java packages, Maven artifact IDs, CLI commands and existing URLs remain
lowercase `orvin`. The unreleased .NET package and namespace use `OpenResearch.orVIN`,
with `orVIN` / `orVIN.Checks` projects. No published .NET API needs migration.

Generated identity metadata and runtime notices are rebuilt from their canonical
inputs. Upstream source snapshots, source IDs, licenses and vehicle facts are unchanged.
The API health response and visible wordmark use the new name. Its released wheel
pin remains unchanged until the next stable release is adopted normally.

Validation: source/provenance reconstruction passed, as did 43 Python tests, 50 Java
tests, 44 tooling tests, .NET behavioral checks, 4,866 Java/Python and 3,244 .NET/Python
parity comparisons. The fresh JAR/wheel have identical runtime data. API lint and
15 tests passed; the browser preview shows the renamed wordmark/title/footer.
GitHub already uses `orVIN`; the GitLab display name was updated to `orVIN-api`.

Released in 0.3.0 and verified on the public API on 2026-09-26. The page tagline
and wordmark dot were removed. The daily updater accepts GitHub owner/repository
casing changes while preserving exact host, release-tag, filename and checksum checks.
