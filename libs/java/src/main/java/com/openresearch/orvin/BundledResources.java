package com.openresearch.orvin;

import java.io.IOException;
import java.io.InputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Objects;
import java.util.Map;
import java.util.HashMap;
import java.util.Set;
import java.nio.charset.StandardCharsets;

final class BundledResources {
    private BundledResources() { }

    static byte[] read(String path) throws IOException {
        String resolved = path.startsWith("/") ? path : "/META-INF/orvin/" + path;
        byte[] content = raw(resolved);
        if (resolved.startsWith("/META-INF/orvin/")) {
            String name = resolved.substring("/META-INF/orvin/".length());
            verify(content, Manifest.HASHES.get(name));
        }
        return content;
    }

    private static byte[] raw(String path) throws IOException {
        try (InputStream stream = Objects.requireNonNull(BundledResources.class.getResourceAsStream(path),
                "Missing bundled resource: " + path)) {
            return stream.readAllBytes();
        }
    }

    private static final class Manifest {
        private static final Map<String, String> HASHES = load();
        private static Map<String, String> load() {
            Set<String> capabilities = Set.of("patterns", "conditional-literals", "year-cycles", "relations",
                    "decimal-scaling", "catalogue-consensus", "cross-market");
            try {
                String[] lines = new String(raw("/META-INF/orvin/manifest.tsv"), StandardCharsets.UTF_8).split("\n");
                String[] version = lines[0].split("\t");
                if (!version[1].equals("orvin-runtime-1") || !capabilities.containsAll(java.util.List.of(version[2].split(","))))
                    throw new IllegalStateException("Unsupported ORvin runtime format/capabilities");
                Map<String, String> hashes = new HashMap<>();
                for (String line : lines) {
                    String[] c = line.split("\t", -1);
                    if (c[0].equals("F")) hashes.put(c[1], c[2]);
                }
                return Map.copyOf(hashes);
            } catch (IOException e) { throw new IllegalStateException("Missing runtime manifest", e); }
        }
    }

    static void verify(byte[] content, String expectedSha256) {
        try {
            String actual = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(content));
            if (!actual.equals(expectedSha256))
                throw new IllegalStateException("Dataset/resource mismatch; run tools/dataset.py --update-runtime");
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 unavailable", e);
        }
    }
}
