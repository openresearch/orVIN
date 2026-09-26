package com.openresearch.orvin;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class VehicleAnswerTest {
    @Test void ownerAuthorizedGolfUsesTheNormalizedContract() {
        // User-contributed Golf 5 from Austria. Explicit permission and expectation provenance:
        // data/identity/fixtures.json. Model year is rule-derived, not owner-confirmed.
        VehicleAnswer answer = VinDecoder.bundled().decodeVehicle("WVWZZZ1KZ5P087443", new VinDecoder.Context(
                java.util.Optional.empty(), java.util.Optional.of("AT")));
        assertEquals("vw", answer.vehicle().makeId().orElseThrow());
        assertEquals("VW", answer.vehicle().make().orElseThrow());
        assertEquals("vw:golf", answer.vehicle().modelId().orElseThrow());
        assertEquals("Golf", answer.vehicle().model().orElseThrow());
        assertEquals(2005, answer.vehicle().modelYear().orElseThrow());
        assertTrue(answer.vehicle().productionYear().isEmpty());
        assertFalse(answer.toShortJson().contains("candidates"));
        assertTrue(answer.toShortJson().contains("vw-vin-chart-2005"));
        assertTrue(answer.toShortJson().length() < 15000);
    }

    @Test void longExtendsShortAndKeepsEveryApprovalWithoutMutableAliases() {
        VehicleAnswer answer = VinDecoder.bundled().decodeVehicle("WVWZZZ1KZ5P000001");
        Map<String, Object> longWithoutDetails = new LinkedHashMap<>(answer.longResult());
        Map<String, Object> details = JsonValues.object(longWithoutDetails.remove("details"));
        assertEquals(answer.shortResult(), longWithoutDetails);
        long approvals = JsonValues.object(details.get("evidence")).values().stream()
                .filter(e -> "TYPE_APPROVAL".equals(JsonValues.object(e).get("kind"))).count();
        assertTrue(approvals > 0);
        assertEquals(VinDecoder.bundled().decode("WVWZZZ1KZ5P000001").typeApprovals().candidates().size(), approvals);
        assertThrows(UnsupportedOperationException.class, () -> answer.shortResult().clear());
        assertThrows(UnsupportedOperationException.class, () -> ((Map<?, ?>) answer.shortResult().get("vehicle")).clear());
        assertThrows(UnsupportedOperationException.class, () -> ((Map<?, ?>) answer.longResult().get("details")).clear());
    }

    @Test void conflictingYearAndProductionYearDoNotBecomeModelYears() {
        VehicleAnswer conflict = VinDecoder.bundled().decodeVehicle("WVWZZZ1KZ5P000001", new VinDecoder.Context(
                java.util.Optional.of(2006), java.util.Optional.of("AT")));
        assertTrue(conflict.vehicle().modelYear().isEmpty());
        assertEquals("CONFLICT", JsonValues.object(conflict.shortResult().get("fieldStatus")).get("modelYear"));
        assertTrue(conflict.toShortJson().contains("vw-vin-chart-2005"));
        VehicleAnswer tesla = VinDecoder.bundled().decodeVehicle("XP7YGAEK0TB000001");
        assertEquals(2026, tesla.vehicle().productionYear().orElseThrow());
        assertTrue(tesla.vehicle().modelYear().isEmpty());
    }

    @Test void kbaCreditSurvivesAndInvalidVinDoesNotGuessAMake() {
        VehicleAnswer kba = HsnTsnLookup.bundled().lookupVehicle("0603", "bmt");
        assertEquals("0603", kba.shortResult().get("hsn"));
        assertEquals("Golf Sportsvan", kba.vehicle().model().orElseThrow());
        assertTrue(kba.vehicle().modelYear().isEmpty());
        assertTrue(kba.toShortJson().contains("dl-de/by-2-0"));
        assertTrue(kba.toShortJson().contains("Normalized output labels"));
        VehicleAnswer invalid = VinDecoder.bundled().decodeVehicle("WVWZZZ1KZ5P00000I");
        assertTrue(invalid.vehicle().make().isEmpty());
        assertEquals("INVALID_CHARACTERS", invalid.shortResult().get("inputStatus"));
        assertEquals(List.of(), invalid.shortResult().get("sources"));
    }
}
