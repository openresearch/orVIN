package com.openresearch.orvin;

import java.io.IOException;
import java.io.InputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Objects;

final class BundledResources {
    private BundledResources() { }

    static byte[] read(String path) throws IOException {
        try (InputStream stream = Objects.requireNonNull(BundledResources.class.getResourceAsStream(path),
                "Missing bundled resource: " + path)) {
            return stream.readAllBytes();
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
