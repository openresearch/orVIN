# Contributing

Submit dataset changes through a reviewed GitHub pull request. Keep the data, provenance and
regression fixtures together. Do not import a large unreviewed list to improve apparent coverage.

Read [AGENTS.md](AGENTS.md), the canonical source, licensing and attribution policy
for human and AI-assisted contributions. It covers runtime data, decoding rules,
normalization, research, fixtures and packaged output. Claude Code imports the same
policy through `CLAUDE.md`. Use the [data-change PR template](.github/PULL_REQUEST_TEMPLATE/data-change.md)
for changes to these areas; incomplete rights assessments stay research-only.

## Required evidence

1. The canonical additions or corrections in the relevant `data/` source/rule files,
   source pins and importers, plus their regenerated projections. Direct edits to a
   generated bulk projection fail validation; see [NHTSA updates](docs/nhtsa-data.md).
2. An authoritative source for every factual mapping and manufacturer field.
3. Publisher, exact URL, publication/version/date (or an explicit reason it is unavailable),
   retrieval date, and relevant section, row, page or API fields.
4. A concrete reuse basis and link to the source's applicable terms. An open code repository,
   public download or citation alone does not establish redistribution rights.
5. Behavior fixtures in the relevant shared fixture file, plus focused Python, Java and .NET
   tests for new matching behavior such as ambiguity or scope restrictions. Prefer
   synthetic VINs; real VINs require the publication permission specified in `AGENTS.md`.
   Expected values must come from reviewed
   evidence; never generate a regression's expected output from the implementation being tested.
6. Required source credits, terms links and modification notices in source metadata,
   `data/LICENSE.md`, all library distributions, and short/long output where applicable.

Retain source files only where their redistribution is permitted. Otherwise retain precise
references and any permitted supporting extracts. Do not upload customer VINs, private vehicle
records or copyrighted guides without permission. AI-generated assertions are not evidence.

## Example: correcting an existing name

For a hypothetical correction to `american-honda`:

- Verify the corrected legal/manufacturer name in an authoritative record and assess its reuse terms.
- Update the bulk source pin/importer or explicitly introduce a separately sourced overlay design.
  Do not hand-edit the generated projection. Add a source ID with the record's date/version and
  exact supporting fields. Keep historical
  source references when they explain the change; do not overwrite a snapshot while retaining its hash.
- Change the name on the existing stable manufacturer identity when it is the same entity. A
  different legal entity needs its own ID and an appropriately constrained assignment.
- Update or add the expected behavior fixture and a test if the changed field is not yet asserted.
- Increment the dataset version and describe the before/after behavior in the pull request.

`data/dataset.json` contains complete real examples of sourced entries. The reviewed fixtures
use synthetic VIN tails and are independent golden expectations. Do not refresh those expectations
automatically when changing data.

## Scope and ambiguity

Only add `brand`, `category` or manufacturer `country` when the cited evidence supports that field.
Absence means unknown. Never derive assembly country from manufacturer country or a WMI prefix.
Represent a low-volume assignment using its six-character key; its suffix is at VIN positions 12–14.

Use `fromModelYear`, `toModelYear` and/or `markets` only for evidenced constraints. Bounds are
inclusive. A source's last-updated date is not a model year. Do not narrow a scope merely to hide
a conflict. If evidence supports multiple overlapping mappings, assign a shared `ambiguityGroup`
and give each an `ambiguityReason`, then add a test that preserves all candidates without guessing.
The simple seed fixture format asserts unique mappings; an ambiguity/scope contribution must
extend the fixture format and runner as needed, with independent expected candidates and context.

## Checks

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/requirements.txt
.venv/bin/python tools/dataset.py
PYTHONPATH=libs/python python3 -m unittest discover -s libs/python/tests
(cd libs/java && ./mvnw -Dpython=../../.venv/bin/python verify)
dotnet run --project libs/dotnet/orVIN.Checks -c Release
python3 tools/check_parity.py --dotnet libs/dotnet/orVIN.Checks/bin/Release/net8.0/orVIN.Checks.dll
git diff --check
```

CI checks schema, malformed identifiers, missing provenance/reuse fields, unknown references,
duplicates/conflicts, snapshot hashes, complete source reconstruction and behavioral regressions.
Fixtures are independently reviewed examples; do not manufacture a golden result for every imported
row by copying the importer's output. The build reconstructs and compares every bulk row. It builds on
Java 17, 21 and 25 and compares repeat main-JAR builds. CI cannot prove factual accuracy, source
authority or legal permission. A maintainer must review those before merging.

Code and original documentation contributions are under Apache-2.0. Original dataset contributions
are under CC0-1.0 to the extent you own their rights, while imported material retains its own terms.
See [data/LICENSE.md](data/LICENSE.md). Do not apply CC0 to someone else's protected work.

## KBA and cross-language changes

KBA has separate canonical data and terms in `data/kba/`; see [import instructions](docs/kba-data.md).
Keep leading zeroes, model labels, nulls, statistical markers and reference dates. Retain all
candidates for repeated HSN/TSN pairs; never turn a missing entry into evidence of invalidity.
Use reviewed KBA rows in `data/kba/fixtures.json`; those expectations participate in complete cross-language parity checks.
Synthetic tests cover ambiguity and missing counts even when the current source has unique keys.

Update Python, Java and .NET together when changing lookup semantics. `tools/check_parity.py` compares
complete public results, including unknown fields and provenance. After intentional data edits,
run `.venv/bin/python tools/dataset.py --update-runtime` to refresh the shared compiled runtime bundle
and include the diff. The source snapshot/table is shared; do not add separate editable copies
to any language directory. Python packaging copies the shared data only into build artifacts.
