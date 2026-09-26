using System.Collections;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace OpenResearch.ORvin;

internal static class J
{
    internal static Dictionary<string, object?> Obj(object? value) => value as Dictionary<string, object?> ?? new();
    internal static Dictionary<string, object?> Map(params object?[] pairs)
    {
        var result = new Dictionary<string, object?>();
        for (var i = 0; i < pairs.Length; i += 2) result[(string)pairs[i]!] = pairs[i + 1];
        return result;
    }
    internal static object? Get(object? value, string key) => Obj(value).GetValueOrDefault(key);
    internal static List<object?> List(object? value) => value is IEnumerable items and not string and not IDictionary
        ? items.Cast<object?>().ToList() : new();
    internal static string Str(object? value) => Convert.ToString(value, System.Globalization.CultureInfo.InvariantCulture) ?? "";
    internal static object? Parse(string value) => From(JsonSerializer.Deserialize<JsonElement>(value));
    private static object? From(JsonElement value) => value.ValueKind switch
    {
        JsonValueKind.Object => value.EnumerateObject().ToDictionary(p => p.Name, p => From(p.Value)),
        JsonValueKind.Array => value.EnumerateArray().Select(From).ToList(),
        JsonValueKind.String => value.GetString(),
        JsonValueKind.Number => value.GetInt32(),
        JsonValueKind.True => true, JsonValueKind.False => false, _ => null
    };
    internal static string Canonical(object? value)
    {
        if (value is null) return "null";
        if (value is bool b) return b ? "true" : "false";
        if (value is string s)
        {
            var text = new StringBuilder("\"");
            foreach (char c in s) text.Append(c switch
            {
                '"' => "\\\"", '\\' => "\\\\", '\b' => "\\b", '\f' => "\\f", '\n' => "\\n", '\r' => "\\r", '\t' => "\\t",
                < ' ' or > '~' => "\\u" + ((int)c).ToString("x4"), _ => c.ToString()
            });
            return text.Append('"').ToString();
        }
        if (value is IDictionary<string, object?> map)
            return "{" + string.Join(",", map.OrderBy(p => p.Key, StringComparer.Ordinal).Select(p => Canonical(p.Key) + ":" + Canonical(p.Value))) + "}";
        if (value is IEnumerable items) return "[" + string.Join(",", items.Cast<object?>().Select(Canonical)) + "]";
        return Str(value);
    }
    internal static string Id(object? value) => Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(Canonical(value)))).ToLowerInvariant()[..24];
    internal static List<string> Sorted(IEnumerable<string> values) => values.Distinct().Order(StringComparer.Ordinal).ToList();
    internal static string Decode(string text) => Encoding.UTF8.GetString(Convert.FromBase64String(text));
}
