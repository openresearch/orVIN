# Compiled runtime format 1

This internal format is shared by Python, Java and .NET. It is versioned separately
from public JSON. Its authoring inputs and compiler live in the repository; installed
libraries need only the resulting bundle. Adding supported rules is a data change.

## Build and integrity

```
python tools/identity.py --generate
python tools/compile_dataset.py --generate
python tools/dataset.py
```

Fetch/update source snapshots separately through reviewed source adapters. The last
command reconstructs all source projections and checks the exact runtime bytes.
Generation sorts records, uses UTF-8/LF, retains deterministic compressed shards and
contains no build timestamp. Repeating it from identical inputs changes nothing.

`manifest.tsv` contains tab-separated records:

| Tag | Remaining cells |
| --- | --- |
| `V` | `orvin-runtime-1`, comma-separated required capabilities |
| `P` | decision-policy version |
| `C` | compiler path, compiler SHA-256 |
| `I` | repository input path, SHA-256 |
| `F` | bundle-relative file path, SHA-256 |

Runtimes reject unsupported versions/capabilities and verify resources when loaded.
Shards are lazy and caches bounded. Package checks verify the complete inventory,
including notices, and reject additional original archives or fixtures. Source record
paths refer to repository evidence when that original is intentionally not packaged.

## Tables and operations

The logical bundle has several indexed tables; there is no row per possible VIN.

- `dataset.tsv`: common `V/S/M/A` version, source, manufacturer and constrained WMI
  assignment records. Both ordinary and extended WMIs retain exact associations.
- `identity/index.tsv`: exact make/model aliases, canonical IDs, display names and
  source/locator references. Missing aliases remain unmapped. This is not fuzzy matching.
- `kba/types.tsv`: exact type-code rows; leading zeros, null markers and counts survive.
- `astra/index.tsv` and `astra/patterns/`: field definitions, source records and
  correlated approval masks. A dot matches one VIN character. Remarks belong to rows.
- `decoding/index.tsv` and 256 pattern shards: field definitions, schema intervals,
  compiled patterns/captures, literal values, relational joins and decimal conversions.
  Source-specific numeric identifiers remain lineage keys. The profile defines which
  fields participate in operations; engine code does not hard-code those identifiers.
- `policy.tsv`: flattened JSON policy. Dotted paths and `.length` describe arrays;
  each row is path, scalar type (`S`, `I`, `B`), value. String values are base64 UTF-8.
- `rules.tsv`: generic whole-VIN conditional literal groups, described below.
  KBA SV 3.1 rows compile here as distinct manufacturer-directory fields; their
  page/row lineage and correlated alternatives survive. `kba-wmi/metadata.json`
  carries the original PDF digest and full reuse assessment. Neither the PDF nor
  its authoring row snapshot is packaged. See [KBA WMI data](kba-wmi-data.md).

Pattern matching uses the same limited character-class/repetition language across
engines. Input normalization trims ASCII spaces and uppercases ASCII letters only.
17-character alphabet validation does not authenticate a VIN. Source-internal ranking
preserves priority, timestamp descending/null-first, shortest non-star key, key text and
insertion ID. That ordering never ranks independent source claims against one another.
Decimal conversions use the profile scale and half-away-from-zero rounding; conversions
do not chain already-rounded values. Year codes retain all applicable cycles, including
missing alternatives. Model year, calendar production year and approval date are distinct.

## Conditional literal rules

Author new reviewed rules in `data/rules/*.json` with `format: "orvin-literals-1"`.
The schema rejects unknown attributes. Every emitted field must cite a registered
source and use a known field code. New sources still require the provenance and rights
review in `AGENTS.md`; a valid rule is not permission to use an unreviewed source.

Every cell after the tag in `rules.tsv` is base64 UTF-8:

| Tag | Cells |
| --- | --- |
| `R` | ID, whole-VIN pattern, excluded pattern or empty, scope label, comma-separated countries or empty, model-year constraint or empty, stage, warning, conflict warning |
| `F` | group ID, zero-based condition position (`-1` means unconditional), accepted characters, field code, literal value, source ID, evidence kind, rule ID, source key/locator |

Patterns allow VIN literals, `.`, character classes and bounded `{n}` repeats. There
are no scripts or expressions. Each group yields a correlated alternative; all matching
groups are evaluated. Existing Tesla and Golf input formats are translated by the
compiler only; runtimes have no make-specific dispatch.

## Selection invariants

An applicable field claim (including unresolved competing claims) blocks foreign
fallback for that field. Agreeing supported claims resolve; differing applicable values
remain ambiguous. If only foreign claims exist, agreement can supply a suggestion,
with requested/source market and attribution. Differing foreign values remain ambiguous.
Supplying a country never turns another country's rules into applicable facts.

An applicable year contradiction blocks model/year fallback and preserves alternatives.
A foreign rule with a contradictory supplied year cannot serve as the fallback. A
compatible WMI may establish the marque. Exact catalogue consensus remains conditional;
missing mappings and different model identities prevent resolution. No row-count voting
or first-match selection is used. Foreign technical claims stay in evidence, not the
resolved specification object. These generic invariants are implemented in each engine;
reviewed factual tables, scope, aliases, profile parameters and messages are compiled once.

## Compatibility and validation

Public entry points and short/long structure remain compatible. The policy version is
`vehicle-identity-v2`; decoding bundle hashes change because the generated index excludes
legacy OEM opcodes. Explicit foreign markets now expose conditional evidence instead of
`OUT_OF_SCOPE`. The raw source catalogue can contain additional sources because
all matching paths are evaluated; verify evidence references rather than a fixed catalogue
length. Short output still credits its selected evidence. Do not compare provenance
hashes across versions as if they were facts.

The test suite checks independent sourced examples, synthetic data-only rules with JP/BR/NZ
scope, duplicate/order invariance, conflicts, unsupported programs, near misses and source
references. Full parity separately compares complete JSON, including evidence IDs and
attribution. Parity establishes implementation agreement, not real-world truth or licensing.
