# KBA WMI directory and market applicability

Reviewed **2026-09-26**. Implemented in the source checkout: 5,261 directory rows
for 3,827 valid identifiers, including 3,054 identifiers absent from the NHTSA
September 2026 WMI projection. See [the import guide](../../kba-wmi-data.md)
and [KBA/NHTSA conflict analysis](comparison.md).

## Inspected sources

- KBA, [World Manufacturer Identifier portal](https://www.kba-online.de/wmi_prod/webapp-nezo/),
  introduction and three-/six-character examples, inspected in the browser.
  KBA assigns WMIs to manufacturers headquartered in Germany. Extended identifiers
  use VIN positions 1–3 and 12–14. The portal links to the current annual directory.
- KBA, [Hersteller von Kraftfahrzeugen und -anhängern](https://www.kba.de/DE/Themen/Typgenehmigung/CoC_Daten_Fahrzeugtypdaten/Veroeffentlichungen/SV3.html?nn=3505666),
  download table, inspected in the browser. Both SV 3.1 (alphabetical) and SV 3.2
  (numerical) are dated 15 January 2026. Other formats are offered on request as
  paid work; this is not evidence of an open structured download or API.
- KBA, [SV 3.1, 15 January 2026](https://www.kba.de/SharedDocs/Downloads/DE/SV/sv31_pdf.pdf?__blob=publicationFile&v=3),
  official PDF retrieved and text-extracted locally. 151 PDF pages, 1,274,271 bytes;
  SHA-256 `d4a7daa14f46571fbcbe1e242567f0c1b79dd49793ea916e57b740c0495440f8`.
  The original is not committed or packaged. Page numbers below are one-based PDF
  page numbers, not the printed table pagination. Page 1 identifies the edition;
  pages 4–5 explain scope; page 6 begins the manufacturer table; page 151 is the legal notice.
- ISO, [ISO 3780:2009](https://www.iso.org/standard/45844.html), public abstract:
  WMI is an international manufacturer-identification system forming the first
  section of the VIN. The full paid standard was not obtained or copied.
- NHTSA, [vPIC FAQ](https://vpic.nhtsa.dot.gov/api/Home/Index/FAQ),
  “Foreign Vehicle Information”: foreign-vehicle decoding coverage depends on
  manufacturer submissions for intended US importation, use or sale.
- NHTSA, [interpretation NCC-240821-001, 11 September 2024](https://www.nhtsa.gov/es/node/141061),
  “Background and Relevant Provisions”, “Country of Manufacture” and “BMW Interpretation”:
  international coordination of WMI assignments; KBA's assignment role; WMI alone
  does not establish the vehicle's assembly country. This is an agency interpretation,
  not a statement that every country's VIN rules are identical.

Web pages were inspected as rendered/extracted content without original response-byte
hashes. The directly retrieved SV 3.1 PDF has the byte digest recorded above.

## What the directory adds

SV 3.1 pages 4–5 describe manufacturers with national HSNs and special collective
codes, with WMIs included where known. Page 6 contains foreign as well as German
manufacturers. Its columns include HSN, WMI parts 1 and 2, manufacturer label, full
manufacturer name and manufacturer location. This is not a complete global WMI
register. The reproducible comparison with NHTSA is retained in
`data/kba-wmi/comparison.json`; repeated entries remain correlated alternatives.

The KBA and NHTSA records refer to the same international identifier system;
they are separate datasets with different coverage. A verified WMI assignment
can identify a manufacturer regardless of the caller's registration/sales market.
The publisher's country is provenance, not automatically an applicability restriction.
That is the implemented interpretation of the cited international system, not a
claim that all fields attached to a WMI are globally valid.

Keep legal manufacturer separate from retail make: multiple makes, historical
entities and multiple HSNs can be associated with an identifier. Preserve extended
WMIs and conflicting assignments. An HSN association is not an exact VIN-to-TSN
mapping. WMI alone does not resolve model, year, engine or factory.

## Current implementation

`tools/kba_wmi.py` extracts the pinned PDF and the common compiler emits generic
rules for its directory facts in every market. These facts remain distinct from
retail make and vehicle HSN/TSN; repeated rows are preserved in long output.

`tools/nhtsa.py` imports WMI assignments without sales-market constraints, while
retaining the source's limits about historical validity. `libs/python/orvin/lookup.py`
applies any explicit assignment constraints; `answer.py` can resolve a unique
normalized make from WMI evidence. Rich NHTSA patterns have a separate US-market
scope and participate in the documented cross-market suggestion policy.

A local smoke check on the compiled-runtime branch with synthetic VIN
`WVWZZZ1KZ5P000001` retained make `VW` for AT, DE, US and JP. This is a behavior
check, not independent ground truth or proof of global completeness.

## Reuse basis and attribution

The reuse basis is **SV 3.1, 15 January 2026, PDF page 151 (Impressum,
Copyright)**. It permits reproduction and dissemination with KBA source
acknowledgement, including partial, digital and indirectly obtained content.
The runtime uses `LicenseRef-KBA-SV31-Attribution`, an orVIN descriptive identifier
for that notice, not an SPDX-listed license or a CC0 dedication.

Required credit identifies Kraftfahrt-Bundesamt, Flensburg, SV 3.1, edition
15 January 2026, retrieval 26 September 2026, the exact dataset URL and copyright
page. The modification statement identifies extraction/normalization by orVIN.
The source record, original PDF digest and full assessment are in
`data/kba-wmi/metadata.json` and travel with every installed package. Long output
credits the directory evidence; short output credits the primary facts it exposes.
No publisher endorsement is implied. The original PDF is not redistributed.

The import preserves page/row locators, missing cells and repeated identifiers.
WMI/HSN associations are many-to-many; no vehicle HSN/TSN, retail marque,
assembly location, model or model year is inferred from these directory entries.
Invalid printed identifiers are recorded as exclusions, not silently corrected.
This PDF source remains manually reviewed and is outside automatic source refreshes.
