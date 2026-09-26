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
    private final RuntimePolicy policy = RuntimePolicy.get();
    private String p(String key) { return policy.text("patternProfile." + key); }
    private int n(String key) { return policy.number("patternProfile." + key); }
    private final List<LiteralRule> literalRules = loadLiterals();
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

    private static List<LiteralRule> loadLiterals() {
        Map<String, LiteralRule> result = new LinkedHashMap<>();
        try {
            for (String line : new String(BundledResources.read("rules.tsv"), StandardCharsets.UTF_8).split("\n")) {
                String[] cells = line.split("\t", -1);
                String[] c = java.util.Arrays.stream(cells).skip(1).map(RichDecoder::text).toArray(String[]::new);
                if (cells[0].equals("R")) result.put(c[0], new LiteralRule(Pattern.compile(c[1]),
                        c[2].isEmpty() ? null : Pattern.compile(c[2]), c[3], c[4].isEmpty() ? List.of() : List.of(c[4].split(",")),
                        c[5].isEmpty() ? null : Integer.valueOf(c[5]), c[6], c[7], c[8], new ArrayList<>()));
                else if (cells[0].equals("F")) result.get(c[0]).claims().add(new LiteralClaim(Integer.parseInt(c[1]), c[2], c[3], c[4], c[5], c[6], c[7], c[8]));
                else throw new IllegalStateException("Unsupported literal-rule operation");
            }
        } catch (IOException e) { throw new IllegalStateException("Cannot load literal rules", e); }
        return List.copyOf(result.values());
    }

    private List<VehicleDetails> literals(String vin, Context context) {
        List<VehicleDetails> results = new ArrayList<>();
        for (LiteralRule rule : literalRules) {
            if (!rule.pattern().matcher(vin).matches() || rule.exclude() != null && rule.exclude().matcher(vin).matches()) continue;
            boolean foreign = !rule.markets().isEmpty() && !rule.markets().contains(context.market().orElse(""));
            boolean conflict = rule.year() != null && context.modelYear().filter(y -> !y.equals(rule.year())).isPresent();
            if (conflict && foreign) continue;
            Map<String, List<Evidence>> facts = new TreeMap<>();
            for (LiteralClaim claim : rule.claims()) {
                if (claim.position() >= 0 && claim.characters().indexOf(vin.charAt(claim.position())) < 0) continue;
                var entry = elements.entrySet().stream().filter(e -> e.getValue().code().equals(claim.code())).findFirst().orElseThrow();
                Evidence fact = new Evidence(entry.getKey(), claim.value(), claim.value(), claim.source(), sources.get(claim.source()).url(),
                        claim.kind(), claim.rule(), Optional.empty(), claim.keys());
                List<Evidence> group = facts.computeIfAbsent(claim.code(), k -> new ArrayList<>());
                if (!group.contains(fact)) group.add(fact);
            }
            Map<String, Field> fields = new TreeMap<>();
            facts.forEach((code, evidence) -> {
                Element element = elements.get(evidence.get(0).elementId());
                List<String> values = evidence.stream().map(Evidence::value).distinct().sorted().toList();
                fields.put(code, new Field(element.label(), element.dataType(), values.size() > 1 ? Knowledge.AMBIGUOUS : foreign ? Knowledge.NEEDS_CONTEXT : Knowledge.KNOWN, values, evidence));
            });
            results.add(new VehicleDetails(conflict ? "CONTEXT_CONFLICT" : foreign ? "NEEDS_CONTEXT" : "DECODED", Optional.of(dataset), rule.scope(), referenceYear,
                    List.of(rule.stage()), List.of(conflict ? rule.conflictWarning() : rule.warning()), conflict ? Map.of() : fields,
                    List.of(new Alternative(Optional.ofNullable(rule.year()), rule.scope(), facts)), sourcesFor(fields, List.of(new Alternative(Optional.ofNullable(rule.year()), rule.scope(), facts)))));
        }
        return results;
    }

    private List<Integer> years(String vin, Context context, String wmi) {
        int code = p("yearCodes").indexOf(vin.charAt(n("yearPosition")));
        if (code < 0) return List.of();
        int base = n("yearBase") + code;
        if (context.modelYear().isPresent()) {
            int supplied = context.modelYear().get();
            return supplied >= n("yearBase") && (supplied - base) % n("yearCycle") == 0 ? List.of(supplied) : List.of();
        }
        Wmi w = wmis.get(wmi);
        boolean light = policy.numbers("patternProfile.cycleDiscriminator.vehicleTypes").contains(w.type()) || w.type() == n("cycleDiscriminator.conditionalType") && w.truck().equals(p("cycleDiscriminator.truckType"));
        boolean digit = vin.charAt(n("cycleDiscriminator.position")) >= '0' && vin.charAt(n("cycleDiscriminator.position")) <= '9';
        List<Integer> years = new ArrayList<>();
        for (int year = base; year <= referenceYear + n("yearHorizon"); year += n("yearCycle")) {
            if (!light || (year < n("cycleDiscriminator.beforeYear")) == digit) years.add(year);
        }
        return years;
    }

    private Alternative decodeYear(String vin, String wmi, int year, Context context) {
        String key = java.util.stream.IntStream.range(0, n("keySlices.length")).mapToObj(i -> vin.substring(n("keySlices." + i + ".0"), n("keySlices." + i + ".1"))).collect(java.util.stream.Collectors.joining(p("keySeparator")));
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
                        formula ? n("formulaPriority") : schema.start(), rule.changed(), rule.keys(), rule.id(), fact));
            }
        }
        List<Match> engineMatches = matches.getOrDefault(n("engineElement"), List.of());
        if (!engineMatches.isEmpty()) {
            Evidence parent = engineMatches.stream().min(Comparator.comparingInt(Match::priority).reversed()
                    .thenComparing(Match::changed, Comparator.nullsFirst(Comparator.reverseOrder()))
                    .thenComparing(Comparator.comparingInt(Match::id).reversed())).orElseThrow().fact();
            for (Engine engine : engines.getOrDefault(parent.attributeId().strip().toLowerCase(Locale.ROOT), List.of())) {
                Evidence fact = fact(engine.element(), engine.value(), engine.attribute(), "ENGINE_MODEL",
                        parent.ruleId() + "/engine:" + engine.id(), parent.schemaId().orElse(null), parent.keys());
                matches.computeIfAbsent(engine.element(), e -> new ArrayList<>()).add(
                        new Match(n("enginePriority"), engine.changed(), parent.keys(), engine.id(), fact));
            }
        }
        Map<Integer, List<Evidence>> facts = new TreeMap<>();
        matches.forEach((element, items) -> {
            items.sort(ORDER);
            facts.put(element, policy.numbers("patternProfile.multipleElements").contains(element) ? items.stream().map(Match::fact).distinct().toList()
                    : List.of(items.get(0).fact()));
        });
        if (facts.containsKey(n("modelElement"))) {
            Evidence parent = facts.get(n("modelElement")).get(0);
            Model model = models.get(parent.attributeId());
            if (model != null) facts.put(n("makeElement"), List.of(fact(n("makeElement"), model.name(), model.make(), "MODEL_MAKE",
                    parent.ruleId() + "/make:" + model.make(), parent.schemaId().orElse(null), parent.keys())));
        }
        for (Conversion conversion : conversions) {
            if (!matches.containsKey(conversion.from()) || facts.containsKey(conversion.to())
                    || facts.getOrDefault(conversion.from(), List.of()).size() != 1) continue;
            Evidence parent = facts.get(conversion.from()).get(0);
            try {
                BigDecimal original = new BigDecimal(parent.value());
                BigDecimal number = conversion.operator().equals("*") ? original.multiply(conversion.factor())
                        : original.divide(conversion.factor(), n("conversionScale"), RoundingMode.HALF_UP);
                String value = number.setScale(n("conversionScale"), RoundingMode.HALF_UP).stripTrailingZeros().toPlainString();
                facts.put(conversion.to(), List.of(fact(conversion.to(), value, value, "UNIT_CONVERSION",
                        parent.ruleId() + "/conversion:" + conversion.id(), parent.schemaId().orElse(null), parent.keys())));
            } catch (NumberFormatException | ArithmeticException ignored) {
                // Non-numeric source text remains available as-is; do not invent a converted value.
            }
        }
        if (!facts.isEmpty()) facts.put(n("yearElement"), List.of(fact(n("yearElement"), Integer.toString(year), Integer.toString(year),
                context.modelYear().isPresent() ? "CALLER_CONTEXT" : "VIN_YEAR", "model-year", null, vin.substring(n("yearPosition"), n("yearPosition") + 1))));
        Map<String, List<Evidence>> fields = new LinkedHashMap<>();
        facts.forEach((element, value) -> fields.put(elements.get(element).code(), value));
        return new Alternative(Optional.of(year), p("market"), fields);
    }

    private VehicleDetails patternsResult(String vin, Structure structure, Context context) {
        if (structure != Structure.MODERN_FORMAT) return result("INVALID_INPUT", List.of(), Map.of(), List.of());
        String wmi = vin.substring(0, 3) + (vin.charAt(n("extendedWmi.position")) == p("extendedWmi.character").charAt(0) ? vin.substring(n("extendedWmi.suffixStart"), n("extendedWmi.suffixEnd")) : "");
        if (!wmis.containsKey(wmi)) return result("UNKNOWN", List.of(), Map.of(), List.of());
        List<Integer> years = years(vin, context, wmi);
        if (years.isEmpty()) return result(context.modelYear().isPresent() ? "CONTEXT_CONFLICT" : "UNKNOWN",
                List.of(p("yearConflictWarning")), Map.of(), List.of());
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
                    : !context.market().orElse("").equals(p("market")) ? Knowledge.NEEDS_CONTEXT : Knowledge.KNOWN;
            fields.put(code, new Field(element.label(), element.dataType(), status, new ArrayList<>(values), new ArrayList<>(evidence)));
        }
        List<String> warnings = new ArrayList<>();
        if (!context.market().orElse("").equals(p("market")) && !codes.isEmpty())
            warnings.add(context.market().isEmpty() ? p("unknownMarketWarning") : p("fallbackMessage").replace("{sourceMarket}", p("market")).replace("{requestedMarket}", context.market().orElseThrow()));
        if (years.size() > 1)
            warnings.add(p("yearAlternativesWarning"));
        String status = codes.isEmpty() ? "UNKNOWN" : !context.market().orElse("").equals(p("market")) ? "NEEDS_CONTEXT" : "DECODED";
        return result(status, warnings, fields, alternatives);
    }

    private VehicleDetails result(String status, List<String> warnings, Map<String, Field> fields, List<Alternative> alternatives) {
        return new VehicleDetails(status, Optional.of(dataset), p("market"), referenceYear, policy.strings("patternProfile.stages"), warnings, fields, alternatives, sourcesFor(fields, alternatives));
    }

    private List<SourceDocument> sourcesFor(Map<String, Field> fields, List<Alternative> alternatives) {
        Set<String> used = new TreeSet<>();
        fields.values().forEach(f -> f.evidence().forEach(e -> used.add(e.sourceId())));
        alternatives.forEach(a -> a.fields().values().forEach(f -> f.forEach(e -> used.add(e.sourceId()))));
        return used.stream().map(sources::get).toList();
    }

    VehicleDetails decode(String vin, Structure structure, Context context) {
        VehicleDetails patterns = patternsResult(vin, structure, context);
        if (structure != Structure.MODERN_FORMAT) return patterns;
        List<VehicleDetails> results = new ArrayList<>(literals(vin, context));
        results.add(patterns);
        List<VehicleDetails> meaningful = results.stream().filter(r -> !r.fields().isEmpty() || !r.alternatives().isEmpty()).toList();
        List<VehicleDetails> conflicts = results.stream().filter(r -> r.status().equals("CONTEXT_CONFLICT") &&
                (!r.marketScope().equals(p("market")) || context.market().orElse("").equals(p("market")))).toList();
        List<Alternative> alternatives = meaningful.stream().flatMap(r -> r.alternatives().stream()).toList();
        if (!conflicts.isEmpty()) {
            VehicleDetails first = conflicts.get(0);
            return new VehicleDetails(first.status(), first.dataset(), first.marketScope(), referenceYear, first.stages(), first.warnings(), Map.of(), alternatives, sourcesFor(Map.of(), alternatives));
        }
        if (meaningful.isEmpty()) return patterns;
        if (meaningful.size() == 1) return meaningful.get(0);
        Set<String> codes = new TreeSet<>(), scopes = new TreeSet<>();
        meaningful.forEach(r -> { codes.addAll(r.fields().keySet()); scopes.add(r.marketScope()); });
        Map<String, Field> fields = new TreeMap<>();
        for (String code : codes) {
            List<Field> all = meaningful.stream().filter(r -> r.fields().containsKey(code)).map(r -> r.fields().get(code)).toList();
            List<Field> applicable = meaningful.stream().filter(r -> !r.status().equals("NEEDS_CONTEXT") && r.fields().containsKey(code) && r.fields().get(code).status() != Knowledge.NEEDS_CONTEXT).map(r -> r.fields().get(code)).toList();
            List<Field> selected = applicable.isEmpty() ? all : applicable;
            List<String> values = selected.stream().flatMap(f -> f.possibilities().stream()).distinct().sorted().toList();
            List<Evidence> evidence = selected.stream().flatMap(f -> f.evidence().stream()).distinct().toList();
            Knowledge status = values.size() > 1 ? Knowledge.AMBIGUOUS : selected.stream().anyMatch(f -> f.status() == Knowledge.UNKNOWN) ? Knowledge.UNKNOWN : applicable.isEmpty() ? Knowledge.NEEDS_CONTEXT : Knowledge.KNOWN;
            fields.put(code, new Field(selected.get(0).label(), selected.get(0).dataType(), status, values, evidence));
        }
        return new VehicleDetails(fields.values().stream().anyMatch(f -> f.status() == Knowledge.KNOWN) ? "DECODED" : "NEEDS_CONTEXT", Optional.of(dataset), scopes.size() == 1 ? scopes.iterator().next() : "MULTIPLE", referenceYear,
                meaningful.stream().flatMap(r -> r.stages().stream()).distinct().toList(), meaningful.stream().flatMap(r -> r.warnings().stream()).filter(w -> !w.isEmpty()).distinct().toList(), fields, alternatives, sourcesFor(fields, alternatives));
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
    private record LiteralClaim(int position, String characters, String code, String value, String source, String kind, String rule, String keys) { }
    private record LiteralRule(Pattern pattern, Pattern exclude, String scope, List<String> markets, Integer year, String stage, String warning, String conflictWarning, List<LiteralClaim> claims) { }
}
