package com.openresearch.orvin;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/** Sourced vehicle facts, with separate configurations for unresolved model-year cycles. */
public record VehicleDetails(String status, Optional<VinDecoder.DatasetInfo> dataset, String marketScope,
                             int referenceYear, List<String> stages, List<String> warnings,
                             Map<String, Field> fields, List<Alternative> alternatives, List<SourceDocument> sources) {
    public VehicleDetails {
        stages = List.copyOf(stages);
        warnings = List.copyOf(warnings);
        fields = Collections.unmodifiableMap(new LinkedHashMap<>(fields));
        alternatives = List.copyOf(alternatives);
        sources = List.copyOf(sources);
    }

    /** NHTSA variable codes, for example Model, PlantCity, EngineModel and FuelTypePrimary. */
    public VinDecoder.Resolution<String> field(String code) {
        Field field = fields.get(code);
        return field == null ? new VinDecoder.Resolution<>(VinDecoder.Knowledge.UNKNOWN, List.of())
                : new VinDecoder.Resolution<>(field.status(), field.possibilities());
    }

    static VehicleDetails unavailable() {
        return new VehicleDetails("UNAVAILABLE", Optional.empty(), "US", 2026,
                List.of(), List.of(), Map.of(), List.of(), List.of());
    }

    /** Edition and exact locator for each used source; absent archive hashes are explicit. */
    public record SourceDocument(String id, String title, String publisher, String url, String edition,
                                 String section, String retrievedOn, String reuseBasis,
                                 Optional<String> archivePath, Optional<String> archiveSha256,
                                 Optional<String> inspectedSha256, String evidencePath) { }

    /** Values remain source strings, including numeric values. Only KNOWN exposes value(). */
    public record Field(String label, String dataType, VinDecoder.Knowledge status,
                        List<String> possibilities, List<Evidence> evidence) {
        public Field {
            possibilities = List.copyOf(possibilities);
            evidence = List.copyOf(evidence);
        }
        public Optional<String> value() {
            return status == VinDecoder.Knowledge.KNOWN ? Optional.of(possibilities.get(0)) : Optional.empty();
        }
    }

    /** Source row identity and derivation kind; associated/converted facts are not direct VIN characters. */
    public record Evidence(int elementId, String value, String attributeId, String sourceId, String sourceUrl, String kind,
                           String ruleId, Optional<Integer> schemaId, String keys) { }

    /** Keep these configurations separate: fields from different alternatives must not be combined. */
    public record Alternative(Optional<Integer> modelYear, String market, Map<String, List<Evidence>> fields) {
        public Alternative {
            Map<String, List<Evidence>> copy = new LinkedHashMap<>();
            fields.forEach((key, value) -> copy.put(key, List.copyOf(value)));
            fields = Collections.unmodifiableMap(copy);
        }
    }
}
