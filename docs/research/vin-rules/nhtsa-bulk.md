# NHTSA bulk data: feasibility and inspected schema

Reviewed **2026-09-25**. Follow-up implementation now imports all public usable WMIs and embeds
the complete source ZIP in both distributions; see [implemented import](../../nhtsa-data.md).
This assessment describes the source and remaining detailed decoder work, not a claim that
orVIN reproduces NHTSA's full decoding. The original six WMI records were a seed choice.

**Recommendation:** use the official monthly standalone dataset as the shared
data source for both libraries. Export language-neutral tables, retain source
IDs and metadata, and bundle the same generated archive in the Python package
and Java JAR. Broad WMI identification is straightforward. Detailed VIN decoding
also requires implementing the published decoding semantics; possessing every
row alone does not reproduce the decoder.

## Exact inspected download

The official [standalone download page](https://vpic.nhtsa.dot.gov/downloads/)
provides a PostgreSQL plain SQL dump and a SQL Server backup. Its documentation
describes the standalone product as VIN-decoding focused, not a replacement for
all catalog APIs. PostgreSQL 17+ is required **to restore/run that database**;
orVIN can instead parse the text during data preparation and use portable files
at runtime. No database server is inherently required for a native library.

- Source: [September 2026 PostgreSQL plain ZIP](https://vpic.nhtsa.dot.gov/downloads/vPICList_lite_2026_09.plain.zip)
- Download-page release date: **2026-09-19**. SQL header says generation started
  **2026-09-16 13:10:07**, database PostgreSQL 17.6, pg_dump 18.3.
- Downloaded ZIP: **76,201,016 bytes**; one SQL member: **336,419,728 bytes**.
- ZIP SHA-256: `1ee4a1e22526a606b492ce4ab301894465afbf43dc00946df6d503c3102d5911`.
- SQL SHA-256: `9338854895d77cc12bf2c291a94d205d8193508574737c82f2b5426b6f8aaf6b`.
- Pinned archive: `data/nhtsa/vPICList_lite_2026_09.plain.zip`. The extracted inspection SQL
  remains ignored at `target/research/vpic-2026-09.sql`.

The SQL was inspected as text, **never executed or restored**. Counts below were
measured by streaming PostgreSQL `COPY ... FROM stdin` blocks through their
`\.` terminators. There are **97 tables** and **15 stored functions**. These
counts identify this exact snapshot, not a promise about later releases.

## Table inventory relevant to portable decoding

Every table below is in schema `vpic`. Columns are the exact COPY column order;
`id` values must survive export for referential integrity and provenance.

| Table | Rows | Columns / role |
| --- | ---: | --- |
| `wmi` | 13,001 | `id,wmi,manufacturerid,makeid,vehicletypeid,createdon,updatedon,countryid,publicavailabilitydate,trucktypeid,processedon,noncompliant,noncompliantsetbyovsc` |
| `manufacturer` | 23,003 | `id,name` |
| `make` | 12,361 | `id,name,createdon,updatedon` |
| `manufacturer_make` | 13,051 | `id,manufacturerid,makeid` |
| `wmi_make` | 14,172 | `wmiid,makeid` — authoritative join used by the decoding function |
| `model` | 32,009 | `id,name,createdon,updatedon` |
| `make_model` | 32,009 | `id,makeid,modelid,createdon,updatedon` |
| `vehicletype` | 9 | `id,name,displayorder,formtype,description,includeinequipplant` |
| `country` | 199 | `id,name,displayorder` |
| `vinschema` | 25,229 | `id,name,sourcewmi,createdon,updatedon,tobeqced` |
| `wmi_vinschema` | 41,774 | `id,wmiid,vinschemaid,yearfrom,yearto,orgid` |
| `pattern` | 1,678,690 | `id,vinschemaid,keys,elementid,attributeid,createdon,updatedon` |
| `element` | 160 | `id,name,code,lookuptable,description,isprivate,groupname,datatype,minallowedvalue,maxallowedvalue,isqs,decode,weight` |
| `enginemodel` | 346 | `id,name,description` |
| `enginemodelpattern` | 2,510 | `id,enginemodelid,elementid,attributeid,createdon,updatedon` |
| `vehiclespecschema` | 6,656 | `id,makeid,createdon,updatedon,vehicletypeid,sourcedate,tobeqced` |
| `vehiclespecschema_model` | 7,550 | `id,vehiclespecschemaid,modelid` |
| `vehiclespecschema_year` | 12,882 | `id,vehiclespecschemaid,year` |
| `vspecschemapattern` | 17,149 | `id,schemaid` |
| `vehiclespecpattern` | 226,001 | `id,vspecschemapatternid,iskey,elementid,attributeid,createdon,updatedon` |
| `conversion` | 6 | `id,fromelementid,toelementid,formula` — displacement-unit conversions |
| `defaultvalue` | 186 | `id,elementid,vehicletypeid,defaultvalue,createdon,updatedon` |
| `vindescriptor` | 69 | `id,descriptor,modelyear,createdon,updatedon` |
| `vinexception` | 18,805 | `id,vin,checkdigit,createdon,updatedon` — production check-digit exceptions |
| `wmiyearvalidchars` | 8,808,281 | `id,wmi,year,position,char` — validation/error-correction support |
| `wmiyearvalidchars_cacheexceptions` | 0 | Empty in this snapshot; preserve its schema if keeping a lossless source archive. |
| `errorcode` | 15 | `id,name,additionalerrortext,weight` |
| `decodingoutput` | 0 | Empty result-storage table, not a precomputed VIN universe. |

The remaining tables include lookup dictionaries for fuel, body, restraint,
transmission, drivetrain, EV and safety attributes, plus NCSA definitions.
`pattern.attributeid` is a string: it can mean a lookup-table ID or a literal
value, according to the element. It must not be globally parsed as an integer.
`pattern.keys_regex` is a generated column defined by the SQL, so it is absent
from COPY data and must be generated by the exporter or interpreted at runtime.

Measured COPY payload sizes explain the archive size: `pattern` is 98,926,776
bytes (21,483,261 bytes with zlib level 9); `wmiyearvalidchars` is 212,755,320
bytes (47,832,790 compressed); `vehiclespecpattern` is 13,632,341 bytes
(2,869,663 compressed). The character-validation cache accounts for most bytes.
These are measurements of individual COPY payloads, not forecasts of the final
orVIN JAR or a claim that the cache can be omitted while preserving every feature.

## What broad WMI coverage actually means

The dump contains **13,001 distinct WMIs**: **3,172 three-character** and
**9,829 six-character** identifiers. The six-character form uses positions 1–3
and 12–14 in the applicable low-volume layout.

| Vehicle type | WMI rows |
| --- | ---: |
| Trailer | 9,624 |
| Motorcycle | 1,579 |
| Low Speed Vehicle | 482 |
| Passenger Car | 348 |
| Truck | 314 |
| Multipurpose Passenger Vehicle | 241 |
| Incomplete Vehicle | 230 |
| Bus | 164 |
| Off-Road Vehicle | 19 |

These are WMI records, **not 13,001 passenger-car brands**. Country is source
WMI metadata; do not promote it to actual assembly country. Plant-country
information is separately represented by element 75 and pattern matching.

Do not join solely through `wmi.makeid`: it is NULL in **12,828 rows**. Use
`wmi_make` and the `make` dictionary. All WMIs have at least one such association:
12,475 have exactly one; **526 have multiple**, with a maximum of 41. For example,
`1C4` associates with Volkswagen, Lancia, Dodge, Chrysler, Jeep, Fiat and Ram in
this snapshot. A single brand cannot be returned confidently from that prefix
alone. The decoder first uses a decoded model to resolve make where possible;
only otherwise does it use a uniquely associated WMI make.

All WMI manufacturer references resolve. One WMI has a NULL public-availability
date; two have `noncompliant=true`. None has a future public-availability date
relative to review day. Preserve these flags and apply a documented public
export policy; do not silently turn administrative timestamps into production
validity dates. WMI-to-schema year ranges represent decoding applicability and
are different from a legal claim about every year a manufacturer held a WMI.

## API option for an earlier, smaller expansion

[GetWMIsForManufacturer documentation](https://vpic.nhtsa.dot.gov/api/)
allows either manufacturer or vehicle-type filtering, with at least one supplied.
Confirmed read-only on 2026-09-25:

- [All passenger-car WMIs](https://vpic.nhtsa.dot.gov/api/vehicles/GetWMIsForManufacturer?vehicleType=2&format=json): **348 records**.
- [All truck WMIs](https://vpic.nhtsa.dot.gov/api/vehicles/GetWMIsForManufacturer?vehicleType=3&format=json): **312 records**.

Each result has WMI, manufacturer ID/name, vehicle type, country and administrative
dates. [DecodeWMI](https://vpic.nhtsa.dot.gov/api/vehicles/DecodeWMI/WVW?format=json)
also returns make, common name and manufacturer website/parent fields. Therefore
the list response is not a lossless substitute for per-WMI decoding responses.
The truck list count differs from the dump; source/filter differences must be
reconciled rather than assuming identical snapshots. No customer VIN is needed
for any of these catalog operations.

## Actual decoding semantics to port

These observations come from the exact SQL member above, especially
`spvindecode`, `spvindecode_core`, `spvindecode_errorcode` and helpers. Extracted
function text is retained under ignored `target/research/<function>.txt` for
implementation review.

1. **Input and WMI extraction.** `fvinwmi` takes three characters and appends
   positions 12–14 when the third character is `9` and enough input exists.
   Decide explicitly how orVIN's stricter input normalization and unsupported
   formats relate to the NHTSA procedure; do not accidentally inherit truncation
   from PostgreSQL fixed-length declarations.
2. **Construct the pattern key.** Full-VIN matching uses positions **4–8**, a
   literal `|`, then positions **10–17**. Position 9 is excluded. This is not
   simply matching a prefix of the original VIN.
3. **Pattern language.** Without brackets, PostgreSQL LIKE uses `*` converted
   to `_`, followed by `%`: `*` consumes exactly one character and the suffix
   may continue. Bracket patterns use `sqlwild_to_regex`, including character
   classes/ranges and escaping. `#` patterns perform numeric substring capture.
   Counts: 860,533 rows contain `*`; 353,620 contain `[`; 17,708 contain `#`;
   132,763 contain `|`; nine contain `_`. These sets overlap. A literal-prefix
   decoder will miss substantial data.
4. **Schema and visibility.** Join by WMI and schema; constrain input year to
   `[yearfrom, yearto]`, with absent end treated as 2999. Apply public availability,
   QC and private-element rules. Ordinary pattern matching excludes element IDs
   26/27/29/39 (make/manufacturer/year/type); they have other sources. There are
   **13 private elements** in the dictionary; not every catalog row is a public
   output variable.
5. **Conflict precedence.** The ordinary per-element ranking is year-from
   descending, effective change timestamp descending, length after removing `*`
   **ascending**, bracket-stripped key ascending, then insertion order (patterns
   are inserted by ascending ID). Several note fields keep multiple values.
   Do not replace this with an assumed “most specific pattern wins” rule.
6. **Derived facts and enrichment.** Engine-model patterns can supply more
   engine facts. Six conversion rows convert displacement units. Vehicle-spec
   enrichment matches make/model/year/type and requires all `iskey` facts to
   match already decoded facts, then supplies missing attributes at lower
   priority. Defaults depend on vehicle type. Preserve `source` distinctions
   instead of labelling all outputs directly encoded in the VIN.
7. **Year selection is procedural.** `fvinmodelyear2` uses position 10, vehicle
   type/light-truck metadata, position 7, and the current year plus two. The main
   decoder can try different 30-year cycles, consider caller-supplied year and
   schema availability, then score passes by errors, element weights, matched
   patterns and year. This is US-scope logic, not a universal European rule.
   An explicit evaluation date is needed for deterministic results over time.
8. **Validation and repair are separate features.** Check-digit routines,
   per-WMI/year permitted characters, descriptor exceptions and VIN exceptions
   drive errors, correction suggestions and unused positions. Exporting the
   1.68 million patterns alone does not reproduce those outputs.

Function inventory: `felementattributevalue`, `ferrorvalue`,
`fextractvalidcharsperwmiyear`, `fvalidcharsinkey`, `fvalidcharsinregex`,
`fvincheckdigit`, `fvincheckdigit2`, `fvindescriptor`, `fvinmodelyear2`, `fvinwmi`,
`spvindecode`, `spvindecode_core`, `spvindecode_errorcode`, `spvindecodemultiple`,
`sqlwild_to_regex`. The three central decoder functions occupy approximately
323, 567 and 205 lines respectively, excluding helper logic. That is manageable
porting work, but a different scope from importing a WMI dictionary.

## Portable export and embedding plan

**Lossless data export is possible.** Preserve the 97 table schemas and their
rows in a versioned archive, including NULLs, Unicode, timestamps, booleans,
source IDs, flags and pattern strings. PostgreSQL COPY escaping (`\N`, escaped
tabs/newlines/backslashes) must be decoded properly. SQL must be parsed as data,
never executed as part of a consumer library or an unreviewed refresh.

For efficient consumption, generate separate archive entries for dictionaries,
WMI/schema indices, rule shards and validation caches. Java can embed these as
resources and Python can read the same archive; neither must load the whole
uncompressed SQL into memory. Index/shard patterns by schema and schema by WMI.
The 8.8-million-row character cache should be loaded only when the corresponding
validation feature needs it. Keep the source dump as a pinned release/source
artifact rather than adding a 336 MB SQL file to routine source control.

**Lossless output equivalence requires more than lossless rows.** Choices must
be explicit: port NHTSA precedence/year/error semantics faithfully, or expose
orVIN's own conservative results with documented differences. A best-effort
pattern stage must not be described as all NHTSA decoding. Preserve unmatched,
conflicting and unsupported results; do not invent engine, trim or years merely
because other rows for the same manufacturer contain them.

Suggested implementation sequence:

1. Import all public WMI/manufacturer/make/type associations, with many-to-many
   brand resolution and extended WMI handling; export a manifest with source
   URL, publication date, hashes and row counts.
2. Add the complete canonical table archive shared by Python and Java; verify
   every exported row/foreign-key count and exercise actual JAR resource loading
   without network or the repository checkout.
3. Implement patterned facts, formula captures, value dictionaries and explicit
   model-year constraints; expose which decoder stages are supported.
4. Implement derivation/enrichment and validation/year-resolution stages, with
   synthetic fixtures and parity checks against official examples/partial VINs.
   A restored reference database could later be used for differential tests,
   but this assessment did not execute or restore it.

## Coverage and reuse

[NHTSA's vPIC scope statement](https://vpic.nhtsa.dot.gov/) is US sale/importation
focused. Downloading its entirety cannot create missing German/European model
rules. Keep the manufacturer research for those gaps and for understanding the
source behind ambiguous fields. HSN/TSN remains a separate KBA lookup; these
tables do not establish a universal VIN-to-HSN/TSN mapping.

[NHTSA Terms of Use, Ownership](https://www.nhtsa.gov/about-nhtsa/terms-use)
permits copying/distributing published information and disclaims accuracy and
third-party-rights warranties. Retain this source-specific reuse basis and
attribution. Do not relabel imported facts, SQL procedures or third-party OEM
documents as orVIN-owned CC0 material. Any literal port of stored-function code
needs its own recorded provenance/reuse assessment; an implementation from
reviewed semantics should also cite the snapshot used.
