# VIN rule research: common framework

Research date: 2026-09-25. This describes possible extensions, not additional implemented decoding.
No customer VIN was sent to research services or added to fixtures.

## What ORvin currently returns

Both libraries now use 12,998 WMIs from the September 2026 NHTSA bulk snapshot, replacing the
six-assignment seed. See [import and coverage](../../nhtsa-data.md). This does not establish
globally complete coverage of those manufacturers. They return sourced
manufacturer/brand/category facts, candidates and explicit unknown/ambiguous/context states.
The independent structural check assesses only length and alphabet, not checksum or authenticity.
The development libraries also return supported model, engine, fuel, trim, model-year
and plant fields from bounded NHTSA stages, plus scoped Tesla and Golf extensions.
See [the implemented contract](../../rich-decoding.md); this is not full vPIC equivalence.

The KBA operation accepts independently supplied HSN/TSN. It supplies manufacturer/model labels,
dated registration counts and source attribution from the 2026-01-01 stock snapshot. It does not
derive those codes from a VIN and is not a VIN-to-engine or VIN-to-equipment database.

## Useful general primary sources

- [49 CFR 565.15](https://www.ecfr.gov/current/title-49/subtitle-B/chapter-V/part-565/subpart-B/section-565.15)
  defines US VIN content. Depending on vehicle class, manufacturer tables explain model/line,
  body, engine, restraint and other attributes. It defines a position-nine check digit, a
  position-ten model-year code and a plant code at position eleven. The year-cycle discriminator
  in its table note has a specific vehicle-class scope. These requirements are not global rules.
- [49 CFR 565.16(c–d)](https://www.ecfr.gov/current/title-49/subtitle-B/chapter-V/part-565/subpart-B/section-565.16)
  requires manufacturers within scope to submit decoding information and amendments. This
  explains why official NHTSA manufacturer-submission PDFs are productive research sources.
- [EU Regulation 2021/535](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX%3A32021R0535),
  Annex II, sets VIN structure requirements. Its provisions and amendments have applicability
  dates; they cannot be retroactively imposed on every European vehicle. Confirm the version
  and vehicle/type-approval scope before implementing a checksum or layout rule.
- [NHTSA vPIC API](https://vpic.nhtsa.dot.gov/api/) documents partial VIN decoding, explicit
  model-year context, WMI lookup and manufacturer Part 565 discovery. It recommends supplying a
  known model year. Its output is a useful comparison source for covered vehicles, not proof
  that the same interpretation applies to European variants.
- [Official standalone vPIC databases](https://vpic.nhtsa.dot.gov/downloads/) now supply the
  shared WMI foundation. The September 2026 ZIP is pinned and embedded in both distributions;
  native libraries use its reviewed public pattern stages. SQL is archived as evidence,
  never executed; vehicle-spec/default/error-scoring stages remain unimplemented.

## Distinguish three kinds of information

| Kind | Examples | Evidence needed |
| --- | --- | --- |
| Direct character rule | An engine code in specified positions; plant code; scoped year code | Official table with exact model/year/market/layout scope |
| Attribute associated with a decoded type | Engine displacement, cylinder count, fuel, drive configuration | A cited mapping from the encoded type/configuration to each output field |
| Individual-vehicle database lookup | Original paint, exact build date, complete option list, service/accident history, mileage | An authorized data service or build record; not assumed to be encoded in the VIN |

Some OEMs encode a trim, transmission or particular option in a scoped table. That does not mean
the full as-built configuration is recoverable from every VIN. A check-digit match does not
authenticate the vehicle, and model year must remain distinct from build date or registration year.

## Proposed rule representation

The first bounded NHTSA implementation is present; further enrichment stages need review.
For manufacturer-specific gaps, extend the language-neutral data with small declarative rules.
Each rule should identify the document/revision, source URL and page, reuse basis, applicable
WMIs/layouts, make/model family, market and year range. Preserve source text separately from
normalized output labels. Use explicit position ranges and conjunctions: a multi-character
configuration table must not be split into independent one-character facts without evidence.

Resolve applicability before applying a rule. Missing market/year context should retain candidates
or return `NEEDS_CONTEXT`; overlapping incompatible rules should return `AMBIGUOUS`. Unsupported
fields stay unknown. Avoid circular reasoning in which a guessed year selects the table that is
then cited as proof of that year. Preserve multiple possible year cycles until evidence resolves them.

Add independent synthetic fixtures for matches, near misses, scope boundaries, ambiguity and
missing context. Run them in Python and Java, then compare full public results. Do not use a
customer's real VIN as a test fixture or silently issue online VIN lookups.

## Reuse and implementation readiness

Availability of an OEM PDF on a public government server establishes accessibility, not an open
license for the PDF or wholesale table republication. Assess the exact factual extraction,
attribution and source-specific reuse basis before bundling new data. Government rules, NHTSA
API facts, OEM-authored submissions and OEM manuals are separate source categories. A document
can therefore be technically useful while its redistribution assessment remains open.

Research reports record evidence and gaps. They do not silently extend the shipped dataset's
coverage, license claims or API fields.
