# Washington EV masked-prefix benchmark

This is a **correlated observational benchmark**, not independent manufacturer ground truth. Washington State Department of Licensing explicitly says that its **make, model, and model-year labels are obtained by decoding VINs**. Agreement therefore measures consistency with another decoded population dataset, and may reflect shared upstream rules or errors.

The snapshot contains **18,376 distinct first-ten-character prefixes**, representing **299,705 registrations and 51 makes** in Washington's EV/PHEV population as of **August 31, 2026**. It was retrieved on September 25, 2026 UTC. It does not represent the general vehicle population or establish European decoding coverage. The selected US market is an assumption based on the registration jurisdiction; registration does not establish a vehicle's original market specification.

## Source and reuse

The source is [Electric Vehicle Population Data](https://data.wa.gov/Transportation/Electric-Vehicle-Population-Data/f6w7-q2d2), published by Washington State Department of Licensing. [Dataset metadata](https://data.wa.gov/api/views/f6w7-q2d2.json) identifies its license as [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). `source.json` records the exact aggregate query, retrieval time, source and compressed-snapshot SHA-256 hashes, source update timestamp, selected column descriptions, modifications, attribution, and license.

**Contains information from Washington State Department of Licensing's Electric Vehicle Population Data, available under the Open Database License (ODbL) 1.0.**

`groups.json.gz` is the exact aggregate-query JSON response compressed with a fixed gzip timestamp. It contains only `vin_1_10`, `make`, `model`, `model_year`, and an aggregate `vehicle_count`. No owner or location fields were requested or retained. `source.json` retains only the relevant metadata description fields, not the source metadata's contact/owner records.

The grouped database and derived prefix-result database are made available under ODbL 1.0, separately from the repository's software license. Preserve the attribution and license notice when redistributing them; modified derivative databases are subject to the applicable ODbL obligations, including share-alike. These files are validation material outside the packaged `data/` directory and must not be bundled as production decode rules.

## Reproduce

From the repository root, Python 3.10 or newer and the standard library suffice:

```sh
python3 tools/benchmark_wa.py
python3 -m unittest discover -s tools -p test_benchmark_wa.py -v
```

The default run is offline. To refresh the public aggregate snapshot and rerun:

```sh
python3 tools/benchmark_wa.py --refresh
```

Refreshing replaces this dataset snapshot and its manifest. The tool checks the source update timestamp before and after retrieval and refuses responses that reach the query row limit, instead of silently accepting a possibly truncated dataset. `--limit 100 --output validation/wa-ev/smoke.json` is an optional partial run; its report explicitly says that the full snapshot was not evaluated.

## What is measured

For each published ten-character prefix, the tool calls the Python library three times with synthetic continuations `A000001`, `F500000`, and `Z999999`. These are deliberately declared probes; they are not actual vehicle VINs. It passes `Context(market="US")` and **does not supply the observed model year to the decoder**. It reads only the public `brand`, `model`, and `modelYear` resolutions.

A prediction is scored as known only when all three probes return the same `KNOWN` value for that field. Disagreement, unknown/ambiguous results, and incomplete probe agreement are separate abstention categories. Agreement between these three probes does **not** prove agreement across every possible plant or serial continuation. The original check-digit character is left unchanged and no claim is made that a probe is an authenticated or checksum-valid VIN. This fixture cannot validate assembly plant, serial number, trim, engine, equipment, or other facts depending on missing characters.

Prefixes with third character `9` are excluded because the missing positions 12–14 can identify an extended WMI. Conflicting observed labels, if present, are preserved and excluded per field rather than arbitrarily choosing one. The current snapshot has two such extended-WMI prefixes and no conflicting grouped labels.

**Coverage** is the fraction of eligible source prefixes with a consensus known prediction. **Exact precision** is the fraction of those known predictions matching the observed label. Neither unknown results nor excluded conflicts count as wrong known answers. The report gives unweighted prefix metrics and separate registration-count-weighted metrics. Registration weighting repeats the same prefix prediction by its aggregate count; those are not independent vehicle-level observations.

Only case and repeated whitespace are normalized; punctuation and suffixes are retained. `aliases.json` supports explicit, make-scoped observed/decoded model-label pairs with a documented reason. It currently contains **no aliases**, so exact and alias precision coincide. Naming differences are therefore visible as mismatches, which are disagreements with this observational source and not automatically decoder defects. Adding aliases must preserve both strict and alias-adjusted metrics.

`benchmark.json` records the complete metrics, per-make results, bounded mismatch examples, configuration, source/dataset/tool/code hashes and limitations. `benchmark-prefixes.json.gz` preserves every prefix's observed label, consensus prediction, status and aggregate weight for diagnosis. Neither file includes actual complete VINs. Results describe the particular recorded decoder and dataset hashes; rerun after changing the library or its data.

## Checked-in result

The complete snapshot has 18,374 eligible prefixes after excluding the two extended-WMI prefixes. No model aliases are applied.

| Field | Consensus known prefixes | Prefix coverage | Exact label agreement among known predictions | Registration-weighted coverage |
| --- | ---: | ---: | ---: | ---: |
| Make | 18,284 | 99.510% | 100% | 99.948% |
| Model | 17,193 | 93.572% | 100% | 95.727% |
| Model year | 17,193 | 93.572% | 100% | 95.727% |

There are no known-label mismatches in this snapshot. This exact agreement is compatible with the source's already VIN-decoded labels; it does **not** establish 100% real-world accuracy or independent European validation.

Model decoding abstains for 1,181 prefixes. Year decoding abstains for 505 ambiguous, 149 probe-incomplete, and 527 unknown prefixes. Model prefix coverage is lower for Ford (67.6%), GMC (41.7%), and Rivian (43.9%). Azure Dynamics, BrightDrop, Mullen Automotive, and Ram have no consensus known model predictions in this sample. These gaps can guide further diagnosis, but missing positions and the conservative probe protocol can contribute to an abstention; they do not by themselves prove that a full real VIN is undecodable.
