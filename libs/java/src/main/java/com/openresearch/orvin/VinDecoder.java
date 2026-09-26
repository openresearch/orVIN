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

/** Thread-safe offline manufacturer lookup and sourced vehicle decoding; never VIN authentication. */
public final class VinDecoder {
    private final DatasetInfo dataset;
    private final Map<String, List<Assignment>> byWmi;
    private final Set<String> extendedPrefixes;
    private final RichDecoder rich;
    private final ApprovalDecoder approvals;

    VinDecoder(DatasetInfo dataset, List<Assignment> assignments) {
        this(dataset, assignments, null);
    }

    VinDecoder(DatasetInfo dataset, List<Assignment> assignments, RichDecoder rich) {
        this(dataset, assignments, rich, null);
    }

    VinDecoder(DatasetInfo dataset, List<Assignment> assignments, RichDecoder rich, ApprovalDecoder approvals) {
        this.rich = rich;
        this.approvals = approvals;
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
     * internal whitespace, replace lookalikes or perform Unicode folding. Rich decoding separately
     * infers model-year candidates within documented source scope.
     * A recognized prefix may coexist with invalid characters elsewhere in the identifier.
     */
    public Result decode(String supplied, Context context) {
        Objects.requireNonNull(supplied, "supplied");
        Objects.requireNonNull(context, "context");
        String normalized = InputNormalization.normalize(supplied);
        Structure structure = assess(normalized);
        if (structure == Structure.UNSUPPORTED_LENGTH) {
            return new Result(supplied, normalized, structure, MatchStatus.UNSUPPORTED_FORMAT,
                    List.of(), dataset, context, details(normalized, structure, context), typeApprovals(normalized, structure));
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
        return new Result(supplied, normalized, structure, status, matches, dataset, context,
                details(normalized, structure, context), typeApprovals(normalized, structure));
    }

    /** Normalized identity with short and long projections of the same decision. */
    public VehicleAnswer decodeVehicle(String supplied) { return decodeVehicle(supplied, Context.unknown()); }

    public VehicleAnswer decodeVehicle(String supplied, Context context) {
        return VehicleAnswer.from(decode(supplied, context));
    }

    private VehicleDetails details(String vin, Structure structure, Context context) {
        return rich == null ? VehicleDetails.unavailable() : rich.decode(vin, structure, context);
    }

    private TypeApprovals typeApprovals(String vin, Structure structure) {
        return approvals == null ? TypeApprovals.unavailable() : approvals.decode(vin, structure);
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

    /** Caller-supplied context, distinct from separately decoded year candidates. */
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
                         List<Assignment> candidates, DatasetInfo dataset, Context context, VehicleDetails details,
                         TypeApprovals typeApprovals) {
        public Result { candidates = List.copyOf(candidates); }

        /** Compatibility constructor for results without Swiss approval candidates. */
        public Result(String supplied, String normalized, Structure structure, MatchStatus status,
                      List<Assignment> candidates, DatasetInfo dataset, Context context, VehicleDetails details) {
            this(supplied, normalized, structure, status, candidates, dataset, context, details, TypeApprovals.unavailable());
        }

        /** Compatibility constructor for manufacturer-only results. */
        public Result(String supplied, String normalized, Structure structure, MatchStatus status,
                      List<Assignment> candidates, DatasetInfo dataset, Context context) {
            this(supplied, normalized, structure, status, candidates, dataset, context, VehicleDetails.unavailable());
        }

        public Resolution<Manufacturer> manufacturer() {
            return resolve(a -> Optional.of(a.manufacturer()));
        }
        public Resolution<String> brand() {
            Resolution<String> decoded = details.field("Make");
            return decoded.status() == Knowledge.KNOWN ? decoded : resolve(Assignment::brand);
        }
        public Resolution<Category> category() { return resolve(Assignment::category); }
        public Resolution<String> manufacturerCountry() { return resolve(a -> a.manufacturer().country()); }

        public Resolution<String> model() { return details.field("Model"); }
        public Resolution<String> modelYear() { return details.field("ModelYear"); }
        /** Comes from plant patterns, never the WMI country. */
        public Resolution<String> assemblyCountry() { return details.field("PlantCountry"); }

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
