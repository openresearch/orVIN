using static OpenResearch.ORvin.J;

namespace OpenResearch.ORvin;

internal sealed class AnswerBuilder
{
    private readonly Dictionary<string, object?> raw;
    private readonly bool vin;
    private readonly Bundle policy = Bundle.Default;
    private readonly IdentityCatalogue catalogue = IdentityCatalogue.Default;
    private readonly Dictionary<string, string> primary = Bundle.Default.Primary;
    private readonly Dictionary<string, Dictionary<string, object?>> sources;
    private readonly Dictionary<string, Dictionary<string, object?>> evidence = new(), normalizations = new(), decisions = new();
    private readonly Dictionary<string, object?> vehicle = new();
    private readonly Dictionary<string, string> status = new();
    private readonly List<Dictionary<string, object?>> alternatives = new(), assumptions = new();
    private readonly List<string> wmiIds = new(), approvalIds = new();
    private readonly Dictionary<string, List<string>> richIds = new();
    private static Dictionary<string, object?> O(object? parent, string key) => Obj(Get(parent, key));
    private static bool Identity(string name) => name is "make" or "model";
    internal AnswerBuilder(Dictionary<string, object?> input, bool isVin)
    {
        raw = Obj(Parse(Canonical(input))); vin = isVin; sources = new(catalogue.Sources);
        foreach (var name in primary.Keys)
        {
            if (Identity(name)) vehicle[name + "Id"] = null;
            vehicle[name] = null; status[name] = "UNKNOWN";
            decisions[name] = Map("reason", "NO_EVIDENCE", "evidenceIds", Array.Empty<string>(), "normalizationRuleIds", Array.Empty<string>(), "alternativeIds", Array.Empty<string>());
        }
        Collect();
    }
    private void AddSource(Dictionary<string, object?> source)
    {
        string sid = Str(source["id"]); var merged = new Dictionary<string, object?>(source);
        if (sources.TryGetValue(sid, out var known)) foreach (var (key, value) in known) if (value is not null) merged[key] = value;
        sources[sid] = merged;
    }
    private string Fact(object? item)
    {
        var fact = Obj(item); string eid = "fact:" + Id(fact); var record = new Dictionary<string, object?>(fact);
        if (Equals(record.GetValueOrDefault("sourceUrl"), sources[Str(fact["sourceId"])].GetValueOrDefault("url"))) record.Remove("sourceUrl");
        evidence[eid] = Map("kind", "VIN_FACT", "sourceIds", new[] { fact["sourceId"] }, "record", record); return eid;
    }
    private List<string> Facts(object? value) => Sorted(List(value).Select(Fact));
    private void Collect()
    {
        if (!vin)
        {
            var dataset = O(raw, "dataset"); var source = O(dataset, "source"); string sid = "kba-fz-types-" + dataset["referenceDate"];
            AddSource(new(source) { ["id"] = sid, ["edition"] = dataset["referenceDate"] });
            foreach (var item in List(raw["candidates"]))
            {
                var row = Obj(item); string eid = "kba:" + row["sourceObjectId"];
                evidence[eid] = Map("kind", "KBA_TYPE", "sourceIds", new[] { sid }, "record", row); approvalIds.Add(eid);
            }
            if (Str(raw["inputStatus"]) == "VALID" && approvalIds.Count == 0)
            {
                evidence["kba:lookup"] = Map("kind", "LOOKUP_CHECK", "sourceIds", new[] { sid }, "record", Map("hsn", raw["normalizedHsn"], "tsn", raw["normalizedTsn"], "referenceDate", dataset["referenceDate"], "result", "NO_MATCH"));
                foreach (var name in new[] { "make", "model" }) { decisions[name]["reason"] = "NO_TYPE_CODE_MATCH"; decisions[name]["evidenceIds"] = new[] { "kba:lookup" }; }
            }
            return;
        }
        foreach (var item in List(raw["candidates"]))
        {
            var row = Obj(Parse(Canonical(item))); var manufacturer = O(row, "manufacturer");
            var documents = List(row["sources"]).Concat(List(manufacturer["sources"])).Select(Obj).ToList();
            row.Remove("sources"); manufacturer.Remove("sources");
            foreach (var source in documents) AddSource(source);
            string eid = "wmi:" + row["id"]; evidence[eid] = Map("kind", "WMI_ASSIGNMENT", "sourceIds", Sorted(documents.Select(s => Str(s["id"]))), "record", row); wmiIds.Add(eid);
        }
        foreach (var section in new[] { "details", "typeApprovals" }) foreach (var source in List(Get(raw[section], "sources"))) AddSource(Obj(source));
        var details = O(raw, "details");
        foreach (var (code, field) in O(details, "fields")) richIds[code] = Facts(Get(field, "evidence"));
        foreach (var item in List(details["alternatives"]))
        {
            var alternative = Obj(item);
            alternatives.Add(Map("id", "configuration:" + Id(alternative), "kind", "VIN_CONFIGURATION", "modelYear", alternative["modelYear"], "market", alternative["market"],
                "fields", O(alternative, "fields").ToDictionary(p => p.Key, p => (object?)Facts(p.Value))));
        }
        foreach (var item in List(Get(raw["typeApprovals"], "candidates")))
        {
            var row = Obj(item); string eid = "approval:" + row["sourceId"] + ":" + row["sourceRow"];
            evidence[eid] = Map("kind", "TYPE_APPROVAL", "sourceIds", new[] { row["sourceId"] }, "record", row); approvalIds.Add(eid);
        }
    }
    private void Select(string name, IEnumerable<object?> input, string knowledge, IEnumerable<string> ids, string reason, object? makeId = null)
    {
        var values = input.ToList(); bool missing = values.Count == 0;
        List<Dictionary<string, object?>> mappings = new(); List<(string? Id, object? Value)> mapped = new();
        foreach (var value in values)
        {
            var mapping = name == "make" ? catalogue.Make(value) : name == "model" ? catalogue.Model(makeId, value) : null;
            if (Identity(name))
            {
                missing |= mapping is null;
                if (mapping is not null) { mappings.Add(mapping); mapped.Add((Str(mapping["id"]), mapping["name"])); }
            }
            else if (int.TryParse(Str(value), out var year)) mapped.Add((null, year)); else missing = true;
        }
        var unique = mapped.Distinct().ToList();
        var resolved = unique.Count > 1 ? "AMBIGUOUS" : missing || knowledge == "UNKNOWN" ? "UNKNOWN" : policy.Text("statuses." + knowledge);
        status[name] = resolved; bool selected = resolved is "RESOLVED" or "SUGGESTED";
        vehicle[name] = selected ? unique[0].Value : null; if (Identity(name)) vehicle[name + "Id"] = selected ? unique[0].Id : null;
        foreach (var mapping in mappings) normalizations[Str(mapping["ruleId"])] = mapping;
        var evidenceIds = Sorted(ids);
        decisions[name] = Map("reason", missing && values.Count > 0 && Identity(name) ? "UNMAPPED_IDENTITY" : resolved == "AMBIGUOUS" ? "COMPETING_IDENTITIES" : reason,
            "evidenceIds", evidenceIds, "normalizationRuleIds", Sorted(mappings.Select(m => Str(m["ruleId"]))),
            "alternativeIds", Sorted(alternatives.Where(a => O(a, "fields").Values.Any(v => List(v).Select(Str).Intersect(evidenceIds).Any())).Select(a => Str(a["id"]))));
    }
    private void Assume(string code, IEnumerable<string> fields)
    {
        var names = fields.ToList(); if (names.Count > 0) assumptions.Add(Map("code", code, "fields", names));
    }
    internal VehicleAnswer Resolve()
    {
        if (vin)
        {
            if (Str(raw["structure"]) != "MODERN_FORMAT") return Finish();
            var rich = O(raw, "details"); var fields = O(rich, "fields"); var context = O(raw, "context");
            foreach (var (name, code) in primary)
                if (fields.TryGetValue(code, out var item)) { var field = Obj(item); Select(name, List(field["possibilities"]), Str(field["status"]), richIds[code], "SCOPED_VIN_RULE", vehicle["makeId"]); }
            var candidates = List(raw["candidates"]).Select(Obj).ToList();
            if (status["make"] != "RESOLVED" && wmiIds.Count > 0 && (!fields.ContainsKey("Make") || status["make"] == "UNKNOWN" && Str(Get(raw["brand"], "status")) == "KNOWN"))
                Select("make", candidates.Select(r => r["brand"]), Str(Get(raw["brand"], "status")), wmiIds, "WMI_ASSIGNMENT");
            if (status["make"] == "SUGGESTED" && Str(Get(raw["brand"], "status")) == "KNOWN" && candidates.Count > 0 &&
                candidates.All(r => catalogue.Make(r["brand"]) is { } mapping && Equals(mapping["id"], vehicle["makeId"])))
                Select("make", candidates.Select(r => r["brand"]), "KNOWN", wmiIds, "WMI_ASSIGNMENT");
            var conditional = primary.Keys.Where(name => status[name] == "SUGGESTED" && fields.ContainsKey(primary[name])).ToList();
            if (status["make"] == "SUGGESTED" && conditional.Count == 0) Assume("MATCH_CONSTRAINTS_UNCONFIRMED", ["make"]);
            bool conflict = Str(rich["status"]) == "CONTEXT_CONFLICT" && (Str(rich["marketScope"]) != policy.Text("patternProfile.market") || Str(context["market"]) == policy.Text("patternProfile.market"));
            if (context["modelYear"] is not null) evidence["context:modelYear"] = Map("kind", "CALLER_CONTEXT", "sourceIds", Array.Empty<string>(), "record", context);
            if (conflict)
            {
                foreach (var name in new[] { "model", "modelYear" })
                {
                    vehicle[name] = null; status[name] = "CONFLICT"; decisions[name]["reason"] = "CALLER_CONTEXT_CONFLICT";
                    decisions[name]["evidenceIds"] = Sorted(new[] { "context:modelYear" }.Concat(alternatives.SelectMany(a => List(Get(a["fields"], primary[name])).Select(Str))));
                    decisions[name]["alternativeIds"] = Sorted(alternatives.Select(a => Str(a["id"])));
                }
                vehicle["modelId"] = null;
            }
            if (approvalIds.Count > 0)
            {
                var rows = approvalIds.Select(eid => O(evidence[eid]["record"], "fields")).ToList();
                foreach (var name in new[] { "make", "model" })
                {
                    if (status[name] is not ("UNKNOWN" or "SUGGESTED") || name == "model" && conflict) continue;
                    if (name == "model" && (vehicle["makeId"] is null || rows.Any(r => catalogue.Make(r.GetValueOrDefault("make")) is not { } make || !Equals(make["id"], vehicle["makeId"])))) continue;
                    string key = name == "make" ? "make" : "type";
                    if (status[name] == "SUGGESTED")
                    {
                        var mapped = rows.Select(r => name == "make" ? catalogue.Make(r.GetValueOrDefault(key)) : catalogue.Model(vehicle["makeId"], r.GetValueOrDefault(key))).ToList();
                        if (mapped.Count > 0 && mapped.All(m => m is not null) && !mapped.Select(m => m!["id"]).ToHashSet().SetEquals(new[] { vehicle[name + "Id"] }))
                        {
                            vehicle[name] = vehicle[name + "Id"] = null; status[name] = "AMBIGUOUS"; decisions[name]["reason"] = "COMPETING_CONDITIONAL_SOURCES";
                            decisions[name]["evidenceIds"] = Sorted(List(decisions[name]["evidenceIds"]).Select(Str).Concat(approvalIds));
                            foreach (var mapping in mapped) normalizations[Str(mapping!["ruleId"])] = mapping;
                            decisions[name]["normalizationRuleIds"] = Sorted(List(decisions[name]["normalizationRuleIds"]).Select(Str).Concat(mapped.Select(m => Str(m!["ruleId"]))));
                        }
                        continue;
                    }
                    Select(name, rows.Select(r => r.GetValueOrDefault(key)), "NEEDS_CONTEXT", approvalIds, "CATALOGUE_CONSENSUS", vehicle["makeId"]);
                    if (status[name] == "SUGGESTED") Assume(policy.Text("catalogue.assumptionCode"), [name]);
                }
            }
            if (vehicle["makeId"] is null && vehicle["modelId"] is not null)
            {
                vehicle["model"] = vehicle["modelId"] = null; status["model"] = "AMBIGUOUS"; decisions["model"]["reason"] = "PRIMARY_MAKE_UNRESOLVED";
                decisions["model"]["evidenceIds"] = Sorted(List(decisions["model"]["evidenceIds"]).Concat(List(decisions["make"]["evidenceIds"])).Select(Str));
            }
            if (status["model"] is "AMBIGUOUS" or "CONFLICT" && status["modelYear"] == "SUGGESTED")
            { vehicle["modelYear"] = null; status["modelYear"] = "UNKNOWN"; decisions["modelYear"]["reason"] = "IDENTITY_APPLICABILITY_UNRESOLVED"; }
            var year = context["modelYear"];
            if (year is not null && !conflict)
            {
                if (vehicle["modelYear"] is not null && !Equals(vehicle["modelYear"], year)) { vehicle["modelYear"] = null; status["modelYear"] = "CONFLICT"; decisions["modelYear"]["reason"] = "CALLER_CONTEXT_CONFLICT"; }
                else { vehicle["modelYear"] = year; status["modelYear"] = "PROVIDED"; decisions["modelYear"]["reason"] = "CALLER_CONTEXT"; }
                decisions["modelYear"]["evidenceIds"] = Sorted(List(decisions["modelYear"]["evidenceIds"]).Select(Str).Append("context:modelYear"));
            }
            foreach (var assumption in assumptions) assumption["fields"] = List(assumption["fields"]).Where(name => status[Str(name)] == "SUGGESTED").ToList();
            assumptions.RemoveAll(a => List(a["fields"]).Count == 0);
            conditional = primary.Keys.Where(name => status[name] == "SUGGESTED" && Str(decisions[name]["reason"]) == "SCOPED_VIN_RULE").ToList();
            if (conditional.Count > 0)
            {
                var ids = conditional.SelectMany(name => List(decisions[name]["evidenceIds"]).Select(Str)).ToHashSet();
                var markets = Sorted(alternatives.Where(a => O(a, "fields").Values.Any(v => List(v).Select(Str).Any(ids.Contains))).Select(a => Str(a["market"])));
                var requested = context["market"];
                if (requested is null && markets.SequenceEqual(new[] { policy.Text("patternProfile.market") })) Assume(policy.Text("patternProfile.assumptionCode"), conditional);
                else assumptions.Add(Map("code", policy.Text("patternProfile.fallbackCode"), "fields", conditional, "requestedMarket", requested, "sourceMarkets", markets,
                    "message", policy.Text("patternProfile.fallbackMessage").Replace("{sourceMarket}", string.Join(", ", markets)).Replace("{requestedMarket}", requested is null ? "an unspecified market" : Str(requested))));
            }
        }
        else if (Str(raw["inputStatus"]) == "VALID" && approvalIds.Count > 0)
        {
            var rows = List(raw["candidates"]).Select(Obj).ToList(); Select("make", rows.Select(r => r["manufacturer"]), "KNOWN", approvalIds, "TYPE_CODE_LOOKUP");
            if (vehicle["makeId"] is not null) Select("model", rows.Select(r => r["tradeName"]), "KNOWN", approvalIds, "TYPE_CODE_LOOKUP", vehicle["makeId"]);
        }
        return Finish();
    }
    private Dictionary<string, object?> Credit(string sid, IEnumerable<string> fields)
    {
        var s = sources[sid]; object? First(params string[] keys) => keys.Select(k => s.GetValueOrDefault(k)).FirstOrDefault(v => v is not null && Str(v) != "");
        return Map("id", sid, "publisher", s.GetValueOrDefault("publisher"), "title", s.GetValueOrDefault("title"), "url", s.GetValueOrDefault("url"),
            "edition", First("edition", "publicationVersion"), "license", s.GetValueOrDefault("license"), "termsUrl", First("termsUrl", "licenseUrl", "reuseUrl"), "reuseBasis", s.GetValueOrDefault("reuseBasis"),
            "attribution", Str(s.GetValueOrDefault("publisher")) + " — " + Str(s.GetValueOrDefault("title")), "modifications", First("modifications") ?? "Source labels normalized by ORvin; original facts retained in evidence.", "fields", Sorted(fields));
    }
    private VehicleAnswer Finish()
    {
        Dictionary<string, HashSet<string>> common = new();
        var allSources = normalizations.Values.Select(m => Str(m["sourceId"])).Concat(evidence.Values.SelectMany(e => List(e["sourceIds"]).Select(Str))).ToHashSet();
        foreach (var (name, decision) in decisions)
        {
            var used = List(decision["evidenceIds"]).SelectMany(eid => List(evidence[Str(eid)]["sourceIds"]).Select(Str))
                .Concat(List(decision["normalizationRuleIds"]).Select(rid => Str(normalizations[Str(rid)]["sourceId"]))).ToHashSet();
            string[] paths = vehicle[name] is null ? ["/fieldStatus/" + name] : Identity(name) ? ["/vehicle/" + name, "/vehicle/" + name + "Id"] : ["/vehicle/" + name];
            foreach (var sid in used) { if (!common.TryGetValue(sid, out var group)) common[sid] = group = new(); group.UnionWith(paths); }
            allSources.UnionWith(used);
        }
        var summary = Map("schemaVersion", 1);
        if (vin) { summary["vin"] = raw["normalized"]; summary["inputStatus"] = Str(raw["structure"]) == "MODERN_FORMAT" ? "SUPPORTED_FORMAT" : raw["structure"]; }
        else { summary["hsn"] = raw["normalizedHsn"]; summary["tsn"] = raw["normalizedTsn"]; summary["inputStatus"] = Str(raw["inputStatus"]) == "VALID" ? "SUPPORTED_FORMAT" : raw["inputStatus"]; }
        summary["vehicle"] = vehicle; summary["fieldStatus"] = status.ToDictionary(p => p.Key, p => (object?)p.Value); summary["assumptions"] = assumptions;
        summary["sources"] = common.OrderBy(p => p.Key, StringComparer.Ordinal).Select(p => Credit(p.Key, p.Value)).ToList();
        string[] creditKeys = ["id", "publisher", "title", "url", "edition", "license", "termsUrl", "reuseBasis", "modifications"];
        var sourceDetails = allSources.ToDictionary(sid => sid, sid => (object?)sources[sid].Where(p => !creditKeys.Contains(p.Key)).ToDictionary(p => p.Key, p => p.Value));
        var datasets = Map("lookup", raw["dataset"], "identity", catalogue.Metadata);
        Dictionary<string, object?> variables = new(), specifications = new(), input;
        List<Dictionary<string, object?>> diagnostics = new();
        if (vin)
        {
            datasets["decoding"] = Get(raw["details"], "dataset"); datasets["typeApprovals"] = Get(raw["typeApprovals"], "dataset");
            foreach (var name in new[] { "details", "typeApprovals" })
            {
                var section = O(raw, name); var diagnostic = Map("source", name, "status", section["status"], "marketScope", section["marketScope"], "warnings", section["warnings"]);
                if (name == "details") { diagnostic["referenceYear"] = section["referenceYear"]; diagnostic["stages"] = section["stages"]; } diagnostics.Add(diagnostic);
            }
            diagnostics.Add(Map("source", "typeApprovals", "candidateCount", approvalIds.Count));
            variables["decoding"] = O(raw["details"], "fields").ToDictionary(p => p.Key, p => (object?)Map("label", Get(p.Value, "label"), "dataType", Get(p.Value, "dataType"), "status", Get(p.Value, "status")));
            variables["typeApprovals"] = O(raw["typeApprovals"], "fields").ToDictionary(p => p.Key, p => (object?)Map("label", Get(p.Value, "label"), "sourceColumn", Get(p.Value, "sourceColumn"), "unit", Get(p.Value, "unit")));
            foreach (var (code, item) in O(raw["details"], "fields"))
                if (!primary.ContainsValue(code) && Str(Get(item, "status")) == "KNOWN") specifications[code] = Map("value", Get(item, "value"), "status", "RESOLVED", "dataType", Get(item, "dataType"), "evidenceIds", richIds[code]);
            input = Map("supplied", raw["supplied"], "context", raw["context"], "structure", raw["structure"]);
        }
        else
        {
            datasets["lookup"] = O(raw, "dataset").Where(p => p.Key != "source").ToDictionary(p => p.Key, p => p.Value);
            input = Map("suppliedHsn", raw["suppliedHsn"], "suppliedTsn", raw["suppliedTsn"], "inputStatus", raw["inputStatus"]);
            diagnostics.Add(Map("source", "kba", "status", raw["status"], "candidateCount", approvalIds.Count));
        }
        Dictionary<string, object?> rules = new();
        foreach (var item in evidence.Values.Where(e => Str(e["kind"]) == "VIN_FACT"))
        {
            var record = O(item, "record"); var rule = new[] { "sourceId", "ruleId", "schemaId", "keys", "kind" }.ToDictionary(k => k, k => record[k]); rules["rule:" + Id(rule)] = rule;
        }
        var details = Map("meta", Map("library", "ORvin", "policyVersion", policy.Text("version"), "datasets", datasets), "input", input,
            "decisions", decisions.ToDictionary(p => p.Key, p => (object?)p.Value), "specifications", specifications, "alternatives", alternatives,
            "evidence", evidence.ToDictionary(p => p.Key, p => (object?)p.Value), "provenance", Map("rules", rules, "variables", variables,
            "normalizationRules", normalizations.ToDictionary(p => p.Key, p => (object?)p.Value), "sourceDetails", sourceDetails,
            "additionalSources", Sorted(allSources.Except(common.Keys)).Select(sid => Credit(sid, ["/details/evidence"])).ToList()), "diagnostics", diagnostics);
        return new VehicleAnswer(summary, details);
    }
}
