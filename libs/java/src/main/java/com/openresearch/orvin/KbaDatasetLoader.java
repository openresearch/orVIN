package com.openresearch.orvin;

import com.openresearch.orvin.HsnTsnLookup.DatasetInfo;
import com.openresearch.orvin.HsnTsnLookup.Source;
import com.openresearch.orvin.HsnTsnLookup.TypeEntry;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.StringReader;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

final class KbaDatasetLoader {
    private KbaDatasetLoader() { }

    static HsnTsnLookup load() {
        try {
            String[] m = new String(BundledResources.read("/com/openresearch/orvin/kba-metadata.tsv"),
                    StandardCharsets.UTF_8).stripTrailing().split("\t", -1);
            if (m.length != 14) throw new IllegalStateException("Invalid KBA metadata");
            BundledResources.verify(BundledResources.read("/META-INF/orvin/kba/metadata.json"), m[13]);
            DatasetInfo info = new DatasetInfo(m[0], m[1], LocalDate.parse(m[2]), Integer.parseInt(m[3]),
                    new Source(m[4], m[5], URI.create(m[6]), URI.create(m[7]), LocalDate.parse(m[8]),
                            m[9], URI.create(m[10]), m[11], m[12]));
            byte[] table = BundledResources.read("/META-INF/orvin/kba/types.tsv");
            BundledResources.verify(table, info.sha256());
            List<TypeEntry> entries = new ArrayList<>(info.recordCount());
            try (BufferedReader reader = new BufferedReader(new StringReader(new String(table, StandardCharsets.UTF_8)))) {
                if (!"hsn\ttsn\tmanufacturer\ttradeName\tregisteredCount\tcountMarker\tsourceObjectId".equals(reader.readLine()))
                    throw new IllegalStateException("Invalid KBA table header");
                for (String line; (line = reader.readLine()) != null;) {
                    String[] c = line.split("\t", -1);
                    if (c.length != 7) throw new IllegalStateException("Invalid KBA table row");
                    entries.add(new TypeEntry(c[0], c[1], optional(c[2]), optional(c[3]),
                            optional(c[4]).map(Long::valueOf), optional(c[5]), Long.parseLong(c[6])));
                }
            }
            if (entries.size() != info.recordCount()) throw new IllegalStateException("Incomplete KBA table");
            return new HsnTsnLookup(info, entries);
        } catch (IOException | RuntimeException e) {
            throw new IllegalStateException("Cannot load the bundled KBA dataset", e);
        }
    }

    private static Optional<String> optional(String value) {
        return value.equals("\\N") ? Optional.empty() : Optional.of(value);
    }
}
