"""Readable command-line views; the public library results remain unchanged."""
import json


def _text(value):
    # Keep names readable while escaping terminal controls and embedded newlines.
    return json.dumps(str(value), ensure_ascii=False)[1:-1]


def _label(value):
    return value.replace("_", " ").capitalize()


def _resolution(field, transform=str):
    if field["status"] == "KNOWN":
        return _text(transform(field["value"]))
    possibilities = "; ".join(_text(transform(value)) for value in field["possibilities"])
    label = _label(field["status"])
    return f"{label} (possible: {possibilities})" if possibilities else label


def _status(result):
    count = len(result["candidates"])
    return f"Status: {_label(result['status'])} ({count} {'match' if count == 1 else 'matches'})"


def vin_summary(result):
    structure = {
        "MODERN_FORMAT": "17 characters; allowed VIN alphabet (checksum not checked)",
        "INVALID_CHARACTERS": "Contains characters outside the VIN alphabet",
        "UNSUPPORTED_LENGTH": "Unsupported length; only 17-character VINs are supported",
    }
    lines = [f"VIN: {_text(result['normalized'])}", _status(result),
             "Manufacturer: " + _resolution(result["manufacturer"], lambda m: m["name"]),
             "Brand: " + _resolution(result["brand"]),
             "Category: " + _resolution(result["category"], _label),
             "Manufacturer country: " + _resolution(result["manufacturerCountry"]),
             "Assembly country: " + _resolution(result["assemblyCountry"]),
             "Structure: " + structure[result["structure"]]]
    if result["status"] == "NEEDS_CONTEXT":
        lines.append("Model-year or market context is needed to establish this match.")
    elif result["status"] == "UNKNOWN":
        lines.append("No assignment in this dataset; this does not establish that the VIN is invalid.")
    details = result["details"]
    lines.append("Vehicle details: " + _label(details["status"]))
    for code, field in details["fields"].items():
        if code not in ("Make", "PlantCountry"):
            lines.append(_text(field["label"]) + ": " + _resolution(field))
    for warning in details["warnings"]:
        lines.append(_text(warning))
    approvals = result["typeApprovals"]
    if approvals["candidates"]:
        lines.append(f"Swiss type-approval candidates: {len(approvals['candidates'])}")
        for key in ("make", "type", "engineCode", "fuelCode", "displacementCc", "powerKw"):
            if key in approvals["fields"]:
                field = approvals["fields"][key]
                values = field["possibilities"]
                suffix = f" … ({len(values)} alternatives; see --json)" if len(values) > 8 else ""
                unit = f" ({field['unit']})" if field["unit"] else ""
                lines.append("Possible " + _text(field["label"]) + unit + ": " +
                             "; ".join(map(_text, values[:8])) + suffix)
        lines.extend(_text(w) for w in approvals["warnings"])
    lines.append("Coverage: sourced VIN patterns; exact build date and complete options are not available.")
    lines.append("Dataset: " + _text(result["dataset"]["version"]))
    sources = {}
    for candidate in result["candidates"]:
        for source in candidate["sources"] + candidate["manufacturer"]["sources"]:
            sources.setdefault(source["id"], source)
    for source in details["sources"]:
        sources.setdefault(source["id"], source)
    for source in approvals["sources"]:
        sources.setdefault(source["id"], source)
    for source in sources.values():
        lines.append(f"Source: {_text(source['publisher'])} — {_text(source['url'])}")
    lines.append("Use --json for the complete result and source details.")
    return "\n".join(lines)


def hsntsn_summary(result):
    lines = [f"HSN / TSN: {_text(result['normalizedHsn'])} / {_text(result['normalizedTsn'])}", _status(result)]
    if result["status"] == "INVALID_INPUT":
        lines.append("Input: " + _label(result["inputStatus"]))
        lines.append("Use a four-digit HSN (keep leading zeroes) and a three-character TSN.")
    elif result["status"] == "UNKNOWN":
        lines.append("No entry in this dated snapshot; this does not establish that the codes are invalid.")
    for index, entry in enumerate(result["candidates"], start=1):
        if len(result["candidates"]) > 1:
            lines.append(f"Candidate {index}:")
        for name, key in (("Manufacturer", "manufacturer"), ("Trade / model name", "tradeName")):
            lines.append(f"{name}: " + ("Unknown" if entry[key] is None else _text(entry[key])))
        count = "Unknown" if entry["registeredCount"] is None else f"{entry['registeredCount']:,}"
        lines.append(f"Registered vehicles: {count}")
        if entry["countMarker"] is not None:
            lines.append("Statistical marker: " + _text(entry["countMarker"]))
    dataset = result["dataset"]
    source = dataset["source"]
    lines.extend(["Reference date: " + _text(dataset["referenceDate"]),
                  "Dataset: " + _text(dataset["version"]),
                  f"Source: {_text(source['publisher'])} — {_text(source['url'])}",
                  f"License: {_text(source['license'])} — {_text(source['licenseUrl'])}",
                  "Modifications: " + _text(source["modifications"]),
                  "Use --json for the complete result and source details."])
    return "\n".join(lines)
