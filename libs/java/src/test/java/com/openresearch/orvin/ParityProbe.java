package com.openresearch.orvin;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.lang.reflect.RecordComponent;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

/** Test-only JSON adapter: compare the complete public Java result to the Python result. */
public final class ParityProbe {
    private ParityProbe() { }

    public static void main(String[] args) throws Exception {
        try (var input = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8))) {
            for (String line; (line = input.readLine()) != null;) {
                String[] c = line.split("\t", -1);
                Object result = c[0].equals("vin")
                        ? VinDecoder.bundled().decode(decode(c[1]), new VinDecoder.Context(
                                c[2].isEmpty() ? Optional.empty() : Optional.of(Integer.valueOf(c[2])),
                                c[3].isEmpty() ? Optional.empty() : Optional.of(c[3])))
                        : HsnTsnLookup.bundled().lookup(decode(c[1]), decode(c[2]));
                System.out.println(json(result));
            }
        }
    }

    private static String decode(String value) {
        return new String(Base64.getDecoder().decode(value), StandardCharsets.UTF_8);
    }

    private static String json(Object value) throws ReflectiveOperationException {
        if (value == null) return "null";
        if (value instanceof Optional<?> optional) return json(optional.orElse(null));
        if (value instanceof Number || value instanceof Boolean) return value.toString();
        if (value instanceof Set<?> set) return json(set.stream().map(Object::toString).sorted().toList());
        if (value instanceof Collection<?> collection) {
            StringBuilder out = new StringBuilder("[");
            for (Object item : collection) {
                if (out.length() > 1) out.append(',');
                out.append(json(item));
            }
            return out.append(']').toString();
        }
        if (value.getClass().isRecord()) {
            Map<String, Object> fields = new LinkedHashMap<>();
            for (RecordComponent c : value.getClass().getRecordComponents())
                fields.put(c.getName(), c.getAccessor().invoke(value));
            if (value instanceof VinDecoder.Result r) {
                fields.put("manufacturer", r.manufacturer());
                fields.put("brand", r.brand());
                fields.put("category", r.category());
                fields.put("manufacturerCountry", r.manufacturerCountry());
                fields.put("assemblyCountry", r.assemblyCountry());
            }
            if (value instanceof VinDecoder.Resolution<?> r) fields.put("value", r.value());
            if (value instanceof HsnTsnLookup.Result r) fields.put("value", r.value());
            StringBuilder out = new StringBuilder("{");
            for (var field : fields.entrySet()) {
                if (out.length() > 1) out.append(',');
                out.append(json(field.getKey())).append(':').append(json(field.getValue()));
            }
            return out.append('}').toString();
        }
        StringBuilder out = new StringBuilder("\"");
        for (char c : value.toString().toCharArray()) {
            if (c == '\\' || c == '"') out.append('\\').append(c);
            else if (c < 32 || c > 126) out.append(String.format("\\u%04x", (int) c));
            else out.append(c);
        }
        return out.append('"').toString();
    }
}
