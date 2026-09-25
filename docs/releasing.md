# Builds, releases and consumption

Java and Python releases share a `vMAJOR.MINOR.PATCH` tag and version. Development descriptors
remain `0.1.0-SNAPSHOT` and `0.1.0.dev0`; the workflow stamps build copies from the tag.
[Version 0.1.0](https://github.com/openresearch/orvin/releases/tag/v0.1.0) was published on
2026-09-25 from commit `4641b5c61af219ff18c937685d5ba2e3ddc5198e`; its
[release workflow passed](https://github.com/openresearch/orvin/actions/runs/36189579018).
Pushing a code/CI branch does not publish packages.

## GitHub Actions

[`ci.yml`](../.github/workflows/ci.yml) runs on pull requests and pushes to `main`/`codex/**`,
and supports reusable/manual runs. It verifies Java 17/21/25 and Python 3.10/3.14, source
reconstruction, embedded data, cross-language results, installed wheels and Java build
reproducibility. Candidate JARs are retained for seven days.

[`release.yml`](../.github/workflows/release.yml) runs for pushed `v*` tags. It:

1. Requires the complete CI matrix to pass.
2. Validates a stable `vMAJOR.MINOR.PATCH` tag and stamps matching Maven/Python versions and SCM tag.
3. Builds/tests release artifacts, checks Python metadata, compares every embedded data file,
   compares Java/Python results, and exercises the installed wheel outside the checkout.
4. Checks artifact coordinates/versions and creates `release.json` with source commit and dataset
   identities, plus `SHA256SUMS` covering all release assets.
5. Publishes the exact tested Java JAR, sources, Javadoc and POM to **GitHub Packages** at
   `https://maven.pkg.github.com/openresearch/orvin`.
6. Creates a **GitHub Release** with those Java files, Python wheel/sdist, manifest and checksums.

The workflow uses the repository's automatic `GITHUB_TOKEN`; no publishing PAT or PyPI secret
is required. Its publishing job requests `packages: write` and `contents: write`. Organization
policies must permit Actions and package creation. Workflow actions are pinned to commit SHAs.

Manual **Run workflow** on Release is always a dry run: enter a prospective tag such as `v0.1.0`.
It runs the build checks and uploads assembled assets, but never deploys a package or creates
a release. The workflow must exist on the default branch to use GitHub's manual-run UI.
Stable releases only are supported; prerelease/build-metadata tags fail validation.

## Publish a version

Merge the reviewed implementation/workflows into `main`, confirm CI is green, then tag the
specific reviewed commit. For example, for the next patch release:

```sh
git tag -a v0.1.1 <reviewed-commit-sha> -m "Orvin 0.1.1"
git push origin v0.1.1
```

The tag push triggers publication. Confirm both the GitHub package and release assets exist
before declaring the version available. Never move a published tag or replace an existing
version. A failure after Maven publication can leave the package available before release assets
exist; inspect the run and complete only the missing step using its verified artifacts. Blindly
rerunning deployment can fail on existing coordinates. Use a new version for changed content.

The main JAR includes the entire shared dataset and is about 74 MB. Source JARs and Python
distributions also include data. Dataset versions/hashes remain independent of library versions.

## Use Java from Gradle or Maven

These examples consume the published **0.1.0** release. Nothing in Tourfold is changed by this
setup. Both build systems consume the same `com.openresearch:orvin:0.1.0` artifact.

GitHub requires authentication for Maven/Gradle packages, including public ones. Set
`ORVIN_GITHUB_USER` to your username and `ORVIN_GITHUB_TOKEN` to a classic PAT with
`read:packages` and repository access. Keep credentials outside committed files; other CI systems
can store them as masked secrets. See GitHub's [Maven authentication](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-apache-maven-registry)
and [Gradle registry guidance](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-gradle-registry).

Gradle Kotlin DSL:

```kotlin
repositories {
    maven {
        name = "orvinGitHub"
        url = uri("https://maven.pkg.github.com/openresearch/orvin")
        credentials {
            username = providers.environmentVariable("ORVIN_GITHUB_USER").orNull
            password = providers.environmentVariable("ORVIN_GITHUB_TOKEN").orNull
        }
        content { includeModule("com.openresearch", "orvin") }
    }
}
dependencies {
    implementation("com.openresearch:orvin:0.1.0")
}
```

Maven `pom.xml`:

```xml
<repositories>
  <repository>
    <id>orvin-github</id>
    <url>https://maven.pkg.github.com/openresearch/orvin</url>
    <snapshots><enabled>false</enabled></snapshots>
  </repository>
</repositories>
<dependencies>
  <dependency>
    <groupId>com.openresearch</groupId>
    <artifactId>orvin</artifactId>
    <version>0.1.0</version>
  </dependency>
</dependencies>
```

Server in your user-level `~/.m2/settings.xml`:

```xml
<settings>
  <servers>
    <server>
      <id>orvin-github</id>
      <username>${env.ORVIN_GITHUB_USER}</username>
      <password>${env.ORVIN_GITHUB_TOKEN}</password>
    </server>
  </servers>
</settings>
```

For development snapshots, `mvn install` and Gradle's `mavenLocal()` remain available locally.
Consuming the JAR needs Java 17+, without Python, a database or runtime network calls.

## Python distribution

The wheel/sdist are GitHub Release assets, **not PyPI publications**. After publication:

```sh
python -m pip install https://github.com/openresearch/orvin/releases/download/v0.1.0/orvin-0.1.0-py3-none-any.whl
```

Alternatively download the wheel, verify `SHA256SUMS`, and install it locally. Python 3.10+
is required; no JDK or runtime dependencies are needed. Maven Central and PyPI remain separate
future setup: namespace ownership, credentials/trusted publisher configuration and Central
signing have not been provisioned.

## Local checks

```sh
.venv/bin/python -m pip install -r tools/release-requirements.txt
(cd libs/java && ./mvnw -Dpython=../../.venv/bin/python clean verify)
PYTHONPATH=libs/python python3 -m unittest discover -s libs/python/tests
.venv/bin/python -m build libs/python
python3 tools/check_parity.py
python3 tools/check_packages.py --jar libs/java/target/orvin-0.1.0-SNAPSHOT.jar --wheel libs/python/dist/orvin-0.1.0.dev0-py3-none-any.whl
```

To rehearse release stamping, use a disposable copy/worktree: `python3 tools/release.py prepare
v0.1.0` changes its POM/Python version, then follow the workflow's build/check commands.
`tools/release.py` never publishes. CI does not write version changes back to the source branch.
Review source authority, attribution and dataset diffs with data updates. Repository protection
is separate organization configuration; CODEOWNERS/templates alone do not enforce review.
