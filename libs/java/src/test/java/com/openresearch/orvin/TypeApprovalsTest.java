package com.openresearch.orvin;

import static org.junit.jupiter.api.Assertions.*;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;

class TypeApprovalsTest {
    private final VinDecoder decoder = VinDecoder.bundled();

    @Test
    void independentBydPrefixEvidenceRemainsACandidateWithItsSourceAndRemarks() {
        // CEM BYD SEAL September 2025 p.1 independently corroborates LGXC, SEAL and EKE approval.
        // Remaining characters are synthetic and exercise the more detailed ASTRA ABJ201 mask.
        var result = decoder.decode("LGXCF6AD000000001", new VinDecoder.Context(Optional.empty(), Optional.of("DE")));
        var approvals = result.typeApprovals();
        assertEquals("CANDIDATES", approvals.status());
        assertEquals("CH", approvals.marketScope());
        assertTrue(approvals.dataset().isPresent());
        var candidate = approvals.candidates().stream().filter(c -> c.approvalId().equals("ABJ201")).findFirst().orElseThrow();
        assertEquals("BYD", candidate.fields().get("make"));
        assertEquals("SEAL", candidate.fields().get("type"));
        assertEquals("e13*2018/858-2018/858*00639", candidate.fields().get("euApproval"));
        assertEquals("LGXCF6.D.........", candidate.vinPattern());
        assertEquals(List.of("LGXCF6.D........."), candidate.matchedPatterns());
        assertTrue(candidate.sourceRow() > 1);
        assertTrue(candidate.fields().get("remarks").contains("e13*2018/858*00639*00"));
        assertFalse(approvals.fields().containsKey("remarks"));
        assertFalse(approvals.warnings().isEmpty());
        var source = approvals.sources().stream().filter(s -> s.id().equals(candidate.sourceId())).findFirst().orElseThrow();
        assertTrue(source.url().endsWith("TG-Automobil.txt"));
        assertTrue(source.archiveSha256().orElseThrow().matches("[0-9a-f]{64}"));
        assertFalse(source.reuseBasis().isBlank());
        assertTrue(result.model().value().isEmpty(), "Approval names must not become decoded model facts");
    }

    @Test
    void broadGolfPatternKeepsAllConfigurationsAndDoesNotOverrideOemFacts() {
        var result = decoder.decode("WVWZZZ1KZ5P000001");
        var approvals = result.typeApprovals();
        assertTrue(approvals.candidates().size() > 100, "Do not truncate broad candidate sets");
        assertTrue(approvals.fields().get("engineCode").possibilities().size() > 1);
        assertEquals("Golf", result.model().value().orElseThrow());
        assertEquals("2005", result.modelYear().value().orElseThrow());
        assertFalse(result.details().fields().containsKey("EngineModel"));
        for (var candidate : approvals.candidates()) {
            assertFalse(candidate.matchedPatterns().isEmpty());
            candidate.fields().forEach((key, value) -> {
                if (!key.equals("remarks")) assertTrue(approvals.fields().get(key).possibilities().contains(value));
            });
        }
        // The recorded approval row is retained as a correlated configuration.
        var row = approvals.candidates().stream().filter(c -> c.approvalId().equals("1VD226")).findFirst().orElseThrow();
        assertEquals("BCA", row.fields().get("engineCode"));
        assertEquals("1390", row.fields().get("displacementCc"));
        assertEquals("55", row.fields().get("powerKw"));
    }

    @Test
    void explicitAlternativesKeepOriginalTextAndExcludedShortPrefixesStayExcluded() {
        for (String vin : List.of("WAPB333L00ME44001", "WAPB333L00UE46001")) {
            var approvals = decoder.decode(vin).typeApprovals();
            var row = approvals.candidates().stream().filter(c -> c.approvalId().equals("1AF712")).findFirst().orElseThrow();
            assertEquals("WAPB333L0.ME44... / WAPB333L0.UE46...", row.vinPattern());
            assertEquals(1, row.matchedPatterns().size());
            assertEquals(vin.substring(10, 14), row.matchedPatterns().get(0).substring(10, 14));
        }
        assertTrue(decoder.decode("VF3LBYHYP00000001").typeApprovals().candidates().stream()
                .noneMatch(c -> c.approvalId().equals("1PD453")), "Initial projection excludes short legacy patterns");
    }

    @Test
    void invalidUnknownAndCustomDecodersExposeDistinctEmptyStates() {
        for (String vin : List.of("", "LGX", "LGXCF6ID000000001", "LGXCF6AD00000000😀")) {
            var result = decoder.decode(vin).typeApprovals();
            assertEquals("INVALID_INPUT", result.status());
            assertTrue(result.candidates().isEmpty());
            assertTrue(result.fields().isEmpty());
            assertTrue(result.sources().isEmpty());
        }
        var unknown = decoder.decode("ZZZ00000000000000").typeApprovals();
        assertEquals("NO_MATCH", unknown.status());
        assertTrue(unknown.warnings().isEmpty());
        var custom = new VinDecoder(new VinDecoder.DatasetInfo("custom", "unused"), List.of());
        var result = custom.decode("LGXCF6AD000000001");
        assertEquals("UNAVAILABLE", result.typeApprovals().status());
        assertTrue(result.typeApprovals().dataset().isEmpty());
        var compatible = new VinDecoder.Result(result.supplied(), result.normalized(), result.structure(), result.status(),
                result.candidates(), result.dataset(), result.context(), result.details());
        assertEquals("UNAVAILABLE", compatible.typeApprovals().status());
    }

    @Test
    void nestedCollectionsAreImmutableAndConcurrentDecodingKeepsCandidatesSeparate() {
        var result = decoder.decode("LGXCF6AD000000001").typeApprovals();
        assertThrows(UnsupportedOperationException.class, () -> result.candidates().clear());
        assertThrows(UnsupportedOperationException.class, () -> result.fields().clear());
        assertThrows(UnsupportedOperationException.class, () -> result.sources().clear());
        assertThrows(UnsupportedOperationException.class, () -> result.warnings().clear());
        assertThrows(UnsupportedOperationException.class, () -> result.fields().get("make").possibilities().clear());
        assertThrows(UnsupportedOperationException.class, () -> result.candidates().get(0).fields().clear());
        assertThrows(UnsupportedOperationException.class, () -> result.candidates().get(0).matchedPatterns().clear());
        Map<String, String> expected = Map.of("LGXCF6AD000000001", "ABJ201", "WVWZZZ1KZ5P000001", "1VD226",
                "VF3LBYHYP00000001", "1PD183", "WAPB333L00ME44001", "1AF712");
        java.util.stream.IntStream.range(0, 16).parallel().forEach(i -> expected.forEach((vin, approval) ->
                assertTrue(decoder.decode(vin).typeApprovals().candidates().stream().anyMatch(c -> c.approvalId().equals(approval)))));
    }
}
