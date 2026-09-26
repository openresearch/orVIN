# Normalized answers and JSON output

Available in ORvin 0.2.0 and later. All libraries resolve one identity and expose
two views:

- Short: `schemaVersion`, normalized `vin` (or string `hsn`/`tsn`), `inputStatus`,
  `vehicle`, `fieldStatus`, `assumptions`, and self-contained `sources` credits.
- Long: exactly the short object, extended with `details`. Removing `details`
  produces the short object without recomputing any decision.

## Commands

```sh
./vin.sh WVWZZZ1KZ5P000001
./vin.sh WVWZZZ1KZ5P000001 --json
./vin.sh WVWZZZ1KZ5P000001 --json --long
./vin.sh WVWZZZ1KZ5P000001 --long --json
./vin.sh WVWZZZ1KZ5P000001 --json=long
./hsntsn.sh 0603 BMT --json
./hsntsn.sh 0603 BMT --json --long
```

The VIN above is synthetic. Default output, `--json` and `--json=short` are
identical. `--long`, `--json --long` and `--json=long` choose the extended view.
Contradictory explicit selectors such as `--json=short --long` are usage errors.
The shell scripts only forward to the Python CLI; no Java or compilation is used.
The CLI selects serialization; the library owns validation, normalization and decisions.

**CLI migration:** default output is now short JSON instead of readable text, and
bare `--json` selects normalized short JSON instead of the old raw result. Use
`--long` for the evidence view. Existing raw Python `decode`/`lookup` and Java
`decode`/`lookup` methods remain available. No lookup changes the source labels in
those raw results. Invalid VIN characters now produce exit code 2 as well as an
explicit invalid-input status, even if the WMI alone is recognized.

## Library APIs

```python
from orvin import Context, HsnTsnLookup, VinDecoder

answer = VinDecoder.bundled().decode_vehicle("WVWZZZ1KZ5P000001", Context(market="AT"))
assert answer.vehicle["make"] == "VW"
assert answer.vehicle["model"] == "Golf"
assert answer.vehicle["modelYear"] == 2005
short = answer.short()
long = answer.long()
assert {k: v for k, v in long.items() if k != "details"} == short

german_type = HsnTsnLookup.bundled().lookup_vehicle("0603", "BMT")
assert german_type.vehicle["model"] == "Golf Sportsvan"
```

```java
var answer = VinDecoder.bundled().decodeVehicle("WVWZZZ1KZ5P000001");
System.out.println(answer.vehicle().make().orElse(null)); // VW
System.out.println(answer.vehicle().modelYear().orElse(null)); // 2005
String shortJson = answer.toShortJson();
String longJson = answer.toLongJson();
var shortValues = answer.shortResult();
var longValues = answer.longResult();
var germanType = HsnTsnLookup.bundled().lookupVehicle("0603", "BMT");
```

Python projections are independent dictionaries. Java projections are deeply
immutable JSON-compatible maps/lists, with typed optional accessors for identity.
There are no new runtime dependencies. Numeric identity years are JSON integers;
unknown properties are null. Original technical values remain source strings in
long evidence and specifications, with datatype/variable metadata preserved.

C# (.NET 8+, next release):

```csharp
using OpenResearch.ORvin;
var answer = VinDecoder.Bundled().DecodeVehicle("WVWZZZ1KZ5P000001", new Context(market: "AT"));
var shortJson = answer.Short(); // System.Text.Json.Nodes.JsonObject
var longJson = answer.Long();
var germanType = HsnTsnLookup.Bundled().LookupVehicle("0603", "BMT");
```

C# projections are fresh JSON objects; modifying one does not alter cached data.
The library market remains optional. The web application requires a country choice
for VINs and may prefill an explicit browser locale region. This is editable context,
not evidence of original sales specification or geolocation.

## Interpretation and limits

`RESOLVED` identifies a field supported by applicable evidence. `SUGGESTED` is a
useful conditional answer whose assumptions remain in short output. `PROVIDED`
marks independently supplied year context. `AMBIGUOUS`, `CONFLICT` and `UNKNOWN`
keep null primary values. Model year is never replaced by production year or an
approval/reference date. A legal manufacturer remains separate from the marque.

The shared catalogue contains 12,447 exact make-label bindings and 32,010
make-scoped model-label bindings, generated from retained NHTSA/ASTRA sources
with narrowly specified OEM/KBA aliases. These are catalogue entries, not counts
of VIN-decodable models. Names such as Volkswagen/VW use one canonical identity.
No fuzzy matching, generic prefix stripping or corporate-group merging is used.
Unmapped engine/trim-bearing Swiss type labels and compound KBA model labels
remain unknown until separately reviewed family mappings are added.

Applicable direct VIN facts take priority over broad catalogue candidates.
A compatible WMI assignment can resolve the make; US-only model/year evidence
with unknown market stays suggested. In the next release, any market may supply a
fallback when applicable evidence has no answer. For example, US evidence with
requested market NZ remains `SUGGESTED`, with `CROSS_MARKET_MATCH`,
`requestedMarket: "NZ"`, `sourceMarkets: ["US"]` and an explicit applicability
message. This applies to all country pairs, not only AT/DE or US evidence.
Applicable answers and conflicts block weaker foreign suggestions. Foreign
technical fields are retained in evidence, never promoted to established specifications.
Conflicting independently supplied context is not hidden by a catalogue fallback. Competing conditional model identities stay ambiguous, and their
incompatible year/configuration claims are not mixed into one vehicle.

Swiss exact-label consensus currently supplies suggestions. A later reviewed,
scoped identifying rule may resolve specific fields; no ASTRA identity rules are
promoted by this change. The raw approval API still returns candidates and keeps
all engine/trim alternatives with their approval-specific remarks.

Long `details` contains:

| Property | Meaning |
| --- | --- |
| `meta` | Resolver policy and dataset versions/hashes |
| `input` | Original input and independently supplied context |
| `decisions` | Per-primary-field reason codes and evidence/mapping references |
| `specifications` | Additional known scoped decoder facts; original values and datatypes |
| `alternatives` | Correlated VIN configurations referring to evidence IDs |
| `evidence` | Each fact, WMI association, KBA row and matching approval once |
| `provenance` | Used rule locators, normalization bindings, variable definitions, source details and additional source credits |
| `diagnostics` | Source status, market scope, decoding stages, warnings and approval counts |

Long output is intentionally complete and can be large for broad masks. It never
silently truncates approval records. Source metadata is deduplicated by ID; the
common `sources` list is unchanged and detail-only credits appear in
`details.provenance.additionalSources`. Credits retain original publisher, URL,
edition, reuse basis, terms and transformation notice. Applicable data/document
terms are not replaced by the code license.

## Reproducibility and owner-contributed fixture

`tools/identity.py --generate` rebuilds `data/identity/index.tsv` from the retained
snapshots. The ordinary offline dataset validator checks its hash and exact
reconstruction, including per-binding source IDs/locators. All artifacts include
the same compiled index and provenance. Do not hand-edit the generated index.

[The contributed fixture](../data/identity/fixtures.json) is attributed as
**User-contributed Golf 5 from Austria.** The owner explicitly authorized its VIN
in repository tests on 2026-09-26. Golf 5 and Austria are owner-reported; model year
2005 is a documented-rule expectation, not independent owner confirmation.
The fixture is never a VIN-specific decoding override and was not sent to an
external service. The decoder still uses the general scoped Golf rule.
