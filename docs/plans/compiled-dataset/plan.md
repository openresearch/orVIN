# Compiled dataset and generic runtimes

Status: proposed; implementation has not started. Based on `main` at `b2b8ac8`,
reviewed on 2026-09-26.

## Objective

Make ORvin's vehicle knowledge live in reviewed data and build tooling. Python and
Java should execute the same generated dataset through small, generic evaluators.
Adding a make, model, alias or rule expressible by the supported operations should
require no library source changes. New operations still require an explicit format
and engine change in both languages.

Keep the existing offline packages, complete bundled dataset, public APIs, source
attribution, and short/long answer contract. This work does not itself add coverage.

## What exists today

| Area | Current implementation | Gap |
| --- | --- | --- |
| Acquisition | `tools/nhtsa.py`, `tools/kba.py`, `tools/astra.py`, `tools/refresh_data.py` fetch or import pinned inputs. | Keep source-specific acquisition in tooling. |
| Compilation | `tools/decoding.py` resolves dictionaries and generates pattern shards; `tools/astra.py` compiles masks; `tools/identity.py` builds aliases. | Generated formats still reflect separate providers and OEM layouts. |
| Runtime decoding | Python `details.py` and Java `RichDecoder.java` interpret compiled patterns. | Both also implement Tesla/Golf paths, US year-cycle rules, source ranking, joins and conversion policy. |
| Identity resolution | Python `answer.py` and Java `AnswerBuilder.java` choose normalized fields and construct explanations. | Source arbitration, fallback rules and status policy are independently coded twice. |
| Packaging | Both artifacts embed all of `data/`; parity and byte-for-byte packaging checks exist. | WMI loading also uses a Java-only TSV projection; there is no single runtime contract for all inputs. |

Concrete examples:

- [`details.py`](../../../libs/python/orvin/details.py) contains `_europe`, `_oem`,
  `_years` and `_pass`; [`RichDecoder.java`](../../../libs/java/src/main/java/com/openresearch/orvin/RichDecoder.java)
  repeats these operations. Tesla sequence validation and Golf-specific stage and
  warning strings are runtime code, even though their factual mappings are data.
- Those decoders return the first matching OEM path before evaluating other paths.
  This is a policy choice hidden in control flow and can conceal overlapping claims
  when coverage grows. Changing it needs a reviewed behavior change, not an unnoticed
  side effect of moving files.
- [`answer.py`](../../../libs/python/orvin/answer.py) and
  [`AnswerBuilder.java`](../../../libs/java/src/main/java/com/openresearch/orvin/AnswerBuilder.java)
  separately implement WMI fallback, US assumptions, Swiss catalogue consensus,
  context conflicts and make/model/year consistency.
- [`tools/identity.py`](../../../tools/identity.py) already moves normalization to
  build time, but reviewed display preferences and explicit aliases are Python
  constants rather than separately reviewable policy and mapping records.

The current design is partly compiled and data-driven, but the libraries are not
yet generic consumers of one normalized rule contract.

## Target flow

```mermaid
flowchart TD
    A[Pinned NHTSA, KBA and ASTRA snapshots] --> C[Source adapters and dataset compiler]
    B[Reviewed rules, identities and decision policy] --> C
    C --> D[Versioned normalized runtime bundle]
    D --> P[Generic Python evaluator]
    D --> J[Generic Java evaluator]
    P --> O[Normalized answer with evidence]
    J --> O
```

Fetching is explicit and separate from compilation. Compilation and ordinary builds
work offline from pinned inputs. The runtime reads only the compiled bundle for
decisions; retained originals remain bundled for inspection and traceability.

One normalized dataset means one logical contract, not one enormous JSON file or
one table that conflates VIN facts, WMI assignments, HSN/TSN types and approvals.

## Dataset contract

Use JSON plus schemas for human-authored rules and policy. Compile to deterministic,
indexed UTF-8 tables and compressed shards, retaining the existing dependency-free
runtime approach. Both languages read identical compiled bytes, including WMI data.
Introduce `data/generated/` incrementally; do not relocate every existing source
snapshot as part of the first migration.

The bundle should contain:

- **Manifest:** format, dataset and decision-policy versions; required engine
  capabilities; compiler identity, input hashes and hashes for every runtime file.
  Unsupported formats or operations fail clearly during loading.
- **Identities and fields:** stable make/model IDs, reviewed display names, typed
  fields, units and explicit mapping outcomes. Canonicalize static values at build
  time. Preserve original labels and unmapped records; missing mappings must not
  disappear from consensus checks.
- **Matching rules:** VIN predicates, ordinary/extended WMI keys, exact HSN/TSN
  keys, scope constraints, year-code tables, capture positions and lookup tables.
  Include whether missing context makes a rule conditional and whether supplied
  context excludes it or creates a contradiction.
- **Claims and alternatives:** values or bounded extraction/derivation operations,
  evidence kind, configuration/group IDs and parent references. Keep catalogue
  candidates distinct from identifying evidence and keep their specifications
  correlated; a shared VIN mask does not make all engines true for one car.
- **Selection metadata:** source-internal order and cardinality, explicit reviewed
  supersession, evidence roles and the decision table for statuses, assumptions
  and fallback. Do not use one numeric source score or let import order pick a winner.
- **Provenance:** field-to-rule-to-source lineage, precise upstream locators,
  snapshot hashes, editions, reuse assessments, required credits and notices.
  Store explanatory reason codes/messages with the policy or rule they explain.

Separate upstream selection semantics (such as NHTSA's ordering of matching
patterns) from ORvin's cross-source resolution. Preserve the former while reviewing
changes to the latter explicitly. A US-scoped rule and an approval catalogue are
different evidence roles, not universally higher/lower ranked providers.

## What remains in a library

A library validates input, verifies/loads indexed data, evaluates applicable rules,
retains compatible alternatives, applies the shared decision policy and serializes
the answer. It also handles caching, immutable/fresh results and language bindings.

Use a small, specified set of operations: exact lookup, bounded position/pattern
matching, context constraints, table-driven year alternatives, literal/captured
values, relational lookup, decimal scaling, grouping, selection and consensus.
Define character normalization, match boundaries, nulls, ordering, decimal precision
and rounding once in the format specification. Source wildcard syntax must be
translated by the compiler into the common representation.

This is a constrained evaluator, not a general programming language. No embedded
Python, Java, SQL or arbitrary expressions. Generic evaluation code exists twice;
vehicle facts, provider interpretation and reviewed policy are authored once.

It is neither practical nor correct to precompute one row per possible VIN. Matching
and decisions depend on the queried VIN, optional market/year context and competing
claims. The compiler can precompute aliases, joins, lookup values and static ordering;
the runtime must still evaluate query-dependent conditions and captures.

## Implementation sequence

1. **Specify the contract and establish the baseline.** Inventory existing runtime
   decisions; distinguish generic mechanics, source semantics and ORvin policy.
   Specify the minimal operations against actual existing inputs. Record behavior,
   package size, cold-start time and warm-query performance. Keep independent
   sourced fixtures as the correctness authority; old output is a regression aid.
2. **Compile an OEM vertical slice.** Add the manifest/schema and compiler entry
   point, move reviewed aliases/display preferences to declarative inputs, and
   express the existing Golf and Tesla rules in the common format. Implement the
   necessary generic evaluator in both languages. Verify the same existing answers
   and provenance with no Golf/Tesla-specific runtime branches. Keep other paths
   on their existing implementation temporarily.
3. **Migrate exact lookups and approval candidates.** Compile WMI and KBA indices,
   then ASTRA masks, normalized labels and correlated approval records. Retain
   leading zeros, missing mappings, original remarks and every relevant candidate.
   Remove language-specific WMI projection as the new common reader takes over.
4. **Migrate NHTSA semantics.** Compile schema applicability, public patterns,
   multi-value fields, year schemes, engine/model relations, source-internal
   precedence and conversions into the same contract. Precompute what is static;
   preserve query-dependent conditions, source lineage and conditional US scope.
   Avoid expanding every rule across all VINs or years just to simplify the engine.
5. **Unify resolution and public projections.** Feed all applicable claims into the
   generic resolver using the versioned policy. Remove source-specific fallback
   branches and early-return dispatch. Review every newly exposed overlap or changed
   result; do not force old behavior where it concealed conflicts. Preserve API
   shapes and raw access through compatibility projections. Any intentional public
   behavior/provenance-ID changes need migration notes and appropriate versioning.
6. **Switch validation, packaging and refreshes.** Rebuild the complete compiled
   bundle from pinned inputs and reject stale output. Check all source/field
   references, installed artifacts and language parity. Update release manifests,
   provenance inventories and refresh output allowlists. Delete superseded runtime
   paths after migration checks pass, avoiding two permanent decoder systems.

Each step should be a reviewable change. Do not add the pending BMW/Subaru coverage
inside the architectural migration; that would obscure whether changed answers
come from new evidence or a different evaluator.

## Acceptance and release boundaries

- An additional rule using existing operations changes only reviewed input data,
  fixtures and generated output, with no Python/Java runtime edits. A controlled
  synthetic example demonstrates this rather than relying only on a code search.
- Runtime decisions do not branch on manufacturer names, provider names, source
  IDs or source-specific numeric field IDs. Original source identifiers remain
  available as evidence and in compatibility projections.
- Compare old/new results and Python/Java results separately. Exercise positive,
  near-miss, missing-context, year-cycle, overlap, conflicting-context and partially
  mapped catalogue cases. Input/rule reordering and duplicate rows must not change
  selected identity merely by changing order or apparent vote counts.
- Review changed behavior against independently sourced expected facts; parity
  cannot prove that the shared compiler is correct. Never regenerate expected
  fixtures solely from the new implementation.
- Short/long JSON retain their exact relationship: long is short plus `details`.
  Both preserve required attribution; all evidence references resolve. Model year,
  production year and approval dates remain distinct.
- JAR and wheel embed the identical complete dataset, including retained raw
  snapshots and notices. Lookup performs no network access or raw-source parsing.
- Demonstrate deterministic rebuilds, bounded loading, and acceptable size/startup/
  query performance against the recorded baseline before replacing the old paths.
- Daily structured-data refreshes may update generated output only through the
  reviewed compiler and existing gates. New rules, policy, operations, sources or
  license assessments remain manual changes. Expanding the output allowlist must
  not authorize edits to curated inputs or expected fixtures.

Recommended first implementation: steps 1 and 2. The existing Golf and Tesla rules
are a small, concrete demonstration of data-only vehicle knowledge before tackling
the much larger NHTSA compiler.
