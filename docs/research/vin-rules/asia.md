# Asian makes: public VIN rule evidence

Discovery and verification date: **2026-09-25**. This is the Asian portion of a practical 50-make survey, not a sales ranking. These findings are research candidates; no rules from this report have been added to either library. No customer VIN was submitted to an external service.

All character positions below are one-based. “Verified table” means the cited document contains an actual mapping, not that its complete contents, applicability, or licensing are ready for import. PDF page numbers count from the first PDF page unless a printed page is specified. US Part 565 submissions apply to their stated models, model years, and markets; manufacturing in Japan or Europe does not establish applicability to Japanese or European deliveries. A document's year-code table does not establish that its other rules apply across all those years.

## Shared discovery and reuse findings

The [official NHTSA Manufacturer Information Database](https://vpic.nhtsa.dot.gov/mid/) exposes a Part 565 search. Searching the manufacturer's legal name finds many documents absent from search-engine results. Manufacturer-detail pages mostly show Part 566 history and are insufficient by themselves. The public search page's table endpoint, `POST https://vpic.nhtsa.dot.gov/mid/AjaxHandler/AjaxHandler565TopLevel`, accepts the form's manufacturer-name and date filters. At verification, its `aaData` records supplied the model-year range and document UUID used by `/mid/home/displayfile/<UUID>`. This is an observed website interface, not a promised stable API.

[NHTSA's terms, Ownership section](https://www.nhtsa.gov/about-nhtsa/terms-use), allow copying and distribution of information presented on the site. That is a concrete candidate reuse basis for NHTSA-published information, but is not a CC0 dedication. Its disclaimer also makes no guarantee concerning third-party rights. Several OEM documents retain explicit proprietary notices. **OEM-specific redistribution permission for the underlying tables/PDFs has not been established in this survey.** Preserve the publisher, original notices, scope, revision, retrieval date, URL and checksum; resolve the import basis before distributing rule datasets or original documents. Summaries and small illustrative facts below are not wholesale table copies.

## Per-make evidence

### Toyota — verified table, narrow US model scope

- Source: [2025MY Subaru and Toyota GR86 Part 565 submission, GR24-056, 2024-10-30](https://vpic.nhtsa.dot.gov/mid/home/displayfile/72bb4585-2803-4a75-a8dd-47b21498cc21), PDF p.12, Attachment XI (chart dated 2024-07-09), US sales.
- Verified: `JF1` is Subaru manufacture; positions 4–5 `ZN` identify the Toyota GR86 coupe in this scheme. The chart supplies engine, trim, restraints, year and plant/transmission combinations. Position 11 distinguishes 6AT/6MT as well as plant. Thus the vehicle's brand cannot always be inferred from manufacturer identity alone.
- Separate evidence: [Toyota Vehicle Specification](https://www.toyota.com/owners/vehicle-specification/) advertises color and installed equipment from a VIN lookup. This is **database enrichment**, not publication of VIN character rules.
- Gap/reuse: other Toyota models and EU VINs need their own tables. NHTSA policy above is a candidate basis; OEM redistribution permission not established.

### Lexus — verified table, US MY2022 IS

- Source: [22MY Lexus IS Vehicle Identification Number Coding System, 22-06-015-00](https://vpic.nhtsa.dot.gov/mid/home/displayfile/e62fe25d-d6e3-4d9a-b6e7-563121fd6c45), PDF pp.2–3, sections 1–4, NHTSA US submission.
- Verified: positions 1–3 manufacturer/type; 4 body/trim; 5 engine; 6 restraint equipment; 7 series and drive configuration; 8 make/line; 10 year; 11 plant. The engine table includes displacement, cylinders, injection and rated power. Position 11 `5` identifies Tahara in this scoped chart.
- Gap/reuse: this cannot become a generic Lexus or European IS rule. NHTSA policy is a candidate basis; OEM redistribution permission not established.

### Honda — verified table, US MY2023 CR-V

- Source: [Vehicle Identification Numbers, American Honda, 2022-05-10](https://vpic.nhtsa.dot.gov/mid/home/displayfile/72a52595-5bd6-4457-af90-39f7f8e2c3e9), PDF pp.2–4.
- Verified: p.2 supplies WMI, positions 4–8 model code, 9 check digit, 10 model year, 11 plant and 12–17 production sequence. P.3 maps complete five-character codes to trim, 2WD/4WD, CVT, five-door SUV, weight class, restraints and engine. P.4 supplies the engine's fuel, cylinders, displacement, power and turbo information. Example: `RS3H2` is CR-V LX 2WD CVT under this scheme.
- Gap/reuse: header lists Honda and Acura WMIs, but the attached model table is CR-V-specific. European CR-V coverage is not established. NHTSA policy is a candidate basis; OEM redistribution permission not established.

### Acura — verified table, US MY2026 RDX

- Source: [Vehicle Identification Numbers, American Honda, 2025-07-09](https://vpic.nhtsa.dot.gov/mid/home/displayfile/d511b7b9-2cea-4576-9899-f113bee1c71b), PDF pp.2–4.
- Verified: `5J8`, year `T`, plant `L` (East Liberty) and positions 4–8 model-code table. That table distinguishes RDX equipment grades and gives 4WD, ten-speed automatic, five-door SUV, weight class, restraints and engine. The engine-characteristics page describes the K20C4's 2.0-litre gasoline turbo four and rated power.
- Gap/reuse: only this RDX model year is established; do not project a US Acura table onto a Honda sold elsewhere. NHTSA policy is a candidate basis; OEM redistribution permission not established.

### Nissan — verified tables, US MY2025

- Source: [Model Year 2025 Vehicle Identification Number Coding System, W-2352-E, 2024-12-04](https://vpic.nhtsa.dot.gov/mid/home/displayfile/78f9a1e7-b33f-4550-b06c-a0b00b19a85f), PDF pp.4–14.
- Verified: model-specific WMI, engine/motor, line, model-change number, body/grade, restraint or chassis/weight/brake combinations, year and plant. Altima p.4 places engine at 4, line at 5, grade/body at 7; MPV layouts require their own interpretation. Ariya p.5 includes battery/motor alternatives.
- Gap/reuse: not European Qashqai/Juke rules. NHTSA policy is a candidate basis; OEM redistribution permission not established.

### Infiniti — verified tables, US MY2025

- Source: [Nissan W-2352-E](https://vpic.nhtsa.dot.gov/mid/home/displayfile/78f9a1e7-b33f-4550-b06c-a0b00b19a85f), PDF pp.15–18, QX50/QX55/QX60/QX80.
- Verified: QX50 p.15 supplies `3PC`, 2.0-litre engine code, line, grade/body, drive/restraint/weight combinations, year and COMPAS plant. QX55 p.16 supplies a distinct grade table despite the shared manufacturer and engine.
- Gap/reuse: country of retail sale and unlisted options remain unknown. NHTSA policy is a candidate basis; OEM redistribution permission not established.

### Mazda — verified table, US MY2026 CX-30, with serial boundaries

- Source: [Subsequent Amendment of 2026 Model Year VIN Coding for CX-30, NH26/1, dated 2026-01-08](https://vpic.nhtsa.dot.gov/mid/home/displayfile/09dda193-d8de-441e-916a-5e87d57a3d1a), PDF pp.2–3. Retrieved directly from the official MID because the web text tool could not open the new URL.
- Verified: p.2 defines layout and plant codes; p.3 maps `3MV`, `DM`, restraint/weight/drive, grade/body, engine, year and plant. **Position 7 trim interpretation changes within MY2026:** the chart separates production through 2025-12-31 (serials 100009–126756) from production starting 2026-01-01 (126759 onward). Some codes still identify multiple trims. Do not fill the serial gap by inference.
- Gap/reuse: a generic header also mentions an Israel WMI, but that does not widen the attached CX-30 table to Europe. NHTSA policy is a candidate basis; OEM redistribution permission not established.

### Subaru — verified tables, US MY2025

- Source: [GR24-056, 2024-10-30](https://vpic.nhtsa.dot.gov/mid/home/displayfile/72bb4585-2803-4a75-a8dd-47b21498cc21), PDF pp.2–11, model-specific attachments.
- Verified: Legacy, Outback, Impreza, Crosstrek, Forester variants, Ascent, WRX and BRZ charts provide model/body, engine, grade/options, restraints, weight where applicable, model year and plant/transmission. WRX p.10 distinguishes CVT and 6MT using position 11. Specific package equipment is sometimes encoded, not universally absent from VINs.
- Gap/reuse: each model has its own scheme; these are explicitly US-sale vehicles. NHTSA policy is a candidate basis; OEM redistribution permission not established.

### Mitsubishi — verified table, North American MY2018

- Source: [2018 Model VIN Codes, effective November 2017](https://static.nhtsa.gov/odi/tsbs/2017/MC-10127435-9999.pdf), single-page Mitsubishi Motors North America chart archived by NHTSA.
- Verified: 1 country, 2 manufacturer, 3 vehicle type, 4 restraints/weight grouping, 5–6 car line/series, 7 body, 8 engine, 9 check digit, 10 year, 11 plant, 12–17 sequence. Engine alternatives include a PHEV combustion/electric combination. Some series codes cover several trims; some mappings are Canada-only.
- Gap/reuse: historical, not current or European coverage. Explicit 2017 Mitsubishi copyright; redistribution permission not established, notwithstanding NHTSA's general publication policy.

### Suzuki — verified historical table, US/Canada MY2002

- Source: [archived Vehicle Identification Number Coding System, 01-022-N11B-8603](https://static.nhtsa.gov/nhtsa/downloads/MfrMail/01-022-N11B-8603.pdf), PDF p.3 “2002 Model Year SUZUKI AERIO”; p.2 Vitara family and p.4 Esteem are additional leads.
- Verified on Aerio page: WMI `JS2`; position 4 line; 5 body/drive combination; 6 engine; 7 design sequence; 8 body; 9 check digit; 10 year; 11 Kosai plant; 12–17 sequence. The page expressly limits its WMI description to US and Canada.
- Gap/reuse: the archive's first page is an unrelated Subaru cover letter, so provenance must cite the actual Suzuki page, not assume the wrapper describes it. Current European Suzuki tables not verified. NHTSA policy is a candidate basis; OEM redistribution permission not established.

### Hyundai — verified table, North America/Mexico MY2027 Nexo

- Source: [2027MY V.I.N Decoding Guide, Hyundai Nexo, 2026-08-18](https://vpic.nhtsa.dot.gov/mid/home/displayfile/3060a9c9-a21b-4251-985d-8609979cf0ae), PDF pp.2–3; directly retrieved from MID.
- Verified: `KM8`; 4 make/line; 5 series; 6 body/drive/weight; 7 restraint code; 8 FCEV powertrain; 9 check digit; 10 year; 11 Ulsan plant; 12–17 sequence. The restraint table names North America/Mexico. This is a future model year documented before the discovery date.
- Gap/reuse: not European Nexo coverage. Explicit HATCI information-asset/protection notice; redistribution permission not established. Do not mistake a public submission for an open license.

### Kia — verified table, US-built MY2025 EV6

- Source: [2025MY V.I.N Decoding Guide, cover 2024-11-20, chart 2024-11-12](https://vpic.nhtsa.dot.gov/mid/home/displayfile/cb5fa075-7db5-45f4-8f77-d6aac7cb02ed), PDF pp.2–3, Georgia-built EV6.
- Verified: `5XY`, 4 make/line, 5 grade group, 6 body/drive/weight, 7 restraints, 8 electric powertrain, 10 year and 11 plant. Powertrain codes describe battery electrical characteristics and front/rear motor output. A grade code covers Light, Light Long Range and Wind together, so it cannot uniquely return one trim.
- Gap/reuse: do not apply this to Korean-built European EV6s. Explicit HATCI proprietary notice; redistribution permission not established.

### Genesis — verified table, US MY2027 G70

- Source: [27MY V.I.N Decoding Guide, Genesis G70, 2026-07-17](https://vpic.nhtsa.dot.gov/mid/home/displayfile/abf674e9-c74c-4b54-8109-8fdf8412e623), PDF pp.2–3; directly retrieved from MID.
- Verified: `KMT`, 4 make/line, 5 series, 6 body, 7 restraints, 8 engine, 10 year, 11 plant. **Series code `6` lists both 2.5T AWD and 2.5T Sport Prestige RWD.** Drive and trim therefore need alternatives rather than an invented single answer. Engine and plant are separately documented.
- Gap/reuse: a strong real-world ambiguity fixture; European applicability unverified. Explicit HATCI proprietary notice; redistribution permission not established.

### Isuzu — verified table, US MY2025 medium/heavy incomplete vehicles

- Source: [Isuzu Motors Limited Vehicle Identification Number for 2025 Model Year Vehicles, issued January 2024](https://vpic.nhtsa.dot.gov/mid/home/displayfile/266539cd-0b1b-481c-bd76-5ca86aebca24), PDF pp.2–6, Tables A–I; directly retrieved from MID.
- Verified: 1–3 manufacturer/type; 4 weight/brakes; 5 make/series; 6 cab; 7 chassis; 8 engine; 10 year; 11 plant; **12 model/engine/weight combination; 13–17 sequence**. It covers `JAL` and `54D` manufacture, not just one legal manufacturer. Engine table includes gasoline, diesel and electric alternatives.
- Gap/reuse: revision page removes some entries that remain visible in earlier tables; a curator must reconcile these before import. European D-Max not covered. NHTSA policy is a candidate basis; OEM redistribution permission not established.

### Daihatsu — verified scanned table, US MY1992

- Source: [Daihatsu 1992 Model Vehicle Identification Number Coding System, submission 1991-08-07, 01-22-N11B-4703](https://vpic.nhtsa.dot.gov/mid/home/displayfile/5f717df1-9bfd-44d9-9d7b-8b84ca17c457), PDF pp.2–5 (printed pp.1–4). This is an image-only scan, visually inspected.
- Verified: `JD1` passenger car and `JD2` MPV; positions 4–8 describe body/transmission, car line, model designation, series and engine. Charade and Rocky have different tables. Position 11 has Kyoto/Ikeda plant codes; year `N` means 1992 here, illustrating why a present-day year-cycle guess is unsafe.
- Gap/reuse: no modern EU/Japanese-market coverage established. NHTSA policy is a candidate basis; OEM redistribution permission not established.

### BYD — verified US commercial table; partial European family evidence

- US source: [BYD electric incomplete VIN Coding System, 2025-01-20](https://vpic.nhtsa.dot.gov/mid/home/displayfile/0c69ec59-2c6a-4023-8c16-2ac89e6620e1), PDF pp.1–3, Tables 1–5, MY2025 onward as stated. `LG9` plus positions 12–14 `BYD` forms the extended manufacturer identifier. Positions 4–8 describe commercial chassis line, weight class, cab, brakes and motor-power band; 11 plant; 15–17 serial. This is **not** a Seal/Atto passenger-car scheme.
- European source: [BYD Seal 6 DM-i / Touring type HK taximeter installation memorandum, revision 00, July 2026](https://www.cem.es/sites/default/files/2026-09/20260721_aut_cat_preinstallacio_taximetre_byd_seal_6_dm-i_hk-rev0_csv.pdf), PDF p.2, signed OEM table in a Generalitat de Catalunya document; [CEM catalog](https://www.cem.es/es/node/9456) published 2026-09-16. It associates type HK, both commercial names, approval `e4*2018/858*00275`, gasoline PHEV and fixed prefix `LC0C` for the covered vehicles. The shared prefix does **not** separate sedan from Touring or establish uniqueness among all BYDs.
- Gap/reuse: NHTSA policy is a candidate basis for the US publication; OEM and CEM-document redistribution permission not established. Passenger-car field-by-field rules remain missing.

### Geely — partial official description; passenger-car table not found

- Source: [English owner's manual hosted by Geely Israel](https://geely.co.il/wp-content/uploads/2025/01/%D7%A1%D7%A4%D7%A8-%D7%A0%D7%94%D7%92-%D7%90%D7%A0%D7%92%D7%9C%D7%99%D7%AA-2.pdf), printed p.9, “Owner's Manual and Vehicle Identification”; publication/model year not established from the inspected section. It states that the 17-character VIN contains manufacturer, production year, body variant and assembly-plant information but publishes no character/value mapping there. The [European manuals portal](https://www.geelyauto.eu/geely-manuals) is a further lead, not verified decoding evidence.
- A misleading search hit was checked: [Zhejiang Geely Ming VIN submission, 2024-12-02](https://vpic.nhtsa.dot.gov/mid/home/displayfile/0226b793-3f21-45ca-9697-bca085a86f68) supplies `LB2` motorcycle/scooter rules. It must not be used for Geely passenger cars. Zeekr filings likewise do not automatically cover the Geely marque.
- Gap/reuse: no importable passenger-car mapping established; redistribution permission not established.

## Best-first implementation recommendations

1. **Build scope and ambiguity support before broadening the table count.** Every rule needs market, model-year interval, WMI and relevant pattern constraints. Mazda additionally needs serial/production boundaries; Genesis and Kia demonstrate genuine multiple outcomes; Isuzu and BYD demonstrate nonstandard serial boundaries. Preserve combinations of correlated fields, not independent sets that create nonexistent trim/drive combinations.
2. **For a contained technical pilot, start with Honda CR-V and Acura RDX**, followed by a small Nissan/Infiniti model set. The documents are short or well structured, give useful fields, and have explicit applicability. Clear the concrete reuse basis, curate exact mappings, and add both positive and out-of-scope fixtures. US-only results must say so.
3. **For German/European usefulness, prioritize European OEM evidence next.** The signed BYD type-approval applicability table is a useful narrow lead, not a substitute for a complete EU decoding guide. Seek equivalent OEM homologation, emergency-response and repair documents by market and model; do not import North American rules merely because a nameplate also sells in Germany.
4. **Separate encoded facts from enrichment.** A VIN-pattern table can expose model family, engine configuration, body, certain grades/options, restraints and plant where documented. Color, full as-built option lists, exact build day, registration identity and service history need separate evidence or an OEM database. Even a documented model year is not the exact manufacture date.
5. **Treat this as a source map, not a claim of complete make support.** This survey verified a scoped table for 16 makes, with historical-only examples for some and commercial-only detail for BYD. Geely passenger-car mappings remain unverified. Exhaustive years, revisions, export markets and current coverage still require further curation.
