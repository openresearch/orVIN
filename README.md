# ORvin

European expansion: both libraries now expose sourced Swiss type-approval
candidates alongside direct VIN facts. See the [100-model coverage report](docs/european-coverage.md)
for implemented fields, catalogue gaps and validation limits. Candidate
configurations are not proof of an individual vehicle's build specification.

Shared vehicle reference data with independent, offline **Python and Java** libraries.
VIN manufacturer lookup uses **12,998 WMIs** from the September 2026 NHTSA bulk dataset.
The development version also decodes vehicle details from **1,343,387 public VIN patterns**,
with explicit market/year scope and separately sourced European Tesla Model Y rules.
German HSN/TSN lookup includes **63,260 KBA entries at 2026-01-01**. Both distributions embed the
complete NHTSA source archive and KBA snapshot. Neither library has runtime dependencies or makes network calls.

```text
data/             Canonical datasets, provenance, snapshots, licenses and fixtures
libs/python/      Python 3.10+ package
libs/java/        Java 17+ library, pom.xml, Maven wrapper and .mvn/
tools/            Data import/validation and cross-language verification
vin.sh            Python VIN lookup
hsntsn.sh         Python HSN/TSN lookup
```

## Try it immediately

Only **Python 3.10+** is required. No JDK, compilation, package installation or network access:

```sh
./vin.sh 1HGAAAAAAAAAAAAAA   # synthetic VIN example
./vin.sh 1HGCM82603A000000 --market US   # synthetic Accord configuration
./vin.sh XP7YGAEK0TB000001 --market DE   # synthetic Berlin Model Y configuration
./hsntsn.sh 0005 AMQ
./hsntsn.sh 0603 BMT
./vin.sh 1HGAAAAAAAAAAAAAA --json
./hsntsn.sh 0005 AMQ --json
```

Both scripts print **normalized short JSON** by default. `--json` explicitly selects
that same view; `--long` or `--json --long` adds explanations and complete evidence.
The long response is exactly the short object plus `details`. Both include source
attribution. See [normalized output and migration](docs/normalized-output.md).

For example, `./vin.sh WVWZZZ1KZ5P000001 --json` returns VW / Golf / model year
2005, with production year unknown. The synthetic VIN exercises the scoped European
Golf rule. `./hsntsn.sh 0603 BMT` returns VW / Golf Sportsvan with unknown years.
Unreviewed family aliases stay unknown; original labels and counts remain in long evidence.

Scripts work from any working directory, including paths with spaces. Set `ORVIN_PYTHON` to a
Python executable if needed. Use `--help`; VIN also accepts `--model-year` and `--market` for
independently known context. Exit codes: `0` for completed lookups (including unknown/ambiguous),
`2` for malformed arguments, invalid HSN/TSN, VIN characters or unsupported VIN length, `1` for environment/data
errors. VIN character assessment is shown separately from recognition.

## Python

Use `PYTHONPATH=libs/python` in a checkout, or install with `python3 -m pip install ./libs/python`.
The installed package bundles the same shared data and works outside the repository.

```python
from orvin import Context, HsnTsnLookup, VinDecoder

# Normalized API in the current development checkout:
answer = VinDecoder.bundled().decode_vehicle("WVWZZZ1KZ5P000001")
print(answer.vehicle)  # VW / Golf / 2005; productionYear is None
short_json_values = answer.short()
long_json_values = answer.long()

# The original source-level API is retained:

vin = VinDecoder.bundled().decode("1HGAAAAAAAAAAAAAA")
print(vin["manufacturer"]["value"]["name"])

# These richer APIs require the current development version, after v0.1.0.
vehicle = VinDecoder.bundled().decode("1HGCM82603A000000", Context(market="US"))
print(vehicle["model"]["value"])                       # Accord
print(vehicle["modelYear"]["value"])                   # "2003"
print(vehicle["details"]["fields"]["PlantCity"]["value"])  # MARYSVILLE

result = HsnTsnLookup.bundled().lookup("0005", "AMQ")
if result["status"] == "RECOGNIZED":
    print(result["value"]["tradeName"])
print(result["dataset"]["source"]["license"])
```

Results are fresh JSON-compatible dictionaries. Unknown optional fields are `None`; candidates
are retained for ambiguous results. See [Python package](libs/python/README.md).

## Java / Kotlin

All Maven files live in `libs/java/`. To validate data and build/install the Java artifact:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/requirements.txt
cd libs/java
./mvnw -Dpython=../../.venv/bin/python verify
./mvnw -Dpython=../../.venv/bin/python install
```

Building requires JDK 17+ and the Python data validator. The Maven wrapper needs `curl` or `wget`
and `unzip` for its first download. Build dependencies need network access initially; consuming
the resulting library requires only Java. On Windows use `mvnw.cmd` and the corresponding
virtual-environment path. Java CI covers 17, 21 and 25.

```xml
<dependency>
  <groupId>com.openresearch</groupId>
  <artifactId>orvin</artifactId>
  <version>0.1.0</version>
</dependency>
```

```java
import com.openresearch.orvin.HsnTsnLookup;
import com.openresearch.orvin.VinDecoder;

var vin = VinDecoder.bundled().decode("1HGAAAAAAAAAAAAAA");
System.out.println(vin.manufacturer().value().map(VinDecoder.Manufacturer::name));
var result = HsnTsnLookup.bundled().lookup("0005", "AMQ");
System.out.println(result.value().flatMap(HsnTsnLookup.TypeEntry::tradeName));
System.out.println(result.dataset().referenceDate());

// Normalized API in the current development version, after v0.1.0:
var answer = VinDecoder.bundled().decodeVehicle("WVWZZZ1KZ5P000001");
System.out.println(answer.vehicle().make()); // Optional[VW]
System.out.println(answer.toShortJson());
System.out.println(answer.toLongJson());

// Original source-level detail API:
var vehicle = VinDecoder.bundled().decode("1HGCM82603A000000",
    new VinDecoder.Context(java.util.Optional.empty(), java.util.Optional.of("US")));
System.out.println(vehicle.model().value());
System.out.println(vehicle.details().field("PlantCity").value());
```

Kotlin uses the same artifact: `implementation("com.openresearch:orvin:0.1.0")`.
**[Version 0.1.0 is released](https://github.com/openresearch/orvin/releases/tag/v0.1.0).**
Java is published to GitHub Packages; configure its repository and authentication using the
[Maven/Gradle instructions](docs/releasing.md). Python wheel/sdist downloads are release assets.
Local source builds still use the development versions `0.2.0-SNAPSHOT` / `0.2.0.dev0`.

GitHub Actions builds both libraries. Pushing a stable `vX.Y.Z` tag runs the CI matrix, publishes
`com.openresearch:orvin:X.Y.Z` to GitHub Packages, and attaches Java artifacts plus Python
wheel/sdist and checksums to a GitHub Release. Manual Release runs only build/check artifacts.
See [releasing and Maven/Gradle setup](docs/releasing.md) for authentication and consumption examples.

## Coverage and uncertainty

The shared dataset contains 11,604 manufacturer entities and 14,169 WMI/brand associations
across nine vehicle categories, including trailers, motorcycles and low-volume manufacturers.
These are not counts of passenger-car brands. Examples:

| WMI | NHTSA manufacturer | Category |
| --- | --- | --- |
| `1HG` | AMERICAN HONDA MOTOR CO., INC. | Passenger car |
| `JTD` | TOYOTA MOTOR CORPORATION | Passenger car |
| `WBA` | BMW AG | Passenger car |
| `WVW` | VOLKSWAGEN AG | Passenger car |
| `1FD` | FORD MOTOR COMPANY | Incomplete vehicle |
| `1H9` + `333` | HOMBILT TRAILERS INC | Trailer |
| `5YJ` | TESLA, INC. | Passenger car |
| `WDD` | Mercedes-Benz Cars | Passenger car |

The extended identifier joins VIN positions 1–3 and 12–14. WMI source snapshots were captured
on 2026-09-25; those dates do not establish historical assignment intervals. NHTSA primarily
covers manufacturers reporting for the US market; a complete download is not global VIN coverage.
The source has 13,001 WMIs; three exclusions are recorded explicitly (two malformed identifiers
and one without a public-availability date). All remain in the archived source. The 526 WMIs
associated with multiple brands retain every candidate; for example, `1C4` has seven possibilities.

HSN/TSN returns KBA manufacturer/trade-name labels, optional population counts and statistical
markers, and source row IDs. Model-name alternatives are preserved as reported. KBA labels are
not automatically merged with WMI identities. See [KBA source details](docs/kba-data.md).

HSN is a four-digit string; TSN is three ASCII letters/digits. Preserve leading zeroes. Matching
only trims ASCII spaces and uppercases ASCII letters. Longer registration-document codes are
not silently truncated. Missing codes stay unknown: this snapshot is not a register of every
type ever assigned. **KBA supplies no VIN-to-HSN/TSN mapping in this dataset.** Supply codes separately.

VIN structure checks length/alphabet, not checksum, authenticity or registration. A known WMI
can coexist with invalid characters elsewhere. Unknown WMI does not prove invalidity. The
rich decoder returns model, scoped year, plant/country, engine, fuel, body, trim, drivetrain,
transmission and other public attributes where matching rules exist. `details.fields` uses
NHTSA variable codes; values are strings, including numeric values. Every field retains evidence.
NHTSA results require independently known `--market US` to become unconditional; absent market
retains conditional possibilities, and an explicit non-US market excludes those rules.

European additions currently cover Berlin/Shanghai Tesla Model Y configurations documented for
2025–2027. They return **production year**, separately from model year. Your market does not need
to be US for these OEM rules. A separate bounded European Golf 1K model-year-2005 rule resolves Golf V, year and
Mosel/Wolfsburg plant. Other historical years and unreviewed layouts remain unknown.
See [source traceability and audit](docs/provenance-audit.md).
Exact production dates, complete options, history and VIN-to-HSN/TSN remain unavailable.
Manufacturer country stays unknown; source WMI geography is never used as assembly country.

`status` and `candidates` retain the original WMI lookup outcome; `details.status` describes the
vehicle-rule result. A decoded model can resolve `brand` while all WMI associations remain
available for audit. Unresolved year cycles are separate `details.alternatives`; do not combine
fields across them. See [rich decoding behavior and limits](docs/rich-decoding.md).

## Embedded datasets and updates

The main JAR embeds every file in `data/` under `META-INF/orvin/`; the Python wheel includes the
same files under `orvin/_data/`. This includes the complete 76.2 MB NHTSA ZIP (97 source tables
and its SQL functions), normalized WMI data, KBA records, provenance, hashes and notices.
Runtime loads small indexes and the required compressed pattern shards through bounded caches.
No database server or SQL execution is needed.

```sh
# Rebuild normalized WMI data from the already bundled ZIP, offline:
python3 tools/nhtsa.py import
python3 tools/decoding.py import
python3 tools/identity.py --generate
.venv/bin/python tools/dataset.py --update-runtime

# Explicitly download, verify and import the pinned official snapshot:
python3 tools/nhtsa.py download
```

Normal builds validate the pinned data offline and never download newer data automatically.
See [NHTSA import and coverage](docs/nhtsa-data.md) and the [50-make research index](docs/research/vin-rules/README.md).

## Develop and contribute

```sh
PYTHONPATH=libs/python python3 -m unittest discover -s libs/python/tests
.venv/bin/python tools/dataset.py
.venv/bin/python -m unittest discover -s tools
# After building Java:
python3 tools/check_parity.py
```

Canonical WMI data is [JSON](data/dataset.json). KBA data is UTF-8 [TSV](data/kba/types.tsv) with
[JSON metadata](data/kba/metadata.json). Both are usable independently of either library. Builds
validate hashes and reconstruct the complete NHTSA WMI and KBA transformations offline. Parity
checks compare complete Java/Python results, including provenance and nulls.

Read [CONTRIBUTING.md](CONTRIBUTING.md), [architecture](docs/architecture.md) and
[release preparation](docs/releasing.md). Changes require data, provenance and behavioral fixtures.

Code/documentation: [Apache-2.0](LICENSE). KBA data: **dl-de/by-2-0**, attributed to the
[Kraftfahrt-Bundesamt source](https://data.gov.de/suche/daten/fz-hersteller-handelsnamen-kfz?ids=c1e3a0b6-0d34-4e99-8181-91bdfb639208)
under its [license](https://www.govdata.de/dl-de/by-2-0). Imported NHTSA facts retain their reuse
notice. Only ORvin-owned data contributions are CC0. Preserve [data notices](data/LICENSE.md);
source data are not relicensed Apache or CC0. Names and marks do not imply endorsement.
