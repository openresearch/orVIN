using System.Text.Json.Nodes;

namespace OpenResearch.ORvin;

/// <summary>One decision with independent, mutable JSON projections. Long extends short with details.</summary>
public sealed class VehicleAnswer
{
    private readonly string shortJson;
    private readonly string longJson;
    internal VehicleAnswer(Dictionary<string, object?> summary, Dictionary<string, object?> details)
    {
        shortJson = J.Canonical(summary);
        longJson = J.Canonical(new Dictionary<string, object?>(summary) { ["details"] = details });
    }
    public JsonObject Short() => JsonNode.Parse(shortJson)!.AsObject();
    public JsonObject Long() => JsonNode.Parse(longJson)!.AsObject();
    public JsonObject Vehicle => Short()["vehicle"]!.AsObject();
}
