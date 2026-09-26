using System.Globalization;
using System.Text.RegularExpressions;
using static OpenResearch.ORvin.J;

namespace OpenResearch.ORvin;

internal sealed class RichDecoder
{
    private readonly Bundle bundle = Bundle.Default;
    private readonly Dictionary<int, (string Code, string Label, string Type)> elements = new();
    private readonly Dictionary<string, (int Type, string Truck)> wmis = new();
    private readonly Dictionary<string, List<(int Id, int Start, int End)>> schemas = new();
    private readonly Dictionary<string, (string Id, string Name)> models = new();
    private readonly Dictionary<string, List<string[]>> engines = new();
    private readonly List<string[]> conversions = new();
    private readonly Dictionary<string, Dictionary<string, object?>> sources = new();
    private readonly Dictionary<int, List<string[]>> buckets = new();
    private readonly Dictionary<int, List<PatternRow>> patterns = new();
    private readonly List<LiteralRule> literals = new();
    private readonly Dictionary<string, object?> dataset;
    private string sourceId = "";
    private int referenceYear;
    private string P(string key) => bundle.Text("patternProfile." + key);
    private int N(string key) => bundle.Number("patternProfile." + key);
    internal static Dictionary<string, object?> Source(string[] c)
    {
        string[] keys = ["id", "title", "publisher", "url", "edition", "section", "retrievedOn", "reuseBasis", "archivePath", "archiveSha256", "inspectedSha256", "evidencePath"];
        return keys.Select((key, i) => (key, value: J.Decode(c[i + 1]))).ToDictionary(p => p.key, p => (object?)(p.value == "" ? null : p.value));
    }
    internal RichDecoder()
    {
        var metadata = bundle.Metadata("decoding"); dataset = Map("version", metadata["version"], "sha256", metadata["indexSha256"]);
        foreach (var c in bundle.Rows("decoding/index.tsv"))
            switch (c[0])
            {
                case "V": referenceYear = int.Parse(c[2]); sourceId = c[3]; break;
                case "D": var source = Source(c); sources[Str(source["id"])] = source; break;
                case "E": elements[int.Parse(c[1])] = (c[2], J.Decode(c[3]), c[4]); break;
                case "W": wmis[c[1]] = (int.Parse(c[3]), c[4]); break;
                case "S": if (!schemas.TryGetValue(c[1], out var group)) schemas[c[1]] = group = new(); group.Add((int.Parse(c[2]), int.Parse(c[3]), int.Parse(c[4]))); break;
                case "M": models[c[1]] = (c[2], J.Decode(c[3])); break;
                case "G": var key = J.Decode(c[1]); if (!engines.TryGetValue(key, out var rows)) engines[key] = rows = new(); rows.Add(c); break;
                case "C": conversions.Add(c); break;
                case "H": break;
                default: throw new InvalidDataException("Unsupported pattern-index operation");
            }
        Dictionary<string, LiteralRule> rules = new();
        foreach (var row in bundle.Rows("rules.tsv"))
        {
            var c = row.Skip(1).Select(J.Decode).ToArray();
            if (row[0] == "R") rules[c[0]] = new(RegexFor(c[1]), c[2] == "" ? null : RegexFor(c[2]), c[3], c[4].Split(',', StringSplitOptions.RemoveEmptyEntries),
                c[5] == "" ? null : int.Parse(c[5]), c[6], c[7], c[8], new());
            else if (row[0] == "F") rules[c[0]].Claims.Add(c);
            else throw new InvalidDataException("Unsupported literal operation");
        }
        literals.AddRange(rules.Values);
    }
    private static Regex RegexFor(string value) => new(value, RegexOptions.CultureInvariant);
    private static bool Full(Regex pattern, string value) { var match = pattern.Match(value); return match.Success && match.Index == 0 && match.Length == value.Length; }
    private List<PatternRow> Patterns(int schema)
    {
        if (patterns.TryGetValue(schema, out var found)) return found;
        var bucket = schema % 256;
        if (!buckets.TryGetValue(bucket, out var rows))
        {
            if (buckets.Count >= 8) buckets.Remove(buckets.Keys.First());
            buckets[bucket] = rows = bundle.Rows($"decoding/patterns-{bucket:000}.tsv.gz").ToList();
        }
        if (patterns.Count >= 32) patterns.Remove(patterns.Keys.First());
        return patterns[schema] = rows.Where(c => int.Parse(c[0]) == schema).Select(c => new PatternRow(int.Parse(c[1]), int.Parse(c[2]), J.Decode(c[3]), J.Decode(c[4]), J.Decode(c[5]), c[6], RegexFor(J.Decode(c[7])), int.Parse(c[8]), int.Parse(c[9]))).ToList();
    }
    private Dictionary<string, object?> Fact(int element, string value, string attr, string kind, string rule, int? schema = null, string key = "") =>
        Map("elementId", element, "value", value, "attributeId", attr, "sourceId", sourceId, "sourceUrl", sources[sourceId]["url"], "kind", kind, "ruleId", rule, "schemaId", schema, "keys", key);
    private List<int> Years(string vin, Context context, string wmi)
    {
        int code = P("yearCodes").IndexOf(vin[N("yearPosition")]); if (code < 0) return new();
        int first = N("yearBase") + code;
        if (context.ModelYear is int supplied) return supplied >= N("yearBase") && (supplied - first) % N("yearCycle") == 0 ? [supplied] : new();
        var w = wmis[wmi];
        bool light = bundle.Strings("patternProfile.cycleDiscriminator.vehicleTypes").Contains(w.Type.ToString(CultureInfo.InvariantCulture)) || w.Type == N("cycleDiscriminator.conditionalType") && w.Truck == P("cycleDiscriminator.truckType");
        bool digit = char.IsAsciiDigit(vin[N("cycleDiscriminator.position")]);
        List<int> years = new();
        for (int year = first; year <= referenceYear + N("yearHorizon"); year += N("yearCycle"))
            if (!light || (year < N("cycleDiscriminator.beforeYear")) == digit) years.Add(year);
        return years;
    }
    private Dictionary<string, object?> Pass(string vin, string wmi, int year, Context context)
    {
        string key = string.Join(P("keySeparator"), Enumerable.Range(0, N("keySlices.length")).Select(i => vin[N($"keySlices.{i}.0")..N($"keySlices.{i}.1")]));
        Dictionary<int, List<MatchRow>> matches = new();
        void Add(int element, MatchRow match) { if (!matches.TryGetValue(element, out var group)) matches[element] = group = new(); group.Add(match); }
        foreach (var schema in schemas.GetValueOrDefault(wmi, new()))
        {
            if (year < schema.Start || year > schema.End) continue;
            foreach (var row in Patterns(schema.Id))
            {
                var match = row.Regex.Match(key); if (!match.Success || match.Index != 0) continue;
                bool formula = row.Capture >= 0;
                string value = formula ? key.Substring(row.Capture, row.Length) : row.Value;
                var fact = Fact(row.Element, value, formula ? value : row.Attribute, formula ? "NUMERIC_PATTERN" : "PATTERN", row.Id.ToString(CultureInfo.InvariantCulture), schema.Id, row.Keys);
                Add(row.Element, new(formula ? N("formulaPriority") : schema.Start, row.Changed, row.Keys, row.Id, fact));
            }
        }
        if (matches.TryGetValue(N("engineElement"), out var engine))
        {
            var parent = engine.OrderByDescending(m => m.Priority).ThenByDescending(m => m.Changed == "").ThenByDescending(m => m.Changed, StringComparer.Ordinal).ThenByDescending(m => m.Id).First().Fact;
            foreach (var c in engines.GetValueOrDefault(Str(parent["attributeId"]).Trim().ToLowerInvariant(), new()))
            {
                int element = int.Parse(c[3]);
                var fact = Fact(element, J.Decode(c[5]), J.Decode(c[4]), "ENGINE_MODEL", parent["ruleId"] + "/engine:" + c[2], (int?)parent["schemaId"], Str(parent["keys"]));
                Add(element, new(N("enginePriority"), c[6], Str(parent["keys"]), int.Parse(c[2]), fact));
            }
        }
        Dictionary<int, List<Dictionary<string, object?>>> facts = new();
        foreach (var (element, items) in matches)
        {
            var ordered = items.OrderByDescending(m => m.Priority).ThenByDescending(m => m.Changed == "").ThenByDescending(m => m.Changed, StringComparer.Ordinal)
                .ThenBy(m => m.Keys.Replace("*", "").Length).ThenBy(m => m.Keys.Replace("[", "").Replace("]", ""), StringComparer.Ordinal).ThenBy(m => m.Id);
            facts[element] = (bundle.Strings("patternProfile.multipleElements").Contains(element.ToString(CultureInfo.InvariantCulture)) ? ordered : ordered.Take(1)).Select(m => m.Fact).GroupBy(Canonical).Select(g => g.First()).ToList();
        }
        if (facts.TryGetValue(N("modelElement"), out var modelFacts) && models.TryGetValue(Str(modelFacts[0]["attributeId"]), out var model))
        {
            var parent = modelFacts[0]; facts[N("makeElement")] = [Fact(N("makeElement"), model.Name, model.Id, "MODEL_MAKE", parent["ruleId"] + "/make:" + model.Id, (int?)parent["schemaId"], Str(parent["keys"]))];
        }
        foreach (var c in conversions)
        {
            int from = int.Parse(c[2]), to = int.Parse(c[3]);
            if (!matches.ContainsKey(from) || facts.ContainsKey(to) || !facts.TryGetValue(from, out var parents) || parents.Count != 1) continue;
            var parent = parents[0];
            if (!decimal.TryParse(Str(parent["value"]), NumberStyles.Float, CultureInfo.InvariantCulture, out var number)) continue;
            try
            {
                var factor = decimal.Parse(c[5], CultureInfo.InvariantCulture);
                number = c[4] == "*" ? number * factor : number / factor;
                string value = decimal.Round(number, N("conversionScale"), MidpointRounding.AwayFromZero).ToString("0.############################", CultureInfo.InvariantCulture);
                facts[to] = [Fact(to, value, value, "UNIT_CONVERSION", parent["ruleId"] + "/conversion:" + c[1], (int?)parent["schemaId"], Str(parent["keys"]))];
            }
            catch (ArithmeticException) { /* Keep the original unconverted value. */ }
        }
        if (facts.Count > 0) facts[N("yearElement")] = [Fact(N("yearElement"), year.ToString(CultureInfo.InvariantCulture), year.ToString(CultureInfo.InvariantCulture), context.ModelYear is null ? "VIN_YEAR" : "CALLER_CONTEXT", "model-year", key: vin[N("yearPosition")].ToString())];
        return Map("modelYear", year, "market", P("market"), "fields", facts.OrderBy(p => p.Key).ToDictionary(p => elements[p.Key].Code, p => (object?)p.Value));
    }
    private Dictionary<string, object?> Result(string status, IEnumerable<string> warnings, Dictionary<string, object?> fields, List<object?> alternatives, string? scope = null, IEnumerable<string>? stages = null) =>
        Map("status", status, "dataset", dataset, "marketScope", scope ?? P("market"), "referenceYear", referenceYear,
            "stages", stages ?? bundle.Strings("patternProfile.stages"), "warnings", warnings, "fields", fields, "alternatives", alternatives, "sources", Array.Empty<object>());
    private Dictionary<string, object?> Field(string code, List<object?> evidence, List<string> values, string status)
    {
        var element = elements[(int)Get(evidence[0], "elementId")!];
        return Map("label", element.Label, "dataType", element.Type, "status", status, "possibilities", values, "value", status == "KNOWN" ? values[0] : null, "evidence", evidence);
    }
    private Dictionary<string, object?> PatternResult(string vin, string structure, Context context)
    {
        if (structure != "MODERN_FORMAT") return Result("INVALID_INPUT", [], new(), new());
        var wmi = vin[..3] + (vin[N("extendedWmi.position")].ToString() == P("extendedWmi.character") ? vin[N("extendedWmi.suffixStart")..N("extendedWmi.suffixEnd")] : "");
        if (!wmis.ContainsKey(wmi)) return Result("UNKNOWN", [], new(), new());
        var years = Years(vin, context, wmi);
        if (years.Count == 0) return Result(context.ModelYear is null ? "UNKNOWN" : "CONTEXT_CONFLICT", [P("yearConflictWarning")], new(), new());
        var alternatives = years.Select(y => (object?)Pass(vin, wmi, y, context)).ToList();
        var codes = Sorted(alternatives.SelectMany(a => Obj(Get(a, "fields")).Keys));
        Dictionary<string, object?> fields = new();
        foreach (var code in codes)
        {
            var groups = alternatives.Select(a => List(Get(Get(a, "fields"), code))).ToList();
            var evidence = groups.SelectMany(g => g).GroupBy(Canonical).Select(g => g.First()).ToList();
            var values = evidence.Select(e => Str(Get(e, "value"))).Distinct().ToList();
            var status = values.Count > 1 ? "AMBIGUOUS" : groups.Any(g => g.Count == 0) ? "UNKNOWN" : context.Market != P("market") ? "NEEDS_CONTEXT" : "KNOWN";
            fields[code] = Field(code, evidence, values, status);
        }
        List<string> warnings = new();
        if (context.Market != P("market") && codes.Count > 0) warnings.Add(context.Market is null ? P("unknownMarketWarning") : P("fallbackMessage").Replace("{sourceMarket}", P("market")).Replace("{requestedMarket}", context.Market));
        if (years.Count > 1) warnings.Add(P("yearAlternativesWarning"));
        return Result(codes.Count == 0 ? "UNKNOWN" : context.Market != P("market") ? "NEEDS_CONTEXT" : "DECODED", warnings, fields, alternatives);
    }
    private List<Dictionary<string, object?>> LiteralResults(string vin, Context context)
    {
        List<Dictionary<string, object?>> results = new();
        foreach (var rule in literals)
        {
            if (!Full(rule.Pattern, vin) || rule.Exclude is not null && Full(rule.Exclude, vin)) continue;
            bool foreign = rule.Markets.Length > 0 && !rule.Markets.Contains(context.Market);
            bool conflict = rule.Year is not null && context.ModelYear is not null && rule.Year != context.ModelYear;
            if (conflict && foreign) continue;
            Dictionary<string, object?> facts = new();
            foreach (var c in rule.Claims)
            {
                int position = int.Parse(c[1]); if (position >= 0 && !c[2].Contains(vin[position])) continue;
                int eid = elements.First(e => e.Value.Code == c[3]).Key;
                var fact = Map("elementId", eid, "value", c[4], "attributeId", c[4], "sourceId", c[5], "sourceUrl", sources[c[5]]["url"], "kind", c[6], "ruleId", c[7], "schemaId", null, "keys", c[8]);
                var group = List(facts.GetValueOrDefault(c[3])); if (!group.Any(f => Canonical(f) == Canonical(fact))) group.Add(fact); facts[c[3]] = group;
            }
            Dictionary<string, object?> fields = new();
            foreach (var (code, value) in facts.OrderBy(p => p.Key, StringComparer.Ordinal))
            {
                var evidence = List(value); var values = Sorted(evidence.Select(e => Str(Get(e, "value"))));
                fields[code] = Field(code, evidence, values, values.Count > 1 ? "AMBIGUOUS" : foreign ? "NEEDS_CONTEXT" : "KNOWN");
            }
            results.Add(Result(conflict ? "CONTEXT_CONFLICT" : foreign ? "NEEDS_CONTEXT" : "DECODED", [conflict ? rule.ConflictWarning : rule.Warning], conflict ? new() : fields,
                [Map("modelYear", rule.Year, "market", rule.Scope, "fields", facts)], rule.Scope, [rule.Stage]));
        }
        return results;
    }
    internal Dictionary<string, object?> Decode(string vin, string structure, Context context)
    {
        var pattern = PatternResult(vin, structure, context); var result = pattern;
        if (structure == "MODERN_FORMAT")
        {
            var results = LiteralResults(vin, context); results.Add(pattern);
            var meaningful = results.Where(r => Obj(r["fields"]).Count > 0 || List(r["alternatives"]).Count > 0).ToList();
            var conflicts = results.Where(r => Str(r["status"]) == "CONTEXT_CONFLICT" && (Str(r["marketScope"]) != P("market") || context.Market == P("market"))).ToList();
            var alternatives = meaningful.SelectMany(r => List(r["alternatives"])).ToList();
            if (conflicts.Count > 0) { result = new(conflicts[0]); result["fields"] = new Dictionary<string, object?>(); result["alternatives"] = alternatives; }
            else if (meaningful.Count == 1) result = meaningful[0];
            else if (meaningful.Count > 1)
            {
                Dictionary<string, object?> fields = new();
                foreach (var code in Sorted(meaningful.SelectMany(r => Obj(r["fields"]).Keys)))
                {
                    var all = meaningful.Where(r => Obj(r["fields"]).ContainsKey(code)).Select(r => Obj(Get(r["fields"], code))).ToList();
                    var applicable = meaningful.Where(r => Str(r["status"]) != "NEEDS_CONTEXT" && Obj(r["fields"]).ContainsKey(code) && Str(Get(Get(r["fields"], code), "status")) != "NEEDS_CONTEXT").Select(r => Obj(Get(r["fields"], code))).ToList();
                    var selected = applicable.Count > 0 ? applicable : all;
                    var values = Sorted(selected.SelectMany(f => List(f["possibilities"]).Select(Str)));
                    var evidence = selected.SelectMany(f => List(f["evidence"])).GroupBy(Canonical).Select(g => g.First()).ToList();
                    fields[code] = Field(code, evidence, values, values.Count > 1 ? "AMBIGUOUS" : selected.Any(f => Str(f["status"]) == "UNKNOWN") ? "UNKNOWN" : applicable.Count > 0 ? "KNOWN" : "NEEDS_CONTEXT");
                }
                var scopes = Sorted(meaningful.Select(r => Str(r["marketScope"])));
                result = Result(fields.Values.Any(f => Str(Get(f, "status")) == "KNOWN") ? "DECODED" : "NEEDS_CONTEXT",
                    meaningful.SelectMany(r => List(r["warnings"]).Select(Str)).Where(s => s != "").Distinct(), fields, alternatives,
                    scopes.Count == 1 ? scopes[0] : "MULTIPLE", meaningful.SelectMany(r => List(r["stages"]).Select(Str)).Distinct());
            }
        }
        var used = Obj(result["fields"]).Values.SelectMany(f => List(Get(f, "evidence")))
            .Concat(List(result["alternatives"]).SelectMany(a => Obj(Get(a, "fields")).Values.SelectMany(List)));
        result["sources"] = Sorted(used.Select(f => Str(Get(f, "sourceId")))).Select(id => sources[id]).ToList();
        return result;
    }
    private sealed record PatternRow(int Id, int Element, string Keys, string Attribute, string Value, string Changed, Regex Regex, int Capture, int Length);
    private sealed record MatchRow(int Priority, string Changed, string Keys, int Id, Dictionary<string, object?> Fact);
    private sealed record LiteralRule(Regex Pattern, Regex? Exclude, string Scope, string[] Markets, int? Year, string Stage, string Warning, string ConflictWarning, List<string[]> Claims);
}
