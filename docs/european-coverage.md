# European VIN coverage

Development snapshot, reviewed 2026-09-26. The target is Europe overall, with
Germany and Austria prioritized. ASTRA support shipped in 0.2.0. The next release adds a shared compiled runtime
bundle, cross-market suggestions and .NET support; it does not add new factual coverage.

## What now works

The offline libraries load **122,273 Swiss passenger-car type approvals** from
ASTRA, containing **125,065 VIN templates**, **247 WMI prefixes** and **154 original
make labels**. These counts include historical and specialist marques; they are
not counts of fully supported manufacturers. The complete original source is
retained losslessly in a 20.7 MB gzip archive in the repository. The next release
packages only its runtime projection, source metadata and required notices.

`VinDecoder.decode(...)` now also returns `typeApprovals` (Java:
`result.typeApprovals()`). This contains:

- Each matching approval ID, original source row, original VIN template and the
  matching alternative templates.
- Original make/type/variant names, body style, EU type-approval number, drive and
  fuel codes, engine name, displacement, power, seats and doors where supplied.
- The full remarks for **each approval**, including restrictions and exceptions.
- A source document with edition, locator, retrieval date, reuse basis and hashes.

The CLI returns the normalized short answer. `--json --long`
retains all configurations and remarks in `details`. A long candidate list means the source
template cannot distinguish those configurations. Values in different rows must
not be combined into a fictitious vehicle.

These are **Swiss catalogue candidates**, not established facts about the input
car. Even a single matching approval is conditional: this collection does not
prove the vehicle's original market or build configuration. It can help research
European cars while preserving that distinction. Existing scoped OEM/NHTSA facts
remain in `details`; the new candidates do not overwrite `model`, `modelYear`,
engine or plant facts. An explicitly supplied year does not establish an approval.

For example, a synthetic `TMBABC5E0J0000001` finds Škoda Octavia approval variants.
It does not identify an exact engine, production date or model year. The synthetic
BYD specimen `LGXCH6AD0S0000001` retains separate SEAL approvals ABJ202 and ABJ204
with different engine/power pairs, as well as broader overlapping catalogue rows.

## The 100-model worklist

The [sourced worklist](research/europe-priority/README.md) combines 50 European
2024 targets, 23 additional Austrian 2025 targets, and 27 German 2025 additions.
It is a practical priority selection, not a claimed pan-European top-100 ranking.
Observation periods are kept separate; new registrations are not fleet stock.

**93 of the 100 target label queries find shipped approval rows.** The
[machine-readable list](research/europe-priority/models-100.json) records the exact
make/type query, count, original approval IDs, source rows and example templates
for every target. This measures catalogue presence, not VIN decoding accuracy,
unique identification or coverage of every generation and year.

The seven queries without approval hits are Tesla Model Y, Škoda Elroq, CUPRA
Terramar, Volkswagen ID.7, Audi Q6, Volkswagen Transporter and Volkswagen Tayron.
Model Y already has separate scoped OEM decoding for reviewed Berlin/Shanghai
layouts. The Transporter query deliberately does not equate T-series, Caravelle
and Multivan labels without further review. Other gaps may reflect naming,
excluded templates or the dated source. They are visible rather than filled with
guessed rules.

Recheck all counts and 279 cited examples offline:

```sh
python tools/europe_coverage.py
```

This audit also runs through `tools/provenance.py` and `tools/dataset.py` in CI.

## What remains unknown

ASTRA does not publish complete individual VINs in these open data. Approval dates
are not model years or production dates. Manufacturer identity/address does not
establish the assembly factory. A template may cover several engines or bodies;
remarks can further restrict a configuration. The importer therefore preserves
alternatives and does not manufacture precise answers from catalogue data.

The first projection accepts only complete 17-position masks with a literal WMI
and at least one further fixed position. Dots are unknown positions. Explicit
spaced slash alternatives must all pass. It excludes 5,942 passenger rows with
unreviewed/malformed/too-broad syntax and 82,458 non-passenger rows. It does not
repair O/0, pad short prefixes or discard an invalid alternative silently. All
excluded rows remain in the archived source for subsequent work.

The [ASTRA review](research/astra-review.md) documents the official placeholder
schema, reuse basis, exact source digests and independent partial BYD check.
Existing [50-make research](research/vin-rules/README.md) and forum/community
leads remain available. A public forum table is not automatically a globally
applicable rule; new facts still need explicit market/year/layout boundaries.

## Validation data

The [Washington EV benchmark](../validation/wa-ev/README.md) provides 18,376
public masked VIN-prefix label groups across 51 makes. In the recorded run,
make coverage is 99.510%; model/year coverage is 93.572% each, with 100% exact
agreement among results the decoder resolves. No model aliases were applied.

This is an **observational US EV regression benchmark**, not independent European
ground truth: the source labels themselves are VIN-decoded. Only ten VIN
characters are public; three explicitly synthetic continuations check agreement
but cannot establish the real plant or every possible continuation. Two prefixes
requiring extended-WMI characters are excluded. Abstentions and per-make gaps
remain in the report. The source and results carry separate ODbL attribution and
are outside the production dataset/packages.

European validation is still limited. The independent BYD memorandum corroborates
a partial prefix/model/type-approval relationship; it is not a general labelled
VIN test set. The provenance manifests distinguish this from synthetic parser
specimens and source-correlated NHTSA comparison responses.

## Reproduction and provenance

`tools/astra.py --compile` reconstructs the projection from the pinned original
archive. `tools/astra.py` independently compares that reconstruction with the
shipped projection. `tools/dataset.py` runs this alongside the NHTSA/KBA checks.
Original and compressed-source SHA-256 values are recorded. Runtime loaders
verify the index and every accessed WMI shard; Java/Python parity tests compare
the complete candidate results. See [source audit](provenance-audit.md) and
[dataset terms](../data/LICENSE.md).
