using static OpenResearch.ORvin.J;

namespace OpenResearch.ORvin;

internal sealed class Approvals
{
    private readonly Dictionary<string, object?> dataset;
    private readonly Dictionary<string, object?> source = new();
    private readonly Dictionary<string, Dictionary<string, object?>> definitions = new();
    private readonly Dictionary<string, string> shards = new();
    private readonly Dictionary<string, List<string[]>> cache = new();
    internal Approvals()
    {
        var metadata = Bundle.Default.Metadata("astra"); dataset = Map("version", metadata["version"], "sha256", metadata["indexSha256"]);
        foreach (var c in Bundle.Default.Rows("astra/index.tsv"))
            switch (c[0])
            {
                case "D": source = RichDecoder.Source(c); break;
                case "F": definitions[c[1]] = Map("label", J.Decode(c[2]), "sourceColumn", J.Decode(c[3]), "unit", J.Decode(c[4])); break;
                case "W": shards[c[1]] = c[2]; break;
            }
    }
    internal Dictionary<string, object?> Decode(string vin, string structure)
    {
        var candidates = new List<Dictionary<string, object?>>();
        if (structure == "MODERN_FORMAT" && shards.TryGetValue(vin[..3], out var path))
        {
            if (!cache.TryGetValue(path, out var rows))
            {
                if (cache.Count >= 8) cache.Remove(cache.Keys.First());
                cache[path] = rows = Bundle.Default.Rows("astra/" + path).ToList();
            }
            foreach (var row in rows)
            {
                var masks = row[3].Split(',').Where(m => m.Length == 17 && m.Select((c, i) => c == '.' || c == vin[i]).All(b => b)).ToList();
                if (masks.Count == 0) continue;
                var values = definitions.Keys.Select((key, i) => (key, value: row[4 + i])).Where(p => p.value != "").ToDictionary(p => p.key, p => (object?)J.Decode(p.value));
                candidates.Add(Map("approvalId", row[0], "sourceId", source["id"], "sourceRow", int.Parse(row[1]), "vinPattern", J.Decode(row[2]), "matchedPatterns", masks, "fields", values));
            }
        }
        var fields = new Dictionary<string, object?>();
        foreach (var (key, definition) in definitions)
        {
            if (key == "remarks") continue;
            var values = Sorted(candidates.Select(c => Get(c["fields"], key)).Where(v => v is not null).Select(Str));
            if (values.Count > 0) fields[key] = new Dictionary<string, object?>(definition) { ["possibilities"] = values };
        }
        return Map("status", structure != "MODERN_FORMAT" ? "INVALID_INPUT" : candidates.Count > 0 ? "CANDIDATES" : "NO_MATCH",
            "dataset", dataset, "marketScope", Bundle.Default.Text("catalogue.market"), "warnings", candidates.Count > 0 ? Bundle.Default.Strings("catalogue.warnings") : new(),
            "fields", fields, "candidates", candidates, "sources", candidates.Count > 0 ? new[] { source } : Array.Empty<Dictionary<string, object?>>());
    }
}
