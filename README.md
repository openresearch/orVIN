# ORvin

**An open VIN database. Offline decoding for Python and Java.**

We’re building an open, traceable database for identifying vehicles from their VINs.
ORvin brings public vehicle datasets and documented decoding rules together in one
language-neutral dataset, with Python and Java libraries that return consistent results.

**[Try it online →](https://orvin.openresearch.com)** ·
[Releases](https://github.com/openresearch/orvin/releases) ·
[API and output](docs/normalized-output.md) ·
[Contribute](CONTRIBUTING.md)

- **One normalized answer:** make, model, model year and production year, with a
  status for each field. Known aliases share a name; unknowns and conflicts stay explicit.
- **Traceable results:** sources and attribution in every answer. Expand the result
  to inspect specifications, alternatives and the evidence behind each decision.
- **Fully offline:** both packages embed the complete dataset. No runtime
  dependencies, database server or calls to upstream providers.
- **German registration codes:** HSN/TSN lookup alongside VIN decoding.

## Python

Requires **Python 3.10+**. Install the released package from GitHub:

```sh
python3 -m pip install https://github.com/openresearch/orvin/releases/download/v0.2.1/orvin-0.2.1-py3-none-any.whl
```

```python
import json
from orvin import VinDecoder

answer = VinDecoder.bundled().decode_vehicle("WVWZZZ1KZ5P000001")  # synthetic VIN
print(answer.vehicle["make"])       # VW
print(answer.vehicle["model"])      # Golf
print(answer.vehicle["modelYear"])  # 2005
print(json.dumps(answer.short(), indent=2))  # normalized answer, status and sources
# answer.long() adds detailed evidence to the same answer.
```

The package also installs a CLI:

```sh
orvin vin WVWZZZ1KZ5P000001 --json
orvin vin WVWZZZ1KZ5P000001 --json --long
orvin hsntsn 0603 BMT --json
```

[Python guide](libs/python/README.md). The package is distributed through GitHub
Releases; it is not yet on PyPI. From a checkout, `./vin.sh` and `./hsntsn.sh`
provide the same commands without installation or compilation.

## Java / Kotlin

Requires **Java 17+**. Configure the GitHub Packages repository using the
[Maven or Gradle setup](docs/releasing.md#use-java-from-gradle-or-maven), then add:

```xml
<dependency>
  <groupId>com.openresearch</groupId>
  <artifactId>orvin</artifactId>
  <version>0.2.1</version>
</dependency>
```

For Gradle: `implementation("com.openresearch:orvin:0.2.1")`.
GitHub Packages requires authentication, including for public packages.

```java
import com.openresearch.orvin.VinDecoder;

var answer = VinDecoder.bundled().decodeVehicle("WVWZZZ1KZ5P000001"); // synthetic VIN
System.out.println(answer.vehicle().model().orElse(null)); // Golf
System.out.println(answer.toShortJson()); // normalized answer, status and sources
// answer.toLongJson() adds detailed evidence to the same answer.
```

The JAR includes the same dataset as Python. It needs no Python installation at runtime.

## Data and coverage

ORvin combines [NHTSA VIN data](docs/nhtsa-data.md),
[German KBA type records](docs/kba-data.md),
[Swiss ASTRA type approvals](docs/research/astra-review.md) and reviewed manufacturer-specific rules.
The language-neutral files in [`data/`](data/) can also be used independently of either library.

Coverage varies by manufacturer, market and year. Where supported, rules can identify
factory, engine, fuel, body and other specifications. Type-approval matches remain
candidate configurations; exact build dates, complete options and vehicle history
are outside current coverage. HSN/TSN codes must be supplied separately.
See the [European coverage report](docs/european-coverage.md) and
[decoding limits](docs/rich-decoding.md).

## Help build the database

Contribute documented rules, source datasets, corrections or independently verified
examples. Every addition needs traceable evidence, a reviewed reuse basis and tests.
Start with the [contribution guide](CONTRIBUTING.md) and [source policy](AGENTS.md).

Python lives in [`libs/python/`](libs/python/), Java in [`libs/java/`](libs/java/).
Both consume the shared dataset and are checked for equivalent results.
See [architecture](docs/architecture.md), [builds and releases](docs/releasing.md)
and [automatic data updates](docs/automatic-updates.md).

## License

Code and documentation: [Apache-2.0](LICENSE). Original dataset contributions:
**CC0-1.0**, to the extent contributors own the rights. Imported data retains its
source-specific terms and attribution requirements; see [data licenses and notices](data/LICENSE.md).
