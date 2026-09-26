"""Explicit online refresh of the three reviewed structured sources. Never edits custom rules."""
import argparse
from datetime import date, datetime
from email.utils import parsedate_to_datetime
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen
import zipfile

import astra
import kba
import nhtsa

ROOT = nhtsa.ROOT
DOWNLOADS = "https://vpic.nhtsa.dot.gov/downloads/"


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def download(url, target, maximum):
    request = Request(url, headers={"User-Agent": "orVIN structured-data refresh"})
    with urlopen(request, timeout=120) as response, target.open("wb") as output:
        if response.url.split("/", 3)[:3] != url.split("/", 3)[:3]:
            raise ValueError("Source redirected to another origin; review required")
        size = 0
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            size += len(chunk)
            if size > maximum:
                raise ValueError("Source exceeds its reviewed download size limit")
            output.write(chunk)
        if not size:
            raise ValueError("Empty source download")
        return dict(response.headers)


def latest_nhtsa(html):
    entries = re.findall(r'plain backup file\s+"(vPICList_lite_(\d{4}_\d{2})\.plain\.zip)"'
                         r'\s+updated on\s+(\d{2}/\d{2}/\d{4})', html)
    if not entries:
        raise ValueError("NHTSA download listing format changed")
    filename, edition, published = max(entries, key=lambda entry: entry[1])
    published = datetime.strptime(published, "%m/%d/%Y").date()
    if published > date.today() or not re.fullmatch(r"\d{4}_(0[1-9]|1[0-2])", edition):
        raise ValueError("Unexpected NHTSA edition/publication date")
    return filename, edition, published.isoformat()


def count_guard(label, old, new):
    # Conservative operational tripwires, not a claim of factual completeness.
    # A larger correction is reviewed rather than silently redefining the threshold.
    if new <= 0 or (old and not old * 0.95 <= new <= old * 1.5):
        raise ValueError(f"{label}: unexpected count change {old} -> {new}; review required")


def exclusion_guard(label, old_excluded, old_total, new_excluded, new_total):
    if not old_total or not new_total or new_excluded / new_total > old_excluded / old_total + 0.01:
        raise ValueError(f"{label}: exclusion rate increased by more than one percentage point; review required")


def sql_contract(archive):
    """Pin schema and function bodies as a contract; changing SQL semantics needs review."""
    with zipfile.ZipFile(archive) as zipped:
        names = zipped.namelist()
        if len(names) != 1 or not re.fullmatch(r"vPICList_lite_\d{4}_\d{2}\.sql", names[0]):
            raise ValueError("Unexpected NHTSA archive members")
        schema, functions = {}, []
        collecting = False
        with zipped.open(names[0]) as stream:
            for raw in stream:
                line = raw.decode("utf-8-sig")
                match = nhtsa.COPY.fullmatch(line)
                if match:
                    if match[1] in schema:
                        raise ValueError("Duplicate NHTSA table")
                    schema[match[1]] = match[2].split(", ")
                if line.startswith("CREATE FUNCTION "):
                    collecting = True
                if collecting:
                    functions.append(line)
                    if re.match(r'^\s*\$[^$]*\$;', line):
                        collecting = False
        if collecting or not functions or not schema:
            raise ValueError("Incomplete NHTSA schema/function contract")
        return {"schema": schema, "functionsSha256": hashlib.sha256("".join(functions).encode()).hexdigest()}


def preserve_referenced_source(source, archive):
    """Keep old source bytes only when reviewed fixtures still cite that edition."""
    fixture_paths = [ROOT / "data/identity/fixtures.json", ROOT / "data/vehicle-fixtures.json",
                     ROOT / "data/astra/review.json"]
    cited = any(source["id"] in p.read_text() for p in fixture_paths)
    if cited:
        path = ROOT / "data/snapshots/metadata.json"
        history = read(path)
        if not any(s["id"] == source["id"] for s in history):
            history.append({**source, "snapshot": archive.relative_to(ROOT / "data").as_posix(),
                            "sha256": nhtsa.sha256(archive)})
            write(path, history)
    return cited


def command(*args):
    subprocess.run(args, cwd=ROOT, check=True)


def refresh(apply=False):
    old_nhtsa = read(ROOT / "data/nhtsa/metadata.json")
    old_astra = read(ROOT / "data/astra/metadata.json")
    old_kba = read(ROOT / "data/kba/metadata.json")
    old_decoding = read(ROOT / "data/decoding/metadata.json")
    today = date.today().isoformat()
    pins = read(ROOT / "tools/source-pins.json")
    versions = [pins["nhtsa"]["version"], pins["identityVersion"], pins["decodingVersion"], old_kba["version"]]
    prefix = today.replace("-", ".") + "."
    revision = max([int(v[len(prefix):]) for v in versions if v.startswith(prefix)] + [0]) + 1
    version = prefix + str(revision)
    report = {"checkedOn": today, "changed": [], "sources": {}}
    with tempfile.TemporaryDirectory(prefix="orvin-refresh-") as temporary:
        staging = Path(temporary)
        listing = staging / "nhtsa-listing.html"
        download(DOWNLOADS, listing, 2 * 1024 * 1024)
        filename, edition, publication = latest_nhtsa(listing.read_text())
        if edition < pins["nhtsa"]["edition"]:
            raise ValueError("NHTSA listing would downgrade the pinned edition")
        archive = staging / filename
        download(DOWNLOADS + filename, archive, 512 * 1024 * 1024)
        sha = nhtsa.sha256(archive)
        nhtsa_changed = sha != old_nhtsa["source"]["sha256"]
        report["sources"]["nhtsa"] = {"url": DOWNLOADS + filename, "edition": edition,
            "sha256": sha, "previousSha256": old_nhtsa["source"]["sha256"],
            "previousCounts": old_decoding["counts"]}
        if nhtsa_changed:
            previous = ROOT / "data" / old_nhtsa["source"]["snapshot"]
            if sql_contract(archive) != sql_contract(previous):
                raise ValueError("NHTSA schema or SQL decoding semantics changed; manual review required")
            report["changed"].append("nhtsa")

        astra_raw = staging / "TG-Automobil.txt"
        headers = download(astra.SOURCE_URL, astra_raw, 768 * 1024 * 1024)
        astra_sha = nhtsa.sha256(astra_raw)
        astra_changed = astra_sha != old_astra["source"]["inspectedSha256"]
        modified = headers.get("Last-Modified")
        edition_date = parsedate_to_datetime(modified).date().isoformat() if modified else today
        if edition_date > today:
            raise ValueError("ASTRA modification date is in the future")
        report["sources"]["astra"] = {"url": astra.SOURCE_URL, "sha256": astra_sha,
            "lastModified": modified, "previousSha256": old_astra["source"]["inspectedSha256"],
            "previousCounts": old_astra["counts"]}
        if astra_changed:
            with astra_raw.open("rb") as new, gzip.open(ROOT / "data" / old_astra["source"]["archivePath"], "rb") as old:
                if new.readline() != old.readline():
                    raise ValueError("ASTRA column schema changed; manual review required")
            report["changed"].append("astra")

        metadata_file = staging / "kba-service.json"
        download(kba.SERVICE + "?f=json", metadata_file, 2 * 1024 * 1024)
        service = read(metadata_file)
        expected_types = {name: ("esriFieldTypeOID" if name == "ObjectId" else
                           "esriFieldTypeInteger" if name == "Anzahl" else "esriFieldTypeString") for name in kba.FIELDS}
        if {f["name"]: f["type"] for f in service["fields"]} != expected_types:
            raise ValueError("KBA field schema changed; manual review required")
        if service.get("copyrightText") or service.get("description"):
            raise ValueError("KBA source notices changed; review against existing reuse assessment")
        if not isinstance(service.get("editingInfo", {}).get("lastEditDate"), int):
            raise ValueError("KBA no longer provides a snapshot modification timestamp")
        dates = kba.query(where="1=1", outFields="Berichtszeitpunkt", returnDistinctValues="true", returnGeometry="false")
        if dates.get("exceededTransferLimit"):
            raise ValueError("Incomplete KBA reference-date discovery")
        latest_date = max(datetime.strptime(r["attributes"]["Berichtszeitpunkt"], "%d.%m.%Y").date()
                          for r in dates["features"]).isoformat()
        if latest_date < old_kba["referenceDate"] or latest_date > today:
            raise ValueError("Unexpected KBA reference date")
        kba.download(latest_date, version, staging / "kba")
        new_kba = kba.validate(staging / "kba")
        download(kba.SERVICE + "?f=json", metadata_file, 2 * 1024 * 1024)
        if read(metadata_file).get("editingInfo") != service.get("editingInfo"):
            raise ValueError("KBA changed during retrieval; retry with a coherent snapshot")
        kba_changed = new_kba["sha256"] != old_kba["sha256"] or latest_date != old_kba["referenceDate"]
        count_guard("KBA rows", old_kba["recordCount"], new_kba["recordCount"])
        report["sources"]["kba"] = {"url": kba.SERVICE, "referenceDate": latest_date,
            "sha256": new_kba["sha256"], "previousSha256": old_kba["sha256"], "rows": new_kba["recordCount"]}
        if kba_changed:
            report["changed"].append("kba")
        if not apply or not report["changed"]:
            return report

        # All downloads and source contracts passed. This checkout is disposable;
        # the workflow commits only after complete validation and behavioral tests.
        if nhtsa_changed:
            source = next(s for s in read(ROOT / "data/decoding/sources.json") if s["id"] == old_nhtsa["source"]["id"])
            previous = ROOT / "data" / old_nhtsa["source"]["snapshot"]
            keep_old = preserve_referenced_source(source, previous)
            # A corrected file may retain its upstream name. Move the old evidence
            # to a content-addressed local name before installing the corrected bytes.
            if previous.name == filename and keep_old:
                retained = previous.with_name(previous.name.replace(".plain.zip", "_" + nhtsa.sha256(previous)[:12] + ".plain.zip"))
                previous.rename(retained)
                history_path = ROOT / "data/snapshots/metadata.json"
                history = read(history_path)
                for item in history:
                    if item["id"] == source["id"]:
                        item["snapshot"] = retained.relative_to(ROOT / "data").as_posix()
                        item["archivePath"] = item["snapshot"]
                write(history_path, history)
            pins["nhtsa"] = {"edition": edition, "version": version, "retrievedOn": today,
                "publishedOn": publication, "sha256": sha,
                "title": "NHTSA vPIC standalone database, " + edition.replace("_", "-"),
                "sourceId": "nhtsa-vpic-" + edition.replace("_", "-") + "-" + sha[:12]}
            pins["decodingVersion"] = version
            pins["referenceYear"] = int(edition[:4])
            write(ROOT / "tools/source-pins.json", pins)
            command(sys.executable, "tools/nhtsa.py", "import", "--archive", str(archive))
            if not keep_old and previous.name != filename:
                previous.unlink()
            new = read(ROOT / "data/nhtsa/metadata.json")
            for key in ("runtimeWmiCount", "runtimeManufacturerCount", "runtimeAssignmentCount"):
                count_guard("NHTSA " + key, old_nhtsa[key], new[key])
            for table, old in old_nhtsa["tables"].items():
                if old["rowCount"]:
                    count_guard("NHTSA table " + table, old["rowCount"], new["tables"][table]["rowCount"])
            command(sys.executable, "tools/decoding.py", "import")
            counts = read(ROOT / "data/decoding/metadata.json")["counts"]
            count_guard("NHTSA exported patterns", old_decoding["counts"]["exportedPatterns"], counts["exportedPatterns"])
            exclusion_guard("NHTSA decoding", old_decoding["counts"]["sourcePatterns"] - old_decoding["counts"]["exportedPatterns"],
                            old_decoding["counts"]["sourcePatterns"], counts["sourcePatterns"] - counts["exportedPatterns"], counts["sourcePatterns"])
            report["sources"]["nhtsa"]["counts"] = counts
        if astra_changed:
            source = dict(old_astra["source"])
            previous = ROOT / "data" / source["archivePath"]
            keep_old = preserve_referenced_source(source, previous)
            source.update(id="astra-targa-automobil-" + edition_date + "-" + astra_sha[:12],
                          edition=f"HTTP Last-Modified {modified or 'not supplied'}; retrieved {today}",
                          retrievedOn=today, inspectedSha256=astra_sha)
            source["archivePath"] = f"astra/TG-Automobil-{edition_date}-{astra_sha[:12]}.txt.gz"
            destination = ROOT / "data" / source["archivePath"]
            with astra_raw.open("rb") as src, destination.open("wb") as out:
                with gzip.GzipFile(fileobj=out, mode="wb", filename="", mtime=0) as compressed:
                    shutil.copyfileobj(src, compressed)
            source["archiveSha256"] = nhtsa.sha256(destination)
            new = astra.compile_snapshot(destination, astra.DIRECTORY, source, "astra-" + version)
            for key in ("sourceRows", "passengerRows", "approvalRows", "patterns", "wmis"):
                count_guard("ASTRA " + key, old_astra["counts"][key], new["counts"][key])
            exclusion_guard("ASTRA patterns", old_astra["counts"]["excludedPatternRows"], old_astra["counts"]["passengerRows"],
                            new["counts"]["excludedPatternRows"], new["counts"]["passengerRows"])
            report["sources"]["astra"]["counts"] = new["counts"]
            write(astra.DIRECTORY / "metadata.json", new)
            if not keep_old:
                previous.unlink()
            command(sys.executable, "tools/europe_coverage.py", "--refresh")
        if kba_changed:
            for name in ("source.json.gz", "types.tsv", "metadata.json"):
                shutil.copyfile(staging / "kba" / name, ROOT / "data/kba" / name)
        pins["identityVersion"] = version
        write(ROOT / "tools/source-pins.json", pins)
        command(sys.executable, "tools/identity.py", "--generate")
        command(sys.executable, "tools/compile_dataset.py", "--generate")
        command(sys.executable, "tools/dataset.py", "--update-runtime")
        report["datasetVersion"] = version
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Regenerate in a clean disposable checkout")
    parser.add_argument("--report", type=Path, default=ROOT / "target/data-refresh.json")
    args = parser.parse_args()
    if args.apply and subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        parser.error("--apply requires a clean checkout; use a disposable branch/worktree")
    report = refresh(args.apply)
    write(args.report, report)
    print(json.dumps(report, sort_keys=True))
    if output := __import__("os").environ.get("GITHUB_OUTPUT"):
        with open(output, "a") as stream:
            stream.write("changed=" + str(bool(report["changed"])).lower() + "\n")


if __name__ == "__main__":
    main()
