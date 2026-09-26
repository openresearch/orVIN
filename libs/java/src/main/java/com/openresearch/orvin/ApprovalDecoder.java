package com.openresearch.orvin;

import com.openresearch.orvin.TypeApprovals.Candidate;
import com.openresearch.orvin.TypeApprovals.Field;
import com.openresearch.orvin.VehicleDetails.SourceDocument;
import com.openresearch.orvin.VinDecoder.DatasetInfo;
import com.openresearch.orvin.VinDecoder.Structure;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.TreeSet;
import java.util.zip.GZIPInputStream;

/** Matches sourced Swiss approval masks without influencing decoded vehicle facts. */
final class ApprovalDecoder {
    private static final String ROOT = "/META-INF/orvin/astra/";
    private final DatasetInfo dataset;
    private final SourceDocument source;
    private final Map<String, Definition> definitions;
    private final Map<String, Shard> shards;
    // All access is synchronized; immutable rows can be safely used after eviction.
    private final Map<String, List<Row>> cache = new LinkedHashMap<>(16, 0.75f, true);

    static ApprovalDecoder load() {
        try {
            String[] metadata = new String(BundledResources.read("astra-metadata.tsv"), StandardCharsets.UTF_8)
                    .strip().split("\t", -1);
            byte[] index = BundledResources.read(ROOT + "index.tsv");
            BundledResources.verify(index, metadata[1]);
            return new ApprovalDecoder(new String(index, StandardCharsets.UTF_8), new DatasetInfo(metadata[0], metadata[1]));
        } catch (IOException e) {
            throw new IllegalStateException("Cannot load bundled ASTRA type approvals", e);
        }
    }

    private ApprovalDecoder(String index, DatasetInfo dataset) {
        this.dataset = dataset;
        Map<String, Definition> fields = new LinkedHashMap<>();
        Map<String, Shard> entries = new HashMap<>();
        SourceDocument document = null;
        for (String line : index.split("\n")) {
            String[] c = line.split("\t", -1);
            switch (c[0]) {
                case "V" -> {
                    if (!c[1].equals(dataset.version())) throw new IllegalStateException("ASTRA dataset version mismatch");
                }
                case "D" -> document = new SourceDocument(text(c[1]), text(c[2]), text(c[3]), text(c[4]),
                        text(c[5]), text(c[6]), text(c[7]), text(c[8]), optional(text(c[9])),
                        optional(text(c[10])), optional(text(c[11])), text(c[12]));
                case "F" -> fields.put(c[1], new Definition(text(c[2]), text(c[3]), text(c[4])));
                case "W" -> entries.put(c[1], new Shard(c[2], c[3]));
                default -> throw new IllegalStateException("Unknown ASTRA index record: " + c[0]);
            }
        }
        source = Objects.requireNonNull(document, "ASTRA source metadata missing");
        definitions = Collections.unmodifiableMap(fields);
        shards = Map.copyOf(entries);
    }

    private static String text(String value) {
        return new String(Base64.getDecoder().decode(value), StandardCharsets.UTF_8);
    }

    private static Optional<String> optional(String value) {
        return value.isEmpty() ? Optional.empty() : Optional.of(value);
    }

    private synchronized List<Row> rows(String wmi) {
        List<Row> existing = cache.get(wmi);
        if (existing != null) return existing;
        Shard shard = shards.get(wmi);
        if (shard == null) return List.of();
        List<Row> result = new ArrayList<>();
        try {
            byte[] compressed = BundledResources.read(ROOT + shard.path());
            BundledResources.verify(compressed, shard.sha256());
            try (var stream = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
                String content = new String(stream.readAllBytes(), StandardCharsets.UTF_8);
                for (String line : content.split("\n")) {
                    String[] c = line.split("\t", -1);
                    if (c.length != 4 + definitions.size())
                        throw new IllegalStateException("Malformed ASTRA approval record");
                    Map<String, String> fields = new LinkedHashMap<>();
                    int column = 4;
                    for (String key : definitions.keySet()) {
                        String value = c[column++];
                        if (!value.isEmpty()) fields.put(key, text(value));
                    }
                    List<String> patterns = List.of(c[3].split(",", -1));
                    if (patterns.stream().anyMatch(pattern -> !pattern.matches("[A-HJ-NPR-Z0-9.]{17}")))
                        throw new IllegalStateException("Malformed ASTRA VIN mask");
                    result.add(new Row(c[0], Integer.parseInt(c[1]), text(c[2]), patterns,
                            Collections.unmodifiableMap(fields)));
                }
            }
        } catch (IOException e) {
            throw new IllegalStateException("Cannot load bundled ASTRA approval patterns", e);
        }
        List<Row> immutable = List.copyOf(result);
        cache.put(wmi, immutable);
        if (cache.size() > 8) cache.remove(cache.keySet().iterator().next());
        return immutable;
    }

    TypeApprovals decode(String vin, Structure structure) {
        List<Candidate> candidates = new ArrayList<>();
        if (structure == Structure.MODERN_FORMAT) {
            for (Row row : rows(vin.substring(0, 3))) {
                List<String> matched = row.patterns().stream().filter(pattern -> matches(pattern, vin)).toList();
                if (!matched.isEmpty()) candidates.add(new Candidate(row.id(), source.id(), row.number(),
                        row.original(), matched, row.fields()));
            }
        }
        Map<String, Field> fields = new LinkedHashMap<>();
        definitions.forEach((key, definition) -> {
            if (key.equals("remarks")) return;
            var values = new TreeSet<String>();
            for (Candidate candidate : candidates) {
                String value = candidate.fields().get(key);
                if (value != null) values.add(value);
            }
            if (!values.isEmpty()) fields.put(key, new Field(definition.label(), definition.sourceColumn(),
                    definition.unit(), new ArrayList<>(values)));
        });
        return new TypeApprovals(structure != Structure.MODERN_FORMAT ? "INVALID_INPUT"
                : candidates.isEmpty() ? "NO_MATCH" : "CANDIDATES", Optional.of(dataset), RuntimePolicy.get().text("catalogue.market"),
                candidates.isEmpty() ? List.of() : RuntimePolicy.get().strings("catalogue.warnings"), fields, candidates,
                candidates.isEmpty() ? List.of() : List.of(source));
    }

    private static boolean matches(String pattern, String vin) {
        for (int i = 0; i < 17; i++) {
            char expected = pattern.charAt(i);
            if (expected != '.' && expected != vin.charAt(i)) return false;
        }
        return true;
    }

    private record Definition(String label, String sourceColumn, String unit) { }
    private record Shard(String path, String sha256) { }
    private record Row(String id, int number, String original, List<String> patterns, Map<String, String> fields) { }
}
