package com.openresearch.orvin;

import static com.openresearch.orvin.HsnTsnLookup.*;
import static org.junit.jupiter.api.Assertions.*;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;

class HsnTsnLookupTest {
    private final HsnTsnLookup lookup = HsnTsnLookup.bundled();

    @TestFactory
    Stream<DynamicTest> reviewedSourceFixtures() throws Exception {
        try (var reader = new BufferedReader(new InputStreamReader(Objects.requireNonNull(
                getClass().getResourceAsStream("/kba-fixtures.tsv")), StandardCharsets.UTF_8))) {
            return reader.lines().map(line -> line.split("\t", -1)).toList().stream()
                    .map(c -> DynamicTest.dynamicTest(c[0] + "/" + c[1], () -> {
                        Result result = lookup.lookup(c[0], c[1]);
                        assertEquals(MatchStatus.RECOGNIZED, result.status());
                        assertEquals(new TypeEntry(c[0], c[1], optional(c[2]), optional(c[3]),
                                optional(c[4]).map(Long::valueOf), optional(c[5]), Long.parseLong(c[6])),
                                result.value().orElseThrow());
                        assertEquals(LocalDate.of(2026, 1, 1), result.dataset().referenceDate());
                        assertEquals("dl-de/by-2-0", result.dataset().source().license());
                    }));
        }
    }

    @Test
    void preservesLeadingZeroesAndOnlyNormalizesAsciiSpacesAndCase() {
        Result result = lookup.lookup(" 0005 ", "amq");
        assertEquals(" 0005 ", result.suppliedHsn());
        assertEquals("amq", result.suppliedTsn());
        assertEquals("0005", result.normalizedHsn());
        assertEquals("AMQ", result.normalizedTsn());
        assertEquals(MatchStatus.RECOGNIZED, result.status());
    }

    @Test
    void rejectsMalformedCodesInsteadOfTruncatingOrPadding() {
        assertEquals(InputStatus.INVALID_HSN, lookup.lookup("5", "AMQ").inputStatus());
        assertEquals(InputStatus.INVALID_HSN, lookup.lookup("０００５", "AMQ").inputStatus());
        for (String tsn : List.of("AMQ12345", "aſq", "\tAMQ", "A Q")) {
            Result result = lookup.lookup("0005", tsn);
            assertEquals(InputStatus.INVALID_TSN, result.inputStatus());
            assertEquals(MatchStatus.INVALID_INPUT, result.status());
            assertTrue(result.value().isEmpty());
        }
        assertEquals(InputStatus.INVALID_HSN_AND_TSN, lookup.lookup("", "").inputStatus());
        assertThrows(NullPointerException.class, () -> lookup.lookup(null, "AMQ"));
    }

    @Test
    void missingEntriesRemainUnknown() {
        Result result = lookup.lookup("9999", "ZZZ");
        assertEquals(InputStatus.VALID, result.inputStatus());
        assertEquals(MatchStatus.UNKNOWN, result.status());
        assertTrue(result.candidates().isEmpty());
        assertTrue(result.value().isEmpty());
    }

    @Test
    void duplicateKeysRetainEveryCandidateAndStatisticalMarkers() {
        TypeEntry a = new TypeEntry("0005", "AMQ", Optional.of("Synthetic"), Optional.empty(),
                Optional.empty(), Optional.of("."), 1);
        TypeEntry b = new TypeEntry("0005", "AMQ", Optional.of("Synthetic"), Optional.of("Alternative"),
                Optional.empty(), Optional.of("."), 2);
        Result result = new HsnTsnLookup(lookup.dataset(), List.of(a, b)).lookup("0005", "AMQ");
        assertEquals(MatchStatus.AMBIGUOUS, result.status());
        assertEquals(List.of(a, b), result.candidates());
        assertTrue(result.value().isEmpty());
        assertTrue(result.candidates().get(0).registeredCount().isEmpty());
        assertEquals(".", result.candidates().get(0).countMarker().orElseThrow());
        assertThrows(UnsupportedOperationException.class, () -> result.candidates().clear());
    }

    private static Optional<String> optional(String value) {
        return value.equals("\\N") ? Optional.empty() : Optional.of(value);
    }
}
