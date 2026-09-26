"""Verify that release artifacts contain the exact compiled runtime bundle, byte-for-byte."""
import argparse
import hashlib
from pathlib import Path
import zipfile

from nhtsa import ROOT, sha256


def check(path, prefix):
    files = sorted(p for p in (ROOT / "data/generated").rglob("*") if p.is_file())
    with zipfile.ZipFile(path) as archive:
        actual = {n[len(prefix):] for n in archive.namelist() if n.startswith(prefix) and not n.endswith("/")}
        expected = {p.relative_to(ROOT / "data/generated").as_posix() for p in files}
        if actual != expected:
            raise ValueError(f"Unexpected/missing packaged files: {sorted(actual ^ expected)}")
        for path_in_repo in files:
            name = prefix + path_in_repo.relative_to(ROOT / "data/generated").as_posix()
            digest = hashlib.sha256()
            with archive.open(name) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != sha256(path_in_repo):
                raise ValueError(f"Packaged data mismatch: {name}")
    print(f"Verified all {len(files)} shared data files in {path.name} ({path.stat().st_size:,} bytes)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jar", type=Path)
    parser.add_argument("--wheel", type=Path)
    args = parser.parse_args()
    if not args.jar and not args.wheel:
        parser.error("supply --jar and/or --wheel")
    if args.jar:
        check(args.jar, "META-INF/orvin/")
    if args.wheel:
        check(args.wheel, "orvin/_data/")


if __name__ == "__main__":
    main()
