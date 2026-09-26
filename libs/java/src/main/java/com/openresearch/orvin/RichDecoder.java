package com.openresearch.orvin;

import com.openresearch.orvin.VehicleDetails.Alternative;
import com.openresearch.orvin.VehicleDetails.Evidence;
import com.openresearch.orvin.VehicleDetails.Field;
import com.openresearch.orvin.VehicleDetails.SourceDocument;
import com.openresearch.orvin.VinDecoder.Context;
import com.openresearch.orvin.VinDecoder.DatasetInfo;
import com.openresearch.orvin.VinDecoder.Knowledge;
import com.openresearch.orvin.VinDecoder.Structure;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.regex.Pattern;
import java.util.zip.GZIPInputStream;

/** Native implementation of the documented bounded NHTSA stages; never executes SQL. */
final class RichDecoder {
    private static final String ROOT = "/META-INF/orvin/decoding/";
    private static final String YEAR_CODES = "ABCDEFGHJKLMNPRSTVWXY123456789";
    private static final Set<Integer> MULTIPLE = Set.of(121, 129, 150, 154, 155, 114, 169);
    private static final List<String> STAGES = List.of("public-patterns", "model-make", "engine-model", "displacement-conversion");
    private static final Comparator<Match> ORDER = Comparator.comparingInt(Match::priority).reversed()
            .thenComparing(Match::changed, Comparator.nullsFirst(Comparator.reverseOrder()))
            .thenComparingInt(m -> m.keys().replace("*", "").length())
            .thenComparing(m -> m.keys().replace("[", "").replace("]", ""))
            .thenComparingInt(Match::id);

    private final Map<Integer, Element> elements = new HashMap<>();
    private final Map<String, Wmi> wmis = new HashMap<>();
    private final Map<String, List<Schema>> schemas = new HashMap<>();
    private final Map<String, Model> models = new HashMap<>();
    private final Map<String, List<Engine>> engines = new HashMap<>();
    private final Map<String, String> hashes = new HashMap<>();
    private final List<Conversion> conversions = new ArrayList<>();
    // Access under synchronized methods; bounded caches avoid retaining every manufacturer.
    private final Map<Integer, Map<Integer, List<String[]>>> buckets = new LinkedHashMap<>(16, 0.75f, true);
    private final Map<Integer, List<Rule>> rules = new LinkedHashMap<>(64, 0.75f, true);
    private DatasetInfo dataset;
    private int referenceYear;
    private String source;
    private final Map<String, SourceDocument> sources = new HashMap<>();
    private String europeSource;
    private String europeUrl;
    private final Map<Integer, String> europeRequirements = new HashMap<>();
    private final Map<String, Integer> europeYears = new HashMap<>();
    private final Map<String, Map<String, String>> europeLayouts = new HashMap<>();
    private final List<OemAttribute> europeAttributes = new ArrayList<>();
    private final Map<String, OemRule> oemRules = new LinkedHashMap<>();

    static RichDecoder load() {
        try {
            String[] metadata = new String(BundledResources.read("decoding-metadata.tsv"), StandardCharsets.UTF_8).strip().split("\t");
            byte[] index = BundledResources.read(ROOT + "index.tsv");
            BundledResources.verify(index, metadata[1]);
            return new RichDecoder(new String(index, StandardCharsets.UTF_8), metadata[1]);
        } catch (IOException e) {
            throw new IllegalStateException("Cannot load bundled decoding rules", e);
        }
    }

    private RichDecoder(String index, String digest) {
        for (String line : index.split("\n")) {
            String[] c = line.split("\t", -1);
            switch (c[0]) {
                case "V" -> {
                    dataset = new DatasetInfo(c[1], digest);
                    referenceYear = Integer.parseInt(c[2]);
                    source = c[3];
                }
                case "D" -> {
                    SourceDocument document = new SourceDocument(text(c[1]), text(c[2]), text(c[3]), text(c[4]),
                            text(c[5]), text(c[6]), text(c[7]), text(c[8]), Optional.ofNullable(nullable(text(c[9]))),
                            Optional.ofNullable(nullable(text(c[10]))), Optional.ofNullable(nullable(text(c[11]))), text(c[12]));
                    sources.put(document.id(), document);
                }
                case "E" -> elements.put(Integer.valueOf(c[1]), new Element(c[2], text(c[3]), c[4]));
                case "W" -> wmis.put(c[1], new Wmi(Integer.parseInt(c[3]), c[4]));
                case "S" -> schemas.computeIfAbsent(c[1], key -> new ArrayList<>()).add(
                        new Schema(Integer.parseInt(c[2]), Integer.parseInt(c[3]), Integer.parseInt(c[4])));
                case "M" -> models.put(c[1], new Model(c[2], text(c[3])));
                case "G" -> engines.computeIfAbsent(text(c[1]), key -> new ArrayList<>()).add(
                        new Engine(Integer.parseInt(c[2]), Integer.parseInt(c[3]), text(c[4]), text(c[5]), nullable(c[6])));
                case "C" -> conversions.add(new Conversion(c[1], Integer.parseInt(c[2]), Integer.parseInt(c[3]),
                        c[4], new BigDecimal(c[5])));
                case "H" -> hashes.put(c[1], c[2]);
                case "T" -> { europeSource = c[1]; europeUrl = c[2]; }
                case "R" -> europeRequirements.put(Integer.parseInt(c[1]) - 1, c[2]);
                case "Y" -> europeYears.put(c[1], Integer.valueOf(c[2]));
                case "L" -> europeLayouts.computeIfAbsent(c[1] + c[2], key -> new HashMap<>()).put(c[3], text(c[4]));
                case "A" -> europeAttributes.add(new OemAttribute(Integer.parseInt(c[1]) - 1, c[2], c[3], text(c[4])));
                case "O" -> oemRules.put(c[1], new OemRule(Pattern.compile(text(c[2])), Integer.parseInt(c[3]), new TreeMap<>()));
                case "F" -> oemRules.get(c[1]).fields().computeIfAbsent(c[2], key -> new ArrayList<>())
                        .add(new String[] {text(c[3]), c[4], c[5]});
                default -> throw new IllegalStateException("Unknown decoding index row");
            }
        }
    }

    private static String text(String base64) {
        return new String(Base64.getDecoder().decode(base64), StandardCharsets.UTF_8);
    }

    private static String nullable(String value) { return value.isEmpty() ? null : value; }

    private synchronized List<Rule> patterns(int schema) {
        List<Rule> existing = rules.get(schema);
        if (existing != null) return existing;
        int bucket = schema % 256;
        Map<Integer, List<String[]>> rows = buckets.get(bucket);
        if (rows == null) {
            String name = String.format(Locale.ROOT, "patterns-%03d.tsv.gz", bucket);
            rows = new HashMap<>();
            try {
                byte[] compressed = BundledResources.read(ROOT + name);
                BundledResources.verify(compressed, hashes.get(name));
                try (var stream = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
                    String contents = new String(stream.readAllBytes(), StandardCharsets.UTF_8);
                    for (String line : contents.split("\n")) {
                        String[] c = line.split("\t", -1);
                        rows.computeIfAbsent(Integer.valueOf(c[0]), key -> new ArrayList<>()).add(c);
                    }
                }
            } catch (IOException e) {
                throw new IllegalStateException("Cannot load decoding patterns", e);
            }
            buckets.put(bucket, rows);
            if (buckets.size() > 8) buckets.remove(buckets.keySet().iterator().next());
        }
        List<Rule> compiled = rows.getOrDefault(schema, List.of()).stream().map(c -> new Rule(
                Integer.parseInt(c[1]), Integer.parseInt(c[2]), text(c[3]), text(c[4]), text(c[5]), nullable(c[6]),
                Pattern.compile(text(c[7])), Integer.parseInt(c[8]), Integer.parseInt(c[9]))).toList();
        rules.put(schema, compiled);
        if (rules.size() > 32) rules.remove(rules.keySet().iterator().next());
        return compiled;
    }

    private Evidence fact(int element, String value, String attribute, String kind, String rule, Integer schema, String key) {
        return new Evidence(element, value, attribute, source,
                sources.get(source).url(),
                kind, rule, Optional.ofNullable(schema), key);
    }

    private VehicleDetails europe(String vin) {
        Map<String, String> layout = europeLayouts.get(vin.substring(0, 3) + vin.charAt(10));
        if (layout == null || europeRequirements.entrySet().stream().anyMatch(
                e -> e.getValue().indexOf(vin.charAt(e.getKey())) < 0)) return null;
        if (!vin.substring(11).matches("[0-9]{6}") || vin.substring(11).equals("000000")) return null;
        Map<String, String[]> values = new TreeMap<>();
        layout.forEach((code, value) -> values.put(code, new String[] {value, "layout:" + vin.substring(0, 3) + vin.charAt(10)}));
        for (OemAttribute attribute : europeAttributes) {
            if (attribute.characters().indexOf(vin.charAt(attribute.position())) >= 0)
                values.put(attribute.code(), new String[] {attribute.value(), "position:" + (attribute.position() + 1) + ":" + vin.charAt(attribute.position())});
        }
        values.put("ProductionYear", new String[] {Integer.toString(europeYears.get(vin.substring(9, 10))), "position:10:" + vin.charAt(9)});
        Map<String, Field> fields = new LinkedHashMap<>();
        Map<String, List<Evidence>> facts = new LinkedHashMap<>();
        values.forEach((code, value) -> {
            var entry = elements.entrySet().stream().filter(e -> e.getValue().code().equals(code)).findFirst().orElseThrow();
            Element element = entry.getValue();
            Evidence evidence = new Evidence(entry.getKey(), value[0], value[0], europeSource, europeUrl,
                    "OEM_RULE", value[1], Optional.empty(), "");
            facts.put(code, List.of(evidence));
            fields.put(code, new Field(element.label(), element.dataType(), Knowledge.KNOWN, List.of(value[0]), List.of(evidence)));
        });
        return new VehicleDetails("DECODED", Optional.of(dataset), "GLOBAL", referenceYear,
                List.of("tesla-model-y-2025-oem-rules"),
                List.of("Production year is a calendar year, not model year or exact build date."), fields,
                List.of(new Alternative(Optional.empty(), "GLOBAL", facts)), usedSources(fields));
    }

    private VehicleDetails oem(String vin, Context context) {
        for (var ruleEntry : oemRules.entrySet()) {
            OemRule rule = ruleEntry.getValue();
            if (!rule.pattern().matcher(vin).matches()) continue;
            boolean conflict = context.modelYear().filter(year -> year != rule.year()).isPresent();
            Map<String, Field> fields = new LinkedHashMap<>();
            Map<String, List<Evidence>> facts = new LinkedHashMap<>();
            rule.fields().forEach((code, associations) -> {
                var entry = elements.entrySet().stream().filter(e -> e.getValue().code().equals(code)).findFirst().orElseThrow();
                List<Evidence> evidence = associations.stream().map(a -> new Evidence(entry.getKey(), a[0], a[0], a[1], a[2],
                        "OEM_RULE_COMBINATION", ruleEntry.getKey(), Optional.empty(), rule.pattern().pattern())).toList();
                facts.put(code, evidence);
                fields.put(code, new Field(entry.getValue().label(), entry.getValue().dataType(), Knowledge.KNOWN,
                        List.of(associations.get(0)[0]), evidence));
            });
            return new VehicleDetails(conflict ? "CONTEXT_CONFLICT" : "DECODED", Optional.of(dataset), "EUROPEAN_LAYOUT", referenceYear,
                    List.of("vw-europe-golf-1k-2005"),
                    conflict ? List.of("Supplied model year conflicts with this documented European VIN layout.")
                            : List.of("Golf family only; filler characters do not identify engine or trim. Model year is not exact build date."),
                    conflict ? Map.of() : fields, List.of(new Alternative(Optional.of(rule.year()), "EUROPEAN_LAYOUT", facts)), usedSources(fields));
        }
        return null;
    }

    private List<Integer> years(String vin, Context context, String wmi) {
        int code = YEAR_CODES.indexOf(vin.charAt(9));
        if (code < 0) return List.of();
        int base = 1980 + code;
        if (context.modelYear().isPresent()) {
            int supplied = context.modelYear().get();
            return supplied >= 1980 && (supplied - base) % 30 == 0 ? List.of(supplied) : List.of();
        }
        Wmi w = wmis.get(wmi);
        boolean light = w.type() == 2 || w.type() == 7 || w.type() == 3 && w.truck().equals("1");
        boolean digit = vin.charAt(6) >= '0' && vin.charAt(6) <= '9';
        List<Integer> years = new ArrayList<>();
        for (int year = base; year <= referenceYear + 2; year += 30) {
            if (!light || (year < 2010) == digit) years.add(year);
        }
        return years;
    }

    private Alternative decodeYear(String vin, String wmi, int year, Context context) {
        String key = vin.substring(3, 8) + "|" + vin.substring(9);
        Map<Integer, List<Match>> matches = new TreeMap<>();
        for (Schema schema : schemas.getOrDefault(wmi, List.of())) {
            if (year < schema.start() || year > schema.end()) continue;
            for (Rule rule : patterns(schema.id())) {
                if (!rule.regex().matcher(key).lookingAt()) continue;
                boolean formula = rule.capture() >= 0;
                String value = formula ? key.substring(rule.capture(), rule.capture() + rule.length()) : rule.value();
                String attribute = formula ? value : rule.attribute();
                Evidence fact = fact(rule.element(), value, attribute, formula ? "NUMERIC_PATTERN" : "PATTERN",
                        Integer.toString(rule.id()), schema.id(), rule.keys());
                matches.computeIfAbsent(rule.element(), e -> new ArrayList<>()).add(new Match(
                        formula ? 100 : schema.start(), rule.changed(), rule.keys(), rule.id(), fact));
            }
        }
        List<Match> engineMatches = matches.getOrDefault(18, List.of());
        if (!engineMatches.isEmpty()) {
            Evidence parent = engineMatches.stream().min(Comparator.comparingInt(Match::priority).reversed()
                    .thenComparing(Match::changed, Comparator.nullsFirst(Comparator.reverseOrder()))
                    .thenComparing(Comparator.comparingInt(Match::id).reversed())).orElseThrow().fact();
            for (Engine engine : engines.getOrDefault(parent.attributeId().strip().toLowerCase(Locale.ROOT), List.of())) {
                Evidence fact = fact(engine.element(), engine.value(), engine.attribute(), "ENGINE_MODEL",
                        parent.ruleId() + "/engine:" + engine.id(), parent.schemaId().orElse(null), parent.keys());
                matches.computeIfAbsent(engine.element(), e -> new ArrayList<>()).add(
                        new Match(50, engine.changed(), parent.keys(), engine.id(), fact));
            }
        }
        Map<Integer, List<Evidence>> facts = new TreeMap<>();
        matches.forEach((element, items) -> {
            items.sort(ORDER);
            facts.put(element, MULTIPLE.contains(element) ? items.stream().map(Match::fact).distinct().toList()
                    : List.of(items.get(0).fact()));
        });
        if (facts.containsKey(28)) {
            Evidence parent = facts.get(28).get(0);
            Model model = models.get(parent.attributeId());
            if (model != null) facts.put(26, List.of(fact(26, model.name(), model.make(), "MODEL_MAKE",
                    parent.ruleId() + "/make:" + model.make(), parent.schemaId().orElse(null), parent.keys())));
        }
        for (Conversion conversion : conversions) {
            if (!matches.containsKey(conversion.from()) || facts.containsKey(conversion.to())
                    || facts.getOrDefault(conversion.from(), List.of()).size() != 1) continue;
            Evidence parent = facts.get(conversion.from()).get(0);
            try {
                BigDecimal original = new BigDecimal(parent.value());
                BigDecimal number = conversion.operator().equals("*") ? original.multiply(conversion.factor())
                        : original.divide(conversion.factor(), 6, RoundingMode.HALF_UP);
                String value = number.setScale(6, RoundingMode.HALF_UP).stripTrailingZeros().toPlainString();
                facts.put(conversion.to(), List.of(fact(conversion.to(), value, value, "UNIT_CONVERSION",
                        parent.ruleId() + "/conversion:" + conversion.id(), parent.schemaId().orElse(null), parent.keys())));
            } catch (NumberFormatException | ArithmeticException ignored) {
                // Non-numeric source text remains available as-is; do not invent a converted value.
            }
        }
        if (!facts.isEmpty()) facts.put(29, List.of(fact(29, Integer.toString(year), Integer.toString(year),
                context.modelYear().isPresent() ? "CALLER_CONTEXT" : "VIN_YEAR", "model-year", null, vin.substring(9, 10))));
        Map<String, List<Evidence>> fields = new LinkedHashMap<>();
        facts.forEach((element, value) -> fields.put(elements.get(element).code(), value));
        return new Alternative(Optional.of(year), "US", fields);
    }

    VehicleDetails decode(String vin, Structure structure, Context context) {
        if (structure != Structure.MODERN_FORMAT) return result("INVALID_INPUT", List.of(), Map.of(), List.of());
        VehicleDetails oem = oem(vin, context);
        if (oem != null) return oem;
        VehicleDetails european = europe(vin);
        if (european != null) return european;
        if (context.market().filter(m -> !m.equals("US")).isPresent()) {
            return result("OUT_OF_SCOPE", List.of("NHTSA rules are scoped to US reporting; no applicable non-US rule is bundled for this VIN."), Map.of(), List.of());
        }
        String wmi = vin.substring(0, 3) + (vin.charAt(2) == '9' ? vin.substring(11, 14) : "");
        if (!wmis.containsKey(wmi)) return result("UNKNOWN", List.of(), Map.of(), List.of());
        List<Integer> years = years(vin, context, wmi);
        if (years.isEmpty()) return result(context.modelYear().isPresent() ? "CONTEXT_CONFLICT" : "UNKNOWN",
                List.of("VIN year code does not resolve within this US scheme and supplied context."), Map.of(), List.of());
        List<Alternative> alternatives = years.stream().map(year -> decodeYear(vin, wmi, year, context)).toList();
        Set<String> codes = new TreeSet<>();
        alternatives.forEach(a -> codes.addAll(a.fields().keySet()));
        Map<String, Field> fields = new LinkedHashMap<>();
        for (String code : codes) {
            Set<Evidence> evidence = new LinkedHashSet<>();
            Set<String> values = new LinkedHashSet<>();
            boolean missing = false;
            for (Alternative alternative : alternatives) {
                List<Evidence> facts = alternative.fields().getOrDefault(code, List.of());
                missing |= facts.isEmpty();
                for (Evidence fact : facts) {
                    evidence.add(fact);
                    values.add(fact.value());
                }
            }
            Element element = elements.get(evidence.iterator().next().elementId());
            Knowledge status = values.size() > 1 ? Knowledge.AMBIGUOUS : missing ? Knowledge.UNKNOWN
                    : context.market().isEmpty() ? Knowledge.NEEDS_CONTEXT : Knowledge.KNOWN;
            fields.put(code, new Field(element.label(), element.dataType(), status, new ArrayList<>(values), new ArrayList<>(evidence)));
        }
        List<String> warnings = new ArrayList<>();
        if (context.market().isEmpty() && !codes.isEmpty())
            warnings.add("These possibilities assume US reporting scope; supply market US only when independently known.");
        if (years.size() > 1)
            warnings.add("The VIN year code has multiple possible cycles; alternatives retain each year's associated facts.");
        String status = codes.isEmpty() ? "UNKNOWN" : context.market().isEmpty() ? "NEEDS_CONTEXT" : "DECODED";
        return result(status, warnings, fields, alternatives);
    }

    private VehicleDetails result(String status, List<String> warnings, Map<String, Field> fields, List<Alternative> alternatives) {
        return new VehicleDetails(status, Optional.of(dataset), "US", referenceYear, STAGES, warnings, fields, alternatives, usedSources(fields));
    }

    private List<SourceDocument> usedSources(Map<String, Field> fields) {
        return fields.values().stream().flatMap(f -> f.evidence().stream()).map(Evidence::sourceId)
                .distinct().sorted().map(sources::get).toList();
    }

    private record Element(String code, String label, String dataType) { }
    private record Wmi(int type, String truck) { }
    private record Schema(int id, int start, int end) { }
    private record Model(String make, String name) { }
    private record Engine(int id, int element, String attribute, String value, String changed) { }
    private record Conversion(String id, int from, int to, String operator, BigDecimal factor) { }
    private record Rule(int id, int element, String keys, String attribute, String value,
                        String changed, Pattern regex, int capture, int length) { }
    private record Match(int priority, String changed, String keys, int id, Evidence fact) { }
    private record OemAttribute(int position, String characters, String code, String value) { }
    private record OemRule(Pattern pattern, int year, Map<String, List<String[]>> fields) { }
}
