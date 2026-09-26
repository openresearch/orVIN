"""Commit a validated structured refresh and atomically push main plus a new patch tag."""
import fnmatch
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = (
    "tools/source-pins.json", "data/dataset.json", "data/nhtsa/metadata.json", "data/nhtsa/*.plain.zip",
    "data/kba/metadata.json", "data/kba/source.json.gz", "data/kba/types.tsv",
    "data/astra/metadata.json", "data/astra/index.tsv", "data/astra/TG-Automobil-*.txt.gz",
    "data/astra/patterns/*.tsv.gz", "data/decoding/metadata.json", "data/decoding/sources.json",
    "data/decoding/index.tsv", "data/decoding/patterns-*.tsv.gz", "data/identity/metadata.json",
    "data/identity/index.tsv", "data/snapshots/metadata.json",
    "libs/java/src/main/resources/com/openresearch/orvin/*-metadata.tsv",
    "libs/java/src/main/resources/com/openresearch/orvin/dataset.tsv",
    "docs/research/europe-priority/models-100.json", "docs/data-refresh/latest.json",
)


def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def next_tag(tags):
    versions = [tuple(map(int, t[1:].split("."))) for t in tags
                if re.fullmatch(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", t)]
    if not versions:
        raise ValueError("No existing stable release; initial version must be chosen manually")
    major, minor, patch = max(versions)
    return f"v{major}.{minor}.{patch + 1}"


def check_paths(paths):
    if not paths or any(not any(fnmatch.fnmatchcase(p, pattern) for pattern in ALLOWED) for p in paths):
        raise ValueError("Refresh touched files outside the structured-data allowlist")


def main():
    if os.environ.get("GITHUB_REF") != "refs/heads/main" or os.environ.get("GITHUB_REPOSITORY") != "openresearch/orvin":
        raise ValueError("Refresh publication is restricted to official main")
    report = json.loads((ROOT / "target/data-refresh.json").read_text())
    if not report["changed"]:
        raise ValueError("No changed data to publish")
    report_path = ROOT / "docs/data-refresh/latest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    paths = set(run("git", "diff", "--name-only").splitlines())
    paths.update(run("git", "ls-files", "--others", "--exclude-standard").splitlines())
    check_paths(paths)
    run("git", "fetch", "origin", "main", "--tags")
    if run("git", "rev-parse", "HEAD") != run("git", "rev-parse", "origin/main"):
        raise ValueError("main advanced during validation; retry from its new revision")
    tag = next_tag(run("git", "tag", "--list").splitlines())
    run("git", "config", "user.name", "ORvin data updater")
    run("git", "config", "user.email", "orvin-updater@openresearch.com")
    run("git", "add", "--", *sorted(paths))
    run("git", "commit", "-m", "Refresh structured vehicle data: " + ", ".join(report["changed"]))
    commit = run("git", "rev-parse", "HEAD")
    run("git", "tag", "-a", tag, "-m", "ORvin " + tag[1:] + " structured data refresh")
    run("git", "push", "--atomic", "origin", "HEAD:main", tag)
    with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
        stream.write(f"tag={tag}\ncommit={commit}\n")


if __name__ == "__main__":
    main()
