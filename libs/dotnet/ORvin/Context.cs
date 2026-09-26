namespace OpenResearch.ORvin;

/// <summary>Independently supplied context. Country does not prove original sales specification.</summary>
public sealed record Context
{
    public int? ModelYear { get; }
    public string? Market { get; }
    public Context(int? modelYear = null, string? market = null)
    {
        if (modelYear is < 1886 or > 9999) throw new ArgumentOutOfRangeException(nameof(modelYear));
        if (market is not null && (market.Length != 2 || market.Any(c => c is < 'A' or > 'Z')))
            throw new ArgumentException("Market must use an uppercase two-letter country code", nameof(market));
        ModelYear = modelYear; Market = market;
    }
}
