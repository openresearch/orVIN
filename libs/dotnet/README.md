# orVIN for .NET

Offline VIN and German HSN/TSN lookup. The NuGet package `OpenResearch.orVIN`
targets .NET 8 and later, embeds the same compiled dataset as Python and Java,
and has no runtime package dependencies or network calls.

```csharp
using OpenResearch.orVIN;

var answer = VinDecoder.Bundled().DecodeVehicle(
    "WVWZZZ1KZ5P000001", new Context(market: "AT"));
Console.WriteLine(answer.Short().ToJsonString());
Console.WriteLine(answer.Long().ToJsonString());

var germanType = HsnTsnLookup.Bundled().LookupVehicle("0603", "BMT");
```

`Vehicle`, `Short()` and `Long()` return independent JSON objects. Check
`fieldStatus` before using a value. A match from another country remains
`SUGGESTED`, with its source market and attribution; unknown values stay null.
Model year and production year are distinct.

Build: `dotnet pack libs/dotnet/orVIN -c Release`. Install the generated `.nupkg`
from a local NuGet source, or use the release package when published. Dataset
rights and source notices are embedded and included as `DATA-LICENSE.md` and
`NOTICE`; the code license does not relicense upstream data.
