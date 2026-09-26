package com.openresearch.orvin;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Base64;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import static com.openresearch.orvin.JsonValues.*;

/** Exact source-label identities shared with Python. */
final class IdentityCatalogue {
    private static final List<String> SOURCE_KEYS = List.of("id", "publisher", "title", "url", "edition", "section", "retrievedOn", "reuseBasis", "license", "termsUrl", "modifications", "archiveSha256", "inspectedSha256", "evidencePath");
    final Map<String, Map<String, Object>> makes = new LinkedHashMap<>();
    final Map<String, Map<String, Object>> models = new LinkedHashMap<>();
    final Map<String, Map<String, Object>> sources = new LinkedHashMap<>();
    final Map<String, Object> metadata;
    private static final class Holder { static final IdentityCatalogue INSTANCE = new IdentityCatalogue(); }
    static IdentityCatalogue bundled() { return Holder.INSTANCE; }
    static String key(Object value) {
        if (value == null) return "";
        String text = value.toString().strip();
        StringBuilder out = new StringBuilder();
        for (char c : text.toCharArray()) out.append(c >= 'a' && c <= 'z' ? (char) (c - 32) : c);
        return out.toString();
    }
    static String id(Object value) {
        try {
            byte[] bytes = MessageDigest.getInstance("SHA-256").digest(json(value).getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(bytes).substring(0, 24);
        } catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
    }
    private static String text(String base64) { return new String(Base64.getDecoder().decode(base64), StandardCharsets.UTF_8); }
    private IdentityCatalogue() {
        try {
            String[] meta = new String(BundledResources.read("identity-metadata.tsv"), StandardCharsets.UTF_8).strip().split("\t");
            byte[] bytes = BundledResources.read("/META-INF/orvin/identity/index.tsv");
            BundledResources.verify(bytes, meta[1]);
            metadata = map("version", meta[0], "sha256", meta[1]);
            for (String line : new String(bytes, StandardCharsets.UTF_8).split("\n")) {
                String[] c = line.split("\t", -1);
                if (c[0].equals("S")) {
                    Map<String, Object> source = new LinkedHashMap<>();
                    for (int i = 0; i < SOURCE_KEYS.size(); i++) {
                        String value = text(c[i + 1]);
                        source.put(SOURCE_KEYS.get(i), value.isEmpty() ? null : value);
                    }
                    sources.put(string(source.get("id")), source);
                } else if (c[0].equals("M") || c[0].equals("D")) {
                    int offset = c[0].equals("M") ? 1 : 2;
                    String alias = text(c[offset]);
                    Map<String, Object> row = map("id", c[offset + 1], "name", text(c[offset + 2]), "sourceId", c[offset + 3],
                            "locator", text(c[offset + 4]), "original", alias,
                            "ruleId", "identity:" + id(List.of(c[0], c[0].equals("D") ? c[1] : "", alias)));
                    if (c[0].equals("M")) makes.put(alias, row);
                    else models.put(c[1] + "\u0000" + alias, row);
                } else if (!c[0].equals("V") || !c[1].equals(meta[0])) {
                    throw new IllegalStateException("Invalid identity catalogue record/version");
                }
            }
        } catch (IOException e) { throw new IllegalStateException("Cannot load ORvin identity catalogue", e); }
    }
    Map<String, Object> make(Object name) { return makes.get(key(name)); }
    Map<String, Object> model(Object makeId, Object name) { return models.get(string(makeId) + "\u0000" + key(name)); }
}
