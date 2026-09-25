package com.openresearch.orvin;

import java.net.URI;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

/** Immutable, thread-safe offline manufacturer lookup. A lookup never establishes VIN validity. */
public final class VinDecoder {
    private final DatasetInfo dataset;
    private final Map<String, List<Assignment>> byWmi;
    private final Set<String> extendedPrefixes;

    VinDecoder(DatasetInfo dataset, List<Assignment> assignments) {
        this.dataset = Objects.requireNonNull(dataset);
        this.byWmi = assignments.stream().collect(Collectors.groupingBy(Assignment::wmi,
                Collectors.collectingAndThen(Collectors.toList(), List::copyOf)));
        this.extendedPrefixes = assignments.stream().map(Assignment::wmi).filter(w -> w.length() == 6)
                .map(w -> w.substring(0, 3)).collect(Collectors.toUnmodifiableSet());
    }

    /** Loads the bundled dataset once per class loader. No network or filesystem service is used. */
    public static VinDecoder bundled() {
        return Holder.INSTANCE;
    }

    private static final class Holder {
        private static final VinDecoder INSTANCE = DatasetLoader.load();
    }

    /** Exact dataset version and SHA-256 of the bundled canonical JSON. */
    public DatasetInfo dataset() {
        return dataset;
    }

    /** Decodes using no external model-year or market context. Null is a programming error. */
    public Result decode(String supplied) {
        return decode(supplied, Context.unknown());
    }

    /**
     * Decodes only supported 17-character layouts. Preserves the original string verbatim.
     * Matching trims ASCII space at the ends and uppercases ASCII a-z only. It does not remove
     * internal whitespace, replace lookalikes, perform Unicode folding, or infer a model year.
     * A recognized prefix may coexist with invalid characters elsewhere in the identifier.
     */
    public Result decode(String supplied, Context context) {
        Objects.requireNonNull(supplied, "supplied");
        Objects.requireNonNull(context, "context");
        String normalized = InputNormalization.normalize(supplied);
        Structure structure = assess(normalized);
        if (structure == Structure.UNSUPPORTED_LENGTH) {
            return new Result(supplied, normalized, structure, MatchStatus.UNSUPPORTED_FORMAT,
                    List.of(), dataset, context);
        }
        String prefix = normalized.substring(0, 3);
        String key = extendedPrefixes.contains(prefix) ? prefix + normalized.substring(11, 14) : prefix;
        List<Assignment> matches = byWmi.getOrDefault(key, List.of()).stream()
                .filter(a -> a.constraints().mayApply(context)).toList();
        MatchStatus status;
        if (matches.isEmpty()) {
            status = MatchStatus.UNKNOWN;
        } else if (matches.size() > 1) {
            status = MatchStatus.AMBIGUOUS;
        } else if (!matches.get(0).constraints().isEstablishedBy(context)) {
            status = MatchStatus.NEEDS_CONTEXT;
        } else {
            status = MatchStatus.RECOGNIZED;
        }
        return new Result(supplied, normalized, structure, status, matches, dataset, context);
    }

    private static Structure assess(String value) {
        if (value.length() != 17) return Structure.UNSUPPORTED_LENGTH;
        return value.matches("[A-HJ-NPR-Z0-9]{17}")
                ? Structure.MODERN_FORMAT : Structure.INVALID_CHARACTERS;
    }

    /** MODERN_FORMAT checks only length and alphabet, never checksum, authenticity or registration. */
    public enum Structure { MODERN_FORMAT, INVALID_CHARACTERS, UNSUPPORTED_LENGTH }
    public enum MatchStatus { RECOGNIZED, UNKNOWN, AMBIGUOUS, NEEDS_CONTEXT, UNSUPPORTED_FORMAT }
    public enum Knowledge { KNOWN, UNKNOWN, AMBIGUOUS, NEEDS_CONTEXT }
    public enum Category {
        PASSENGER_CAR, TRUCK, BUS, TRAILER, MOTORCYCLE, INCOMPLETE_VEHICLE,
        LOW_SPEED_VEHICLE, MULTIPURPOSE_PASSENGER_VEHICLE, OFF_ROAD_VEHICLE
    }

    /** Caller-supplied context. Model year is never read from VIN position 10. */
    public record Context(Optional<Integer> modelYear, Optional<String> market) {
        public Context {
            Objects.requireNonNull(modelYear);
            Objects.requireNonNull(market);
            if (modelYear.filter(y -> y < 1886 || y > 9999).isPresent())
                throw new IllegalArgumentException("Model year must be between 1886 and 9999");
            if (market.filter(m -> !m.matches("[A-Z]{2}")).isPresent())
                throw new IllegalArgumentException("Market must use an uppercase two-letter country code");
        }
        public static Context unknown() { return new Context(Optional.empty(), Optional.empty()); }
    }

    /** Empty constraints mean no restriction is established in the dataset, not proof of all-time validity. */
    public record Constraints(Set<String> markets, Optional<Integer> fromModelYear, Optional<Integer> toModelYear) {
        public Constraints {
            markets = Set.copyOf(markets);
            Objects.requireNonNull(fromModelYear);
            Objects.requireNonNull(toModelYear);
        }
        boolean mayApply(Context c) {
            return (c.market().isEmpty() || markets.isEmpty() || markets.contains(c.market().get()))
                    && (c.modelYear().isEmpty() || (c.modelYear().get() >= fromModelYear.orElse(1886)
                    && c.modelYear().get() <= toModelYear.orElse(9999)));
        }
        boolean isEstablishedBy(Context c) {
            return (markets.isEmpty() || c.market().isPresent())
                    && ((fromModelYear.isEmpty() && toModelYear.isEmpty()) || c.modelYear().isPresent());
        }
    }

    public record DatasetInfo(String version, String sha256) { }

    /** Reuse basis belongs to the source; the code license does not replace it. */
    public record Source(String id, String title, URI url, String publisher, LocalDate retrievedOn,
                         String publicationVersion, String section, String license, URI reuseUrl,
                         String reuseBasis, Optional<String> snapshot, Optional<String> snapshotSha256) { }

    /** Country describes the manufacturer only; it must never be used as the assembly country. */
    public record Manufacturer(String id, String name, Optional<String> country, List<Source> sources) {
        public Manufacturer { sources = List.copyOf(sources); }
    }

    /** One possible sourced assignment, including any unresolved historical or market restrictions. */
    public record Assignment(String id, String wmi, Manufacturer manufacturer, Optional<String> brand,
                             Optional<Category> category, Constraints constraints, List<Source> sources,
                             String notes, Optional<String> ambiguityGroup, Optional<String> ambiguityReason) {
        public Assignment { sources = List.copyOf(sources); }
    }

    /** Only KNOWN yields a single value. Other states can retain possibilities without selecting one. */
    public record Resolution<T>(Knowledge status, List<T> possibilities) {
        public Resolution { possibilities = List.copyOf(possibilities); }
        public Optional<T> value() {
            return status == Knowledge.KNOWN ? Optional.of(possibilities.get(0)) : Optional.empty();
        }
    }

    public record Result(String supplied, String normalized, Structure structure, MatchStatus status,
                         List<Assignment> candidates, DatasetInfo dataset, Context context) {
        public Result { candidates = List.copyOf(candidates); }

        public Resolution<Manufacturer> manufacturer() {
            return resolve(a -> Optional.of(a.manufacturer()));
        }
        public Resolution<String> brand() { return resolve(Assignment::brand); }
        public Resolution<Category> category() { return resolve(Assignment::category); }
        public Resolution<String> manufacturerCountry() { return resolve(a -> a.manufacturer().country()); }

        /** Assembly country is intentionally unsupported by this WMI-only release. */
        public Resolution<String> assemblyCountry() { return new Resolution<>(Knowledge.UNKNOWN, List.of()); }

        private <T> Resolution<T> resolve(Function<Assignment, Optional<T>> field) {
            if (candidates.isEmpty()) return new Resolution<>(Knowledge.UNKNOWN, List.of());
            Set<T> values = new LinkedHashSet<>();
            boolean missing = false;
            for (Assignment a : candidates) {
                Optional<T> value = field.apply(a);
                if (value.isPresent()) values.add(value.get());
                else missing = true;
            }
            Knowledge knowledge;
            if (values.size() > 1) knowledge = Knowledge.AMBIGUOUS;
            else if (missing) knowledge = Knowledge.UNKNOWN;
            else if (candidates.stream().anyMatch(a -> !a.constraints().isEstablishedBy(context)))
                knowledge = Knowledge.NEEDS_CONTEXT;
            else knowledge = Knowledge.KNOWN;
            return new Resolution<>(knowledge, new ArrayList<>(values));
        }
    }
}
