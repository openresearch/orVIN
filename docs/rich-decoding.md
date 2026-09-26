# Rich offline decoding (development version after v0.1.0)

Swiss type-approval matching is a separate, additive `typeApprovals` result in both
libraries. Its catalogue candidates preserve original configurations and never
become established VIN facts. See [European coverage](european-coverage.md) for the
100-model audit, source scope and validation limitations.

Both libraries use the same source-derived pattern index and native matching logic.
No online VIN request, database server, SQL execution or Java subprocess is involved.
The first release's WMI/KBA interfaces remain, with additive vehicle details.

## Examples and API

These are synthetic configurations, not customer vehicle identifiers:

```sh
./vin.sh 1HGCM82603A000000 --market US
./vin.sh 1C4RJFBG0FC000000 --market US --json
./vin.sh XP7YGAEK0TB000001 --market DE
```

The first returns Accord, 2003 model year, Marysville/Ohio/USA, J30A4 engine,
gasoline, coupe, EX-V6 and other sourced fields. The second resolves the shared
seven-make WMI to Jeep / Grand Cherokee. The third returns Model Y, Berlin/Germany,
electric powertrain and **2026 production year**, without inventing a model year.

Python: `result["details"]["fields"]["PlantCity"]`.
Java: `result.details().field("PlantCity")` for a resolution, or
`result.details().fields().get("PlantCity")` for the label and evidence.
`model`, `modelYear` and `assemblyCountry` are convenience resolutions on the
VIN result. Attribute values are strings, including numbers; absent values are
`None` / `Optional.empty()`. Numeric conversions round to six decimal places.

Each result includes `details.sources`: complete source records with publisher, title,
edition, exact locator, review date, reuse basis and available archive/inspection hashes.
`evidencePath` identifies the bundled metadata with scope and any missing-hash explanation.

Each field includes status, possible values and evidence identifying the source
URL, original element/attribute IDs, rule/schema IDs and matched key. `PATTERN`
and `NUMERIC_PATTERN` describe direct pattern matches; `MODEL_MAKE`, `ENGINE_MODEL`
and `UNIT_CONVERSION` identify associated or derived facts. `OEM_RULE` identifies
the separately curated manufacturer rules. Local element IDs 10001–10003 describe
production year, battery chemistry and motor configuration; these are not NHTSA IDs.

The original top-level `status` and `candidates` describe WMI lookup. A known
decoded make overrides the brand resolution, while original WMI associations
remain auditable. `details.status` independently describes rich decoding:

| Status | Meaning |
| --- | --- |
| `DECODED` | At least one vehicle rule matched; inspect each field's status |
| `NEEDS_CONTEXT` | Matches exist under a market assumption that was not established |
| `UNKNOWN` | No supported match/year interpretation |
| `OUT_OF_SCOPE` | Explicit non-US market with no applicable OEM extension |
| `CONTEXT_CONFLICT` | Supplied model year conflicts with the supported year code/scheme |
| `INVALID_INPUT` | Rich decoding requires 17 permitted VIN characters |
| `UNAVAILABLE` | A custom WMI-only decoder has no attached rich dataset |

These statuses do not certify authenticity, a correct check digit or registration.
A plant pattern can match without a model pattern: that is a partial result, not
evidence that the whole VIN is valid. Unknown fields are absent from `fields`;
the Java `field(code)` helper and top-level convenience resolutions return UNKNOWN.

## Market and year scope

NHTSA reporting scope is US sale/import/use. An absent market retains conditional
possibilities with `NEEDS_CONTEXT`; it does not infer market from the WMI, factory
or check digit. `Context(market="US")` establishes that scope only when the caller
independently knows it. A German market does not use these US rules.

Automatic year candidates use the source snapshot year (2026), with the published
two-year horizon and the scoped light-vehicle position-seven discriminator.
The same package gives the same answer next year. A supplied model year selects
its cycle only if compatible with the position-ten code. Uncertain cycles remain
separate alternatives, including a cycle for which no pattern exists. Missing
data in one alternative cannot establish a value found only in another. Do not
combine fields from different alternatives into an invented configuration.

Tesla's [Model Y 2025+ service manual](https://service.tesla.com/docs/ModelY/ServiceManual/2025/en-au/air/GUID-BB4CE449-3F8E-4905-AF4A-96DFA87535B5.html)
provides the limited European extension: XP7/B Berlin and LRW/C Shanghai, model
code Y, the reviewed configuration alphabet, and only listed year codes S/T/V.
For those layouts position ten means calendar production year. A caller's model
year is not substituted for it. The rules do not extrapolate to earlier vehicles,
other Tesla models, unlisted plants or new codes. Serial zero is outside the
manual's documented production-sequence range. The selected associations and
scope are reviewed in `data/europe/tesla-model-y.json`.

European Golf rules match only `WVWZZZ1KZ5P` or `WVWZZZ1KZ5W` plus six digits.
They return Golf, V (Typ 1K), model year 2005 and Mosel/Wolfsburg. They combine the
Volkswagen Golf maintenance manual (11.2009, section 3.5.4, printed page 35), the
Golf V historical profile, and only the year/plant columns of the June 2005 VIN
chart. The two historical manuals are Volkswagen-authored documents hosted on
third-party mirrors. The chart's North American 1K=Jetta rule is explicitly excluded.
`OEM_RULE_COMBINATION` identifies this bounded synthesis; each field links to its
relevant documents in `data/europe/vw-golf-1k-2005.json`. No engine, trim, exact
build date or assembly country is asserted by this extension.

## Implemented NHTSA stages

The pinned source contains 1,678,690 pattern rows. The projection exports 1,343,387;
335,302 are excluded by private/undecoded element, special element or QC schema
filters, and one lacks a resolvable value. Every source row is accounted for in
`data/decoding/metadata.json`; all rows remain in the original source ZIP.

Patterns match positions 4–8, `|`, then positions 10–17. Stars consume one
character; classes/ranges and SQL LIKE underscore/percent semantics are compiled
into a shared regex subset. Numeric `#` rules capture the relevant digits.
Schema applicability uses WMI and inclusive model-year bounds. Precedence follows
the inspected core stage: year priority descending, effective timestamp descending
(null first), length without stars ascending, bracket-stripped key ascending, then
source ID ascending. Note fields retain multiple values. Source updates determine
precedence; shorter patterns are not automatically less authoritative.

Engine-model associations have lower priority. Model patterns can identify a make
more precisely than WMI alone. Displacement conversions supply missing units from
original facts, never a chain of rounded results. These are source-derived facts,
not a claim that every returned value occupies its own VIN character.

## Deliberate limits

This is **not full vPIC parity**. The vehicle-spec enrichment stage, default values,
validation-character caches, correction suggestions, check-digit validation and
upstream error/scoring/year-selection passes are not implemented. No defaults are
presented as measured equipment. Exact build date, complete options, paint, mileage,
history and VIN-to-HSN/TSN are not inferred. Source mistakes remain possible; the
library reports sourced interpretations, not certified OEM build records.

The 50-make research is a source survey, not a coverage guarantee. Most European
extensions still need applicable evidence. The narrow Golf exception below does not
extend to other Volkswagen types or model years.

## Rebuild and verification

`python3 tools/decoding.py import` regenerates all shards and the index offline.
`tools/dataset.py` reconstructs the entire projection and checks exact file hashes;
`--update-runtime` intentionally updates Java's pinned index digest. Public pattern
values keep source IDs and Unicode through base64-encoded UTF-8 cells.

Independent fixtures use retained public NHTSA partial-VIN responses and reviewed
Tesla/Volkswagen document associations;
synthetic full identifiers never query an individual vehicle. Tests cover numeric
captures, bracket plants, conflicting contexts, unresolved cycles, manufacturer
ambiguity, source provenance, immutable/fresh results and concurrency. The parity
runner compares complete Python/Java outputs from the packaged JAR. Package checks
verify every shared data file and installed-wheel behavior outside the checkout.
