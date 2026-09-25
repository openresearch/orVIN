# European makes: public VIN rule research

Discovery and inspection date: **2026-09-25**. This is a 17-make slice of a practical
50-make survey, not a sales ranking. These findings are research, not implemented
decoder coverage. No customer VIN was submitted to an external service.

## How to read the evidence

- **Verified table**: an actual OEM or authority-hosted document was opened and a
  table or explicit character rule was inspected. This does not mean all years,
  models, markets, or reuse rights are covered.
- **Partial official description**: useful official explanation, example, or lookup
  documentation exists, but no complete applicable decoding table was established.
- **Submission portal only / not found**: no usable underlying character rule was
  inspected. Absence in this survey does not prove none exists.

US Part 565 filings below are scoped to the stated US model year. A European WMI
does not make a US VDS table applicable to a European-market car. Full build sheets,
paint, installed options, service history, and recalls retrieved using a VIN are
database enrichment unless a source explicitly proves their encoding.

## Coverage index

| Make | Strongest evidence inspected | Practical next scope |
| --- | --- | --- |
| Volkswagen | Verified table; US MY2026 plus UK year explanation | US VDS tables; separately bounded European model-year rule |
| Audi | Verified table; US MY2026 | Annual US passenger-car/MPV tables |
| Škoda | Partial official description with explicit worked rules; 2023 | Narrow Octavia/Enyaq examples, further scope verification |
| SEAT | Partial official description | Find official model/year/plant tables |
| CUPRA | Partial official description | Find brand/model-specific tables |
| Porsche | Verified table; North American bulletin, January 2025 | Versioned model-family and plant rules |
| BMW | Verified table; US MY2026 | WMI plus positions 4–8 and year, plant |
| MINI | Verified table; US MY2026 | WMI plus positions 4–8 and year, plant |
| Mercedes-Benz | Verified table; US MY2019 | Model/engine/restraint and WMI-dependent plant rules |
| smart | Verified table; US MY2019 | Historical EQ fortwo only |
| Opel | Verified narrow applicability table; Spain, 2025 | Astra family evidence; uniqueness still unproven |
| Vauxhall | Partial official description | Owner/manual and lookup evidence, no character table found |
| Renault | Verified narrow applicability table; Spain, 2023 | Scenic IV family evidence |
| Dacia | Verified narrow applicability table; Spain, 2023 | Sandero DJF family evidence |
| Peugeot | Verified narrow applicability table; Spain, 2023 | Rifter family evidence |
| Citroën | Partial official description | Documented build-data lookup, no sufficient decoder rule |
| Fiat | Verified EU VIN-format/type-approval table; page dated 2024 | Type-family candidates after wildcard/overlap review |

## Detailed findings

### Volkswagen

**Verified table.** [2026 Volkswagen U.S. VIN Breakdown](https://vpic.nhtsa.dot.gov/mid/home/displayfile/4bb6e581-1ca4-4087-a0fe-583fe6961468),
submission dated 2025-10-08. PDF pages 3–4 cover passenger cars; pages 5–8 cover MPVs.
The table assigns positions 4 to series/variant, 5 to engine, 6 to restraints,
7–8 to model, 9 to check digit, 10 to model year, 11 to plant, and 12–17 to sequence.
For US MY2026, model code `CD` covers GTI/Golf R, so that code alone does not resolve
the variant. Engine rows carry fuel, displacement, cylinders, power and emissions
certification attributes. Do not apply them to European `ZZZ` VDS patterns.

**Separate European evidence:** [Volkswagen UK: explanation of the tenth VIN character](https://www.volkswagen.co.uk/en/owners-and-services/my-car/xtl-diesel-fuel.html/__layer/layers/owners/my-car/xtl_diesel_fuel/modelyear/master.layer)
explicitly identifies position 10 as model year, with a 2010–2025 table, in an
XTL diesel compatibility explanation. It does not supply a full VDS/plant decoder
or justify extending that table to every historical year.

**Historical European Golf 1K around MY2005 remains unresolved.** Volkswagen's
[archival Golf V profile](https://www.volkswagen-newsroom.com/en/vehicle-data-golf-5-profile-19481)
explicitly identifies the Golf V factory type as `1K` and lists variants produced
during 2005. This verifies a model-family fact, not a VIN position rule: the page
does not establish that positions 7–8 uniquely identify that family, how a 2005
European VIN encodes its model year, or the applicable position-11 plant mapping.
The targeted official-source search did not establish that historical decoder.
Neither the 2026 US filing nor the UK 2010–2025 year table closes this gap.

**Reuse:** redistribution permission not established for the OEM filing or UK
page or archival profile. Public NHTSA hosting is not itself an OEM open license.

### Audi

**Verified table.** [2026 Audi VIN Breakdown Sheet for U.S. Models](https://vpic.nhtsa.dot.gov/mid/home/displayfile/63e38c13-e5a1-4991-b2b9-1812f3e61d66),
seven-page Part 565 filing; inspect the passenger-car and MPV breakdown sheets and
their engine charts. Positions 4/5/6 encode series, engine and restraint pattern;
7–8 identify the model family; 9/10/11/12–17 give check digit/year/plant/sequence.
For example, `GY` in 7–8 groups A3/S3/RS 3; `T` at 10 is MY2026. Model and WMI must
constrain the other character lookups.

[Another 2026 MPV revision](https://vpic.nhtsa.dot.gov/mid/home/displayfile/4e404c82-7775-468b-bdcb-1a16847e9f29)
is an additional discovery lead; it should be compared for supersession before
importing, rather than combining conflicting revisions blindly. European-market
coverage is not established by the US table.

**Reuse:** redistribution permission not established.

### Škoda

**Partial official description with explicit examples.** [What can VIN codes tell you?](https://www.skoda-storyboard.com/en/skoda-world/what-can-vin-codes-tell-you/),
Škoda Auto, 2023-06-13, sections “Vehicle Descriptor Section” and “Every code is an
original”. The Octavia example identifies position 4 `J` as estate/LHD/single-axle
drive, 5 `R` as 1.5 TSI 110 kW, 6 as restraint information, 7–8 `NX` as Octavia,
10 `P` as MY2023, and 11 `Y` as Mladá Boleslav. The article also describes Enyaq
position-5 power codes. This is a useful European source but not an exhaustive
generation/market/date applicability matrix. It explicitly distinguishes model
year from manufacture year and notes plant-code exceptions.

**Reuse:** [Storyboard copyright terms](https://www.skoda-storyboard.com/en/copyright/)
restrict duplication/distribution; the limited news-use permission is not an open
dataset license. Redistribution permission for a rule collection is not established.

### SEAT

**Partial official description; character table not found.** [Leon owner's manual,
MY15 week 22, English UK](https://www.seat.com/datamanual-manual/leon/my15_w22/en-uk/Gama%20Leon_EN.pdf),
“Technical specifications / Vehicle identification data”, distinguishes the VIN
from separate data-sticker fields: model, engine/gearbox codes, paint and options.
Those sticker values must not be represented as information decoded from the VIN.
[SEAT CONNECT FAQ](https://www.seat.com/faqs/seat-connect), “What is the vehicle
identification number…”, establishes identification/location only. Searches of
official SEAT material and the CEM catalog did not establish a usable official
position-to-model/year/plant table. Third-party service-manual mirrors were not
accepted as authoritative rules.

**Reuse:** redistribution permission not established. Next step: obtain an
identified, versioned OEM repair-information or type-approval source.

### CUPRA

**Partial official description; character table not found.** [CUPRA Ateca manual,
November 2018, English](https://www.cupra.com/content/dam/public/cupra-website/owners/your-cupra/cupra-cars-manuals/brochures/cupra-ateca/CUPRA_ATECA_11_2018_EN.pdf),
printed page 349, explains VIN location/display and a separate way to display the
engine identification letters. [CUPRA CONNECT Gen4 FAQ](https://www.cupra.com/en/faqs/cupra-connect/gen-4-general-information)
identifies the VIN as a 17-character vehicle identifier. Neither establishes a
decoding table. Do not assume that every SEAT/VW rule or WMI determines CUPRA as a
unique brand. Searches for CUPRA character rules and CEM homologation material did
not yield a verified table in this pass.

**Reuse:** redistribution permission not established.

### Porsche

**Verified table.** [Product Knowledge Binder, Group 16, D8: Chassis/VIN Numbering
Systems](https://static.nhtsa.gov/odi/tsbs/2025/MC-11015103-0001.pdf), Porsche Cars
North America, 2025-01-21, PDF pages 1–2 / printed pages 7–8. It documents model
designation changes across years: positions 7, 8 and 12 for 1981–2009, a changed
position-7 convention from 2010, and exceptions for Taycan/new Panamera/Macan
Electric. Position 11 has a plant table. Positions 4 and 5 describe model/body
and engine categories but explicitly vary by year; the bulletin refers to separate
model-specific sheets for exact meanings. This is strong evidence for a versioned
rule engine, not a single timeless Porsche map. Listed model-year ranges are US.

**Reuse:** explicit Porsche copyright notice on printed page 8; redistribution
permission not established.

### BMW

**Verified table.** [BMW Model Year 2026 Decipherment of VINs in Accordance with
Part 565](https://vpic.nhtsa.dot.gov/mid/home/displayfile/2c3f8c25-36d4-4062-a462-5e08fad3d53b),
one-page US filing, inspected as extracted text and rendered page. The matrix
combines positions 1–3 and 4–8 with MY2026 to identify model/series, body, fuel,
cylinders, power, displacement and restraint layout. Position 11 has a separate
plant/country table. Examples: `WBA` + `83GG0` and `WBA` + `23GG0` distinguish 228
Gran Coupe from its xDrive version. Search snippets merged some rows incorrectly;
the actual PDF is necessary for transcription. A German WMI alone does not give
the factory, and this filing does not establish European BMW VDS applicability.

**Reuse:** redistribution permission not established for the OEM submission.

### MINI

**Verified table.** [MINI Model Year 2026 Decipherment of VINs in Accordance with
Part 565](https://vpic.nhtsa.dot.gov/mid/home/displayfile/a1a5c253-5568-4ccf-a136-b842ed51d955),
one-page US filing, inspected as rendered PDF and text. Positions 4–8 are a combined
model/body/engine/restraint pattern; the right-hand table supplies fuel, power,
displacement and MPV weight class. `WMZ` + `23GA0` identifies Countryman S ALL4 in
this filing; other patterns distinguish Cooper/Cooper S/JCW body variants. Position
10 uses `T` for MY2026 and position 11 has plant entries, including `2` for Oxford
and `7` for Leipzig. Do not infer that each VDS character independently represents
the same field across all MINI generations. Search snippets had incorrect column
alignment.

**Reuse:** redistribution permission not established.

### Mercedes-Benz

**Verified table.** [Mercedes-Benz and smart VIN Attributes for Model Year 2019](https://vpic.nhtsa.dot.gov/mid/home/displayfile/dc5b88a3-b353-47d9-827b-088b758dee47),
dated 2018-07-25, US Part 565 submission. Pages 1–3 and 5 combine WMI and positions
4–7 with model/body, displacement, engine code, power, transmission and fuel.
Page 4 documents position 8 restraints, 9 check digit, 10 model year, 11 plant,
and 12–17 sequence. Plant code meanings depend on WMI. Scope this to MY2019 US
patterns; the European numeric type-code layout and later models need separate
evidence.

**Reuse:** redistribution permission not established.

### smart

**Verified table, narrow historical scope.** The same [2019 Mercedes-Benz/smart
submission](https://vpic.nhtsa.dot.gov/mid/home/displayfile/dc5b88a3-b353-47d9-827b-088b758dee47),
page 3, lists `WME` with `FJ9B`/`FK9B` in positions 4–7 for EQ fortwo coupe/cabrio,
including electric powertrain information. Page 4 has WME-specific plant entries.
This does not cover current smart #1/#3/#5 models or prove European fortwo rules.

**Reuse:** redistribution permission not established.

### Opel

**Verified narrow applicability table.** [Opel Astra / Astra Sports Tourer taximeter
installation protocol](https://www.cem.es/sites/default/files/2025-04/05_preinstalacion_opel_astra_f.pdf),
Stellantis España, revision 01, February 2025, Spain. PDF page 1 was downloaded and
visually inspected after web extraction timed out. It relates type `F` and the
Astra/Astra Sports Tourer family to fixed VIN pattern `VXKF*****`, covering all
listed engines, fuels, powers and transmissions. This is evidence of a family
association; it cannot resolve those attributes or prove that all matching VINs
worldwide belong to this family. It supplies no model-year range.

**Reuse:** CEM restrictions apply as described below; redistribution permission
not established. Do not generalize to Vauxhall or historic Opel layouts.

### Vauxhall

**Partial official description; usable character table not found.** [Viva owner's
manual, May 2015](https://www.vauxhall.co.uk/content/dam/vauxhall/Home/PDFs/owners/owners-manuals/viva/om_Viva_kta2779_1-vx-en_eu_ed0515_en_vx_online.pdf),
printed page 205, identifies VIN location and directs engine identification to
the certificate of conformity/registration documents. [Official recall checker](https://www.vauxhall.co.uk/owners/maintenance-and-repair/vehicle-recall-check.html)
uses VIN as a database key; its existence is not an offline decoding specification.
Official-source and NHTSA searches did not establish a make-wide VDS/year/plant
table. Opel or US GM tables must not be copied into Vauxhall coverage without
explicit applicability evidence.

**Reuse:** redistribution permission not established.

### Renault

**Verified narrow applicability table.** [Scenic IV / Grand Scenic IV taximeter
installation protocol](https://www.cem.es/sites/default/files/2023-04/04_protocolo_scenic.pdf),
Renault España Comercial, revision 02, March 2023, Spain. The PDF cover table
associates fixed prefix `VF1RFA` with type `RFA`, Scenic/Grand Scenic IV. Section 2,
PDF page 3, identifies the relevant type approval. Engine/fuel/power/gearbox columns
cover all variants, so the prefix cannot resolve them or separate Scenic from
Grand Scenic. Production/model-year boundaries and prefix uniqueness need further
evidence. This is not a universal Renault year rule.

**Reuse:** CEM restrictions apply; redistribution permission not established.

### Dacia

**Verified narrow applicability table.** [Sandero DJF taximeter installation
protocol](https://www.cem.es/sites/default/files/2023-04/04_protocolo_dacia_sandero_djf_rev.00.pdf),
Renault España Comercial, revision 00, March 2023, Spain. PDF cover table associates
`UU1DJF` with Sandero type `DJF`; section 2 on PDF page 3 gives the type approval.
All engines, fuels, powers and transmissions are included, without identifying
them from the prefix. This is a candidate model-family association and still
needs date/uniqueness constraints. It does not cover all Dacia models.

**Reuse:** CEM restrictions apply; redistribution permission not established.

### Peugeot

**Verified narrow applicability table.** [Rifter / e-Rifter taximeter protocol and
Catalan approval](https://www.cem.es/sites/default/files/2023-11/20231124_aut_cat_preinstallacio_taximetre_peugeot_rifter_e-rifter_e-rev1_csv.pdf),
Stellantis España, revision 01, November 2023; approval 2023-11-24, Spain. PDF page
2 / protocol page 1 lists type `E`, fixed VIN pattern `VR3E*****`, Rifter/e-Rifter
and approval `e2*2007/46*0624`. It deliberately covers all fuels/variants. The
pattern therefore cannot establish electric versus combustion propulsion, precise
engine, or gearbox. It is not a complete Peugeot decoder or proof of global prefix
uniqueness.

**Reuse:** CEM restrictions apply; redistribution permission not established.

### Citroën

**Partial official description, database enrichment established.** [Service Box:
VIN entry](https://service.citroen.com/aides/DOC_OI/AC/documents/fr_FR/AIDE/9889/vin_ac.html)
explains lookup by complete VIN or final eight-character VIS. [Vehicle characteristics](https://service.citroen.com/aides/DOC_OI/AC/documents/fr_FR/AIDE/9900/caracteristiques_ac.html)
explicitly says characteristics are retrieved from the technical reference database
`corvet@`, including gearbox/transmission categories. These undated French-market
help pages document a lookup mechanism, not character rules.

A CEM C4/C4X protocol search lead showed only `VR7******`, which is insufficient
to distinguish models; no decoder rule is accepted from it here. The PDF fetch was
intermittent, and the underlying first-page table was not independently inspected.

**Reuse:** redistribution permission not established. A licensed enrichment
adapter would be a different project from a bundled offline decoder.

### Fiat

**Verified EU VIN-format table.** [Technical Information: Type approvals](https://www.technicalinformation.fiat.com/tech-info-web/web/pageLarge.do?id=467),
Stellantis, page dated 2024-04-14, EU homologation context. It associates models,
approval numbers and VIN formats; for instance Tipo/Egea is shown with a `ZFA356`
opening. Rows expose ambiguity: 500 and some Panda formats share an opening;
other brands also share homologation formats. Zeros in the examples are not a
documented general wildcard grammar. Do not turn each displayed format into a
unique model rule without resolving its variable positions, overlap and dates.
No complete engine/trim/year decoder follows from this table.

**Reuse:** [RMI terms](https://www.technicalinformation.fiat.com/tech-info-web/web/pageLarge.do?id=12),
sections 4 and 5, retain intellectual-property rights and restrict unauthorized
copying/disclosure. Redistribution permission is not established.

## Shared source and reuse observations

The [CEM taximeter catalog](https://www.cem.es/es/content/tax%C3%ADmetros) states
that documents come from autonomous communities or vehicle manufacturers. These
are valuable primary technical leads with explicit revisions. An installation
applicability table is not automatically an exhaustive inverse VIN lookup: the
same pattern may cover other types, markets or years beyond the document's scope.

[CEM's legal notice](https://www.cem.es/es/aviso-legal), intellectual-property
section, reserves rights over hosted content and limits the granted use to
downloading intact material for private use. It does not establish an open license
to republish these OEM tables or transform them into a redistributable dataset.
This survey links and summarizes the evidence; it does not bundle their PDFs.

NHTSA manufacturer submissions are particularly useful because they describe real
VIN patterns. Preserve the OEM author and exact document revision instead of
labeling every document on a `.gov` host public domain. The [vPIC analytical manual,
2024 edition](https://rosap.ntl.bts.gov/view/dot/89793/dot_89793_DS1.pdf), introduction,
also explains that some returned information is supplementary research, including
safety technology data; vPIC output is not uniformly direct character decoding.

## Best-first implementation recommendation

1. Build a source-scoped rule model: WMI/pattern, market, model-year interval,
   document revision/page, individual field provenance, ambiguity and unknowns.
   Require explicit applicability; a later or differently marketed car must not
   silently reuse an older rule.
2. Start technical extraction with the complete **VW/Audi/BMW/MINI US MY2026**
   filings. They are small, detailed, and independently testable. Resolve a
   redistribution basis before bundling tables; table availability and license
   suitability are separate gates.
3. For German/European customers, prioritize verified European VW/Škoda sources
   and additional OEM model-family/plant documentation. Fill in missing dates
   and generations before claiming broad coverage. The US-only work does not
   automatically improve European Golf decoding.
4. Treat Fiat and the CEM documents as a second, narrow model-family project.
   Establish uniqueness/overlaps and a reuse basis first. Their “all engines”
   scope cannot support invented engine, power, gearbox, or fuel results.
5. Keep VIN-keyed OEM build data in an optional enrichment interface. Do not
   imply that an offline string decoder can obtain production options, actual
   equipment, maintenance, recall completion, or HSN/TSN from these sources.

The remaining gaps are source-specific reuse permission, complete European
year/model coverage, latest document supersession, historical layouts, and
brand-sharing/multiple-pattern ambiguity. No new rules were imported in this
research task.
