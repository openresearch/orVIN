package com.openresearch.orvin;

import static com.openresearch.orvin.VinDecoder.*;
import static org.junit.jupiter.api.Assertions.*;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

class VinDecoderTest {
    private final VinDecoder decoder = VinDecoder.bundled();

    @TestFactory
    Stream<DynamicTest> sourcedAssignmentFixtures() throws Exception {
        try (var reader = new BufferedReader(new InputStreamReader(Objects.requireNonNull(
                getClass().getResourceAsStream("/fixtures.tsv")), StandardCharsets.UTF_8))) {
            return reader.lines().map(line -> line.split("\t", -1)).toList().stream()
                    .map(c -> DynamicTest.dynamicTest(c[0], () -> {
                        Result result = decoder.decode(c[1]);
                        assertEquals(MatchStatus.RECOGNIZED, result.status());
                        assertEquals(Structure.MODERN_FORMAT, result.structure());
                        assertEquals(c[2], result.manufacturer().value().orElseThrow().id());
                        assertEquals(c[3], result.candidates().get(0).wmi());
                        assertEquals(c[4], result.brand().value().orElseThrow());
                        assertEquals(Category.valueOf(c[5]), result.category().value().orElseThrow());
                        assertEquals("NHTSA", result.candidates().get(0).sources().get(0).publisher());
                    }));
        }
    }

    @Test
    void extendedIdentifiersUsePositionsTwelveThroughFourteenWithoutPrefixFallback() {
        assertEquals("hombilt-trailers", decoder.decode("1H9AAAAAAAA333AAA")
                .manufacturer().value().orElseThrow().id());
        assertEquals(MatchStatus.UNKNOWN, decoder.decode("1H9AAAAAAAAZZZAAA").status());
        assertEquals(MatchStatus.UNKNOWN, decoder.decode("1H9333AAAAAAAAAAA").status());
        assertEquals(MatchStatus.UNSUPPORTED_FORMAT, decoder.decode("1H9333").status());
    }

    @Test
    void preservesInputAndNormalizesOnlyAsciiSpaceAndLetterCase() {
        String original = "  1hgaaaaaaaaaaaaaa  ";
        Result result = decoder.decode(original);
        assertEquals(original, result.supplied());
        assertEquals("1HGAAAAAAAAAAAAAA", result.normalized());
        assertEquals(MatchStatus.RECOGNIZED, result.status());
        assertEquals(Structure.UNSUPPORTED_LENGTH, decoder.decode("\t1HGAAAAAAAAAAAAAA").structure());
        assertEquals(Structure.INVALID_CHARACTERS, decoder.decode("1HGAAAA AAAAAAAAA").structure());
        assertEquals(Structure.INVALID_CHARACTERS, decoder.decode("1HGAAAAAAAAAAAAA\u017f").structure());
    }

    @Test
    void normalizationDoesNotDependOnDefaultLocale() {
        Locale previous = Locale.getDefault();
        try {
            Locale.setDefault(Locale.forLanguageTag("tr-TR"));
            assertEquals("1HGIAAAAAAAAAAAAA", decoder.decode("1hgiaaaaaaaaaaaaa").normalized());
        } finally {
            Locale.setDefault(previous);
        }
    }

    @Test
    void structuralAssessmentAndRecognitionAreIndependent() {
        Result unknown = decoder.decode("ZZZAAAAAAAAAAAAAA");
        assertEquals(Structure.MODERN_FORMAT, unknown.structure());
        assertEquals(MatchStatus.UNKNOWN, unknown.status());
        Result badCharacter = decoder.decode("1HGIAAAAAAAAAAAAA");
        assertEquals(Structure.INVALID_CHARACTERS, badCharacter.structure());
        assertEquals(MatchStatus.RECOGNIZED, badCharacter.status());
        assertEquals(Knowledge.UNKNOWN, unknown.manufacturer().status());
        assertTrue(unknown.manufacturer().value().isEmpty());
    }

    @ParameterizedTest
    @ValueSource(strings = {"", "   ", "1HG", "1HGAAAAAAAAAAAAA", "1HGAAAAAAAAAAAAAAA", "CHASSIS-1962"})
    void unsupportedLayoutsDoNotGuessAResult(String vin) {
        Result result = decoder.decode(vin);
        assertEquals(Structure.UNSUPPORTED_LENGTH, result.structure());
        assertEquals(MatchStatus.UNSUPPORTED_FORMAT, result.status());
        assertTrue(result.candidates().isEmpty());
    }

    @Test
    void assemblyCountryAndUnsourcedManufacturerCountryRemainUnknown() {
        Result result = decoder.decode("JTDAAAAAAAAAAAAAA");
        assertEquals(Knowledge.UNKNOWN, result.assemblyCountry().status());
        assertEquals(Knowledge.UNKNOWN, result.manufacturerCountry().status());
    }

    @Test
    void ambiguousAssignmentsPreserveAllManufacturersAndDoNotChooseABrand() {
        VinDecoder custom = synthetic(List.of(
                assignment("first", "maker-a", "Brand A", unrestricted()),
                assignment("second", "maker-b", "Brand B", unrestricted())));
        Result result = custom.decode("ZZZAAAAAAAAAAAAAA");
        assertEquals(MatchStatus.AMBIGUOUS, result.status());
        assertEquals(Knowledge.AMBIGUOUS, result.manufacturer().status());
        assertEquals(Set.of("maker-a", "maker-b"), result.manufacturer().possibilities().stream()
                .map(Manufacturer::id).collect(java.util.stream.Collectors.toSet()));
        assertEquals(Knowledge.AMBIGUOUS, result.brand().status());
        assertTrue(result.brand().value().isEmpty());
        assertEquals(Knowledge.KNOWN, result.category().status());
    }

    @Test
    void sameManufacturerCanHaveAmbiguousBrandsOrPartlyMissingBrandEvidence() {
        Assignment a = assignment("first", "maker-a", "Brand A", unrestricted());
        Assignment b = assignment("second", "maker-a", "Brand B", unrestricted());
        Result ambiguous = synthetic(List.of(a, b)).decode("ZZZAAAAAAAAAAAAAA");
        assertEquals(Knowledge.KNOWN, ambiguous.manufacturer().status());
        assertEquals(Knowledge.AMBIGUOUS, ambiguous.brand().status());
        Assignment unknownBrand = assignment("third", "maker-a", null, unrestricted());
        Result partial = synthetic(List.of(a, unknownBrand)).decode("ZZZAAAAAAAAAAAAAA");
        assertEquals(Knowledge.UNKNOWN, partial.brand().status());
        assertTrue(partial.brand().value().isEmpty());
    }

    @Test
    void historicalAndMarketConstraintsRequireExplicitContextAndRespectInclusiveBoundaries() {
        Constraints scope = new Constraints(Set.of("US"), Optional.of(2000), Optional.of(2005));
        VinDecoder custom = synthetic(List.of(assignment("scoped", "maker-a", "Brand A", scope)));
        String vin = "ZZZAAAAAA5AAAAAAA";
        Result missing = custom.decode(vin);
        assertEquals(MatchStatus.NEEDS_CONTEXT, missing.status());
        assertEquals(Knowledge.NEEDS_CONTEXT, missing.manufacturer().status());
        assertTrue(missing.manufacturer().value().isEmpty());
        assertEquals(MatchStatus.NEEDS_CONTEXT, custom.decode(vin,
                new Context(Optional.of(2005), Optional.empty())).status());
        for (int year : List.of(2000, 2005)) {
            assertEquals(MatchStatus.RECOGNIZED, custom.decode(vin,
                    new Context(Optional.of(year), Optional.of("US"))).status());
        }
        for (int year : List.of(1999, 2006)) {
            assertEquals(MatchStatus.UNKNOWN, custom.decode(vin,
                    new Context(Optional.of(year), Optional.of("US"))).status());
        }
        assertEquals(MatchStatus.UNKNOWN, custom.decode(vin,
                new Context(Optional.of(2005), Optional.of("DE"))).status());
    }

    @Test
    void bundledProjectionRetainsSourceDigestAndCollectionsCannotBeChanged() throws Exception {
        assertNull(getClass().getResourceAsStream("/META-INF/orvin/dataset.json"));
        String header = new String(BundledResources.read("dataset.tsv"), java.nio.charset.StandardCharsets.UTF_8).split("\n")[0];
        assertEquals(header.split("\t")[2], decoder.dataset().sha256());
        Result result = decoder.decode("1HGAAAAAAAAAAAAAA");
        assertThrows(UnsupportedOperationException.class, () -> result.candidates().clear());
        assertThrows(UnsupportedOperationException.class, () -> result.candidates().get(0).sources().clear());
        assertThrows(UnsupportedOperationException.class, () -> result.manufacturer().possibilities().clear());
    }

    private static Constraints unrestricted() {
        return new Constraints(Set.of(), Optional.empty(), Optional.empty());
    }

    private static VinDecoder synthetic(List<Assignment> assignments) {
        return new VinDecoder(new DatasetInfo("synthetic-test", "unused"), assignments);
    }

    private static Assignment assignment(String id, String manufacturerId, String brand, Constraints constraints) {
        return new Assignment(id, "ZZZ", new Manufacturer(manufacturerId, manufacturerId,
                Optional.empty(), List.of()), Optional.ofNullable(brand), Optional.of(Category.TRAILER),
                constraints, List.of(), "Synthetic test data, not a real WMI assignment.",
                Optional.of("synthetic-ambiguity"), Optional.of("Deliberate test alternatives"));
    }
}
