using System.Text.RegularExpressions;
using static OpenResearch.ORvin.J;

namespace OpenResearch.ORvin;

/// <summary>Offline decoding from the versioned, embedded runtime bundle.</summary>
public sealed class VinDecoder
{
    private static readonly Lazy<VinDecoder> Instance = new(() => new VinDecoder());
    private readonly Dictionary<string, List<Dictionary<string, object?>>> assignments = new();
    private readonly HashSet<string> extended = new();
    private readonly Dictionary<string, object?> dataset;
    private readonly RichDecoder rich = new();
    private readonly Approvals approvals = new();
    private readonly object gate = new();
    public static VinDecoder Bundled() => Instance.Value;
    private VinDecoder()
    {
        Dictionary<string, Dictionary<string, object?>> sources = new(), manufacturers = new();
        dataset = new();
        foreach (var c in Bundle.Default.Rows("dataset.tsv"))
        {
            switch (c[0])
            {
                case "V": dataset = Map("version", c[1], "sha256", c[2]); break;
                case "S": sources[c[1]] = Map("id", c[1], "title", c[2], "url", c[3], "publisher", c[4], "retrievedOn", c[5],
                    "publicationVersion", c[6], "section", c[7], "license", c[8], "reuseUrl", c[9], "reuseBasis", c[10],
                    "snapshot", Empty(c[11]), "snapshotSha256", Empty(c[12])); break;
                case "M": manufacturers[c[1]] = Map("id", c[1], "name", c[2], "country", Empty(c[3]), "sources", c[4].Split(',').Select(s => sources[s]).ToList()); break;
                case "A":
                    var row = Map("id", c[1], "wmi", c[2], "manufacturer", manufacturers[c[3]], "brand", Empty(c[4]), "category", Empty(c[5]),
                        "sources", c[6].Split(',').Select(s => sources[s]).ToList(), "constraints", Map("markets", c[7].Split(',', StringSplitOptions.RemoveEmptyEntries),
                        "fromModelYear", c[8] == "" ? null : int.Parse(c[8]), "toModelYear", c[9] == "" ? null : int.Parse(c[9])),
                        "notes", c[10], "ambiguityGroup", Empty(c[11]), "ambiguityReason", Empty(c[12]));
                    if (!assignments.TryGetValue(c[2], out var group)) assignments[c[2]] = group = new();
                    group.Add(row); if (c[2].Length == 6) extended.Add(c[2][..3]); break;
                default: throw new InvalidDataException("Unsupported assignment operation");
            }
        }
    }
    private static string? Empty(string text) => text == "" ? null : text;
    internal static string Normalize(string text) => new(text.Trim(' ').Select(c => c is >= 'a' and <= 'z' ? (char)(c - 32) : c).ToArray());
    private static bool MayApply(Dictionary<string, object?> row, Context context)
    {
        var c = Obj(row["constraints"]); var markets = List(c["markets"]);
        return (context.Market is null || markets.Count == 0 || markets.Contains(context.Market)) &&
            (context.ModelYear is null || context.ModelYear >= (int)(c["fromModelYear"] ?? 1886) && context.ModelYear <= (int)(c["toModelYear"] ?? 9999));
    }
    private static bool Established(Dictionary<string, object?> row, Context context)
    {
        var c = Obj(row["constraints"]);
        return (List(c["markets"]).Count == 0 || context.Market is not null) &&
            (c["fromModelYear"] is null && c["toModelYear"] is null || context.ModelYear is not null);
    }
    private static Dictionary<string, object?> Resolve(List<Dictionary<string, object?>> rows, Func<Dictionary<string, object?>, object?> get, Context context)
    {
        var values = rows.Select(get).Where(v => v is not null).GroupBy(Canonical).Select(g => g.First()).ToList();
        var status = values.Count > 1 ? "AMBIGUOUS" : rows.Count == 0 || rows.Any(r => get(r) is null) ? "UNKNOWN"
            : rows.Any(r => !Established(r, context)) ? "NEEDS_CONTEXT" : "KNOWN";
        return Map("status", status, "possibilities", values, "value", status == "KNOWN" ? values[0] : null);
    }
    public VehicleAnswer DecodeVehicle(string vin, Context? context = null)
    {
        ArgumentNullException.ThrowIfNull(vin);
        lock (gate) return new AnswerBuilder(Decode(vin, context ?? new()), true).Resolve();
    }
    internal Dictionary<string, object?> Decode(string supplied, Context context)
    {
        var vin = Normalize(supplied);
        var structure = vin.Length != 17 ? "UNSUPPORTED_LENGTH" : Regex.IsMatch(vin, "^[A-HJ-NPR-Z0-9]{17}$", RegexOptions.CultureInvariant) ? "MODERN_FORMAT" : "INVALID_CHARACTERS";
        var rows = new List<Dictionary<string, object?>>();
        var status = "UNSUPPORTED_FORMAT";
        if (vin.Length == 17)
        {
            var key = extended.Contains(vin[..3]) ? vin[..3] + vin[11..14] : vin[..3];
            rows = assignments.GetValueOrDefault(key, new()).Where(r => MayApply(r, context)).ToList();
            status = rows.Count == 0 ? "UNKNOWN" : rows.Count > 1 ? "AMBIGUOUS" : !Established(rows[0], context) ? "NEEDS_CONTEXT" : "RECOGNIZED";
        }
        var result = Map("supplied", supplied, "normalized", vin, "structure", structure, "status", status, "candidates", rows,
            "dataset", dataset, "context", Map("modelYear", context.ModelYear, "market", context.Market));
        foreach (var name in new[] { "manufacturer", "brand", "category" }) result[name] = Resolve(rows, r => r[name], context);
        result["manufacturerCountry"] = Resolve(rows, r => Get(r["manufacturer"], "country"), context);
        var details = rich.Decode(vin, structure, context); result["details"] = details;
        result["typeApprovals"] = approvals.Decode(vin, structure);
        Dictionary<string, object?> Field(string code)
        {
            var field = Obj(Get(details["fields"], code));
            return field.Count == 0 ? Map("status", "UNKNOWN", "possibilities", Array.Empty<string>(), "value", null)
                : Map("status", field["status"], "possibilities", field["possibilities"], "value", field["value"]);
        }
        result["model"] = Field("Model"); result["modelYear"] = Field("ModelYear"); result["assemblyCountry"] = Field("PlantCountry");
        if (Str(Field("Make")["status"]) == "KNOWN") result["brand"] = Field("Make");
        return result;
    }
}
