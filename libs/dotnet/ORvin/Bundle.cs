using System.IO.Compression;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;

namespace OpenResearch.ORvin;

internal sealed class Bundle
{
    internal static readonly Bundle Default = new();
    private readonly Assembly assembly = typeof(Bundle).Assembly;
    private readonly Dictionary<string, string> names;
    private readonly Dictionary<string, string> hashes = new();
    private readonly Dictionary<string, string> policy = new();
    private Bundle()
    {
        names = assembly.GetManifestResourceNames().Where(n => n.StartsWith("ORvin.Data.", StringComparison.Ordinal))
            .ToDictionary(n => n[11..].Replace('\\', '/'), n => n);
        var lines = Encoding.UTF8.GetString(Raw("manifest.tsv")).Split('\n', StringSplitOptions.RemoveEmptyEntries);
        var version = lines[0].Split('\t');
        string[] supported = ["patterns", "conditional-literals", "year-cycles", "relations", "decimal-scaling", "catalogue-consensus", "cross-market"];
        if (version[1] != "orvin-runtime-1" || version[2].Split(',').Except(supported).Any())
            throw new InvalidDataException("Unsupported ORvin runtime format/capabilities");
        foreach (var line in lines) { var c = line.Split('\t'); if (c[0] == "F") hashes.Add(c[1], c[2]); }
        foreach (var c in Rows("policy.tsv")) policy.Add(c[0], c[1] == "S" ? J.Decode(c[2]) : c[2]);
    }
    private byte[] Raw(string name)
    {
        using var stream = assembly.GetManifestResourceStream(names[name]) ?? throw new InvalidDataException("Missing runtime data: " + name);
        using var output = new MemoryStream(); stream.CopyTo(output); return output.ToArray();
    }
    internal byte[] Read(string name)
    {
        var bytes = Raw(name);
        if (Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant() != hashes.GetValueOrDefault(name))
            throw new InvalidDataException("Runtime bundle integrity failure: " + name);
        return bytes;
    }
    internal IEnumerable<string[]> Rows(string name)
    {
        byte[] bytes = Read(name);
        if (name.EndsWith(".gz", StringComparison.Ordinal))
        {
            using var input = new MemoryStream(bytes); using var gzip = new GZipStream(input, CompressionMode.Decompress);
            using var output = new MemoryStream(); gzip.CopyTo(output); bytes = output.ToArray();
        }
        return Encoding.UTF8.GetString(bytes).Split('\n', StringSplitOptions.RemoveEmptyEntries).Select(l => l.Split('\t'));
    }
    internal Dictionary<string, object?> Metadata(string area) => J.Obj(J.Parse(Encoding.UTF8.GetString(Read(area + "/metadata.json"))));
    internal string Text(string key) => policy[key];
    internal int Number(string key) => int.Parse(Text(key), System.Globalization.CultureInfo.InvariantCulture);
    internal List<string> Strings(string key) => Enumerable.Range(0, Number(key + ".length")).Select(i => Text(key + "." + i)).ToList();
    internal Dictionary<string, string> Primary => Enumerable.Range(0, Number("primaryFields.length"))
        .ToDictionary(i => Text($"primaryFields.{i}.name"), i => Text($"primaryFields.{i}.code"));
}
