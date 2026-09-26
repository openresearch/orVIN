# ASTRA type-approval reuse and VIN-prefix review

Reviewed 2026-09-26. This review concerns Swiss approval candidates, not a VIN-to-registration service or proof of an individual vehicle's configuration. No customer VIN was used in research.

## Reuse basis

ASTRA specifically designates its type-approval factual data as Open Government Data: [Fahrzeugdaten](https://www.astra.admin.ch/de/fahrzeugdaten), section 1, links the IVZOD repository and requires careful, professional handling. The [type-approval publication notice](https://www.astra.admin.ch/de/news-homologation), “Typengenehmigungsdaten (Sachdaten) ab sofort frei verfügbar”, identifies the post-1995 TXT collection. The [TARGA documentation](https://www.astra.admin.ch/dam/de/sd-web/7fPLSFMqD6JR/informationsprodukte_typengenehmigungsdaten.pdf), version 1.0, 2020-09-01, §1.3 p.3, expressly designates this exact repository's factual datasets as OGD. These statements establish dataset-specific publication status, rather than relying on unrelated ASTRA traffic-platform terms.

The applicable federal OGD framework is [EMBAG, SR 172.019, Art.10](https://www.fedlex.admin.ch/eli/cc/2023/682/de). The [verified official consolidated PDF, 2025-05-01](https://www.fedlex.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/2023/682/20250501/de/pdf-a/fedlex-data-admin-ch-eli-cc-2023-682-20250501-de-pdf-a.pdf), p.5 Art.10(4), permits unrestricted reuse of OGD while preserving special statutory source-credit requirements. Art.10(2), p.4, excludes restricted material from OGD publication. Art.19, p.8, limits the publication obligation for historical data; it does not create a reuse restriction for already published OGD.

**Conclusion:** the combination of ASTRA's express designation and Art.10(4) supports reuse of these published factual records, including a derived candidate index. Record this as **Swiss federal OGD / EMBAG Art.10(4)**, preserve attribution, original source locator and no-warranty notice. Do not label it CC0, CC BY, or a newly discovered ASTRA-specific license. The schema itself states that data and information are without warranty. ASTRA's OGD designation does not establish redistribution permission for unrelated OEM manuals or photographs.

The [current product overview](https://www.astra.admin.ch/dam/de/sd-web/BakiDqfaJMx8/01%20%C3%9Cbersicht%20Informationsprodukte%20Fahrzeugdaten-20260701.pdf), 2026-07-01, pp.21–22 §2.15, describes current TAS exports, mutable records and monthly publication. It specifically includes model identification for the vehicle/parts trade among the intended uses, and says these products are freely available Open Data. Its update interval concerns TAS, not the older TARGA export.

## What the VIN field means

The [TARGA field description](https://opendata.astra.admin.ch/ivzod/2000-Typengenehmigungen_TG_TARGA/2200-Basisdaten_TG_ab_1995/2220-Datenbeschreibung/Basisdaten_TG_ab_1995.pdf), p.2 column N / field 14, maps `06 Vorziffer` to `tgdtxt.VINCODE`. This is the pattern field. Column V / field 22, `12 Fahrgestellnummer`, instead describes the physical location of the chassis marking; it is not an actual VIN value. The [ASTRA FAQ](https://www.astra.admin.ch/de/faq-fahrzeugdaten), “Sind Fahrgestellnummern verfügbar?”, explicitly says actual chassis numbers are not released.

There is formal placeholder documentation in the [TAS JSON schema](https://opendata.astra.admin.ch/ivzod/4000-Typengenehmigungen_TAS/4250-json-Schema/govServices_TypeApproval_Schema.json), directory timestamp 2026-08-03, `$defs.arrayVinPrefix.items.description`: a dot represents an alphanumeric placeholder and letters O, Q and I are prohibited. Each string has maximum length 17. `$defs.arrayVinPrefix` describes possible chassis-number prefixes and allows up to seven entries; `TypeApproval.properties.chVinPrefix` references it. This documents TAS semantics and corroborates the older TARGA interpretation; it is not an express promise that all legacy text is well formed.

Older schema examples are consistent: p.2 gives Aprilia `ZD4VS.00.........`; p.8 remarks narrow it to `ZD4VSS00.........` for two seats and `ZD4VSP00.........` for one seat. The example shows both a positional wildcard and why remarks can qualify a row's specifications. It is a schema example, not an independent vehicle validation.

Grammar assessment and the first projection's chosen boundary:

- Select passenger categories M1/M1G; match only structurally valid 17-character input VINs.
- Keep the original `06 Vorziffer` string and source row. Split only explicit ` / ` alternatives and trim each resulting piece. The implemented first projection accepts **exactly 17** characters from the VIN alphabet plus dots and excludes short, overlength or unexplained strings rather than repairing them.
- Interpret dots as one unknown VIN position. Prefix semantics would support appending wildcard positions to short strings **as a documented project interpretation**, but the first projection deliberately leaves those rows excluded. The source contains short plain prefixes such as Peugeot `VF3LBYHYP` and short dot-padded values such as Audi `WAU...4B.......`; there is no separate legacy specification explicitly defining right-padding.
- Splitting the legacy slash separator into alternatives is also a project interpretation, corroborated by repeated paired masks, not a quoted normative grammar rule. Examples: TG `1AF712` has `WAPB333L0.ME44... / WAPB333L0.UE46...`; TG `1BA143` has extra spaces surrounding its separator. Do not treat an arbitrary slash inside a malformed token as a regex operator.
- Keep each complete approval row together. Several rows can share a mask while differing in engine, transmission, body or permitted variants. Even one surviving row is a Swiss approval candidate, not a proven configuration. Never promote catalogue possibilities into the decoder's known model/engine/trim fields.
- Preserve remarks per candidate. Approval issue/expiry/extension dates do not determine model year or build date. Manufacturer address does not determine assembly location. A match does not establish that the input vehicle was sold or registered in Switzerland.

Survey of the pinned file found 128,215 M1/M1G rows and 2,861 rows with the explicit spaced separator. There are genuine malformed/overlength legacy masks. The scratch survey's initial acceptance counts deliberately did not trim each alternative; they are diagnostic, not the production import inventory. The stricter first import retains 122,273 approvals and 125,065 masks across 247 WMIs and 154 makes; production counts and exclusions remain the importer's responsibility.

## Independent public check

The OEM-signed [BYD SEAL taximeter installation memorandum](https://www.cem.es/sites/default/files/2025-10/05_protocolo_taximetro_byd_seal_eke_cam_00_signed_0.pdf), September 2025 rev.00, Madrid/Spain, p.1, states commercial model SEAL, type EKE, approval `e13*2018/858*00639` and fixed prefix `LGXC`. ASTRA rows `ABJ201`–`ABJ204` agree on model and approval family, with narrower masks `LGXCF6.D.........`, `LGXCH6.D.........` and `LGXCH6.B.........`.

This independent source checks **partial prefix/model/approval concordance only**. It does not validate every ASTRA fixed position, every brand, or prove uniqueness of `LGXC` (ASTRA also has other BYD models beginning LGXC). A synthetic suffix can exercise implementation matching but is not an independently observed car. No permission to redistribute the full CEM/OEM PDF was established; retain its citation/digest and narrowly derived evidence only.

## Inspected-byte provenance

All sizes/digests below were measured locally; no downloaded research document is proposed for package redistribution. Scratch downloads are under `target/research/astra-review/`.

| Source | Bytes | SHA-256 |
|---|---:|---|
| [TG-Automobil.txt](https://opendata.astra.admin.ch/ivzod/2000-Typengenehmigungen_TG_TARGA/2200-Basisdaten_TG_ab_1995/TG-Automobil.txt), existing import snapshot | 322893637 | `5851dc2bf2cd06efee42a380e75b661eafa4b577a2edc8ecca2269cb9f950b4b` |
| TARGA field description linked above | 776387 | `a6a62e9f48fdf11749d279edcefbed67cfeb7c77fbc071488a7f996397d18c84` |
| TAS JSON schema linked above | 65421 | `5fb35f59455aca0983a36328bfb11e418e05f7af98b82579874ca216b2523d9d` |
| EMBAG consolidated PDF linked above | 247250 | `996b8d697fdfd9278e453b7fff832601a7739bcd914ba9a7c16e0d0d903b0149` |
| BYD SEAL memorandum linked above | 1658269 | `acf011e8ace21a9f7ca0c4808ca17369c37a2d4694a82a5549396ee399610c46` |

ASTRA website pages and the two ASTRA overview PDFs were inspected through the web tool. Direct byte retrieval was reset by the server, so no byte digest is asserted for those versions. The newer TAS schema is a promising future replacement for free-text alternative parsing; moving the importer to TAS is a separate reviewed change.
