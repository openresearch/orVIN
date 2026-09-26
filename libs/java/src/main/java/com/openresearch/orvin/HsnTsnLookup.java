package com.openresearch.orvin;

import java.net.URI;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.stream.Collectors;

/** Offline German type-code lookup. A missing entry does not establish that a code is invalid. */
public final class HsnTsnLookup {
    private final DatasetInfo dataset;
    private final Map<String, List<TypeEntry>> byCode;

    HsnTsnLookup(DatasetInfo dataset, List<TypeEntry> entries) {
        this.dataset = Objects.requireNonNull(dataset);
        this.byCode = entries.stream().collect(Collectors.groupingBy(e -> e.hsn() + e.tsn(),
                Collectors.collectingAndThen(Collectors.toList(), List::copyOf)));
    }

    /** Loads the bundled reference-date snapshot once per class loader; never calls KBA. */
    public static HsnTsnLookup bundled() { return Holder.INSTANCE; }

    private static final class Holder {
        private static final HsnTsnLookup INSTANCE = KbaDatasetLoader.load();
    }

    public DatasetInfo dataset() { return dataset; }

    /**
     * Accepts a four-digit HSN and the three-character TSN, preserving leading zeroes.
     * Trims ASCII spaces at the ends and uppercases ASCII letters only. Longer registration
     * document codes are not silently truncated. Null is a programming error.
     */
    public Result lookup(String hsn, String tsn) {
        String normalizedHsn = InputNormalization.normalize(Objects.requireNonNull(hsn, "hsn"));
        String normalizedTsn = InputNormalization.normalize(Objects.requireNonNull(tsn, "tsn"));
        boolean validHsn = normalizedHsn.matches("[0-9]{4}");
        boolean validTsn = normalizedTsn.matches("[A-Z0-9]{3}");
        InputStatus inputStatus = validHsn
                ? (validTsn ? InputStatus.VALID : InputStatus.INVALID_TSN)
                : (validTsn ? InputStatus.INVALID_HSN : InputStatus.INVALID_HSN_AND_TSN);
        List<TypeEntry> entries = inputStatus == InputStatus.VALID
                ? byCode.getOrDefault(normalizedHsn + normalizedTsn, List.of()) : List.of();
        MatchStatus status = inputStatus != InputStatus.VALID ? MatchStatus.INVALID_INPUT
                : entries.isEmpty() ? MatchStatus.UNKNOWN
                : entries.size() == 1 ? MatchStatus.RECOGNIZED : MatchStatus.AMBIGUOUS;
        return new Result(hsn, tsn, normalizedHsn, normalizedTsn, inputStatus, status, entries, dataset);
    }

    /** Normalized answer for independently supplied type codes. */
    public VehicleAnswer lookupVehicle(String hsn, String tsn) {
        return VehicleAnswer.from(lookup(hsn, tsn));
    }

    public enum InputStatus { VALID, INVALID_HSN, INVALID_TSN, INVALID_HSN_AND_TSN }
    public enum MatchStatus { RECOGNIZED, UNKNOWN, AMBIGUOUS, INVALID_INPUT }

    /** KBA labels are preserved, without splitting model alternatives or linking names to WMI identities. */
    public record TypeEntry(String hsn, String tsn, Optional<String> manufacturer,
                            Optional<String> tradeName, Optional<Long> registeredCount,
                            Optional<String> countMarker, long sourceObjectId) { }

    /** Population counts apply only to referenceDate, which is not a model or production year. */
    public record DatasetInfo(String version, String sha256, LocalDate referenceDate,
                              int recordCount, Source source) { }

    /** Attribution and modifications must travel with redistributed KBA data. */
    public record Source(String title, String publisher, URI url, URI serviceUrl,
                         LocalDate retrievedOn, String license, URI licenseUrl,
                         String modifications, String snapshotSha256) { }

    /** All matching source rows are retained. Empty and ambiguous results do not select a type. */
    public record Result(String suppliedHsn, String suppliedTsn, String normalizedHsn,
                         String normalizedTsn, InputStatus inputStatus, MatchStatus status,
                         List<TypeEntry> candidates, DatasetInfo dataset) {
        public Result { candidates = List.copyOf(candidates); }
        public Optional<TypeEntry> value() {
            return status == MatchStatus.RECOGNIZED ? Optional.of(candidates.get(0)) : Optional.empty();
        }
    }
}
