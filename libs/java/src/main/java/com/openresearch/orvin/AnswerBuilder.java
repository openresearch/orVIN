package com.openresearch.orvin;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import static com.openresearch.orvin.JsonValues.*;

/** Deterministic resolution and projections, mirrored by Python answer.py. */
final class AnswerBuilder {
    private static final Map<String, String> PRIMARY = new LinkedHashMap<>();
    static {
        PRIMARY.put("make", "Make"); PRIMARY.put("model", "Model");
        PRIMARY.put("modelYear", "ModelYear"); PRIMARY.put("productionYear", "ProductionYear");
    }
    private final Map<String, Object> raw;
    private final boolean vin;
    private final IdentityCatalogue catalogue = IdentityCatalogue.bundled();
    private final Map<String, Map<String, Object>> sources = new LinkedHashMap<>(catalogue.sources);
    private final Map<String, Map<String, Object>> evidence = new TreeMap<>();
    private final Map<String, Map<String, Object>> normalizations = new TreeMap<>();
    private final Map<String, Map<String, Object>> decisions = new LinkedHashMap<>();
    private final Map<String, Object> vehicle = new LinkedHashMap<>();
    private final Map<String, String> status = new LinkedHashMap<>();
    private final List<Map<String, Object>> alternatives = new ArrayList<>();
    private final List<Map<String, Object>> assumptions = new ArrayList<>();
    private final List<String> wmiIds = new ArrayList<>();
    private final List<String> approvalIds = new ArrayList<>();
    private final Map<String, List<String>> richIds = new LinkedHashMap<>();

    AnswerBuilder(Map<String, Object> raw, boolean vin) {
        this.raw = raw; this.vin = vin;
        for (String name : PRIMARY.keySet()) {
            if (identity(name)) vehicle.put(name + "Id", null);
            vehicle.put(name, null); status.put(name, "UNKNOWN");
            decisions.put(name, map("reason", "NO_EVIDENCE", "evidenceIds", List.of(), "normalizationRuleIds", List.of(), "alternativeIds", List.of()));
        }
        collect();
    }
    private static boolean identity(String name) { return name.equals("make") || name.equals("model"); }
    private static Map<String, Object> obj(Map<String, Object> parent, String key) { return object(parent.get(key)); }
    private void addSource(Map<String, Object> source) {
        String sid = string(source.get("id"));
        Map<String, Object> merged = new LinkedHashMap<>(source);
        sources.getOrDefault(sid, Map.of()).forEach((k, v) -> { if (v != null) merged.put(k, v); });
        sources.put(sid, merged);
    }
    private String fact(Map<String, Object> fact) {
        String eid = "fact:" + IdentityCatalogue.id(fact);
        Map<String, Object> record = new LinkedHashMap<>(fact);
        if (java.util.Objects.equals(record.get("sourceUrl"), sources.getOrDefault(string(fact.get("sourceId")), Map.of()).get("url"))) record.remove("sourceUrl");
        evidence.put(eid, map("kind", "VIN_FACT", "sourceIds", List.of(fact.get("sourceId")), "record", record));
        return eid;
    }
    private List<String> facts(Object value) {
        Set<String> ids = new TreeSet<>();
        for (Object item : list(value)) ids.add(fact(object(item)));
        return List.copyOf(ids);
    }
    private void collect() {
        if (!vin) {
            Map<String, Object> dataset = obj(raw, "dataset");
            Map<String, Object> source = obj(dataset, "source");
            String sid = "kba-fz-types-" + dataset.get("referenceDate");
            source.put("id", sid); source.put("edition", dataset.get("referenceDate")); addSource(source);
            for (Object item : list(raw.get("candidates"))) {
                Map<String, Object> row = object(item);
                String eid = "kba:" + row.get("sourceObjectId");
                evidence.put(eid, map("kind", "KBA_TYPE", "sourceIds", List.of(sid), "record", row));
                approvalIds.add(eid);
            }
            if ("VALID".equals(raw.get("inputStatus")) && approvalIds.isEmpty()) {
                evidence.put("kba:lookup", map("kind", "LOOKUP_CHECK", "sourceIds", List.of(sid), "record",
                        map("hsn", raw.get("normalizedHsn"), "tsn", raw.get("normalizedTsn"), "referenceDate", dataset.get("referenceDate"), "result", "NO_MATCH")));
                for (String name : List.of("make", "model")) {
                    decisions.get(name).put("reason", "NO_TYPE_CODE_MATCH"); decisions.get(name).put("evidenceIds", List.of("kba:lookup"));
                }
            }
            return;
        }
        for (Object item : list(raw.get("candidates"))) {
            Map<String, Object> row = object(item), manufacturer = obj(row, "manufacturer");
            List<Object> documents = new ArrayList<>(list(row.remove("sources")));
            documents.addAll(list(manufacturer.remove("sources")));
            row.put("manufacturer", manufacturer);
            Set<String> ids = new TreeSet<>();
            for (Object document : documents) {
                Map<String, Object> source = object(document); addSource(source); ids.add(string(source.get("id")));
            }
            String eid = "wmi:" + row.get("id");
            evidence.put(eid, map("kind", "WMI_ASSIGNMENT", "sourceIds", List.copyOf(ids), "record", row)); wmiIds.add(eid);
        }
        for (String section : List.of("details", "typeApprovals"))
            for (Object source : list(obj(raw, section).get("sources"))) addSource(object(source));
        Map<String, Object> details = obj(raw, "details");
        obj(details, "fields").forEach((code, field) -> richIds.put(code, facts(object(field).get("evidence"))));
        for (Object item : list(details.get("alternatives"))) {
            Map<String, Object> alternative = object(item), fields = new TreeMap<>();
            obj(alternative, "fields").forEach((code, values) -> fields.put(code, facts(values)));
            alternatives.add(map("id", "configuration:" + IdentityCatalogue.id(alternative), "kind", "VIN_CONFIGURATION",
                    "modelYear", alternative.get("modelYear"), "market", alternative.get("market"), "fields", fields));
        }
        for (Object item : list(obj(raw, "typeApprovals").get("candidates"))) {
            Map<String, Object> row = object(item);
            String eid = "approval:" + row.get("sourceId") + ":" + row.get("sourceRow");
            evidence.put(eid, map("kind", "TYPE_APPROVAL", "sourceIds", List.of(row.get("sourceId")), "record", row)); approvalIds.add(eid);
        }
    }
    private void select(String name, List<Object> values, String knowledge, List<String> evidenceIds, String reason, Object makeId) {
        List<Map<String, Object>> mappings = new ArrayList<>();
        Map<String, List<Object>> unique = new TreeMap<>();
        boolean missing = values.isEmpty();
        for (Object value : values) {
            Map<String, Object> mapping = name.equals("make") ? catalogue.make(value) : name.equals("model") ? catalogue.model(makeId, value) : null;
            if (identity(name)) {
                missing |= mapping == null;
                if (mapping != null) {
                    mappings.add(mapping); unique.put(string(mapping.get("id")), List.of(mapping.get("id"), mapping.get("name")));
                }
            } else {
                try {
                    int year = Integer.parseInt(string(value));
                    List<Object> pair = new ArrayList<>(); pair.add(null); pair.add(year);
                    unique.put(Integer.toString(year), pair);
                } catch (NumberFormatException e) { missing = true; }
            }
        }
        String resolved = unique.size() > 1 ? "AMBIGUOUS" : missing || knowledge.equals("UNKNOWN") ? "UNKNOWN"
                : knowledge.equals("NEEDS_CONTEXT") ? "SUGGESTED" : "RESOLVED";
        status.put(name, resolved);
        boolean selected = resolved.equals("RESOLVED") || resolved.equals("SUGGESTED");
        List<Object> pair = selected ? unique.values().iterator().next() : null;
        vehicle.put(name, selected ? pair.get(1) : null);
        if (identity(name)) vehicle.put(name + "Id", selected ? pair.get(0) : null);
        Set<String> normalizationIds = new TreeSet<>(), alternativeIds = new TreeSet<>();
        for (Map<String, Object> mapping : mappings) {
            String rid = string(mapping.get("ruleId")); normalizations.put(rid, mapping); normalizationIds.add(rid);
        }
        for (Map<String, Object> alternative : alternatives)
            if (obj(alternative, "fields").values().stream().anyMatch(ids -> list(ids).stream().anyMatch(evidenceIds::contains)))
                alternativeIds.add(string(alternative.get("id")));
        decisions.put(name, map("reason", missing && !values.isEmpty() && identity(name) ? "UNMAPPED_IDENTITY"
                        : resolved.equals("AMBIGUOUS") ? "COMPETING_IDENTITIES" : reason,
                "evidenceIds", List.copyOf(new TreeSet<>(evidenceIds)), "normalizationRuleIds", List.copyOf(normalizationIds),
                "alternativeIds", List.copyOf(alternativeIds)));
    }
    private void assume(String code, List<String> fields) {
        if (!fields.isEmpty()) assumptions.add(map("code", code, "fields", fields));
    }
    VehicleAnswer resolve() {
        if (vin) {
            if (!"MODERN_FORMAT".equals(raw.get("structure"))) return finish();
            Map<String, Object> rich = obj(raw, "details"), fields = obj(rich, "fields");
            PRIMARY.forEach((name, code) -> {
                if (fields.containsKey(code)) {
                    Map<String, Object> field = object(fields.get(code));
                    select(name, list(field.get("possibilities")), string(field.get("status")), richIds.get(code), "SCOPED_VIN_RULE", vehicle.get("makeId"));
                }
            });
            if (!status.get("make").equals("RESOLVED") && !wmiIds.isEmpty() && !fields.containsKey("Make")) {
                List<Object> values = list(raw.get("candidates")).stream().map(a -> object(a).get("brand")).toList();
                select("make", values, string(obj(raw, "brand").get("status")), wmiIds, "WMI_ASSIGNMENT", null);
            }
            if (status.get("make").equals("SUGGESTED") && "KNOWN".equals(obj(raw, "brand").get("status"))) {
                List<Object> rows = list(raw.get("candidates"));
                if (!rows.isEmpty() && rows.stream().allMatch(r -> catalogue.make(object(r).get("brand")) != null &&
                        catalogue.make(object(r).get("brand")).get("id").equals(vehicle.get("makeId"))))
                    select("make", rows.stream().map(r -> object(r).get("brand")).toList(), "KNOWN", wmiIds, "WMI_ASSIGNMENT", null);
            }
            List<String> conditional = PRIMARY.keySet().stream().filter(name -> status.get(name).equals("SUGGESTED") && fields.containsKey(PRIMARY.get(name))).toList();
            assume("US_MARKET_ASSUMED", "US".equals(rich.get("marketScope")) ? conditional : List.of());
            if (status.get("make").equals("SUGGESTED") && conditional.isEmpty()) assume("MATCH_CONSTRAINTS_UNCONFIRMED", List.of("make"));
            boolean conflict = "CONTEXT_CONFLICT".equals(rich.get("status")) &&
                    (!"US".equals(rich.get("marketScope")) || "US".equals(obj(raw, "context").get("market")));
            if (obj(raw, "context").get("modelYear") != null)
                evidence.put("context:modelYear", map("kind", "CALLER_CONTEXT", "sourceIds", List.of(), "record", raw.get("context")));
            if (conflict) {
                for (String name : List.of("model", "modelYear")) {
                    vehicle.put(name, null); status.put(name, "CONFLICT"); decisions.get(name).put("reason", "CALLER_CONTEXT_CONFLICT");
                    Set<String> ids = new TreeSet<>(); ids.add("context:modelYear");
                    for (Map<String, Object> alternative : alternatives)
                        for (Object eid : list(obj(alternative, "fields").get(PRIMARY.get(name)))) ids.add(string(eid));
                    decisions.get(name).put("evidenceIds", List.copyOf(ids));
                    decisions.get(name).put("alternativeIds", alternatives.stream().map(a -> string(a.get("id"))).sorted().toList());
                }
                vehicle.put("modelId", null);
            }
            if (!approvalIds.isEmpty()) {
                List<Map<String, Object>> rows = approvalIds.stream().map(eid -> obj(obj(evidence.get(eid), "record"), "fields")).toList();
                for (String name : List.of("make", "model")) {
                    if (!List.of("UNKNOWN", "SUGGESTED").contains(status.get(name)) || name.equals("model") && conflict) continue;
                    if (name.equals("model") && (vehicle.get("makeId") == null || rows.stream().anyMatch(r ->
                            catalogue.make(r.get("make")) == null || !catalogue.make(r.get("make")).get("id").equals(vehicle.get("makeId"))))) continue;
                    if (status.get(name).equals("SUGGESTED")) {
                        List<Map<String, Object>> mapped = rows.stream().map(r -> name.equals("make") ? catalogue.make(r.get("make")) : catalogue.model(vehicle.get("makeId"), r.get("type"))).toList();
                        Set<Object> ids = new LinkedHashSet<>();
                        mapped.stream().filter(java.util.Objects::nonNull).forEach(m -> ids.add(m.get("id")));
                        if (!mapped.isEmpty() && mapped.stream().allMatch(java.util.Objects::nonNull) && !ids.equals(Set.of(vehicle.get(name + "Id")))) {
                            vehicle.put(name, null); vehicle.put(name + "Id", null); status.put(name, "AMBIGUOUS");
                            Map<String, Object> decision = decisions.get(name); decision.put("reason", "COMPETING_CONDITIONAL_SOURCES");
                            Set<String> evidenceIds = new TreeSet<>(); list(decision.get("evidenceIds")).forEach(eid -> evidenceIds.add(string(eid))); evidenceIds.addAll(approvalIds);
                            decision.put("evidenceIds", List.copyOf(evidenceIds));
                            Set<String> normalizationIds = new TreeSet<>(); list(decision.get("normalizationRuleIds")).forEach(rid -> normalizationIds.add(string(rid)));
                            for (Map<String, Object> mapping : mapped) {
                                String rid = string(mapping.get("ruleId")); normalizations.put(rid, mapping); normalizationIds.add(rid);
                            }
                            decision.put("normalizationRuleIds", List.copyOf(normalizationIds));
                        }
                        continue;
                    }
                    select(name, rows.stream().map(r -> r.get(name.equals("make") ? "make" : "type")).toList(), "NEEDS_CONTEXT", approvalIds,
                            "CATALOGUE_CONSENSUS", vehicle.get("makeId"));
                    if (status.get(name).equals("SUGGESTED")) assume("CATALOGUE_MEMBERSHIP_UNCONFIRMED", List.of(name));
                }
            }
            if (vehicle.get("makeId") == null && vehicle.get("modelId") != null) {
                vehicle.put("model", null); vehicle.put("modelId", null); status.put("model", "AMBIGUOUS");
                decisions.get("model").put("reason", "PRIMARY_MAKE_UNRESOLVED");
                Set<String> ids = new TreeSet<>();
                for (String name : List.of("model", "make")) for (Object eid : list(decisions.get(name).get("evidenceIds"))) ids.add(string(eid));
                decisions.get("model").put("evidenceIds", List.copyOf(ids));
            }
            if (List.of("COMPETING_CONDITIONAL_SOURCES", "PRIMARY_MAKE_UNRESOLVED").contains(decisions.get("model").get("reason")) && status.get("modelYear").equals("SUGGESTED")) {
                vehicle.put("modelYear", null); status.put("modelYear", "UNKNOWN");
                decisions.get("modelYear").put("reason", "IDENTITY_APPLICABILITY_UNRESOLVED");
            }
            Object year = obj(raw, "context").get("modelYear");
            if (year != null && !conflict) {
                if (vehicle.get("modelYear") != null && !vehicle.get("modelYear").equals(year)) {
                    vehicle.put("modelYear", null); status.put("modelYear", "CONFLICT"); decisions.get("modelYear").put("reason", "CALLER_CONTEXT_CONFLICT");
                } else {
                    vehicle.put("modelYear", year); status.put("modelYear", "PROVIDED"); decisions.get("modelYear").put("reason", "CALLER_CONTEXT");
                }
                Set<String> ids = new TreeSet<>(); list(decisions.get("modelYear").get("evidenceIds")).forEach(eid -> ids.add(string(eid))); ids.add("context:modelYear");
                decisions.get("modelYear").put("evidenceIds", List.copyOf(ids));
            }
            for (Map<String, Object> assumption : assumptions)
                assumption.put("fields", list(assumption.get("fields")).stream().filter(name -> !status.get(string(name)).equals("PROVIDED")).toList());
            assumptions.removeIf(a -> list(a.get("fields")).isEmpty());
        } else if ("VALID".equals(raw.get("inputStatus")) && !approvalIds.isEmpty()) {
            List<Object> rows = list(raw.get("candidates"));
            select("make", rows.stream().map(r -> object(r).get("manufacturer")).toList(), "KNOWN", approvalIds, "TYPE_CODE_LOOKUP", null);
            if (vehicle.get("makeId") != null)
                select("model", rows.stream().map(r -> object(r).get("tradeName")).toList(), "KNOWN", approvalIds, "TYPE_CODE_LOOKUP", vehicle.get("makeId"));
        }
        return finish();
    }
    private static Object first(Map<String, Object> source, String... keys) {
        for (String key : keys) if (source.get(key) != null && !source.get(key).equals("")) return source.get(key);
        return null;
    }
    private Map<String, Object> credit(String sid, Set<String> fields) {
        Map<String, Object> source = sources.get(sid);
        Object modifications = source.get("modifications");
        return map("id", sid, "publisher", source.get("publisher"), "title", source.get("title"), "url", source.get("url"),
                "edition", first(source, "edition", "publicationVersion"), "license", source.get("license"),
                "termsUrl", first(source, "termsUrl", "licenseUrl", "reuseUrl"), "reuseBasis", source.get("reuseBasis"),
                "attribution", source.getOrDefault("publisher", "") + " — " + source.getOrDefault("title", ""),
                "modifications", modifications == null || modifications.equals("") ? "Source labels normalized by ORvin; original facts retained in evidence." : modifications,
                "fields", List.copyOf(new TreeSet<>(fields)));
    }
    private VehicleAnswer finish() {
        Map<String, Set<String>> common = new TreeMap<>();
        Set<String> allSources = new TreeSet<>();
        normalizations.values().forEach(m -> allSources.add(string(m.get("sourceId"))));
        for (Map<String, Object> item : evidence.values()) for (Object sid : list(item.get("sourceIds"))) allSources.add(string(sid));
        decisions.forEach((name, decision) -> {
            Set<String> used = new TreeSet<>();
            for (Object eid : list(decision.get("evidenceIds")))
                for (Object sid : list(evidence.get(string(eid)).get("sourceIds"))) used.add(string(sid));
            for (Object rid : list(decision.get("normalizationRuleIds"))) used.add(string(normalizations.get(string(rid)).get("sourceId")));
            List<String> paths = identity(name) ? List.of("/vehicle/" + name, "/vehicle/" + name + "Id") : List.of("/vehicle/" + name);
            if (vehicle.get(name) == null) paths = List.of("/fieldStatus/" + name);
            for (String sid : used) common.computeIfAbsent(sid, key -> new TreeSet<>()).addAll(paths);
            allSources.addAll(used);
        });
        Map<String, Object> summary = map("schemaVersion", 1);
        if (vin) summary.putAll(map("vin", raw.get("normalized"), "inputStatus", "MODERN_FORMAT".equals(raw.get("structure")) ? "SUPPORTED_FORMAT" : raw.get("structure")));
        else summary.putAll(map("hsn", raw.get("normalizedHsn"), "tsn", raw.get("normalizedTsn"), "inputStatus", "VALID".equals(raw.get("inputStatus")) ? "SUPPORTED_FORMAT" : raw.get("inputStatus")));
        summary.putAll(map("vehicle", vehicle, "fieldStatus", status, "assumptions", assumptions,
                "sources", common.entrySet().stream().map(e -> credit(e.getKey(), e.getValue())).toList()));
        Set<String> creditKeys = Set.of("id", "publisher", "title", "url", "edition", "license", "termsUrl", "reuseBasis", "modifications");
        Map<String, Object> sourceDetails = new TreeMap<>();
        for (String sid : allSources) {
            Map<String, Object> detail = new LinkedHashMap<>(sources.get(sid)); creditKeys.forEach(detail::remove); sourceDetails.put(sid, detail);
        }
        List<Map<String, Object>> diagnostics = new ArrayList<>();
        Map<String, Object> datasets = map("lookup", raw.get("dataset"), "identity", catalogue.metadata);
        Map<String, Object> specifications = new TreeMap<>(), variables = new LinkedHashMap<>(), input;
        if (vin) {
            datasets.put("decoding", obj(raw, "details").get("dataset")); datasets.put("typeApprovals", obj(raw, "typeApprovals").get("dataset"));
            for (String name : List.of("details", "typeApprovals")) {
                Map<String, Object> section = obj(raw, name);
                Map<String, Object> diagnostic = map("source", name, "status", section.get("status"), "marketScope", section.get("marketScope"), "warnings", section.get("warnings"));
                if (name.equals("details")) diagnostic.putAll(map("referenceYear", section.get("referenceYear"), "stages", section.get("stages")));
                diagnostics.add(diagnostic);
            }
            diagnostics.add(map("source", "typeApprovals", "candidateCount", approvalIds.size()));
            Map<String, Object> decodingVariables = new TreeMap<>(), approvalVariables = new TreeMap<>();
            obj(obj(raw, "details"), "fields").forEach((code, item) -> {
                Map<String, Object> field = object(item);
                decodingVariables.put(code, map("label", field.get("label"), "dataType", field.get("dataType"), "status", field.get("status")));
            });
            obj(obj(raw, "typeApprovals"), "fields").forEach((code, item) -> {
                Map<String, Object> field = object(item);
                approvalVariables.put(code, map("label", field.get("label"), "sourceColumn", field.get("sourceColumn"), "unit", field.get("unit")));
            });
            variables.put("decoding", decodingVariables); variables.put("typeApprovals", approvalVariables);
            obj(obj(raw, "details"), "fields").forEach((code, item) -> {
                Map<String, Object> field = object(item);
                if (!PRIMARY.containsValue(code) && "KNOWN".equals(field.get("status")))
                    specifications.put(code, map("value", field.get("value"), "status", "RESOLVED", "dataType", field.get("dataType"), "evidenceIds", richIds.get(code)));
            });
            input = map("supplied", raw.get("supplied"), "context", raw.get("context"), "structure", raw.get("structure"));
        } else {
            Map<String, Object> lookup = obj(raw, "dataset"); lookup.remove("source"); datasets.put("lookup", lookup);
            input = map("suppliedHsn", raw.get("suppliedHsn"), "suppliedTsn", raw.get("suppliedTsn"), "inputStatus", raw.get("inputStatus"));
            diagnostics.add(map("source", "kba", "status", raw.get("status"), "candidateCount", approvalIds.size()));
        }
        Map<String, Object> rules = new TreeMap<>();
        for (Map<String, Object> item : evidence.values()) {
            if (!"VIN_FACT".equals(item.get("kind"))) continue;
            Map<String, Object> record = obj(item, "record"), rule = new LinkedHashMap<>();
            for (String key : List.of("sourceId", "ruleId", "schemaId", "keys", "kind")) rule.put(key, record.get(key));
            rules.put("rule:" + IdentityCatalogue.id(rule), rule);
        }
        Map<String, Object> details = map("meta", map("library", "ORvin", "policyVersion", "vehicle-identity-v1", "datasets", datasets), "input", input,
                "decisions", decisions, "specifications", specifications, "alternatives", alternatives, "evidence", evidence,
                "provenance", map("rules", rules, "variables", variables, "normalizationRules", normalizations, "sourceDetails", sourceDetails,
                        "additionalSources", allSources.stream().filter(sid -> !common.containsKey(sid)).map(sid -> credit(sid, Set.of("/details/evidence"))).toList()),
                "diagnostics", diagnostics);
        return new VehicleAnswer(summary, details);
    }
}
