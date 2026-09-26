# VIN rule research: American makes, Volvo, Polestar, Jaguar Land Rover and MG

Discovery/review date: **2026-09-25**. This is the 16-make portion of a practical
50-make survey, not a verified sales ranking. Research only: none of these rules
has been added to the runtime dataset. No customer VIN was sent to a service.

**Result:** official decoding tables were verified for a bounded model/year scope
for 15 makes. MG has useful official identification guidance, but this search did
not establish a public position-to-value decoding table. A verified table does
not establish full brand coverage or redistribution permission.

## Sources and verified scope

| ID | Official document and exact URL | Edition / market / verified location | Reuse assessment |
| --- | --- | --- | --- |
| F25 | [Ford 2025 VIN Guide](https://content.fordpro.com/content/dam/fordpro/us/en-us/pdf/fleet-vehicles/vin-lookup-and-guides/2025-vin-guide.pdf) | US Ford Pro publication; 11 pages, attachment dated March 1, 2024. General positions pp. 2–7; Econoline p. 8; Explorer p. 9; F-650/F-750 p. 10; Lincoln Aviator p. 11. This specific file is a limited attachment, not every 2025 Ford/Lincoln model. | Redistribution permission not established for this OEM-hosted PDF. |
| GM25 | [General Motors LLC: 2025 Vehicle Identification Numbering Standards](https://vpic.nhtsa.dot.gov/mid/home/displayfile/93e823b4-c342-4ae0-8546-c947a390078d) | North American Product Development, revision 9.0, effective September 24, 2024; 60 pages. General positions p. 7 and individual product pages below. Some rows expressly describe non-US/non-Canada configurations; that does not establish all European configurations. | NHTSA public-information copying statement applies to its published information; no separate OEM open-data license identified. Preserve source-specific terms; do not label CC0. Whole-document redistribution permission not independently established. |
| FCA24 | [FCA US LLC: 2024 Truck / MPV Vehicle Identification Number Code Guide](https://vpic.nhtsa.dot.gov/mid/home/displayfile/b5f541b7-8157-415d-889c-7f63628e9e66) | July 12, 2024; five pages. General rules p. 1; Ram pp. 2–3; Jeep p. 4; Chrysler and Dodge p. 5. North American submission with expressly marked Canadian/export/right-hand-drive rows. | Same NHTSA-hosted-document assessment as GM25; no OEM open-data license identified. |
| V25 | [Volvo MY2025 VIN Decoder – USA/Canada](https://vpic.nhtsa.dot.gov/mid/home/displayfile/82093ac4-eb14-4c7b-956a-803ca000db57) | May 24, 2024 cover letter; tables dated March 27, 2024, revision history initial release May 9. PDF pages 2–5 are printed pages 1–4. USA/Canada explicitly. | Same NHTSA-hosted-document assessment as GM25; no OEM open-data license identified. |
| P21 | [Polestar MY2021 VIN Decoder – USA/Canada, Rev 1](https://cdn.polestartechhub.com/vin-decoder/Polestar+MY+2021+VIN+Decoder-Rev+1.pdf) | July 7, 2020; two pages. Polestar Automotive USA Inc.; Polestar 1 and 2. Linked by the public [Polestar Tech Hub VIN Decoder](https://polestartechhub.com/resources/vin-decoder). | Redistribution permission not established. Public OEM document, not an open-data license. |
| J20 | [2020 Jaguar F-TYPE VIN decoder](https://vpic.nhtsa.dot.gov/mid/home/displayfile/03723043-2a59-4275-80a4-e55642b61a8a) | Single-page Jaguar Land Rover Part 565 table. PDF metadata title says `VIN Decoder_2020_JLR_MASTER_Updated 19JAN18.xls`; table explicitly says MY2020. US regulatory submission; European applicability not established. | Same NHTSA-hosted-document assessment as GM25; no OEM open-data license identified. |
| L26 | [2026 Land Rover Discovery VIN decoder](https://vpic.nhtsa.dot.gov/mid/home/displayfile/92c482ad-0aed-48f0-93a3-0a7fe81f00f1) | Single-page Jaguar Land Rover Part 565 table, document title updated March 18, 2026. US regulatory submission, Discovery only. | Same NHTSA-hosted-document assessment as GM25; no OEM open-data license identified. |
| T25 | [Tesla 2025+ Model Y service manual: Vehicle Identification Number](https://service.tesla.com/docs/ModelY/ServiceManual/2025/en-au/air/GUID-BB4CE449-3F8E-4905-AF4A-96DFA87535B5.html) | `VIN Decoding` section; Australian English edition, with explicit Texas/Fremont/Shanghai/Berlin distinctions. Live document; snapshot/date needed before implementation. | Redistribution permission not established; public service documentation is not an open-data license. |
| MG | [MG ZS EV Owner's Manual](https://cdn.mgmotor.eu/manuals/1.-ZS-EV_Owners-Manual.pdf) | European English manual; edition year not established from inspected pages. Printed pp. 3–4, `Vehicle Identification Information` / `Vehicle Identification Label`. | Redistribution permission not established. |

The PDF contents were retrieved and inspected, including V25 and P21 when the
web reader could not open them. The public Polestar page's linked PDFs were
identified in its JavaScript page bundle; no vehicle query was made.

## Make-by-make findings

All positions below are one-based. **Verified table** means a primary-source
table was actually inspected; it does not mean an implementation-ready import
has passed source reconciliation or legal review.

| Make | Evidence strength | What the inspected rules can decode | Concrete scope / gap |
| --- | --- | --- | --- |
| Ford | Verified table | F25: position 4 restraints/brakes/weight class; 5–7 line, body and series; 8 engine; 10 year; 11 plant; 12–17 sequence. | MY2025 Econoline, Explorer and F-650/F-750 tables verified. Explorer p. 9 is a useful first slice. European Focus/Fiesta/Transit rules remain unverified. |
| Lincoln | Verified table | F25 p. 11 maps Aviator configuration, engine, restraints, weight class and plant. Position 5–7 `J7X` identifies Reserve AWD; 8 `C` denotes the listed 3.0-litre gasoline V6. | MY2025 Aviator only in inspected US file. Do not extend to Nautilus/Corsair without their tables. |
| Chevrolet | Verified table | GM25: model/series, body, engine, restraint, year and plant; light trucks add chassis and weight/brake classification. | Corvette p. 13; Malibu p. 14; truck/SUV pp. 26–37; EV pp. 49–52; commercial pp. 59–60. MY2025 only. |
| GMC | Verified table | GM25 p. 38 distinguishes Acadia trim and drive through positions 5–6; 8 `S` identifies the listed 2.5-litre turbo engine. | Acadia–Yukon pp. 38–44; electric models pp. 53–55. MY2025 North American scope. |
| Cadillac | Verified table | GM25 p. 11 distinguishes CT4 trim/drive and some manual/automatic variants; engine, body, restraints and plant also encoded. | CT4/CT5 pp. 11–12; CELESTIQ p. 16; SUVs pp. 22–25; EV SUVs pp. 46–48. |
| Buick | Verified table | GM25 p. 18 gives Enclave trim/drive, engine, restraints, weight/body classification and plant. | Enclave, Encore GX, Envision and Envista pp. 18–21; MY2025. |
| Chrysler | Verified table | FCA24 p. 5 maps positions 5–7 to Pacifica/Voyager/Grand Caravan configuration, drive and trim; general engine/plant rules p. 1. | MY2024 MPVs, with Canada/US labels; passenger-car models not covered. |
| Dodge | Verified table | FCA24 p. 5 distinguishes Durango trims and drive layouts; p. 1 supplies engine and plant information. | MY2024 Durango only. Charger/Challenger require separate passenger-car submissions. |
| Jeep | Verified table | FCA24 p. 4 maps 5–7 jointly to model, body, drive, steering side and trim. | MY2024 Wrangler, Gladiator, Compass, Grand Cherokee and Wagoneer families; respect explicit export and right-hand-drive rows. |
| Ram | Verified table | FCA24 pp. 2–3 map 5–7 jointly to pickup/cab/chassis/van variants, drive, bed/wheelbase and trim; p. 1 provides engine. | MY2024 trucks and ProMaster; some codes yield multiple trim names, which must stay ambiguous. |
| Tesla | Verified table | T25 maps model, body/steering, restraints, battery chemistry, motor arrangement/performance category, year, plant and sequence. | Model Y 2025+ with plant-specific semantics. Battery capacity, Autopilot hardware and software purchases are not established by these fields. |
| Volvo | Verified table | V25 printed pp. 1–3: 4–5 engine/motor including fuel, cylinders, displacement, stated power and drive; 6 version divider; 7 model; 8 trim; 7–8 restraints; 10 year; 11 plant. | MY2025 **USA/Canada**. Includes EX30/EX90 plus listed combustion/hybrid models. Table is an initial revision, not a claim to the latest corrections. |
| Polestar | Verified table | P21 pp. 1–2: 4–5 powertrain (`ED` is the listed electric motor); 6 version divider; 7 model/drive; 8 trim; 7–8 restraints; 10 year; 11 plant. | MY2021 **USA/Canada**, Polestar 1/2. Does not cover newer WMIs, Polestar 3/4, or European configuration changes. |
| Land Rover | Verified table | L26 p. 1: 4 identifies Discovery; **5–8 jointly** give trim, weight class, body/seats, engine, gearbox, drive and restraints; 10 year; 11 plant. | MY2026 Discovery. Plant code 2 identifies Nitra, Slovakia. `SAL` alone must not become UK assembly. |
| Jaguar | Verified table | J20 p. 1: 4 identifies F-TYPE; **5–8 jointly** map configuration to trim, coupe/convertible, engine/power, transmission and drive; 10 year; 11 plant. | MY2020 F-TYPE. `C` at 11 identifies Castle Bromwich. Other models/years and European applicability remain unverified. |
| MG | Partial official description; decoding table not found | MG manual identifies VIN locations and separate motor/transmission identifiers. It describes weight, approval, paint and trim information on the vehicle label. | Those label fields are **not proof of VIN encoding**. No defensible engine/model/plant code map was established for current European MGs. |

## Important implementation consequences

- **Market is a rule predicate.** NHTSA explicitly describes its data as covering
  vehicles intended for US sale/importation; other markets can have limited
  results. The Volvo and Polestar PDFs are even more explicit about USA/Canada.
  A manufacturer producing cars in Europe does not establish European-market
  applicability. [vPIC scope](https://vpic.nhtsa.dot.gov/)
- **Year needs a meaning, not just an integer.** Tesla T25 says position 10 is
  model year for Texas/Fremont and calendar production year for Shanghai/Berlin.
  Keep `modelYear` and `productionYear` separate. Its older [2020–2024 Model Y
  manual](https://service.tesla.com/docs/ModelY/ServiceManual/en-au/air/GUID-0C797294-574D-4EE4-8017-C339A7D58411.html)
  also distinguishes WMI use across model years. Do not reuse a current table
  across all Tesla history.
- **MG illustrates another year distinction.** MG Norway explains that its
  marketed/registered model-year designation can follow first registration,
  while the VIN can indicate an earlier MY. This is an official Norwegian
  policy description, not a decoding table or a German registration rule.
  [MG Norway: Modellår](https://www.mgmotors.no/owners/modell%C3%A5r)
- **Match combinations, not invented independent digits.** The Jaguar/Land
  Rover configuration keys span positions 5–8. FCA keys span 5–7. A rule engine
  needs conjunctive position predicates and must preserve alternatives where
  one key describes multiple configurations.
- **Keep source revisions.** Volvo's later [MY2025 update cover letter, October
  24, 2025](https://vpic.nhtsa.dot.gov/mfrportal/home/coverletter/fffb7e2c-1568-4f57-aa43-f08a9e152d7d)
  says it adds engine code `EY`. The inspected initial PDF therefore cannot be
  treated as complete current MY2025 coverage. Fetch and reconcile its revised
  attachment before importing that year.
- **Enrichment is a separate operation.** NHTSA documents supplemental equipment
  research from manuals and other OEM material, beyond the Part 565 encoding.
  A vPIC result field is not, by itself, proof that those characters directly
  encode an option. Build sheets, recalls, service history, installed packages,
  battery health, and owner/mileage data need separate evidence/data services.
  [vPIC Analytical User's Manual 2022, introduction](https://crashstats.nhtsa.dot.gov/Api/Public/Publication/813547)

## Reuse boundary

[NHTSA Terms of Use, Ownership](https://www.nhtsa.gov/about-nhtsa/terms-use)
permits distribution/copying of published public information and disclaims
accuracy and third-party non-infringement warranties. This is a concrete reuse
basis to assess for factual NHTSA records, not an SPDX license grant for all OEM
documents or an automatic CC0 dedication. Its [linking policy](https://www.nhtsa.gov/privacy-policy/linking-policy)
also says NHTSA cannot authorize reuse of copyrighted material on linked sites.

For every source here, retain publisher, exact URL, document revision, retrieval
date, market/model/year constraints and evidence location. Redistribution
permission for OEM-hosted manuals and wholesale OEM tables remains
**not established**. This report records small factual summaries and links;
it does not vendor the documents or transplant their tables into ORvin.

## Recommended order

1. **Tesla Model Y as the European decoding pilot**, after source-specific reuse
   review: unusually explicit primary documentation for Berlin/Shanghai and
   clear separation of model year versus production year. Add bounded rules and
   synthetic cases for each plant/year family before expanding to other Tesla
   models.
2. **A small US-market proof of the richer schema** using Ford Explorer/Aviator
   or GM product pages. Validate combination matching, restraint/engine fields,
   provenance, unknowns and ambiguity. This demonstrates capability without
   claiming German fleet coverage.
3. **Volvo/Polestar for North American imports**, after reconciling revisions;
   seek equivalent European documents before applying these rules to German
   customer vehicles.
4. **FCA and JLR by exact model/year**, retaining export distinctions and
   compound keys. The verified Discovery and F-TYPE tables offer narrow,
   reviewable additions, not complete Land Rover/Jaguar support.
5. **MG remains a research gap.** Obtain an authoritative European service/type
   approval decoding specification with usable terms. Do not substitute
   community guesses or commercial decoder claims.

Before importing any family: pin the document version, inspect table geometry,
reconcile corrections, establish reuse basis, write factual declarative rules,
and create synthetic boundary/ambiguity fixtures shared by both libraries.
