using System.Text.RegularExpressions;
using static OpenResearch.orVIN.J;

namespace OpenResearch.orVIN;

/// <summary>Exact lookup of independently supplied German type codes, preserving leading zeros.</summary>
public sealed class HsnTsnLookup
{
    private static readonly Lazy<HsnTsnLookup> Instance = new(() => new HsnTsnLookup());
    private readonly Dictionary<string, List<Dictionary<string, object?>>> entries = new();
    private readonly Dictionary<string, object?> dataset;
    public static HsnTsnLookup Bundled() => Instance.Value;
    private HsnTsnLookup()
    {
        var metadata = Bundle.Default.Metadata("kba");
        dataset = new[] { "version", "sha256", "referenceDate", "recordCount" }.ToDictionary(k => k, k => metadata[k]);
        dataset["source"] = new[] { "title", "publisher", "url", "serviceUrl", "retrievedOn", "license", "licenseUrl", "modifications", "snapshotSha256" }.ToDictionary(k => k, k => metadata[k]);
        var rows = Bundle.Default.Rows("kba/types.tsv").ToList(); var keys = rows[0];
        foreach (var c in rows.Skip(1))
        {
            var row = keys.Select((key, i) => (key, value: c[i] == "\\N" ? null : key is "registeredCount" or "sourceObjectId" ? (object)int.Parse(c[i]) : c[i])).ToDictionary(p => p.key, p => p.value);
            string id = Str(row["hsn"]) + Str(row["tsn"]);
            if (!entries.TryGetValue(id, out var group)) entries[id] = group = new(); group.Add(row);
        }
        if (entries.Values.Sum(g => g.Count) != (int)metadata["recordCount"]!) throw new InvalidDataException("Incomplete type-code table");
    }
    public VehicleAnswer LookupVehicle(string hsn, string tsn)
    {
        ArgumentNullException.ThrowIfNull(hsn); ArgumentNullException.ThrowIfNull(tsn);
        var h = VinDecoder.Normalize(hsn); var t = VinDecoder.Normalize(tsn);
        var validH = Regex.IsMatch(h, "^[0-9]{4}$"); var validT = Regex.IsMatch(t, "^[A-Z0-9]{3}$");
        var input = validH ? validT ? "VALID" : "INVALID_TSN" : validT ? "INVALID_HSN" : "INVALID_HSN_AND_TSN";
        var rows = input == "VALID" ? entries.GetValueOrDefault(h + t, new()) : new();
        var status = input != "VALID" ? "INVALID_INPUT" : rows.Count == 0 ? "UNKNOWN" : rows.Count == 1 ? "RECOGNIZED" : "AMBIGUOUS";
        var raw = Map("suppliedHsn", hsn, "suppliedTsn", tsn, "normalizedHsn", h, "normalizedTsn", t, "inputStatus", input,
            "status", status, "candidates", rows, "dataset", dataset, "value", status == "RECOGNIZED" ? rows[0] : null);
        return new AnswerBuilder(raw, false).Resolve();
    }
}
