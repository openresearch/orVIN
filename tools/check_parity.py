"""Compare complete JSON results after building libs/java; not required to use the Python scripts."""
import argparse
import base64
import csv
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "libs/python"))
from orvin import Context, HsnTsnLookup, VinDecoder
from orvin.answer import vin_answer, hsntsn_answer


def encoded(value):
    return base64.b64encode(value.encode()).decode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jar", type=Path, default=ROOT / "libs/java/target/orvin-0.2.0-SNAPSHOT.jar")
    args = parser.parse_args()
    requests, expected = [], []
    decoder = VinDecoder.bundled()
    vins = [f["vin"] for f in json.loads((ROOT / "data/fixtures.json").read_text())]
    vins += [f["vin"] for f in json.loads((ROOT / "data/vehicle-fixtures.json").read_text())]
    vins += [f["vin"] for f in json.loads((ROOT / "data/astra/review.json").read_text())["fixtures"]]
    vins += [f["vin"] for f in json.loads((ROOT / "data/identity/fixtures.json").read_text())]
    vins += ["5VLAA24208A000001", "5UPAA2420AA000001", "XP7YGAEK0RB000001", "XP7YGAEK0TC000001"]
    data = json.loads((ROOT / "data/dataset.json").read_text())
    wmis = sorted({a["wmi"] for a in data["assignments"]})
    # Exercise both ordinary and extended layouts across the full bulk catalog,
    # including all categories and the real seven-brand collision at 1C4.
    sample = set(wmis[::43] + wmis[-1:] + ["1C4", "1H9334"])
    categories = {}
    for assignment in data["assignments"]:
        categories.setdefault(assignment["category"], assignment["wmi"])
    sample.update(categories.values())
    vins += [wmi[:3] + "A" * 8 + wmi[3:] + "A" * 3 if len(wmi) == 6 else wmi + "A" * 14
             for wmi in sorted(sample)]
    vins += ["", "CHASSIS-1962", "ZZZAAAAAAAAAAAAAA", " 1hgaaaaaaaaaaaaaa ", "1HGIAAAAAAAAAAAAA",
             "1HGAAAAAAAAAAAAAſ", "1HGAAAAAAAAAAAA😀", "1H9AAAAAAAA334AAA", "1H9333AAAAAAAAAAA", 'quote"\t\\\n']
    for vin in vins:
        for context in (Context(), Context(2005, "US"), Context(market="US"), Context(market="DE")):
            requests.append("\t".join(["vin", encoded(vin), str(context.model_year or ""), context.market or ""]))
            expected.append(decoder.decode(vin, context))
    lookup = HsnTsnLookup.bundled()
    with (ROOT / "data/kba/types.tsv").open() as stream:
        rows = list(csv.DictReader(stream, delimiter="\t", quoting=csv.QUOTE_NONE))
    # Spread across the source table, plus reviewed missing-label and multi-name cases.
    pairs = [(r["hsn"], r["tsn"]) for r in rows[::317]] + [(rows[-1]["hsn"], rows[-1]["tsn"])]
    pairs += [(f["hsn"], f["tsn"]) for f in json.loads((ROOT / "data/kba/fixtures.json").read_text())]
    pairs += [(" 0005 ", "amq"), ("9999", "ZZZ"), ("5", "AMQ"), ("0005", "AMQ12345"),
              ("", ""), ("０００５", "AMQ"), ("0005", "aſq"), ("0005", "\tAMQ")]
    for hsn, tsn in pairs:
        requests.append("\t".join(["hsntsn", encoded(hsn), encoded(tsn)]))
        expected.append(lookup.lookup(hsn, tsn))
    # The new consumer contract is compared in full, not only its primary values.
    normalized_requests, normalized_expected = [], []
    for request, raw in zip(requests, expected):
        answer = vin_answer(raw) if request.startswith("vin\t") else hsntsn_answer(raw)
        kind, rest = request.split("\t", 1)
        for view, result in (("short", answer.short()), ("long", answer.long())):
            normalized_requests.append(kind + ":" + view + "\t" + rest)
            normalized_expected.append(result)
    requests.extend(normalized_requests)
    expected.extend(normalized_expected)
    # Load production classes AND resources only from the distributable JAR.
    classpath = os.pathsep.join((str(args.jar.resolve()), str(ROOT / "libs/java/target/test-classes")))
    completed = subprocess.run(["java", "-cp", classpath, "com.openresearch.orvin.ParityProbe"],
                               input="\n".join(requests) + "\n", text=True, capture_output=True, check=True)
    actual = [json.loads(line) for line in completed.stdout.splitlines()]
    if len(actual) != len(expected):
        raise AssertionError("Java/Python returned different result counts")
    for index, (left, right) in enumerate(zip(expected, actual)):
        if left != right:
            raise AssertionError(f"Parity mismatch at {requests[index]}:\nPython: {left}\nJava: {right}")
    print(f"Java/Python parity passed for {len(expected)} complete results (including provenance and null fields)")


if __name__ == "__main__":
    main()
