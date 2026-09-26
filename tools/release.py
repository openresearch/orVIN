"""Prepare matching Java/Python/.NET release versions and verified release assets.

This tool never publishes. GitHub Actions publishes only for pushed vX.Y.Z tags;
manual workflow runs exercise the same build without publication.
"""
import argparse
from email.parser import BytesParser
import json
from pathlib import Path
import re
import shutil
import tarfile
import xml.etree.ElementTree as ET
import zipfile

from nhtsa import ROOT, sha256

NS = {"m": "http://maven.apache.org/POM/4.0.0"}


def version_from_tag(tag):
    if not re.fullmatch(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", tag):
        raise ValueError("Release tag must be vMAJOR.MINOR.PATCH, without leading zeroes or prerelease suffixes")
    return tag[1:]


def prepare(tag, root=ROOT):
    version = version_from_tag(tag)
    dotnet_path = root / "libs/dotnet/orVIN/orVIN.csproj"
    dotnet = dotnet_path.read_text(encoding="utf-8")
    dotnet, count = re.subn(r"<Version>[^<]+</Version>", "<Version>" + version + "</Version>", dotnet)
    if count != 1:
        raise ValueError("Expected one .NET package version")
    pom_path = root / "libs/java/pom.xml"
    python_path = root / "libs/python/pyproject.toml"
    pom = pom_path.read_text(encoding="utf-8")
    python = python_path.read_text(encoding="utf-8")
    old_version = ET.fromstring(pom).findtext("m:version", namespaces=NS)
    if old_version is None:
        raise ValueError("Missing Maven project version")
    # Target only the project's first version, never dependency/plugin versions.
    pom, count = re.subn(r"(<version>)" + re.escape(old_version) + r"(</version>)",
                         lambda m: m[1] + version + m[2], pom, count=1)
    if count != 1 or ET.fromstring(pom).findtext("m:version", namespaces=NS) != version:
        raise ValueError("Cannot update Maven project version")
    pom, count = re.subn(r"<tag>[^<]*</tag>", "<tag>" + tag + "</tag>", pom)
    if count != 1:
        raise ValueError("Expected one SCM tag")
    python, count = re.subn(r'^version = "[^"]+"$', 'version = "' + version + '"', python, flags=re.MULTILINE)
    if count != 1:
        raise ValueError("Expected one Python project version")
    # Validate all package versions before changing any file.
    dotnet_path.write_text(dotnet, encoding="utf-8", newline="\n")
    pom_path.write_text(pom, encoding="utf-8", newline="\n")
    python_path.write_text(python, encoding="utf-8", newline="\n")
    return version


def check_pom(content, version):
    pom = ET.fromstring(content)
    for field, expected in (("groupId", "com.openresearch"), ("artifactId", "orvin"), ("version", version)):
        if pom.findtext("m:" + field, namespaces=NS) != expected:
            raise ValueError("Release POM has unexpected " + field)


def check_python_metadata(content, version):
    metadata = BytesParser().parsebytes(content)
    if metadata["Name"] != "orvin" or metadata["Version"] != version:
        raise ValueError("Python artifact name/version differs from the release tag")



def check_nuget_metadata(content, version):
    # NuGet chooses the schema namespace for the metadata it emits; it is not fixed
    # to one SDK version. Identity and version still must match the release exactly.
    metadata = ET.fromstring(content)
    if (metadata.findtext("{*}metadata/{*}id") != "OpenResearch.orVIN"
            or metadata.findtext("{*}metadata/{*}version") != version):
        raise ValueError("NuGet artifact name/version differs from release tag")


def bundle(tag, commit, root=ROOT):
    version = version_from_tag(tag)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Release manifest requires the full source commit SHA")
    java = root / "libs/java"
    python = root / "libs/python/dist"
    jars = [java / "target" / f"orvin-{version}{suffix}.jar" for suffix in ("", "-sources", "-javadoc")]
    wheel = python / f"orvin-{version}-py3-none-any.whl"
    sdist = python / f"orvin-{version}.tar.gz"
    nuget = root / "libs/dotnet/dist" / f"OpenResearch.orVIN.{version}.nupkg"
    pom = java / "pom.xml"
    for path in [*jars, wheel, sdist, nuget, pom]:
        if not path.is_file():
            raise ValueError(f"Release artifact missing: {path.name}")
    with zipfile.ZipFile(nuget) as archive:
        check_nuget_metadata(archive.read("OpenResearch.orVIN.nuspec"), version)
    check_pom(pom.read_bytes(), version)
    with zipfile.ZipFile(jars[0]) as archive:
        check_pom(archive.read("META-INF/maven/com.openresearch/orvin/pom.xml"), version)
    with zipfile.ZipFile(wheel) as archive:
        check_python_metadata(archive.read(f"orvin-{version}.dist-info/METADATA"), version)
    with tarfile.open(sdist) as archive:
        with archive.extractfile(f"orvin-{version}/PKG-INFO") as stream:
            check_python_metadata(stream.read(), version)
    destination = root / "target/release"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    for path in [*jars, wheel, sdist, nuget]:
        shutil.copyfile(path, destination / path.name)
    shutil.copyfile(pom, destination / f"orvin-{version}.pom")
    dataset = json.loads((root / "data/dataset.json").read_text(encoding="utf-8"))
    kba = json.loads((root / "data/kba/metadata.json").read_text(encoding="utf-8"))
    decoding = json.loads((root / "data/decoding/metadata.json").read_text(encoding="utf-8"))
    manifest = {"version": version, "tag": tag, "commit": commit,
                "javaCoordinates": "com.openresearch:orvin:" + version,
                "nugetPackage": "OpenResearch.orVIN", "runtimeFormat": "orvin-runtime-1",
                "runtimeManifestSha256": sha256(root / "data/generated/manifest.tsv"),
                "wmiDatasetVersion": dataset["version"], "wmiDatasetSha256": sha256(root / "data/dataset.json"),
                "kbaDatasetVersion": kba["version"], "kbaTableSha256": kba["sha256"],
                "decodingDatasetVersion": decoding["version"], "decodingIndexSha256": decoding["indexSha256"],
                "decodingSourcesSha256": decoding["sourcesSha256"],
                "artifacts": {p.name: sha256(p) for p in sorted(destination.iterdir())}}
    (destination / "release.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    sums = "".join(sha256(p) + "  " + p.name + "\n" for p in sorted(destination.iterdir()))
    (destination / "SHA256SUMS").write_text(sums, encoding="utf-8")
    print(f"Prepared {len(manifest['artifacts'])} release artifacts, manifest and checksums in {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("version", "prepare", "bundle"))
    parser.add_argument("tag")
    parser.add_argument("--commit")
    args = parser.parse_args()
    if args.command == "bundle":
        if args.commit is None:
            parser.error("bundle requires --commit")
        bundle(args.tag, args.commit)
    elif args.command == "prepare":
        print(prepare(args.tag))
    else:
        print(version_from_tag(args.tag))


if __name__ == "__main__":
    main()
