package com.openresearch.orvin;

import java.util.Collections;
import java.util.Map;
import java.util.Optional;
import static com.openresearch.orvin.JsonValues.*;

/** One normalized answer, exposed as immutable short and extended JSON-compatible values. */
public final class VehicleAnswer {
    private final Map<String, Object> shortResult;
    private final Map<String, Object> longResult;
    VehicleAnswer(Map<String, Object> summary, Map<String, Object> details) {
        shortResult = Collections.unmodifiableMap(object(tree(summary)));
        Map<String, Object> full = object(shortResult);
        full.put("details", tree(details));
        longResult = Collections.unmodifiableMap(full);
    }
    public Map<String, Object> shortResult() { return shortResult; }
    public Map<String, Object> longResult() { return longResult; }
    public String toShortJson() { return json(shortResult); }
    public String toLongJson() { return json(longResult); }
    public Vehicle vehicle() {
        Map<String, Object> v = object(shortResult.get("vehicle"));
        return new Vehicle(text(v, "makeId"), text(v, "make"), text(v, "modelId"), text(v, "model"),
                year(v, "modelYear"), year(v, "productionYear"));
    }
    private static Optional<String> text(Map<String, Object> v, String key) { return Optional.ofNullable(string(v.get(key))); }
    private static Optional<Integer> year(Map<String, Object> v, String key) {
        return Optional.ofNullable(v.get(key)).map(n -> ((Number) n).intValue());
    }
    /** Primary identity; model year and production year deliberately remain separate. */
    public record Vehicle(Optional<String> makeId, Optional<String> make, Optional<String> modelId,
                          Optional<String> model, Optional<Integer> modelYear, Optional<Integer> productionYear) { }
    public static VehicleAnswer from(VinDecoder.Result result) { return new AnswerBuilder(object(tree(result)), true).resolve(); }
    public static VehicleAnswer from(HsnTsnLookup.Result result) { return new AnswerBuilder(object(tree(result)), false).resolve(); }
}
