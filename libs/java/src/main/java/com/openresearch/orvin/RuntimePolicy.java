package com.openresearch.orvin;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.IntStream;

/** Typed scalar tables emitted by the dataset compiler. */
final class RuntimePolicy {
    private final Map<String, String> values = new HashMap<>();
    private static final class Holder { private static final RuntimePolicy INSTANCE = new RuntimePolicy(); }
    static RuntimePolicy get() { return Holder.INSTANCE; }
    private RuntimePolicy() {
        try {
            for (String line : new String(BundledResources.read("/META-INF/orvin/policy.tsv"), StandardCharsets.UTF_8).split("\n")) {
                String[] c = line.split("\t", -1);
                values.put(c[0], c[1].equals("S") ? new String(Base64.getDecoder().decode(c[2]), StandardCharsets.UTF_8) : c[2]);
            }
        } catch (IOException e) { throw new IllegalStateException("Cannot load runtime policy", e); }
    }
    String text(String key) {
        String value = values.get(key);
        if (value == null) throw new IllegalStateException("Missing runtime policy: " + key);
        return value;
    }
    int number(String key) { return Integer.parseInt(text(key)); }
    boolean bool(String key) { return Boolean.parseBoolean(text(key)); }
    List<String> strings(String key) { return IntStream.range(0, number(key + ".length")).mapToObj(i -> text(key + "." + i)).toList(); }
    List<Integer> numbers(String key) { return strings(key).stream().map(Integer::valueOf).toList(); }
}
