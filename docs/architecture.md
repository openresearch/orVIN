# Architecture

## Canonical data

`data/dataset.json` is the language-neutral WMI runtime dataset, deterministically projected from
the pinned NHTSA archive by `tools/nhtsa.py`. Validation reconstructs it completely and rejects
hand edits that diverge from the source. JSON is widely supported, reviewable
without a custom parser, and has a standard schema vocabulary. It is more verbose than YAML but
avoids implicit type conversions and custom tags. Stable manufacturer IDs belong to ORvin;
manufacturer display names may change without forcing an identity change. Imported identities
retain NHTSA numeric IDs, with six compatibility aliases for the original seed records.

The JSON Schema requires sources and reuse information. `tools/dataset.py` additionally checks
cross-references, duplicate JSON keys/IDs, overlapping assignments, invalid year intervals,
source snapshot integrity and ordinary/extended prefix collisions. Text cannot contain control
characters, which keeps the generated TSV unambiguous. Schema version 1 is deliberately small.

Assignments carry a WMI (three or six characters), manufacturer, optional supported brand/category,
source references, optional market/model-year constraints, and explanatory notes. Source references
on a manufacturer support its name and optional country; assignment references must support all
factual fields in that assignment. Human review checks that relationship.

Conflicting mappings with overlapping scopes must share an explicit `ambiguityGroup` and each
must explain the ambiguity. Exact duplicate overlapping mappings are rejected. Adjacent, disjoint
model-year intervals or disjoint markets can coexist. Bounds are inclusive and supplied by evidence,
never computed from source record timestamps. An empty scope means no restriction is recorded;
it does not prove validity for every time or market.

## Java implementation

Implementations live in `libs/python` and `libs/java`; shared canonical data remains in `data`.
All Maven configuration and wrapper files are under `libs/java`.

Java 17 gives consumers records and a widely deployed baseline without preview APIs. Maven's
conventional library lifecycle produces the JAR, source JAR and Javadoc JAR. Maven 3.9.16 and
the Maven wrapper distribution checksum are pinned. Python 3.10+ and `jsonschema` are build tools;
consumers only need Java.

During `generate-resources`, validated JSON is deterministically compiled to an internal TSV and
compared to the checked-in resource under `libs/java/src/main/resources`. Intentional data changes
refresh it with `tools/dataset.py --update-runtime`; normal builds fail on a stale resource.
The library reads it once per class loader and builds an immutable lookup index. The canonical
JSON, complete original NHTSA ZIP, KBA snapshot and notices are bundled under `META-INF/orvin`, so consumers can audit the exact
data. The internal TSV is not a public storage format. This avoids a runtime JSON dependency or
a handwritten general JSON parser. The original ZIP stays compressed and is not loaded or
executed during lookup. It costs a small build-time Python dependency, documented in
the README and installed explicitly in CI.

The resource records have fixed column counts: `V` (version/hash), `S` (source), `M` (manufacturer),
and `A` (assignment). Identifiers cannot contain delimiters. Rows are ordered by type and stable ID;
UTF-8 and LF are explicit. Internal decoder objects and all exposed collections are immutable.

## Matching and uncertainty

The supplied string is preserved. Matching trims ASCII spaces and uppercases ASCII letters only.
Length/alphabet assessment is independent from source lookup. Inputs outside the supported
17-character layout return `UNSUPPORTED_FORMAT`; a legacy identifier is not declared invalid.
Checksum policies vary and are intentionally not evaluated in this release.

Extended lookup is enabled for prefixes present in the dataset's extended assignments. It joins
positions 1–3 and 12–14 and never falls back to the prefix. No global production-volume threshold
or position-3 heuristic is imposed on countries or eras not covered by data. Schema validation
currently rejects mixing ordinary and extended entries for the same prefix; adding evidence for
such a case requires an explicit schema and matching design change.

Explicitly supplied market/model-year context filters candidates. Missing required context retains
possible candidates and marks an otherwise unique result `NEEDS_CONTEXT`. Multiple candidates
produce `AMBIGUOUS`, while fields shared by all candidates can still be known. A field missing on
any candidate is not treated as established. Incomplete evidence remains visible as possibilities.

Manufacturer country and assembly country are separate results. Assembly country now comes
from matching plant rules; the WMI's geographic prefix is never used as a proxy. Rich decoding
has its own scope, status, provenance and model-year alternatives, described in
[rich decoding](rich-decoding.md). Exact build dates and vehicle histories remain unavailable.

## Versioning and reproducibility

Dataset versions use `YYYY.MM.DD.N`, independently from library SemVer. Every result exposes the
dataset version and SHA-256 of the exact canonical JSON. Source snapshots have their own hashes.
Maven output timestamps are fixed, and CI compares two clean main JAR builds on the same JDK.
Reproducibility is claimed for identical source, toolchain and resolved build dependencies, not
across arbitrary JDKs. Future releases should retain the commit, checksums and toolchain identity.

## Python and command-line scripts

The Python implementation uses only the standard library. It reads the shared canonical JSON/TSV
directly in a checkout. Wheels and sdists bundle identical data, source snapshots and notices;
installed packages do not need the checkout. Parsed data is cached, while each public result is a
fresh JSON-compatible dictionary so caller mutations cannot alter subsequent lookups.

`vin.sh` and `hsntsn.sh` locate the checkout relative to themselves, check Python 3.10+, and invoke
the Python package. They never invoke Java, Maven, compilers, pip or network services. Their default
output uses the normalized short projection with uncertainty and source credits;
`--long` or `--json --long` extends it with complete evidence from the Python
library result. Java exposes the equivalent normalized `VehicleAnswer`, typed vehicle
fields and built-in short/long JSON serialization, alongside the existing raw records.
A test-only Java probe enables comparison of complete outputs against Python across sourced fixtures,
invalid input and a spread of the full WMI and KBA catalogs. The adapter loads production classes
and resources from the built JAR. Artifact checks compare every embedded data file byte-for-byte
against shared `data/`. Both implementations also test synthetic ambiguity and
missing evidence independently.

## NHTSA import

`tools/nhtsa.py` streams PostgreSQL COPY blocks as text, decoding NULLs, backslash escapes and
Unicode without executing SQL. It counts all 97 tables while retaining only five lookup tables
in memory. Joins use `wmi_make`, not the mostly empty legacy `wmi.makeid`. Every associated brand
survives as a candidate; 526 multi-brand WMIs have explicit ambiguity groups. Three rejected
WMI rows remain in the complete archive and are listed in `data/nhtsa/metadata.json`.

Build validation verifies the reviewed archive hash, reconstructs every canonical WMI row and
compares the exact output/metadata. Reviewed behavioral fixtures test representative independent
expectations instead of generating thousands of expected outputs from the importer itself.
Conflict checks group by WMI before comparing alternatives, avoiding quadratic work across the
catalog. ID uniqueness is enforced by indexed checks rather than object-array comparisons.

`tools/decoding.py` streams the same source into a shared index and 256 deterministic gzip
shards keyed by schema ID modulo 256. Every normal build reconstructs and compares the complete
projection. It resolves public value dictionaries and preserves source IDs, patterns, timestamps
and compiled matching expressions. Text cells use UTF-8/base64 so embedded newlines are lossless.
Java and Python validate index/shard digests and retain at most eight parsed shards and 32 compiled
schemas per decoder. Java synchronizes cache access; public results remain deeply immutable.
Python returns fresh dictionaries. Source SQL and large validation caches are never expanded at runtime.

The native stages implement explicit applicability, pattern precedence, numeric captures,
model-to-make resolution, engine-model associations and displacement conversions. Rich results
have a separate dataset identity: the index hash also commits to every shard and the curated OEM
rules. See `docs/rich-decoding.md` for boundaries relative to the complete upstream procedure.

## German type data

The canonical KBA table is UTF-8 TSV with JSON provenance metadata, kept separately from WMI
assignments. `tools/kba.py` explicitly imports one annual reference date, retains a compressed
lossless attribute snapshot, verifies completeness by source object IDs and produces deterministic
TSV. Offline validation checks hashes and regenerates the entire table for exact comparison.
The format preserves leading zeroes, nulls and statistical markers; see `docs/kba-data.md`.

Each library lazily builds its own HSN/TSN index, checks the table hash and retains every matching
row. `RECOGNIZED`, `UNKNOWN`, `AMBIGUOUS` and `INVALID_INPUT` distinguish lookup outcomes from
input shape. `value` is present only for a unique entry. KBA source attribution, reference date
and dataset hash accompany every result, including unknown codes. No fuzzy manufacturer linking,
model-label splitting or VIN-to-HSN/TSN inference is performed.
