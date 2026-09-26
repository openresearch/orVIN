package com.openresearch.orvin;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/** Possible Swiss approved types, never established facts about an individual vehicle. */
public record TypeApprovals(String status, Optional<VinDecoder.DatasetInfo> dataset, String marketScope,
                            List<String> warnings, Map<String, Field> fields, List<Candidate> candidates,
                            List<VehicleDetails.SourceDocument> sources) {
    public TypeApprovals {
        warnings = List.copyOf(warnings);
        fields = Collections.unmodifiableMap(new LinkedHashMap<>(fields));
        candidates = List.copyOf(candidates);
        sources = List.copyOf(sources);
    }

    static TypeApprovals unavailable() {
        return new TypeApprovals("UNAVAILABLE", Optional.empty(), "CH", List.of(), Map.of(), List.of(), List.of());
    }

    /** Possible catalogue values only: even a single possibility does not establish a vehicle fact. */
    public record Field(String label, String sourceColumn, String unit, List<String> possibilities) {
        public Field { possibilities = List.copyOf(possibilities); }
    }

    /** Specifications and remarks stay attached to their approval; sourceRow includes the header row. */
    public record Candidate(String approvalId, String sourceId, int sourceRow, String vinPattern,
                            List<String> matchedPatterns, Map<String, String> fields) {
        public Candidate {
            matchedPatterns = List.copyOf(matchedPatterns);
            fields = Collections.unmodifiableMap(new LinkedHashMap<>(fields));
        }
    }
}
