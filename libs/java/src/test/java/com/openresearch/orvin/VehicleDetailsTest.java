package com.openresearch.orvin;

import static com.openresearch.orvin.VinDecoder.*;
import static org.junit.jupiter.api.Assertions.*;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.junit.jupiter.api.Test;

class VehicleDetailsTest {
    private final VinDecoder decoder = VinDecoder.bundled();
    private static Context market(String value) { return new Context(Optional.empty(), Optional.of(value)); }

    @Test
    void independentlyReviewedPublicExamplesDecodeFromBundledResources() throws Exception {
        try (var reader = new BufferedReader(new InputStreamReader(Objects.requireNonNull(
                getClass().getResourceAsStream("/vehicle-fixtures.tsv")), StandardCharsets.UTF_8))) {
            for (String line; (line = reader.readLine()) != null;) {
                String[] c = line.split("\t", -1);
                Result result = decoder.decode(c[1], market(c[2]));
                assertEquals("DECODED", result.details().status(), c[0]);
                VehicleDetails.Field field = result.details().fields().get(c[3]);
                assertNotNull(field, c[0] + ": " + c[3]);
                assertEquals(new String(Base64.getDecoder().decode(c[4]), StandardCharsets.UTF_8),
                        field.value().orElseThrow(), c[0] + ": " + c[3]);
                assertTrue(field.evidence().get(0).sourceUrl().startsWith("https://"));
                assertFalse(result.details().fields().containsKey("ProductionDate"));
                for (var fact : field.evidence()) {
                    var source = result.details().sources().stream().filter(s -> s.id().equals(fact.sourceId())).findFirst().orElseThrow();
                    assertEquals(source.url(), fact.sourceUrl());
                    assertFalse(source.edition().isBlank());
                    assertFalse(source.section().isBlank());
                    assertFalse(source.reuseBasis().isBlank());
                }
            }
        }
    }

    @Test
    void golfRuleDoesNotExtendToJettaOtherYearsOrUnreviewedPlants() {
        Result golf = decoder.decode("WVWZZZ1KZ5P000001");
        assertEquals("Golf", golf.model().value().orElseThrow());
        assertEquals("2005", golf.modelYear().value().orElseThrow());
        assertEquals("MOSEL", golf.details().field("PlantCity").value().orElseThrow());
        assertFalse(golf.details().fields().containsKey("EngineModel"));
        for (String vin : List.of("WVWZZZ1KZ6P000001", "WVWZZZ1KZ5A000001", "3VWZZZ1KZ5P000001", "WVWAA71K05P000001"))
            assertTrue(decoder.decode(vin, market("DE")).details().fields().values().stream().flatMap(f -> f.evidence().stream()).noneMatch(e -> e.kind().startsWith("OEM_RULE")));
        assertEquals("CONTEXT_CONFLICT", decoder.decode("WVWZZZ1KZ5P000001", new Context(Optional.of(2006), Optional.empty())).details().status());
    }

    @Test
    void marketContextPreventsUsRulesBecomingUnconditionalEuropeanFacts() {
        Result conditional = decoder.decode("1HGCM82603A000000");
        assertEquals(Knowledge.NEEDS_CONTEXT, conditional.model().status());
        assertEquals(List.of("Accord"), conditional.model().possibilities());
        assertTrue(conditional.model().value().isEmpty());
        Result germany = decoder.decode("1HGCM82603A000000", market("DE"));
        assertEquals("NEEDS_CONTEXT", germany.details().status());
        assertEquals(List.of("Accord"), germany.model().possibilities());
        assertTrue(germany.model().value().isEmpty());
        assertEquals("HONDA", germany.brand().value().orElseThrow());
    }

    @Test
    void yearCycleAlternativesPreserveMissingFactsAndCallerContextResolvesThem() {
        String vin = "5UPAA2420AA000001";
        Result ambiguous = decoder.decode(vin, market("US"));
        assertEquals(List.of(1980, 2010), ambiguous.details().alternatives().stream()
                .map(a -> a.modelYear().orElseThrow()).toList());
        assertTrue(ambiguous.details().alternatives().get(0).fields().isEmpty());
        assertEquals(Knowledge.UNKNOWN, ambiguous.modelYear().status());
        Result resolved = decoder.decode(vin, new Context(Optional.of(2010), Optional.of("US")));
        assertEquals("2010", resolved.modelYear().value().orElseThrow());
        assertEquals("24", resolved.details().field("TrailerLength").value().orElseThrow());
        Result conflict = decoder.decode(vin, new Context(Optional.of(2011), Optional.of("US")));
        assertEquals("CONTEXT_CONFLICT", conflict.details().status());
        assertTrue(conflict.details().fields().isEmpty());
    }

    @Test
    void numericCapturesBracketMatchingAndConversionsRetainDifferentProvenance() {
        var numeric = decoder.decode("5VLAA24208A000001", new Context(Optional.of(2008), Optional.of("US"))).details();
        assertEquals("2", numeric.field("Axles").value().orElseThrow());
        assertEquals("24", numeric.field("TrailerLength").value().orElseThrow());
        assertEquals("NUMERIC_PATTERN", numeric.fields().get("Axles").evidence().get(0).kind());
        var bmw = decoder.decode("5UXWX7C50BA000000", market("US")).details();
        assertEquals("*****|*[AFK]", bmw.fields().get("PlantCity").evidence().get(0).keys());
        var honda = decoder.decode("1HGCM82603A000000", market("US")).details();
        assertEquals("UNIT_CONVERSION", honda.fields().get("DisplacementL").evidence().get(0).kind());
    }

    @Test
    void decodedModelResolvesSharedMakeAndKeepsTheOriginalWmiAssociations() {
        Result result = decoder.decode("1C4RJFBG0FC000000", market("US"));
        assertEquals("JEEP", result.brand().value().orElseThrow());
        assertEquals("Grand Cherokee", result.model().value().orElseThrow());
        assertEquals(7, result.candidates().size());
    }

    @Test
    void europeanFactoryYearIsNotModelYearAndRulesDoNotExtendBeyondTheirScope() {
        Result berlin = decoder.decode("XP7YGAEK0TB000001");
        assertEquals("Model Y", berlin.model().value().orElseThrow());
        assertEquals("2026", berlin.details().field("ProductionYear").value().orElseThrow());
        assertTrue(berlin.modelYear().value().isEmpty());
        for (String vin : List.of("XP7YGAEK0RB000001", "XP7YGAEK0TC000001", "XP7YGAEZ0TB000001", "XP7YGAEK0TB000000"))
            assertTrue(decoder.decode(vin, market("DE")).details().fields().isEmpty(), vin);
    }

    @Test
    void invalidInputsDoNotDecodeRichFactsAndNestedResultsAreImmutable() {
        for (String vin : List.of("", "1HG", "1HGCM826I3A000000", "1HGCM82603A00000😀")) {
            var details = decoder.decode(vin, market("US")).details();
            assertEquals("INVALID_INPUT", details.status());
            assertTrue(details.fields().isEmpty());
        }
        var details = decoder.decode("1HGCM82603A000000", market("US")).details();
        assertThrows(UnsupportedOperationException.class, () -> details.fields().clear());
        assertThrows(UnsupportedOperationException.class, () -> details.sources().clear());
        assertThrows(UnsupportedOperationException.class, () -> details.alternatives().clear());
        assertThrows(UnsupportedOperationException.class, () -> details.alternatives().get(0).fields().put("Model", List.of()));
        assertThrows(UnsupportedOperationException.class, () -> details.fields().get("Model").evidence().clear());
        assertThrows(UnsupportedOperationException.class, () -> details.alternatives().get(0).fields().get("Model").clear());
    }

    @Test
    void concurrentDecodingDoesNotMixCachedManufacturersOrConfigurations() {
        Map<String, String> expected = Map.of("1HGCM82603A000000", "Accord", "5UXWX7C50BA000000", "X3",
                "1C4RJFBG0FC000000", "Grand Cherokee", "XP7YGAEK0TB000001", "Model Y");
        java.util.stream.IntStream.range(0, 64).parallel().forEach(i -> expected.forEach((vin, model) ->
                assertEquals(model, decoder.decode(vin, market("US")).model().value().orElseThrow())));
    }
}
