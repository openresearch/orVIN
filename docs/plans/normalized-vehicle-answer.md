# Normalized vehicle answer

Design and implementation record, 2026-09-26. Requested by the user: one suggested make, model and
year as the primary library result; consistent names across US, Swiss and custom
sources. In particular, use **VW** as the canonical display name for Volkswagen.
The first implementation is now present in both libraries and scripts; see
[the implemented contract](../normalized-output.md). The detailed design below also
records later expansion work and must not be read as a claim of universal coverage.

## Implementation status

- Implemented: shared hash-pinned exact-label catalogue, canonical VW identity,
  normalized `vehicle`, statuses, assumptions and field-linked source credits.
- Implemented: Python `decode_vehicle` / `lookup_vehicle`, Java `decodeVehicle` /
  `lookupVehicle`, short/long projections, typed Java identity and JSON serialization.
- Implemented: dumb shell wrappers with short JSON default, all agreed `--json` /
  `--long` combinations, and full long evidence indexed once by stable IDs.
- Implemented: conflict preservation, separate production/model years, conservative
  exact Swiss consensus, unchanged raw library APIs, owner-authorized Golf fixture.
- Remaining coverage work: broader reviewed model-family aliases, ASTRA identifying
  rule promotion, and a generalized multi-rule adapter replacing rich-decoder early
  returns before adding overlapping scoped rule families. No new Swiss pattern has
  been promoted to RESOLVED by these output changes.
- Specifications currently preserve additional known scoped facts with source
  variable names, datatypes and original string values; a fully normalized numeric
  engine/body/unit vocabulary remains separate follow-up work.

The CLI migration is intentional: bare `--json` now means the new short view.
The regression that originally exposed the old giant output is covered by a real
script invocation. Both formats retain credits, and long-minus-details equals short.

## Current problem, verified in the code

`libs/python/orvin/lookup.py` and Java `VinDecoder` currently expose source-level
results with a few convenience fields:

- `brand` uses a known rich-decoder make, otherwise WMI associations.
- `model` and `modelYear` use only `details`. Swiss approval candidates never
  contribute to these fields.
- `details` tries custom Golf rules, then Tesla rules, then US-scoped NHTSA
  decoding. These are early returns, not a general cross-source decision policy.
- `typeApprovals` independently returns Swiss candidates with original labels.
  There is no common make/model catalogue or cross-source identity resolver.

Observed with synthetic specimens in the current checkout:

| Specimen | Current primary result | Evidence currently left to callers |
| --- | --- | --- |
| Golf 2005 / European layout | VOLKSWAGEN, Golf, 2005 | 411 Swiss approval candidates use make VW and numerous Golf type/engine labels |
| Octavia / TMB…5E layout | Make, model and year unknown | 910 Swiss approval candidates, make SKODA and many Octavia variants |
| VSS…5F layout | Make/model unknown | 1,238 Swiss candidates include SEAT/CUPRA and multiple model families |
| US Accord example, US context supplied | HONDA, Accord, 2003 | Direct NHTSA evidence |
| Same Accord without market context | Make known; model/year only conditional possibilities | The missing assumption is US reporting scope |
| Reviewed European Tesla Model Y | TESLA, Model Y; model year unknown | Custom rule provides production year 2026, which is not model year |

The application should not implement joins, name mappings, source precedence or
model-family parsing to display a vehicle. That belongs in orVIN.

## Proposed public contract

Add a primary `vehicle` answer with simple nullable values, identical in Python
and Java. Keep raw evidence and a separate explanation of the decision.

```json
{
  "vehicle": {
    "makeId": "vw",
    "make": "VW",
    "modelId": "vw:golf",
    "model": "Golf",
    "modelYear": 2005,
    "productionYear": null
  }
}
```

This is the identity fragment, not a complete response. Short output adds status,
assumptions and attribution; long output adds one `details` object containing the
explanation and evidence. Field decisions retain source/rule/approval references,
normalization rule IDs, rejected/conflicting claims and alternatives there. The
primary fields have at most one value; applications do not choose among sources.

Python usage: `result["vehicle"]["make"]`. Java: `result.vehicle().make()` using
`Optional<String>`; years use `Optional<Integer>`. IDs are stable application keys;
display names may receive reviewed spelling changes without changing identity.

Per-field statuses:

| Status | Primary value | Meaning |
| --- | --- | --- |
| RESOLVED | One value | An applicable reviewed rule or established assignment determines this field without an unresolved material assumption; this may include an ASTRA-derived rule |
| SUGGESTED | One value | Catalogue consensus without a validated identifying rule, or a conditional rule, supports a recommendation; the remaining assumptions are explicit |
| PROVIDED | One value | Independently supplied caller context, compatible with evidence; not claimed as VIN-derived |
| AMBIGUOUS | null | Several equally admissible values remain |
| CONFLICT | null for the affected field | Applicable authoritative claims or caller context contradict each other |
| UNKNOWN | null | No usable evidence, or normalization has not established the identity |

Do not add fabricated probability percentages. A consumer may display the simple
answer by default and inspect statuses when deciding whether to require confirmation.
The library's default policy is fixed and versioned; no caller-defined source-weight
framework is needed for this first implementation.

`make` is the commercial marque. `manufacturer` remains the separate legal entity:
VW and VOLKSWAGEN AG are different kinds of information. Do not replace company
identities with brand aliases or equate every brand owned by one corporate group.

## Swiss evidence: resolve fields according to their support

There is **no blanket SUGGESTED ceiling for ASTRA**. Source origin, decoding method
and resolution status are separate concepts. NHTSA, ASTRA and OEM evidence are
assessed under the same field-level applicability and conflict rules.

The current ASTRA importer matches approval VIN masks and returns candidates. The
[official TARGA field description](https://opendata.astra.admin.ch/ivzod/2000-Typengenehmigungen_TG_TARGA/2200-Basisdaten_TG_ab_1995/2220-Datenbeschreibung/Basisdaten_TG_ab_1995.pdf),
p.2, distinguishes marque, type/variant and VIN-prefix fields; ASTRA also confirms
that individual chassis numbers are not released ([FAQ](https://www.astra.admin.ch/de/faq-fahrzeugdaten)).
These are approval-pattern matches, not a lookup of an individual registered car.
That does not disqualify patterns from resolving make/model: documented VIN rules
also work by patterns. It does mean a compatible approval row cannot automatically
establish every specification of the input vehicle.

Use these boundaries:

- A reviewed, scoped ASTRA-derived pattern-to-make/model rule may produce RESOLVED
  for those fields. Record why the pattern is identifying within its applicable
  layout/market scope, the exact approval rows/remarks, normalization mappings,
  overlapping patterns and exclusions, and independent behavioral examples.
  A mapping review establishes label equivalence; it does not by itself establish
  that an approval mask uniquely identifies a model outside that catalogue.
- All currently retained matching rows agreeing on a normalized family is useful
  evidence, but agreement alone remains SUGGESTED until that identifying scope is
  established. The import is a filtered passenger-vehicle snapshot and excludes
  malformed/short masks; absence of another model is not proof of global uniqueness.
  Caller market CH alone does not prove membership in a particular approval.
- Many compatible approvals may still resolve the same make/model under a reviewed
  identifying rule while leaving engine, trim and exact configuration ambiguous.
  One compatible approval may still leave make/model only suggested if the rule's
  applicability is unverified. Row count is not the resolution criterion.
- A shared SEAT/CUPRA mask cannot resolve either marque without distinguishing
  evidence. A known conflicting identifying rule yields CONFLICT, not a suggestion.
  Missing family mappings block a claim of complete candidate consensus.
- Approval dates do not establish model year. A resolved ASTRA-backed make/model
  can coexist with an unknown model year; a separate scoped year rule may resolve it.

The raw `typeApprovals` API remains a candidate catalogue. Promotion occurs only
through explicit reviewed identity rules in the new resolver, with full lineage.
No existing ASTRA patterns have been promoted by this implementation. The current
Octavia example therefore remains a proposed consensus suggestion until its
identifying scope is separately reviewed. This refines the proposed resolver and
does not change the conservative first-import contract in the ASTRA research review.

## Proposed short and long JSON views

User follow-up: support a compact application-facing JSON answer and a detailed
JSON answer. These are two projections of **the same resolved result**, not two
decoders or different decision policies. This remains a proposed API.

Identity portion of the recommended short form, using a synthetic Golf specimen.
This fragment omits the required `sources` array, specified below; it is not the
complete response:

```json
{
  "schemaVersion": 1,
  "vin": "WVWZZZ1KZ5P000001",
  "inputStatus": "SUPPORTED_FORMAT",
  "vehicle": {
    "makeId": "vw",
    "make": "VW",
    "modelId": "vw:golf",
    "model": "Golf",
    "modelYear": 2005,
    "productionYear": null
  },
  "fieldStatus": {
    "make": "RESOLVED",
    "model": "RESOLVED",
    "modelYear": "RESOLVED",
    "productionYear": "UNKNOWN"
  },
  "assumptions": []
}
```

Short-form contract:

- `vin` is normalized input. `inputStatus` describes format only:
  SUPPORTED_FORMAT, INVALID_CHARACTERS or UNSUPPORTED_LENGTH. It is not a checksum,
  registration or authenticity claim. Invalid/unsupported input retains the shape
  with null vehicle values; detailed input diagnostics stay in the long form.
- Each vehicle property is present consistently. An absent answer is JSON null,
  never an empty string, zero, an “Unknown” display label or a list of candidates.
- IDs are the keys for matching/filtering; make/model strings are canonical display
  names. ID and display-name presence are paired. Numeric years remain integers.
- `fieldStatus` uses the previously defined per-field statuses. It avoids a vague
  overall “high confidence” label when, for example, the make is resolved but the
  year is unknown. Identity IDs inherit the status of their corresponding name.
- A caller-supplied year remains PROVIDED. Catalogue-only family consensus is
  SUGGESTED; a reviewed identifying rule can resolve the family regardless of its
  source country. Null ambiguous/conflicting values retain their distinct status.
- Preserve material assumptions in short form, for example
  `{"code":"US_MARKET_ASSUMED","fields":["model","modelYear"]}`. A suggested
  value must not lose its regional qualification simply because output is compact.
- Initial short output focuses on identity. Engine/body/fuel/power can later be
  added as selected normalized properties with statuses and explicit units, after
  the same conflict/correlation policy is defined for them. Do not dump candidate
  specifications or add dozens of empty optional properties to the first version.

### Attribution is required in short output

Both views must include a self-contained `sources` array. Compact output must not
strip source credits or make consumers perform another lookup to obtain them.
Detailed rule evidence can be omitted from short output; applicable notices cannot.
This is orVIN's output policy even for sources without an attribution obligation.

Each entry has a stable source ID, publisher, title, original dataset/document URL,
source edition or snapshot, a nullable license identifier, a nullable terms URL,
recorded reuse basis, a displayable attribution, a modification notice, and `fields`
(JSON Pointers to the affected returned properties). `license: null` means no named
license has been asserted, not unrestricted reuse. `termsUrl` may point to a license,
statute or publisher terms; do not invent a Creative Commons/SPDX license for OEM
facts, NHTSA information or Swiss statutory OGD. License identifiers retain their
recorded scheme, rather than pretending all identifiers are SPDX-listed.

For example, this is the proposed attribution fragment for a **KBA-backed HSN/TSN
answer**, assuming make/model are supplied by that lookup and reviewed normalization.
The source ID is proposed; the dataset URL, publisher and license come from the
existing KBA metadata. KBA is not currently a VIN decoding source and must not be
attached to the Golf VIN response above merely because the package contains it:

```json
{
  "sources": [
    {
      "id": "kba-hsn-tsn-2026.09.25.1",
      "publisher": "Kraftfahrt-Bundesamt (KBA)",
      "title": "FZ Hersteller Handelsnamen Kfz",
      "url": "https://data.gov.de/suche/daten/fz-hersteller-handelsnamen-kfz?ids=c1e3a0b6-0d34-4e99-8181-91bdfb639208",
      "edition": "Reference date 2026-01-01; orVIN dataset 2026.09.25.1",
      "license": "dl-de/by-2-0",
      "termsUrl": "https://www.govdata.de/dl-de/by-2-0",
      "reuseBasis": "Data licence Germany — attribution — version 2.0",
      "attribution": "Kraftfahrt-Bundesamt (KBA), FZ Hersteller Handelsnamen Kfz; dl-de/by-2-0. Data modified by orVIN.",
      "modifications": "Selected one reference date; renamed columns, sorted rows and encoded nulls. Make/model labels normalized by orVIN.",
      "fields": ["/vehicle/makeId", "/vehicle/make", "/vehicle/modelId", "/vehicle/model"]
    }
  ]
}
```

The KBA license requires a source note containing the provider, license identifier
with a license link and dataset URI, where supplied by the provider; changes must
also be identified ([official terms, sections 2–3](https://www.govdata.de/dl-de/by-2-0),
reviewed 2026-09-26). It does not prescribe JSON as the required presentation format.
Render attribution together with its dataset/terms links and modification notice;
the `attribution` string alone is not a replacement for those structured fields.

Other sources have different bases. [NHTSA's ownership terms](https://www.nhtsa.gov/about-nhtsa/terms-use)
permit copying/distribution of public information; that paragraph does not impose
the same source-note requirements as KBA. Swiss federal OGD is reusable subject to
any special statutory source-credit duties ([Federal Chancellery guidance](https://www.bk.admin.ch/de/sn004-open-government-data-ogd));
this is not itself a blanket attribution license. Retain ASTRA attribution and the
reviewed dataset-specific reuse basis from `data/astra/metadata.json` and
`../research/astra-review.md`. For OEM-derived rules retain the original publisher,
document links and factual-extraction basis without claiming an open document license.

Selection and preservation rules:

- Include the distinct sources supporting returned facts, statuses and material
  assumptions, including the ancestry of derived/normalized values. Deduplicate by
  source identity/snapshot, not just publisher. A Golf synthesis can require several
  Volkswagen documents even though it produces only three identity values.
- For the Golf example, its current scoped rule depends on
  `vw-golf-maintenance-2009`, `vw-golf-v-profile` and `vw-vin-chart-2005`. Preserve
  their individual field associations, plus any additional sources actually used
  by the future resolver/normalization catalogue. Do not blanket-credit all sources
  against all fields. orVIN display-name policy is identified separately from OEM
  factual support.
- Do not include every bundled dataset indiscriminately. Test-only WA data and
  market-ranking research are not runtime answer sources. Sources needed only for
  detailed alternatives belong with the long view's evidence; additional obligations
  attached to distributed datasets still remain in both packages' notices.
- An unresolved answer may still need sources to explain its conflict/ambiguity.
  `sources: []` is allowed only when there is no externally sourced returned content
  or decision and no applicable credit obligation for that projection.
- Record transformations through the full lineage, including imported-data changes,
  factual extraction and label normalization. Metadata is generated from the reviewed
  source catalogue and actual processing, never guessed by the serializer.
- Preserve all applicable attribution/notices without truncation. Source metadata
  helps consumers meet obligations; emitting JSON alone does not discharge every
  application's display, redistribution or other license obligations. orVIN's code
  license does not replace dataset or upstream document terms.

### Long output is a strict extension of short output

Use the exact short object at the root and add **one `details` object**. Do not wrap
it in `summary`, rename primary properties, enrich the `vehicle` object differently,
or provide a second preferred make/model/year inside the detail sections.

The construction is equivalent to this JavaScript pseudocode:

```javascript
const short = projectShort(resolvedResult);
const long = { ...short, details: projectDetails(resolvedResult) };
```

Removing `details` from the new long JSON must produce the new short JSON exactly
under structural equality, including sources, array order, nulls and assumptions.
The resolver runs once; projection mode never changes a decision. This describes
the wire shape, not a requirement to use inheritance in the Java DTOs.

Organize `details` by purpose:

| Property | Contents | Avoid duplication |
| --- | --- | --- |
| `meta` | orVIN version, resolver-policy version, identity-catalogue version and the versions/hashes of used datasets | Reproducibility metadata lives here once |
| `input` | Original input, caller context, detailed format/check-digit findings and applicability | Normalized VIN remains at the root; checksum findings are not authenticity claims |
| `decisions` | One entry per primary field: stable reason code, evidence references, normalization-rule references and relevant alternative references | Selected value and status stay in root `vehicle` / `fieldStatus` |
| `specifications` | Additional selected information, such as legal manufacturer, factory, body, fuel or engine, each with value, status, units where relevant and evidence references | These require their own reviewed selection policy; an approval candidate is not a selected specification |
| `alternatives` | Coherent alternative identities/configurations, applicability conditions, disposition/reason and evidence references | Group equal hypotheses; do not create combinations by crossing independent lists of engines/years/models |
| `evidence` | Indexed original claims, matched rule instances, WMI associations and complete matching approval rows, retaining original labels, IDs, masks and remarks | Store each record once; decisions and alternatives reference its ID |
| `provenance` | Full rule definitions, normalization rules, source review/archive/hash details and credits for additional detail-only sources | Common credits remain in root `sources`; source details extend records by ID |
| `diagnostics` | Stable codes with readable explanations for missing context, source availability, scope exclusions, incomplete mapping and catalogue limitations | Do not repeat all candidate values or turn known limitations into invented probabilities |

Illustrative **decision fragment**, for the scoped synthetic Golf rule (the evidence
index and normalization catalogue are omitted). The `identity:vw:golf` mapping ID
is proposed for this example, not an existing implemented rule:

```json
{
  "details": {
    "decisions": {
      "model": {
        "reason": "SCOPED_VIN_RULE",
        "evidenceIds": ["rule-match:vw-europe-golf-1k-2005-mosel"],
        "normalizationRuleIds": ["identity:vw:golf"],
        "alternativeIds": []
      },
      "modelYear": {
        "reason": "SCOPED_VIN_RULE",
        "evidenceIds": ["rule-match:vw-europe-golf-1k-2005-mosel"],
        "normalizationRuleIds": [],
        "alternativeIds": []
      },
      "productionYear": {
        "reason": "NO_EVIDENCE",
        "evidenceIds": [],
        "normalizationRuleIds": [],
        "alternativeIds": []
      }
    }
  }
}
```

The complete `decisions` map also includes `make`; every real identity normalization
must reference its reviewed mapping. Reason codes distinguish, for
example, `REVIEWED_APPROVAL_IDENTITY_RULE`, `CATALOGUE_CONSENSUS`,
`MARKET_CONTEXT_REQUIRED`, `COMPETING_IDENTITIES` and `NO_EVIDENCE` without making
callers parse a human explanation. An ASTRA-backed RESOLVED result therefore remains
visibly based on an approval-derived rule, and does not imply a registration lookup.

Evidence and provenance structure:

- `evidence` is keyed by response-stable evidence IDs derived from source snapshot,
  upstream key/source row and rule identity where appropriate. Preserve upstream
  IDs alongside them; avoid random UUIDs or row-order-dependent identities. A rule
  match retains observed VIN positions and its rule ID. A raw approval retains
  its original source row, matching masks, all specifications and row-specific remarks.
- `provenance.rules` and `provenance.normalizationRules` are keyed by rule ID.
  Retain scope, derivation, source IDs and precise document/row/field citations.
  Derived claims keep their parents. Store each definition once rather than copying
  it into every field decision. All references must resolve within the long response;
  consumers need no network fetch or installed dataset to understand the evidence.
- `provenance.sourceDetails` is keyed by source ID and extends the credit record
  with hashes, retrieval/review dates, archive/record locators and any additional
  field associations or transformation notes needed for long-only information.
  It does not repeat publisher, title, license and URL already present in credits.
- `provenance.additionalSources` uses the same self-contained credit-entry shape as
  root `sources`, but includes only IDs absent there. It supplies the credits for
  additional facts, candidates and rejected alternatives in the long response.
  Keeping these separate makes root `sources` identical in both projections while
  still attributing every fact in the long view. Cross-references may target either
  credit collection; the same source ID must not appear in both.
- Retain correlated configurations and original values. Do not also emit the old
  source-specific aggregate possibility lists that duplicate the evidence. Never
  merge several approvals' remarks or flatten their engines/transmissions into one
  supposed vehicle. Alternative groups point to complete evidence records.
- `specifications` contains selected values only where an explicit property policy
  exists. In the first normalized API it may be empty while original manufacturer,
  plant and technical claims remain fully available in `evidence`. Do not lose
  existing data or silently invent a new consensus rule for engine/build date.
- Long output is complete by default. Thousands of matching approvals may require
  thousands of records, each included once. No silent top-N truncation; any future
  bounded diagnostic export must explicitly identify omitted evidence/counts and
  cannot masquerade as the complete long output. Grouping must be lossless.
- Retain source-level statuses and candidate counts in diagnostics, including
  distinctions such as unavailable, out of scope, no match and incomplete mapping.
  Use deterministic ordering for arrays and ID generation in both implementations.

### CLI, compatibility and acceptance

User decision: **both repository scripts use short JSON by default**. Keep them as
thin Python entry points; all resolution, projection and serialization belongs in
the Python library/shared CLI. No Java/JDK/compilation step and no separate shell
implementation of the decision policy. Default mode belongs in one CLI formatter
selection, so wrappers do not inject flags that conflict with an explicit override.

| Invocation | Planned output |
| --- | --- |
| `./vin.sh <vin>` | Normalized short VIN JSON, including statuses, assumptions and source credits |
| `./hsntsn.sh <hsn> <tsn>` | Normalized short HSN/TSN JSON with the same vehicle/status/attribution contract |
| Either script with `--long` | The identical short object plus `details` |
| Either script with `--json` | Explicit short JSON, identical to the default |
| Either script with `--json --long` or `--long --json` | Explicit long JSON, identical to `--long` |
| Either script with `--json=short` / `--json=long` | Explicit equivalent format selection |

`--json` selects JSON serialization; `--long` selects detail level independently.
Their order must not matter. The same combinations work for VIN and HSN/TSN.
An explicitly contradictory combination such as `--json=short --long` is a usage
error, rather than a last-argument-wins rule. Agreeing flags may be combined.

The HSN/TSN short response uses normalized string `hsn` and `tsn` keys in place of
`vin`; preserve leading zeroes. Its common keys remain `schemaVersion`,
`inputStatus`, `vehicle`, `fieldStatus`, `assumptions` and `sources`. Long adds exactly
the same `details` structure, with KBA rows/source IDs and reference dates in the
evidence. Never invent a VIN from these codes, infer HSN/TSN from a VIN, or present
KBA's reference/registration date as model year. Without separate year evidence,
`modelYear` and `productionYear` remain null/UNKNOWN. A KBA manufacturer label must
pass reviewed marque normalization; a unique code match is not permission to take
the first of several competing model labels.

These defaults are implemented in the development checkout. The default
change from readable text to short JSON is intentional and must be documented in
the release notes. If readable output remains available via an explicit format
option, derive it from the same short projection rather than the old raw summaries.
Use stdout exclusively for the selected JSON result, stderr for operational errors,
and preserve documented exit-code behavior. Invalid lookup input still receives the
short response shape with validation status and null identity values where feasible;
a dataset-load failure must not be disguised as a successful all-unknown lookup.

The user's requested bare `--json` now selects the new short contract. This
supersedes the earlier proposal to reserve it for legacy output. The current CLI
emits the old full public result for that flag, so document the intentional JSON
contract change in the release and migration notes, along with the new default.
An additive extension of the new short contract is not automatically compatible
with the old JSON contract. Existing Python/Java result access remains available;
new summary/detail projections avoid requiring consumers to implement the resolver.
Avoid adding a runtime JSON framework solely for these views in Java.

Acceptance checks:

- Projecting long to short is exactly removal of `details`. No primary properties,
  statuses, source credits or assumptions differ, and no second decision run occurs.
- Both views preserve SUGGESTED/PROVIDED/conflict distinctions. Shape, nulls, IDs,
  numeric years and deterministic reference/order behavior match in Java and Python.
- Every decision, alternative and derived claim resolves to its full evidence and
  source lineage; zero dangling references. Original source values, remarks and
  complete candidate configurations remain recoverable without external lookups.
- Common and additional source credits cover all included content, with applicable
  provider, dataset, terms and modification notices. No duplicate source IDs,
  fabricated licenses or unrelated/test-only sources; missing required notices
  fail provenance checks.
- Reviewed ASTRA identifying rules can yield RESOLVED, while catalogue-only
  consensus remains SUGGESTED. Multiple engine variants do not automatically lower
  a supported model's status; one approval does not automatically raise it.
- Both scripts default to the corresponding library short projection, including
  credits. Their `--long` outputs reduce to those same defaults by removing
  `details`; VIN and HSN/TSN inputs stay distinct and HSN zeroes survive.
- For both scripts, default output equals `--json` and `--json=short`; `--long`,
  `--json --long`, `--long --json` and `--json=long` produce the same long output.
  Explicitly contradictory detail selectors fail with a usage error.
- Existing raw library result access remains available; the new projections do
  not change raw KNOWN/value semantics. Document the intentional CLI JSON contract
  change. These checks supplement the resolver and packaging tests below.

## Shared identity catalogue

Keep normalization data under `data/identity/`, used by both implementations:

- `makes.json`: stable make IDs, canonical display names, source-specific IDs and
  explicit label aliases. Volkswagen/VOLKSWAGEN/VW resolve to `vw` / `VW`.
  Skoda/SKODA/Škoda resolve to one reviewed identity, displayed as Škoda.
- `models.json`: make-scoped model IDs and canonical family names. Engine, body,
  trim and generation remain separate properties; they are not parsed away blindly.
- `mappings.json`: sourced bindings from NHTSA make/model IDs, original Swiss
  approval rows/type labels and custom rule outputs to canonical identities.
  Every mapping retains its original value, scope, locator and review rationale.
- A manifest/schema with version, hashes and mapping coverage/exclusions. Compiled
  lookup tables remain deterministic and are bundled with the full catalogue.

Prefer upstream numeric IDs and explicit source keys to matching display text.
An exact normalized source label may be an alias only after collision review.
Never merge identities solely through fuzzy matching, capitalization, punctuation
removal, corporate ownership or a shared WMI. Preserve distinct SEAT/CUPRA,
Opel/Vauxhall and BMW/MINI identities.

For model names, curated rules may map several original type labels to a family,
for example reviewed Octavia engine/Combi variants to `skoda:octavia`. The mapping
does not establish the engine or body of the input vehicle. Keep distinct models
such as Yaris/Yaris Cross and Seal/Seal U. Golf/Golf Cabriolet/CrossGolf and regional
marketing names need explicit scope decisions, not generic prefix stripping.

The 100-model research queries are useful input to review, **not ready-made runtime
normalization rules**. Review their aliases, exclusions and collisions before
promotion. Materialize approved Swiss row-to-family mappings so later source edits
cannot silently broaden a regex. Catalogue presence still does not prove an exact
vehicle's configuration.

Audit every observed make label in the bundled inputs. Each must have an explicit
mapping or a recorded unresolved disposition. Cover the common 50 makes and all
100 priority model targets first, then the remaining source labels. Do not silently
pass an unmapped raw name into the normalized answer; preserve it in evidence and
report `UNKNOWN / UNMAPPED_IDENTITY` when it is needed for a decision.

Display-name choices are orVIN policy (including the user's VW preference).
Factual alias/model equivalence mappings additionally need supporting evidence;
record both kinds of provenance rather than pretending a display preference came
from an OEM document.

## Decision policy

1. **Check input and applicability.** Only valid supported layouts produce the
   normalized answer. Apply each rule's market, year and layout restrictions.
   Explicitly incompatible US rules are excluded for a European-market request.
   Swiss catalogue geography alone does not establish a vehicle's original market.

2. **Canonicalize before comparing.** VW and VOLKSWAGEN are agreement after mapping,
   not a conflict. Keep make/model/year claims associated with their original
   configuration and assumptions. Missing or unmapped values are not agreement.

3. **Resolve identifying evidence first.** Applicable documented VIN rules,
   including scoped OEM/custom, NHTSA and reviewed ASTRA-derived identity rules,
   can resolve the fields they actually establish. Raw approval matches do not
   become identifying rules without the review described above. Do not prefer a
   rule simply because it is called “custom” or comes from a particular country.
   A more specific rule may override a broader one only through reviewed scope
   containment or an
   explicit documented supersession. Conflicting applicable direct claims produce
   a conflict; source order must not silently decide the answer.

4. **Use WMI evidence for make.** A unique applicable make assignment can resolve
   the make when no more specific identity is available. A shared multi-brand WMI
   cannot pick a marque. A resolved model carries its associated make; never pair
   a selected model with a different make from another result. Flag contradictory
   broader assignments and preserve them in the explanation.

5. **Use conditional evidence for a suggestion.** When there is no resolved
   value, group remaining Swiss candidates by reviewed canonical make/model.
   If all admissible candidates have a compatible mapped family but no reviewed
   identifying rule applies, suggest that family, even if there are hundreds of
   engine/trim variants. Candidate agreement alone stays `SUGGESTED`. A reviewed
   identifying rule was already considered in step 3 and has no Swiss-specific
   status ceiling. A unique US-only possibility
   with unknown market may likewise be suggested with the explicit US assumption.
   Conditional sources that disagree remain ambiguous; no universal US-versus-CH
   preference chooses a winner. Known incompatible market context excludes the
   conditional US claim entirely.

6. **Do not vote by row count.** More approval variants or repeated imports do not
   make a model more likely. Neither 900 versus 20 rows nor the first/alphabetically
   earliest row is a reason to choose. More fixed VIN characters alone also cannot
   turn a catalogue candidate into a known model. Unmapped/missing competitors
   prevent a claim of complete catalogue consensus.

7. **Keep year semantics exact.** `modelYear` means model year, always an integer.
   `productionYear` stays separate. Never substitute an approval/registration date
   or Tesla production year for model year. Use position 10 only under a documented
   applicable scheme; unresolved 30-year cycles remain alternatives. Caller year
   context is labelled PROVIDED when used, and a contradiction is exposed rather
   than quietly overriding decoded evidence.

8. **Resolve a coherent identity.** Select compatible make/model/year claims,
   not three independent winners that never coexist in one admissible alternative.
   Model year is returned only if it is supported for the chosen family under the
   same assumptions, or is common to all surviving identity alternatives. A make
   or year may remain usable when another field is ambiguous. A direct Golf result
   is not displaced by broad Swiss Jetta/Cabriolet/engine alternatives; those remain
   lower-strength catalogue evidence, not contradictory direct VIN assertions.

Each field records why it was chosen, which evidence agrees, which evidence was
excluded and why alternatives did not win. No weaker fallback should conceal a
direct-evidence or caller-context conflict.

## Implementation sequence

1. **Catalogue and contract:** finalize the shared short contract and long
   `details` extension, Java records and identity schema; import reviewed make
   mappings and initial model-family mappings. Review candidate-derived identifying
   rules separately from label mappings. Produce scope, overlap, exclusion and
   normalization coverage/collision reports.
2. **Evidence adapters:** adapt WMI, NHTSA, custom and Swiss results to common
   canonical claims with source references, scope and configuration relationships.
   Refactor the rich decoder's early-return dispatch sufficiently to expose
   conflicting applicable rules to the resolver; preserve each source's own
   internal matching semantics and existing evidence output.
3. **Python resolver:** implement the versioned policy, common `vehicle` answer
   and `details.decisions` explanation. Keep the policy shared as data where it
   describes mappings and source scope; do not build a generic scoring framework.
4. **Java parity:** implement the same decisions and immutable result records.
   Preserve existing constructors/convenience accessors during the transition.
5. **Consumer experience:** make short JSON the default for both repository
   scripts, including normalized values, per-field status and source attribution.
   Add `--long` and `--json --long` for the strict extension, with full evidence and
   detail-only credits; bare `--json` explicitly selects the default short view.
   Document `vehicle` as the application-facing API and the exact long-to-short
   projection. Preserve raw library result access and document the intentional
   CLI migration rather than silently changing source-specific KNOWN/value semantics.
6. **Validation and packaging:** extend provenance, full reconstruction, shared
   parity fixtures and package checks to include the identity catalogue. Evaluate
   the normalized answer separately from the existing strict/raw benchmark; retain
   both coverage and disagreement reports. No release or Tourfold integration is
   implied by this planning task.

The initial primary answer deliberately focuses on make/model/year. Additional
normalized engine/fuel/body fields can use the same evidence design later; they
must retain configuration correlation rather than mixing approval variants.

## Acceptance examples and regression boundaries

- Golf specimen: `VW / Golf / 2005`, regardless of raw VW/VOLKSWAGEN spelling.
- Octavia specimen: `Škoda / Octavia / null` as a catalogue suggestion once all
  admissible type labels are reviewed/mapped; resolving it additionally requires
  review of its identifying pattern/scope. No fabricated model year.
- A separately reviewed ASTRA identifying-rule fixture may resolve make/model even
  when many engine variants remain; a consensus-only fixture remains suggested.
  Include overlap, excluded-mask and shared-marque counterexamples.
- VSS…5F specimen with unresolved SEAT/CUPRA and model-family competition: no
  arbitrary make/model winner. Show the unresolved fields and alternatives.
- Reviewed EU Model Y: `Tesla / Model Y / null` for model year, with production
  year 2026 separately.
- US Accord with US context: `Honda / Accord / 2003`, resolved; without context,
  a unique conditional suggestion carries the US assumption; explicit DE context
  cannot receive that US-only model/year as a supported answer.
- Manufacturer display normalization never equates legal entities with marques.
- Alias changes never merge SEAT/CUPRA, Opel/Vauxhall, Yaris/Yaris Cross or
  Seal/Seal U; changing input row order/duplicate row count cannot alter a decision.
- Partial mapping, missing candidate fields, equal-strength conflicts, mismatched
  caller year, invalid input, historical year cycles and unmapped brands remain
  visible; no unsupported precision is introduced by the new API.
- Full Python/Java parity includes selected IDs/names, statuses, assumptions,
  alternatives and evidence/normalization rule references. Fresh JAR/wheel checks
  verify the new shared catalogue and installed behavior outside the checkout.

Success is one consistent, useful default answer with reproducible decisions.
Returning null for an unresolved field is part of that contract; forcing a label
for every input would turn missing evidence into false information.
