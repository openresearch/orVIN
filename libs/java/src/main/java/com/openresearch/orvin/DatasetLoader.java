package com.openresearch.orvin;

import com.openresearch.orvin.VinDecoder.Assignment;
import com.openresearch.orvin.VinDecoder.Category;
import com.openresearch.orvin.VinDecoder.Constraints;
import com.openresearch.orvin.VinDecoder.DatasetInfo;
import com.openresearch.orvin.VinDecoder.Manufacturer;
import com.openresearch.orvin.VinDecoder.Source;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/** Reads only the internal build-generated resource. This format is not a public interchange API. */
final class DatasetLoader {
    private DatasetLoader() { }

    static VinDecoder load() {
        Map<String, Source> sources = new HashMap<>();
        Map<String, Manufacturer> manufacturers = new HashMap<>();
        List<Assignment> assignments = new ArrayList<>();
        DatasetInfo info = null;
        try (InputStream stream = new java.io.ByteArrayInputStream(BundledResources.read("dataset.tsv"));
             BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            for (String line; (line = reader.readLine()) != null;) {
                String[] c = line.split("\t", -1);
                switch (c[0]) {
                    case "V" -> info = new DatasetInfo(c[1], c[2]);
                    case "S" -> sources.put(c[1], new Source(c[1], c[2], URI.create(c[3]), c[4],
                            LocalDate.parse(c[5]), c[6], c[7], c[8], URI.create(c[9]), c[10],
                            optional(c[11]), optional(c[12])));
                    case "M" -> manufacturers.put(c[1], new Manufacturer(c[1], c[2], optional(c[3]), refs(c[4], sources)));
                    case "A" -> assignments.add(new Assignment(c[1], c[2],
                            Objects.requireNonNull(manufacturers.get(c[3])), optional(c[4]),
                            optional(c[5]).map(Category::valueOf),
                            new Constraints(c[7].isEmpty() ? Set.of() : Set.copyOf(Arrays.asList(c[7].split(","))),
                                    optional(c[8]).map(Integer::valueOf), optional(c[9]).map(Integer::valueOf)),
                            refs(c[6], sources), c[10], optional(c[11]), optional(c[12])));
                    default -> throw new IllegalStateException("Unknown bundled dataset record: " + c[0]);
                }
            }
        } catch (IOException | RuntimeException e) {
            throw new IllegalStateException("Cannot load the bundled Orvin dataset", e);
        }
        Objects.requireNonNull(info, "Dataset metadata missing");
        return new VinDecoder(info, assignments, RichDecoder.load(), ApprovalDecoder.load());
    }

    private static Optional<String> optional(String value) {
        return value.isEmpty() ? Optional.empty() : Optional.of(value);
    }

    private static List<Source> refs(String ids, Map<String, Source> sources) {
        return Arrays.stream(ids.split(",")).map(id -> Objects.requireNonNull(sources.get(id), id)).toList();
    }
}
