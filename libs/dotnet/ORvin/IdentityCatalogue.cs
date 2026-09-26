using static OpenResearch.ORvin.J;

namespace OpenResearch.ORvin;

internal sealed class IdentityCatalogue
{
    internal static readonly IdentityCatalogue Default = new();
    internal readonly Dictionary<string, Dictionary<string, object?>> Sources = new();
    internal readonly Dictionary<string, object?> Metadata;
    private readonly Dictionary<string, Dictionary<string, object?>> makes = new();
    private readonly Dictionary<(string Make, string Alias), Dictionary<string, object?>> models = new();
    private IdentityCatalogue()
    {
        var meta = Bundle.Default.Metadata("identity"); Metadata = Map("version", meta["version"], "sha256", meta["sha256"]);
        string[] sourceKeys = ["id", "publisher", "title", "url", "edition", "section", "retrievedOn", "reuseBasis", "license", "termsUrl", "modifications", "archiveSha256", "inspectedSha256", "evidencePath"];
        foreach (var c in Bundle.Default.Rows("identity/index.tsv"))
        {
            if (c[0] == "S")
            {
                var source = sourceKeys.Select((key, i) => (key, value: Decode(c[i + 1]))).ToDictionary(p => p.key, p => (object?)(p.value == "" ? null : p.value));
                Sources[Str(source["id"])] = source;
            }
            else if (c[0] is "M" or "D")
            {
                int offset = c[0] == "M" ? 1 : 2; string alias = Decode(c[offset]);
                var row = Map("id", c[offset + 1], "name", Decode(c[offset + 2]), "sourceId", c[offset + 3], "locator", Decode(c[offset + 4]), "original", alias,
                    "ruleId", "identity:" + Id(new[] { c[0], c[0] == "D" ? c[1] : "", alias }));
                if (c[0] == "M") makes[alias] = row; else models[(c[1], alias)] = row;
            }
        }
    }
    private static string Key(object? value) => VinDecoder.Normalize(Str(value).Trim());
    internal Dictionary<string, object?>? Make(object? value) => makes.GetValueOrDefault(Key(value));
    internal Dictionary<string, object?>? Model(object? make, object? value) => models.GetValueOrDefault((Str(make), Key(value)));
}
