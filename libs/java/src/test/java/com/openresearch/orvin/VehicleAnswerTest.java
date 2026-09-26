package com.openresearch.orvin;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class VehicleAnswerTest {
    @Test void kbaWmiDirectoryPreservesExtendedIdentifiersAndAttributionWithoutInventingAMake() {
        var decoder = VinDecoder.bundled();
        // Independently read from SV 3.1 PDF page 6, rows 1 and 12; synthetic VINs.
        var hahn = decoder.decode("W09AAAAAAAAA53001");
        assertEquals("A+A HAHN GMBH", hahn.details().field("ManufacturerDirectoryName").value().orElseThrow());
        assertEquals("1031", hahn.details().field("ManufacturerDirectoryHSN").value().orElseThrow());
        var nearMiss = decoder.decode("W09A53AAAAAAAAAAA");
        assertFalse(nearMiss.details().field("ManufacturerDirectoryName").possibilities().contains("A+A HAHN GMBH"));
        var answer = decoder.decodeVehicle("WAKAAAAAAAAAAAAAA");
        assertTrue(answer.vehicle().make().isEmpty());
        var details = JsonValues.object(answer.longResult().get("details"));
        var specifications = JsonValues.object(details.get("specifications"));
        assertEquals("Kempten", JsonValues.object(specifications.get("ManufacturerDirectoryLocation")).get("value"));
        assertFalse(specifications.containsKey("PlantCity"));
        var provenance = JsonValues.object(details.get("provenance"));
        var credit = JsonValues.list(provenance.get("additionalSources")).stream().map(JsonValues::object)
                .filter(s -> "kba-sv31-2026-01-15".equals(s.get("id"))).findFirst().orElseThrow();
        assertEquals("LicenseRef-KBA-SV31-Attribution", credit.get("license"));
        assertEquals("https://www.kba.de/SharedDocs/Downloads/DE/SV/sv31_pdf.pdf?__blob=publicationFile&v=3#page=151", credit.get("termsUrl"));
        assertTrue(credit.get("modifications").toString().contains("eigene Darstellung"));
    }

    @Test void cobraPreferenceExplainsItsDecisionAndPreservesTheConflictingDirectoryRow() {
        // Reviewed KBA PDF 34/78 versus NHTSA WMI 4873 / make 4657.
        var decoder = VinDecoder.bundled();
        var answer = decoder.decodeVehicle("1CAAAAAAAAAAAAAAA");
        assertEquals("Cobra Industries", answer.vehicle().make().orElseThrow());
        var details = JsonValues.object(answer.longResult().get("details"));
        var evidence = JsonValues.object(details.get("evidence"));
        var decision = JsonValues.object(JsonValues.object(details.get("decisions")).get("make"));
        var preference = JsonValues.list(decision.get("evidenceIds")).stream()
                .map(id -> JsonValues.object(JsonValues.object(evidence.get(id)).get("record")))
                .filter(record -> "SOURCE_PREFERENCE".equals(record.get("kind"))).findFirst().orElseThrow();
        assertEquals("kba-sv31-1ca-prefer-nhtsa", preference.get("ruleId"));
        assertTrue(preference.get("keys").toString().contains("sv31-p034-r078"));
        var specifications = JsonValues.object(details.get("specifications"));
        assertEquals("DAIMLERCHRYSLER CORP (DODGE/BUS)",
                JsonValues.object(specifications.get("ManufacturerDirectoryName")).get("value"));
        assertNotEquals("Cobra Industries", decoder.decodeVehicle("1C3AAAAAAAAAAAAAA").vehicle().make().orElse(""));
    }

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
