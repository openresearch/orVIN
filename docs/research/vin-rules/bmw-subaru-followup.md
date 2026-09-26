# European BMW families and historical Subaru Legacy: follow-up research

Reviewed 2026-09-26. **Research only.** This is step 4 of
`docs/plans/automatic-data-and-library-updates.md`; implementation is deferred until
step 5 has succeeded. No rules, fixtures, importers or automated update policies are
changed by this report.

The requested scope is all BMW passenger-car families, including numbered Series,
X, Z, i and distinct M models, with European applicability. Finding a family in a
source does not establish every generation, engine, market or model year. The
Subaru follow-up concerns the user-reported Legacy Kombi / C22 and the `JF1BG5`
prefix. Complete contributed VINs and their identifying serial suffixes were not
submitted to external searches or services.

## Conclusions

Broad BMW model-family support is feasible without relying on forums. The existing
Swiss ASTRA snapshot contains **22,917 rows whose make is exactly BMW**, all marked
M1, covering every numbered Series from 1 to 8 and the modern X, Z, i and M families
listed below. These are approval records, not 22,917 independently observed cars.
Official BMW Austrian and Greek catalogues provide an independent way to associate
many four-character sales/type codes with a model family, generation and variant.

The defensible combination is an exact ASTRA VIN template plus the relevant OEM
code entry. A price catalogue alone does not prove where its code occurs in a VIN.
Do not create a universal European BMW positions-4-to-7 rule or generate unseen VIN
patterns from sales codes. Keep the complete reviewed template, its WMI and its
remarks, and retain uncertainty where matching approval records disagree.

There is no adequately verified universal European BMW model-year or build-date
rule from this research. Catalogue dates, approval dates and generation production
ranges are not the model year of an individual vehicle. Leave those fields unknown
unless a separately scoped source actually resolves them.

For the contributed BMW prefix, two primary sources agree on **X1 xDrive18d** and
the Austrian catalogue adds **E84**. ASTRA provides a corresponding **N47D20C**
engine candidate. For the Subaru prefix, ASTRA supports **Legacy 2.0 4WD**, estate
body and an **EJ20** engine candidate. The meaning of **C22** and the Subaru's
European year encoding remain unverified.

## Primary source register

Every newly inspected source below was retrieved/reviewed on **2026-09-26**.
Digests identify the bytes inspected during this research; the OEM documents are
not redistributed. Stable IDs below are proposed research identifiers, not new
runtime source records. Existing ASTRA IDs must be reused when promoted.

### astra-targa-automobil-2026-07-30 — existing runtime source

- Publisher: Swiss Federal Roads Office (ASTRA).
- Title: Basisdaten TG ab 1995 — TG-Automobil.
- Exact URL: [TG-Automobil.txt](https://opendata.astra.admin.ch/ivzod/2000-Typengenehmigungen_TG_TARGA/2200-Basisdaten_TG_ab_1995/TG-Automobil.txt).
- Edition: the retained snapshot has HTTP Last-Modified 2026-07-30; metadata records download on 2026-09-26.
- Retained file: `data/astra/TG-Automobil-2026-07-30.txt.gz`.
- Raw SHA-256: `5851dc2bf2cd06efee42a380e75b661eafa4b577a2edc8ecca2269cb9f950b4b`.
- Gzip SHA-256: `81cdeab177baf06d7751567f20bfac8d0325b2dbc9fdf068fffbce7a5bd8c63f`.
- Precise locators: TG identifiers in the tables below; columns `04 Marke`, `04 Typ`, `05 Typ; Variante/Version`, `06 Vorziffer`, `07 Karosserieform`, `09 EU-Gesamtgenehmigung`, `25 Motor Typ`, `27 Hubraum`, `28 Leistung kW`, and row remarks.
- Reuse basis: the repository's existing Swiss OGD assessment under EMBAG Article 10(4), including attribution to ASTRA; see `data/astra/metadata.json` and `data/astra/review.json`. This report does not relabel it as Creative Commons.
- Scope: Swiss approval catalogue. Some records cite EU approvals; that does not turn all specifications into established facts about every matching European vehicle. Swiss registration can include parallel imports; it does not itself establish the original destination market.

### bmw-at-programm-2010-09

- Publisher: BMW Group Austria.
- Title: *Programm 2010. Die Preisliste*.
- Exact URL: [BMW Austria original PDF](https://www.press.bmwgroup.com/austria/article/attachment/T0084722DE/130754).
- Edition: September 2010 (`Stand 09/2010`).
- Inspected SHA-256: `9ef4c933d3e1b354877f3f8a04fd2302e9855309d629a3463d1dbeb2ad5d8a5b`.
- Locators: PDF page 16 / printed page 15, X1/E84 table, code column and `VP11` rows; PDF pages 2–17 contain the model tables. Page numbering here is one-based.
- Reuse basis: citation and selected factual cross-checks; original PDF not redistributed; no open document licence was verified.
- Scope: Austrian offered configurations at that edition. The code-to-model association is explicit; its position in a VIN and an individual car's model year are not.

The X1 table distinguishes `VN11` (sDrive18d) from `VP11` (xDrive18d). Both manual
and automatic X1 xDrive18d entries use `VP11`, so that code alone cannot resolve
transmission. The catalogue also provides older 1/3/5/7 Series, Z4 and X-family
tables. It does not provide a 6 Series table in this edition.

### bmw-gr-pricelist-2018-12-19

- Publisher: BMW Group Hellas.
- Title: *ΑΝΑΛΥΤΙΚΟΣ ΤΙΜΟΚΑΤΑΛΟΓΟΣ BMW/MINI* — detailed BMW/MINI price list.
- Exact URL: [BMW Hellas December 2018 PDF](https://www.bmw.gr/content/dam/bmw/marketGR/bmw_gr/footer/explore-bmw/pricelists-archive/2018/model-pricelists/BMW%20Hellas%20%CE%A4%CE%B9%CE%BC%CE%BF%CE%BA%CE%B1%CF%84%CE%AC%CE%BB%CE%BF%CE%B3%CE%BF%CF%82%2012.2018.pdf.asset.1627480431747.pdf).
- Edition: effective 19 December 2018, protocol 63900.
- Inspected SHA-256: `e99bb96e421ddf39ba83243ea86bb08fa41bdb00e34bb6408b4041c5a18240aa`.
- Locators: PDF pages 1–3, BMW model-code/model columns and generation headings; page 4 is MINI and is outside this task.
- Reuse basis: citation and selected factual cross-checks; original PDF not redistributed; no open document licence was verified.
- Scope: Greek offered configurations at that edition; no VIN layout or individual build-date claim.

This fills useful older-family gaps: page 3 includes G32/6 Series GT, G14/G15/8
Series, G02/X4, I01/i3 and I12/I15/i8. It also separates numbered-Series body
variants and M models. For example `BC41` is M850i xDrive under the 8 Series
heading; it must not be normalized to M8 merely because the badge begins with M.

### bmw-gr-pricelist-2026-07-08

- Publisher: BMW Group Hellas.
- Title: *ΑΝΑΛΥΤΙΚΟΣ ΤΙΜΟΚΑΤΑΛΟΓΟΣ BMW* — detailed BMW price list.
- Exact URL: [BMW Hellas July 2026 PDF](https://www.bmw.gr/content/dam/bmw/marketGR/bmw_gr/footer/BMW_Group_Hellas_Pricelist_08.07.2026.pdf.asset.1785212028335.pdf).
- Edition: effective 8 July 2026, protocol 594356 / 08/07/2026.
- Inspected SHA-256: `1f70b3259e51a27ba887aa69dc13f187dade3bc042d53f1ba1acae0b5a245f24`.
- Locators: all four PDF pages, model-code column and generation/family headings; original page layouts were visually checked.
- Reuse basis: citation and selected factual cross-checks; original PDF not redistributed; no open document licence was verified.
- Scope: Greek catalogue entries. Inclusion, including entries marked new, is not proof of production start, model year or VIN-template applicability.

Pages 1–2 cover 1/2/3/4/5/7 Series, their relevant body variants, M2/M3/M4/M5 and
electric derivatives. Page 3 covers X1/X2/X3/X5/X6/X7, iX1/iX2/iX3 and X5 M/X6 M;
page 4 covers XM, Z4 and iX. The NA0 i3 and NA5 iX3 headings require generation
separation from earlier cars with those badges. The catalogue does not establish
all older 6/8 Series, X4 or Z generations.

### bmw-gr-pricelist-archive-2026-09-26

- Publisher: BMW Group Hellas.
- Title: *Ιστορικοί τιμοκατάλογοι* — historical price lists.
- Exact URL: [official price-list archive](https://www.bmw.gr/el/footer/bmw-explore/pricelists-archive.html).
- Edition: live archive inspected 2026-09-26, links covering 2004–2026.
- Inspected HTML SHA-256: `65ecd094055a24294dbb8a96d552c97f2eb6e81bbbac114e3cbe5db02d99193b`.
- Locator: year sections, model-price-list links; optional-equipment lists are a different document class.
- Reuse basis: discovery citation only; no document licence inferred.

This is a promising source for manual expansion across intervening generations.
It is not a uniform machine-readable decoder: the inspected September 2004 list
contains model/price tables without the four-character code column used later.
That PDF is [BMW Hellas September 2004](https://www.bmw.gr/content/dam/bmw/marketGR/bmw_gr/footer/explore-bmw/pricelists-archive/2004/model-pricelists/BMW%20Hellas%20%CE%A4%CE%B9%CE%BC%CE%BF%CE%BA%CE%B1%CF%84%CE%AC%CE%BB%CE%BF%CE%B3%CE%BF%CF%82%2009.2004.pdf.asset.1627480084018.pdf),
proposed ID `bmw-gr-pricelist-2004-09`, six pages, SHA-256
`2af1b47951aecb80fe3f50a6772d04c674ab69b8da4ae2167d6ebdc831bd1a4b`.
Publisher, retrieval date and citation-only reuse basis are as above. A later
administrative acceptance stamp does not change its September 2004 price edition.
Do not schedule automatic PDF-to-rule promotion.

### bmw-uk-dating-documents-2026-09-26

- Publisher: BMW UK.
- Title: *Exporting or importing a BMW or MINI*.
- Exact URL: [BMW UK import/export documentation](https://www.bmw.co.uk/en/more-bmw/exporting-or-importing-a-bmw-or-mini.html).
- Edition: live page inspected 2026-09-26; no publication date asserted.
- Inspected HTML SHA-256: `a23c24069e78346b50d5761158751ed6d08f3e74c1301d3a0d297f44b8e4a431`.
- Locators: importing vehicles over ten years old; requesting documents; explanation of a VIN-specific certificate of conformity.
- Reuse basis: short factual paraphrase and link; page not redistributed; no open licence asserted.
- Finding: BMW offers a dating letter confirming manufacture date. This identifies an OEM-record route, not an offline VIN date algorithm or a publicly downloadable per-vehicle dataset.

### subaru-jp-catalogue-bg5-1997-06

- Publisher: SUBARU Corporation, official SUGDAS catalogue.
- Title: Legacy Touring Wagon GT V Limited, June 1997 catalogue/specifications.
- Exact URL: [official Subaru E-BG5 catalogue entry](https://ucar.subaru.jp/php/catalog/grade.php?cat_id=4501997).
- Edition: the vehicle catalogue entry is June 1997; website retrieved 2026-09-26.
- Inspected HTML SHA-256: `16d245e501b2beab483bed5054f39a42e3b82e4d49e6c88f6496b7e5bc281edd`.
- Locators: vehicle heading; `型式` row (`E-BG5`), door count, engine and drivetrain sections.
- Reuse basis: selected factual corroboration and citation; original page not redistributed; page carries SUBARU copyright, no open licence verified.
- Scope: Japanese domestic GT V Limited. It independently connects BG5 with the Legacy estate family; it does **not** establish the European VIN layout or the European vehicle's trim, turbocharger, output, transmission or year.

## BMW coverage inventory

This inventory uses the retained ASTRA snapshot and the cited OEM editions, not
third-party decoder labels. A TG example shows a research foothold for a family;
it does not promise that its template uniquely resolves every vehicle. In
particular, short fixed portions can overlap other approvals. Before promotion,
review all matching rows and their remarks, not just the representative below.

| BMW family | Representative ASTRA TG and catalogue label | Independent OEM code-table evidence inspected / remaining gap |
| --- | --- | --- |
| 1 Series | 1BB266 — 116i | Austria 2010; Greece 2018 p.1 and 2026 p.1; generations still need separate joins. |
| 2 Series | 1BE811 — 220d | Greece 2018 p.1 and 2026 p.1 distinguish Coupé, Gran Coupé and Active/Gran Tourer. |
| 3 Series | 1BA806 — 323i touring | Austria 2010; Greece 2018 pp.1–2 and 2026 p.1; do not merge body/generation alternatives. |
| 4 Series | 1BD687 — 428i | Greece 2018 p.2 and 2026 p.2, including separate body styles. |
| 5 Series | 1BA801 — 523i | Austria 2010; Greece 2018 pp.2–3 and 2026 p.2. |
| 6 Series | 1BB233 — 645Ci Coupé | Greece 2018 p.3 has G32 GT; that is not independent corroboration for every earlier 6 Series. |
| 7 Series | 1BA813 — 728i AL | Austria 2010; Greece 2018 p.3 and 2026 pp.2–3. |
| 8 Series | 1BA824 — 840Ci | Greece 2018 p.3 has G14/G15; older E31 needs its own corroboration. |
| X1 | 1BB859 — X1 xDrive18d | Austria 2010 p.16 verifies E84/VP11; Greece 2018 p.3 and 2026 p.3 add newer generations. |
| X2 | 1BK425 — X2 sDrive20i | Greece 2018 p.3 and 2026 p.3. |
| X3 | 1BB229 — X3 3.0i | Austria 2010; Greece 2018 p.3 and 2026 p.3. |
| X4 | 1BF192 — X4 xDrive20i | Greece 2018 p.3. ASTRA's approval type may say X3: use the commercial model evidence. |
| X5 | 1BA967 — X5 4.4i | Austria 2010; Greece 2018 p.3 and 2026 p.3. |
| X6 | 1BB573 — X6 xDrive35d | Austria 2010; Greece 2018 p.3 and 2026 p.3. |
| X7 | 1BN857 — X7 M50d | Greece 2026 p.3. M50d is not a separate X7 M family. |
| XM | ABA625 — XM | Greece 2026 p.4, G09. |
| Z3 | 1BA808 — Z3 | ASTRA prefix evidence; matching period OEM code table still needed. |
| Z4 | 1BB196 — Z4 Roadster 2.5i | Austria 2010/E89; Greece 2018 and 2026/G29. Earlier E85/E86 remains a separate review. |
| Z8 | 1BA979 — Z8 | ASTRA prefix evidence; matching period OEM code table still needed. |
| i3 | 1BE809 — i3 | Greece 2018 p.3/I01; 2026 p.1/NA0 is a different generation and body. |
| i4 | 1BY603 — i4 eDrive40 | Greece 2026 p.2, under G26. |
| i5 | ABB579 — i5 eDrive40 | Greece 2026 p.2, G60/G61. |
| i7 | ABA135 — i7 xDrive60 | Greece 2026 pp.2–3, G70. |
| i8 | 1BF174 — i8 | Greece 2018 p.3, I12/I15. |
| iX | 1BX871 — iX xDrive40 | Greece 2026 p.4, I20; facelift and variant codes need exact joins. |
| iX1 | 1XZ164 — iX1 xDrive30 | Greece 2026 p.3, U11. |
| iX2 | ABC516 — iX2 xDrive30 | Greece 2026 p.3, U10. |
| iX3 | 1BS223 — iX3 | ASTRA older G3XE; Greece 2026 p.3/NA5 is a different generation. |
| 1 Series M Coupé | 1BC148 — 1er M Coupé | ASTRA has `WBSUR91..........`; period OEM code-table corroboration still needed. |
| M2 | 1BG874 — M2 | Greece 2018 p.1/F87 and 2026 p.1/G87. ASTRA approval type can say M3. |
| M3 | 1BA803 — M3 | Austria 2010; Greece 2026 p.1/G80/G81; historical generations remain scoped. |
| M4 | 1BF120 — M4 Coupé | Greece 2018 p.2/F82/F83 and 2026 p.2/G82/G83. |
| M5 | 1BA918 — M5 | Greece 2018 p.2/F90 and 2026 p.2/G90/G99. |
| M6 | 1BB315 — M6 Coupé | ASTRA prefix evidence; matching period OEM code table still needed. |
| M8 | 1BQ168 — M8 | ASTRA has `WBSAE01..........`; do not substitute the 2018 M850i entry as corroboration. |
| M Roadster / M Coupé | 1BA856 / 1BA884 | ASTRA has older MR/C entries; period OEM tables and overlap review still needed. |
| X3 M / X4 M | 1BP684 / 1BP686 | ASTRA has `WBSTS01..........` / `WBSUJ01..........`; period OEM table review still needed. |
| X5 M / X6 M | 1BB764 / 1BB765 | Austria 2010/E70/E71 and Greece 2026 p.3/F95/F96. |
| Z1, original M1, pre-1981/historical BMW lines | No matching Z1 or standalone M1 label found in this retained snapshot | Open, usable VIN-pattern evidence not established by this research. Do not advertise complete historic BMW coverage. |

The ASTRA count is reproducible by reading the CP1252, tab-delimited retained file
and counting `04 Marke == "BMW"`; it is not a count of canonical model families or
unique VIN patterns. The matrix deliberately avoids percentage-coverage claims.
BMW ALPINA, MINI, Rolls-Royce and motorcycles require separate make/scope treatment.

## Exact follow-up cases

### BMW: `WBAVP11..........`

ASTRA TG **1BB859**, physical text row **14522** including the header, and
TG **1BC211**, row **14771**, both associate this complete template with X1
xDrive18d. The former has variant `X1; VP11/5A, -/5B`; the latter has
`X1; VP11/5A000, -/5H000`. Their engine entries are N47D20C, 1,995 cc, 105 kW.
Other matching VP11 approvals also exist; keep their correlated alternatives and
remarks rather than selecting the first row as the vehicle's exact specification.

BMW Austria 2010, PDF p.16 / printed p.15, independently confirms VP11 as
xDrive18d under E84. Proposed source lineage:

1. VIN-template association and catalogue variant: the exact ASTRA TG records.
2. Normalized family X1 and E84 generation: the matched ASTRA label plus that OEM code entry.
3. Engine candidate: the matched ASTRA record, not the price-list heading or user attribution.
4. Model year / production date: unknown; neither source gives the contributed car's date.

The user-reported X1 xDrive18d / E84 / N47 is independent validation of those
reported labels. It is not evidence for an exact build date or every engine suffix.
Current local decoding of a synthetic continuation of this prefix returned no
normalized model during research, despite these records already being bundled.
Implementation should inspect the evidence-to-identity projection before adding
duplicate model rules.

### Subaru: `JF1BG5...........`

ASTRA TG **1SC603**, physical row **83651**, is Legacy 2.0 4WD, type BG,
estate body, EU approval `e1*70/156-93/81*0009`, engine EJ20, 1,994 cc and 85 kW.
It supplies the European approval evidence; the Japanese Subaru catalogue only
corroborates that E-BG5 belongs to the Legacy estate family. Its GT V Limited
turbo specification must not be applied to the European case.

Proposed result is Subaru / Legacy, with body and engine retained as sourced
approval candidates where the complete matching set allows them. Preserve the
user's literal C22 label in fixture provenance, with no invented expansion and
no conversion to a 2.2-litre engine. Owner-reported country, model year and exact
trim must remain absent unless actually supplied or independently established.

The tenth-character `V` is compatible with common year tables, but no inspected
primary source establishes the relevant European Subaru layout for this vehicle.
Do not promote 1997 merely because it looks plausible. A period European Fuji
Heavy Industries/Subaru identification chapter or homologation document is still
needed for year, plant, transmission and serial-dependent interpretations.

## Year, plant and production-date limits

BMW's US model-year 2026 Part 565 filing is primary evidence within its declared
US scope. Its exact URL is [NHTSA-hosted BMW filing](https://vpic.nhtsa.dot.gov/mid/home/displayfile/2c3f8c25-36d4-4062-a462-5e08fad3d53b),
SHA-256 `2b093203776818a712aa6fe7cdd059fa2f44b982be461736bd9fadd0e4cb3ea9`,
retrieved 2026-09-26. This is an existing lead in `europe.md`; do not create a
second runtime identity for it. Publisher BMW, hosted by NHTSA, edition MY2026,
locator the VIN breakdown tables; citation-only reuse, original document not
redistributed. It is not evidence that old European BMWs use the same year or
plant rules. The contributed European BMW has `0` in position 10; no year should
be manufactured from it.

A Subaru of America schematic is similarly scoped: [1999 model-year VIN schematic](https://www.northursalia.com/techdocs/pdf/misc/vin.pdf),
proposed ID `subaru-us-vin-schematic-1999`, *The End Wrench*, Winter 1999,
printed p.19 / PDF p.1. Publisher Subaru of America; this copy is hosted by
NorthUrsalia, not the OEM. The page explicitly describes the US 1999 layout;
its Legacy body and engine codes cannot be transferred to the European BG5 case.
It was inspected through the web PDF reader on 2026-09-26; a direct byte fetch
returned HTTP 403, so **no inspected-byte digest is available**. No access-control
workaround was used, no copy is redistributed, and no open reuse licence was
verified. It is a market-boundary cross-check, not a proposed EU runtime rule.

No inspected source provides a serial-number-to-calendar-date algorithm for all
BMWs or the European Subaru. A known catalogue availability range can eventually
be a separately labelled range with its own source, never silently the main
`modelYear` or `productionDate`.

## Secondary leads and rejection notes

The following were reviewed as leads only. They are **not authorities for the
proposed rules**. Their live versions were reviewed on 2026-09-26; no source-byte
archive was retained, therefore no digest is asserted. No redistribution licence
was verified; links and brief review notes are the only retained material.

| Proposed research ID / publisher | Exact source and locator | Assessment |
| --- | --- | --- |
| `bimmerarchiv-vp11-review-2026-09-26` / Bimmerarchiv | [VP11 entry](https://www.bimmerarchiv.de/code/vp11.html), model designation row | Labels VP11 as sDrive18d, contradicting BMW Austria and ASTRA. Reject as authority for this mapping. |
| `x1forum-vehicle-identification-2023` / x1forum.de participants | [Fahrzeugkenndaten thread](https://www.x1forum.de/forum/thread/3635-fahrzeugkenndaten/), August 2023 discussion, particularly post 7 | Useful search lead about engine/type labels; owner anecdotes are not a primary VIN encoding specification. Do not copy participants' VINs. |
| `bmw-identification-guide-2006-unverified` / publisher unverified, Scribd host | [BMW vehicle-identification guide copy](https://www.scribd.com/document/633986993/bmw), February 2006, sections 1.3/1.3.1 | Mentions European layout differences, but carries an official-use-only marking and lacks verified original publication/reuse provenance. Reject for runtime promotion or redistribution. |
| `subaru-jdm-vin-forum-2021` / SL-i.net participants | [List of JDM VINs](https://sl-i.net/FORUM/archive/index.php/t-20241.html), Reuben post dated 2021-02-07 | Applied-model/chassis-code discussion for Japan; insufficient evidence for a European 17-character VIN rule. |
| `subaru-fsm-forum-index` / SL-i.net participants | [factory-service-manual index](https://sl-i.net/FORUM/showthread.php?18087-Subaru-Factory-Service-Manuals) | Candidate route to a period European identification chapter; returned HTTP 403. Contents were not verified and were not bypassed. |

## Proposed implementation after step 5

1. **Audit current normalization against the existing ASTRA records.** The two
   reported prefixes already have useful source evidence. Distinguish a missing
   canonical model alias or evidence-selection problem from a genuinely missing
   source rule. Preserve candidate semantics and conflicting records.
2. **Build a reviewed BMW family/code concordance in shared data.** Start from all
   retained BMW VIN templates, group candidate labels by family, then corroborate
   generation/type mappings with exact OEM rows. Record each join's source IDs,
   catalogue edition/page/code, TG IDs and scope. Reuse existing manufacturer
   normalization; keep true M models separate from M Performance badges.
3. **Expand gaps by generation, not by guessed badge regex.** Review intervening
   official Greek editions, and period sources for Z3/Z8/M6/M8/1M and older cars.
   If only ASTRA supports a family, say so; do not cite an unrelated modern OEM
   table as independent evidence. Do not infer global market coverage.
4. **Promote only reviewed facts.** Keep original complete templates; do not pad a
   sales code into an invented pattern. Maintain all fixed positions, WMI scope,
   approval remarks and correlated specifications. Preserve model ambiguity for
   overlapping templates. No universal BMW or Subaru year rule is proposed.
5. **Validate behavior with independent, attributed labels.** Use the authorized
   user reports for their stated facts, plus independently documented examples
   when available. Synthetic substitutions test matching and exclusions, not
   real-world correctness. Include cross-family negatives, M-performance versus
   M-model cases, electric-generation name reuse, and unknown-year assertions.
   Run both libraries' required dataset, parity and packaging checks when code or
   rules change.

This report adds research citations only. To include it in the repository's
existing citation audit, the coordinating change must add
`bmw-subaru-followup.md` to `RESEARCH_FILES` in `tools/provenance.py` and regenerate
`docs/research/vin-rules/sources.json`. That inventory registration is deliberately
left to the coordinating agent; it must not be mistaken for runtime-rule approval.
