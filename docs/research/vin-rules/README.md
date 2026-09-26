# Public VIN rules: research index and implementation direction

Research date: **2026-09-25**. Three research agents investigated **50 makes**
with European and German customer usefulness in mind. This is a practical,
Europe-oriented selection, **not an independently verified sales ranking**.
Makes are not the same as legal manufacturers: shared manufacturing, rebadging
and multiple brands under one WMI occur throughout the evidence.

The recommended foundation is the **complete official NHTSA standalone data
snapshot**, supplemented by carefully scoped European rules. This is more useful
than manually recreating a small selection of US tables. Manufacturer documents
remain important for European gaps, understanding ambiguous fields and checking
the meaning of source data.

## Research results and coverage

An inspected table was found for **43 makes within a bounded scope**. This count
includes historical-only, commercial-only and narrow model-family applicability
tables; it does not mean 43 complete passenger-car decoders. Škoda supplies useful
explicit examples without a complete applicability matrix. For the remaining
six makes, this survey did not establish a usable passenger-car character map.

“Verified” means the underlying official table or rule was inspected. It does
not establish exhaustive coverage, the latest revision, runtime support or
permission to redistribute an OEM document. Absence from this survey is not
proof that a source does not exist.

| Report | Makes investigated | Result |
| --- | --- | --- |
| [European makes](europe.md) | Volkswagen, Audi, Škoda, SEAT, CUPRA, Porsche, BMW, MINI, Mercedes-Benz, smart, Opel, Vauxhall, Renault, Dacia, Peugeot, Citroën, Fiat | 17 makes: 12 with scoped tables; Škoda has explicit examples; SEAT, CUPRA, Vauxhall and Citroën lack a usable character map in this pass. |
| [Asian makes](asia.md) | Toyota, Lexus, Honda, Acura, Nissan, Infiniti, Mazda, Subaru, Mitsubishi, Suzuki, Hyundai, Kia, Genesis, Isuzu, Daihatsu, BYD, Geely | 17 makes: 16 with scoped tables, including old US models and commercial vehicles; Geely passenger-car rules remain unverified. |
| [American makes and other global brands](americas-uk.md) | Ford, Lincoln, Chevrolet, GMC, Cadillac, Buick, Chrysler, Dodge, Jeep, Ram, Tesla, Volvo, Polestar, Land Rover, Jaguar, MG | 16 makes: 15 with scoped tables; MG has identification guidance but no verified character map. |
| [NHTSA bulk assessment](nhtsa-bulk.md) | The complete standalone database, independently of the 50-make selection | Inspected September 2026 snapshot, exact hashes, table inventory, WMI associations and decoding procedure semantics. |
| [Common rule framework](framework.md) | Cross-cutting requirements | Scope, provenance, ambiguity, encoded facts versus enrichment, and shared Python/Java fixtures. |
| [KBA WMI directory](../kba-wmi/README.md) | International manufacturer identifiers and the January 2026 directory | Same WMI system as NHTSA; potentially complementary coverage, with conflicting reuse notices still unresolved. No KBA WMI rows imported. |

The regional reports record exact URLs, document editions, relevant pages,
markets, verified fields, gaps and reuse findings. Their implementation-status
notes describe the research stage; the bulk integration below is the subsequent
implementation work.

## Bulk foundation and runtime boundary

Both libraries now use 12,998 usable WMIs, covering 11,604 manufacturer entities and 14,169
WMI/brand associations from the
[September 2026 NHTSA PostgreSQL snapshot](https://vpic.nhtsa.dot.gov/downloads/vPICList_lite_2026_09.plain.zip).
The **complete original ZIP** is embedded in both Python and Java distribution
artifacts. The generated WMI data gives the libraries broad offline manufacturer,
make-association and vehicle-category evidence. The original archive preserves
the complete source snapshot for further work; runtime does not require a JDK
for Python, PostgreSQL or an online VIN request.

**The full rich vPIC decoder is not implemented.** The development libraries now
execute scoped public patterns, year alternatives, numeric captures, model/make and
engine associations, and displacement conversion. Vehicle-specification enrichment,
defaults, VIN repair and error scoring remain outside this increment.
See [the implemented contract](../../rich-decoding.md).

WMI records also cover trailers, motorcycles, trucks and other vehicle classes;
their count is not a count of passenger-car brands. Keep all make associations
when a WMI is shared. Source WMI country is not proof of the individual vehicle's
assembly country. Extended low-volume WMIs require the applicable characters
from positions 12–14 in addition to positions 1–3.

## Where richer information is supported by the research

| Source scope | Useful evidence | Main boundary |
| --- | --- | --- |
| NHTSA standalone database and OEM Part 565 filings | Model/body, engine and fuel, some trim/drive/transmission combinations, restraints, weight class, plant and scoped year information | Predominantly US sale/importation; exact model/year/market predicates and procedure semantics matter. |
| Tesla Model Y service documentation | Plant-dependent configuration and year meaning, including Berlin/Shanghai distinctions | The inspected 2025+ scheme is model-specific; production year and model year can mean different things. |
| Volkswagen UK and Škoda official explanations | Bounded year rules and worked model/body/engine/plant examples | Incomplete historical and model coverage; not comprehensive brand tables. |
| Fiat type approvals and CEM-hosted OEM protocols | Narrow type/model-family associations for Fiat, Opel, Renault, Dacia, Peugeot and BYD | Shared prefixes can cover multiple models and all powertrains; applicability is not an exhaustive inverse lookup. |
| OEM vehicle-information services | Build characteristics retrieved using a VIN | Database enrichment, not proof that the VIN directly encodes every returned field. |

The follow-up historical review supports a **narrow European Golf 1K model-year-2005
rule for Mosel/Wolfsburg**. It combines a Volkswagen maintenance layout, historical
Golf profile and same-year year/plant chart; see the [Volkswagen assessment](europe.md).
Other historical years and layouts remain gaps. A 2026 US chart is not used for them.

The reports also document genuine ambiguity and changing rules: Mazda changes
trim interpretation within one model year at stated serial boundaries; some
Genesis and Kia codes identify multiple configurations; Jaguar/Land Rover use
multi-character configuration keys; Volvo has a later amendment to reconcile.
Preserve correlated alternatives instead of independently combining fields into
configurations that the source never described.

Full paint/options lists, exact build date, registration information, service
history and mileage need separate evidence or an authorized vehicle database.
HSN/TSN remains an independent KBA lookup supplied by the caller; these sources
do not establish a universal VIN-to-HSN/TSN conversion.

## Source and reuse boundaries

[NHTSA's Terms of Use, Ownership section](https://www.nhtsa.gov/about-nhtsa/terms-use)
provides the source-specific copying/distribution basis for its published
information, with accuracy and third-party-rights disclaimers. Retain the
download URL, release date, original archive, hashes and attribution. This does
not make imported records or stored procedures orVIN-owned CC0 material.

That assessment must not be silently extended to every OEM PDF hosted by NHTSA
or linked elsewhere. OEM-specific redistribution permission was not established
for the researched manuals and wholesale tables; several contain express
proprietary notices. The regional reports identify restrictive CEM, Škoda and
Fiat terms. No extra OEM PDF collection is implied by embedding the official
NHTSA standalone archive. Any literal port of stored-procedure code needs its
own recorded provenance and reuse assessment.

## Recommended implementation sequence

1. **Completed: use the bulk WMI foundation in both libraries.** Keep source IDs, extended
   WMIs, many-to-many make associations, source flags and a pinned manifest.
   Verify installed Python packages and Java JARs load their embedded resources
   without network access or the source checkout.
2. **Completed: bounded rich decoding over the shared data.** Use explicit
   year/market context and documented pattern stages. State which stages run;
   incomplete procedure support must not be described as full vPIC parity.
   Compare Python and Java on independent synthetic examples, ambiguity and
   out-of-scope cases.
3. **Add European rules where evidence improves European coverage.** Prioritize
   the documented Tesla Model Y plant/year distinctions and bounded VW/Škoda
   evidence after source-specific reuse and applicability review. Tesla Model Y and
   the narrow Golf MY2005 extension are implemented. Curate CEM/Fiat family associations only
   after checking overlaps, dates and reuse terms.
4. **Keep field provenance and enrichment explicit.** Preserve unknowns and
   unresolved alternatives. Separate direct decoding, associated type facts
   and individual-vehicle database results. Keep customer VINs out of source
   research and test fixtures.

The 50-make survey provides a source map and concrete implementation constraints.
Active decoder coverage must be measured from the implemented rules and their
tests, independently of the number of documents found or source rows packaged.
