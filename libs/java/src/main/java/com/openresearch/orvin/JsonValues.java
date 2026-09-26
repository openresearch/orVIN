package com.openresearch.orvin;

import java.lang.reflect.RecordComponent;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;

/** Internal JSON value conversion for immutable public DTOs; no runtime JSON dependency. */
final class JsonValues {
    private JsonValues() { }
    static Map<String, Object> map(Object... pairs) {
        Map<String, Object> result = new LinkedHashMap<>();
        for (int i = 0; i < pairs.length; i += 2) result.put((String) pairs[i], pairs[i + 1]);
        return result;
    }
    static Map<String, Object> object(Object value) {
        Map<String, Object> result = new LinkedHashMap<>();
        if (value == null) return result;
        if (!(value instanceof Map<?, ?> entries)) throw new IllegalArgumentException("Expected an object");
        entries.forEach((k, v) -> result.put((String) k, v));
        return result;
    }
    static List<Object> list(Object value) {
        return value == null ? List.of() : new ArrayList<>((Collection<?>) value);
    }
    static String string(Object value) { return value == null ? null : value.toString(); }
    static Object tree(Object value) {
        if (value == null || value instanceof String || value instanceof Number || value instanceof Boolean) return value;
        if (value instanceof Optional<?> optional) return tree(optional.orElse(null));
        if (value instanceof Set<?> set) return tree(set.stream().map(Object::toString).sorted().toList());
        if (value instanceof Collection<?> collection) return collection.stream().map(JsonValues::tree).toList();
        if (value instanceof Map<?, ?> entries) {
            Map<String, Object> out = new LinkedHashMap<>();
            entries.forEach((k, v) -> out.put((String) k, tree(v)));
            return Collections.unmodifiableMap(out);
        }
        if (value.getClass().isRecord()) {
            Map<String, Object> out = new LinkedHashMap<>();
            try {
                for (RecordComponent component : value.getClass().getRecordComponents())
                    out.put(component.getName(), tree(component.getAccessor().invoke(value)));
            } catch (ReflectiveOperationException e) {
                throw new IllegalStateException("Cannot read ORvin result record", e);
            }
            if (value instanceof VinDecoder.Result r) {
                out.put("brand", tree(r.brand()));
            }
            if (value instanceof VehicleDetails.Field f) out.put("value", tree(f.value()));
            return Collections.unmodifiableMap(out);
        }
        return value.toString();
    }
    static String json(Object value) {
        if (value == null) return "null";
        if (value instanceof Number || value instanceof Boolean) return value.toString();
        if (value instanceof Map<?, ?>) {
            StringBuilder out = new StringBuilder("{");
            for (var entry : new TreeMap<>(object(value)).entrySet()) {
                if (out.length() > 1) out.append(',');
                out.append(json(entry.getKey())).append(':').append(json(entry.getValue()));
            }
            return out.append('}').toString();
        }
        if (value instanceof Collection<?> collection) {
            StringBuilder out = new StringBuilder("[");
            for (Object item : collection) {
                if (out.length() > 1) out.append(',');
                out.append(json(item));
            }
            return out.append(']').toString();
        }
        StringBuilder out = new StringBuilder("\"");
        for (char c : value.toString().toCharArray()) {
            switch (c) {
                case '"', '\\' -> out.append('\\').append(c);
                case '\b' -> out.append("\\b");
                case '\f' -> out.append("\\f");
                case '\n' -> out.append("\\n");
                case '\r' -> out.append("\\r");
                case '\t' -> out.append("\\t");
                default -> {
                    if (c < 32 || c > 126) out.append(String.format("\\u%04x", (int) c));
                    else out.append(c);
                }
            }
        }
        return out.append('"').toString();
    }
}
