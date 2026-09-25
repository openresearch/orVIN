# German KBA data assessment

Research/import date: 2026-09-25. Python and Java bundle 63,260 entries from the Kfz portal table
at reference date 2026-01-01. Use `HsnTsnLookup.bundled().lookup(hsn, tsn)` or `./hsntsn.sh`.

## Immediately useful: HSN/TSN reference data

The official [FZ 6 2026 catalog record](https://www.govdata.de/suche/daten/fz-6-2026-bestand-an-kraftfahrzeugen-und-kraftfahrzeuganhangern-nach-hersteller-und-typen-am-1-?ids=6ae58c67-8615-4417-85e3-fd05fbfae605)
links the [KBA workbook](https://www.kba.de/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ6/fz6_2026.xlsx?__blob=publicationFile&v=5).
Its `Impressum` identifies the reference date as 2026-01-01 and publication date as 2026-04-13.
The `FZ 6.1` sheet, cells B8:F8, contains exactly these headers:

| Column | Meaning |
| --- | --- |
| Herstellerschlüsselnummer | HSN, preserved as a string including leading zeroes |
| Herstellerklartext | Manufacturer label used by KBA |
| Typschlüsselnummer | TSN, preserved as a string |
| Handelsname | Reported trade/model name |
| Anzahl | Registered population at the reference date |

The workbook does not include VIN, WMI, engine displacement, kW, fuel type, emissions class,
assembly plant or equipment. Those fields must not be invented from a model name.

FZ 6 covers types with assigned national manufacturer/type codes present in the register at the
reference date. KBA explicitly excludes records missing those codes, including relevant individual
approval and modification cases. Consequently, absence from this annual stock dataset does not
establish that an HSN/TSN is invalid or was never assigned. The reference date is not a production year.

## Machine-readable alternative

The official [FZ Hersteller Handelsnamen Kfz catalog record](https://data.gov.de/suche/daten/fz-hersteller-handelsnamen-kfz?ids=c1e3a0b6-0d34-4e99-8181-91bdfb639208)
links KBA's ArcGIS item `8e8ffbf40456487a88768889dc5ce1d7`. Its published
[feature-service table](https://services-eu1.arcgis.com/U09msXRZoxesNntH/arcgis/rest/services/SP_HSN_TSN_92a1e/FeatureServer/0)
has fields `Berichtszeitpunkt`, `Herstellerschluessel`, `Herstellertext`, `Typschluessel`,
`Handelsname`, `Anzahl`, `ZS_Anzahl`, and `ObjectId`. A read-only query confirmed reference dates
2023-01-01 through 2026-01-01. Preserve statistical markers instead of treating them as zero counts.

`tools/kba.py` imports a fixed reference date only when explicitly requested. It records the
server's count and complete object-ID list, downloads bounded ID ranges concurrently, rejects
truncated batches and compares all returned IDs/counts before and after retrieval. The retained
snapshot contains every attribute row and the object-ID list. Builds revalidate its hash, count,
dates, column types and exact transformation into the canonical TSV without any network call.

The similarly named **Pkw** table has a different schema: its inspected fields include manufacturer
label, TSN, trade name, state and count, but no HSN column. Use the **Kfz** table for HSN/TSN lookup;
never reconstruct HSN just by fuzzy matching a manufacturer's text.

## Redistribution terms

The official FZ 6 and Kfz catalog records identify **Datenlizenz Deutschland – Namensnennung 2.0**.
The [license text](https://www.govdata.de/dl-de/by-2-0) allows commercial reuse, modification and
redistribution subject to attribution. Retain the provider name, dataset URI and license link,
and identify modifications. This applies to these identified datasets, not automatically to every
KBA document or service. Imported records must keep their KBA terms rather than be relabeled CC0.

The imported data retain attribution in `data/LICENSE.md`, `NOTICE`, package data and API results:

> Datenquelle: Kraftfahrt-Bundesamt, FZ Hersteller Handelsnamen Kfz, Abrufdatum 2026-09-25;
> Datenlizenz Deutschland – Namensnennung – Version 2.0; Daten für Orvin normalisiert.

Include active links to the exact dataset and license alongside this notice. Use the actual
retrieval date for the imported snapshot, not the research date by default.

## VIN integration and other KBA sources

An HSN/TSN identifies a German type-code entry; it is not a full VIN. These open datasets provide
no VIN-to-HSN/TSN crosswalk. A VIN-only request cannot be assigned an exact TSN from this material.
Keep WMI decoding and German type lookup as separate operations and combine their results only
when the caller supplies independently known HSN/TSN or an authoritative cross-reference exists.

KBA's [WMI portal](https://www.kba-online.de/wmi_prod/webapp-nezo/) describes its German WMI assignment
role and annual manufacturer directory. The current official directory, row semantics and its own
reuse notice still need review before using it to connect HSN manufacturer identities with WMIs.
Do not assume a one-to-one HSN/WMI or manufacturer/brand relationship.

Richer technical type data, CoC data or individual registered-vehicle information needs a separate
access and licensing assessment. The open statistical table is not evidence of permission or
access to those services. No open official VIN-to-type service was established in this research.

## Canonical format and maintenance

`data/kba/types.tsv` is UTF-8 with LF endings and a header. Columns: `hsn`, `tsn`, `manufacturer`,
`tradeName`, `registeredCount`, `countMarker`, `sourceObjectId`. HSN and TSN are strings, never
numbers. `\N` means null; empty strings remain distinct. There is no CSV quoting or escaping:
tabs, line breaks, control characters and literal `\N` in source text are rejected by the importer.
Read with a TSV parser that disables quote processing. All rows share `referenceDate` in
`data/kba/metadata.json`, which also records version, hashes, source URLs and modifications.

The 2026 snapshot has 63,260 distinct HSN/TSN pairs. The libraries nevertheless retain every
candidate and return `AMBIGUOUS` if a future source contains duplicate keys. A unique row with
multiple model names remains one entry with its exact source label. Optional counts and markers
are preserved; null counts are never interpreted as zero. Some trade names are absent.

To deliberately refresh after checking source terms and fields (network access required):

```sh
python3 tools/kba.py --import-date 2026-01-01 --version YYYY.MM.DD.N
.venv/bin/python tools/dataset.py --update-runtime
```

Replace the version placeholder with the actual reviewed revision. Review the data/metadata diff,
update independent fixtures when facts change, and run both library suites and the parity check.
Ordinary validation/builds never invoke this download command. Byte serialization and hashes are
retained in the pinned snapshot; upstream data may change between deliberate refreshes.
