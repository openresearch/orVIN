# KBA WMI directory and market applicability

Reviewed **2026-09-26**. Research only: no KBA WMI rows have been imported into
the runtime dataset, and no existing source scope has been changed.

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

Web pages were inspected as rendered/extracted content; original response-byte
hashes were not captured. Only the directly retrieved SV 3.1 PDF has a byte digest.

## What the directory adds

SV 3.1 pages 4–5 describe manufacturers with national HSNs and special collective
codes, with WMIs included where known. Page 6 contains foreign as well as German
manufacturers. Its columns include HSN, WMI parts 1 and 2, manufacturer label, full
manufacturer name and manufacturer location. This is not a complete global WMI
register. No row-count comparison with NHTSA has been performed, so the number of
additional identifiers is unknown.

The KBA and NHTSA records refer to the same international identifier system;
they are separate datasets with different coverage. A verified WMI assignment
can identify a manufacturer regardless of the caller's registration/sales market.
The publisher's country is provenance, not automatically an applicability restriction.
That is the proposed interpretation of the cited international system, not a
claim that all fields attached to a WMI are globally valid.

Keep legal manufacturer separate from retail make: multiple makes, historical
entities and multiple HSNs can be associated with an identifier. Preserve extended
WMIs and conflicting assignments. An HSN association is not an exact VIN-to-TSN
mapping. WMI alone does not resolve model, year, engine or factory.

## Current implementation

`tools/nhtsa.py` imports WMI assignments without sales-market constraints, while
retaining the source's limits about historical validity. `libs/python/orvin/lookup.py`
applies any explicit assignment constraints; `answer.py` can resolve a unique
normalized make from WMI evidence. Rich NHTSA patterns have a separate US-market
scope and participate in the documented cross-market suggestion policy.

A local smoke check on the compiled-runtime branch with synthetic VIN
`WVWZZZ1KZ5P000001` retained make `VW` for AT, DE, US and JP. This is a behavior
check, not independent ground truth or proof of global completeness.

## Reuse remains unresolved

The inspected 2026 PDF has conflicting notices:

- Pages 4–5 require prior consent for reproduction and dissemination, including parts.
- Page 151 permits reproduction and dissemination with KBA source acknowledgement,
  including digital, partial and indirectly obtained content.

Do not silently prefer the permissive notice, apply the separate FZ 6 open-data
license, or assume transforming the table removes its conditions. Clarify the
applicable terms with KBA before importing or distributing its table. No request
has been sent. The contact printed in this edition is `htyp-wmi@kba.de`.

Once that is resolved, compare full identifiers against NHTSA, review conflicting
legal identities and make mappings, and normalize accepted rows into the common
dataset with source edition, page/row locators, attribution and documented scope.
This is a PDF source: under the existing maintenance policy it requires manual
review and is not automatically included in the structured-data refresh workflow.
