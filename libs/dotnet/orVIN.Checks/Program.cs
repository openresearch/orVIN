using System.Text;
using System.Text.Json.Nodes;
using OpenResearch.orVIN;

static void Check(bool condition, string label)
{
    if (!condition) throw new InvalidOperationException("Failed: " + label);
}

if (args.Contains("--parity"))
{
    for (string? line; (line = Console.ReadLine()) is not null;)
    {
        var c = line.Split('\t'); var kind = c[0].Split(':');
        string Decode(string value) => Encoding.UTF8.GetString(Convert.FromBase64String(value));
        VehicleAnswer answer;
        if (kind[0] == "vin") answer = VinDecoder.Bundled().DecodeVehicle(Decode(c[1]), new Context(c[2] == "" ? null : int.Parse(c[2]), c[3] == "" ? null : c[3]));
        else answer = HsnTsnLookup.Bundled().LookupVehicle(Decode(c[1]), Decode(c[2]));
        Console.WriteLine((kind[1] == "long" ? answer.Long() : answer.Short()).ToJsonString());
    }
    return;
}

// Independently reviewed facts are checked separately from implementation parity.
var decoder = VinDecoder.Bundled();
// KBA SV 3.1, PDF page 6 rows 1/12: independently reviewed manufacturer facts.
var directory = decoder.DecodeVehicle("W09AAAAAAAAA53001", new Context(market: "JP")).Long();
Check(directory["details"]!["specifications"]!["ManufacturerDirectoryName"]!["value"]!.GetValue<string>() == "A+A HAHN GMBH", "extended KBA WMI positions");
var abt = decoder.DecodeVehicle("WAKAAAAAAAAAAAAAA", new Context(market: "AT"));
Check(abt.Vehicle["make"] is null, "manufacturer directory label is not retail make");
Check(abt.Long()["details"]!["specifications"]!["ManufacturerDirectoryLocation"]!["value"]!.GetValue<string>() == "Kempten", "KBA manufacturer location");
var directoryCredit = abt.Long()["details"]!["provenance"]!["additionalSources"]!.AsArray().Single(s => s!["id"]!.GetValue<string>() == "kba-sv31-2026-01-15");
Check(directoryCredit!["license"]!.GetValue<string>() == "LicenseRef-KBA-SV31-Attribution" && directoryCredit["modifications"]!.GetValue<string>().Contains("eigene Darstellung"), "KBA WMI attribution and modification notice");
var golf = decoder.DecodeVehicle("WVWZZZ1KZ5P000001", new Context(market: "AT"));
// Row-specific preference: KBA PDF 34/78 versus NHTSA WMI 4873 / make 4657.
var cobra = decoder.DecodeVehicle("1CAAAAAAAAAAAAAAA", new Context(market: "AT")).Long();
Check(cobra["vehicle"]!["make"]!.GetValue<string>() == "Cobra Industries", "preferred 1CA make");
var cobraDetails = cobra["details"]!;
var preferenceFacts = cobraDetails["decisions"]!["make"]!["evidenceIds"]!.AsArray()
    .Select(id => cobraDetails["evidence"]![id!.GetValue<string>()]!["record"]!);
Check(preferenceFacts.Any(f => f["kind"]?.GetValue<string>() == "SOURCE_PREFERENCE" && f["keys"]!.GetValue<string>().Contains("sv31-p034-r078")), "1CA preference is linked to the make decision");
Check(cobraDetails["specifications"]!["ManufacturerDirectoryName"]!["value"]!.GetValue<string>() == "DAIMLERCHRYSLER CORP (DODGE/BUS)", "original conflicting KBA name retained");
Check(decoder.DecodeVehicle("1C3AAAAAAAAAAAAAA").Vehicle["make"]?.GetValue<string>() != "Cobra Industries", "preference is not a global Chrysler alias");
Check(golf.Vehicle["model"]!.GetValue<string>() == "Golf", "reviewed European Golf family");
Check(golf.Vehicle["make"]!.GetValue<string>() == "VW", "normalized make");
Check(golf.Vehicle["modelYear"]!.GetValue<int>() == 2005, "documented Golf model year");
var extended = golf.Long(); extended.Remove("details"); Check(JsonNode.DeepEquals(extended, golf.Short()), "long extends short");
var altered = golf.Short(); altered["vehicle"]!["model"] = "changed";
Check(golf.Vehicle["model"]!.GetValue<string>() == "Golf", "independent projections");
var conflict = decoder.DecodeVehicle("WVWZZZ1KZ5P000001", new Context(2006, "AT")).Short();
Check(conflict["fieldStatus"]!["model"]!.GetValue<string>() == "CONFLICT" && conflict["vehicle"]!["model"] is null, "caller conflict blocks fallback");
var tesla = decoder.DecodeVehicle("XP7YGAEK0TB000001").Short();
Check(tesla["vehicle"]!["productionYear"]!.GetValue<int>() == 2026 && tesla["vehicle"]!["modelYear"] is null, "production year is not model year");
foreach (var market in new[] { "AT", "JP", "BR", "NZ", "ZA" })
{
    var answer = decoder.DecodeVehicle("1HGCM82603A000000", new Context(market: market)).Short();
    Check(answer["vehicle"]!["model"]!.GetValue<string>() == "Accord" && answer["fieldStatus"]!["model"]!.GetValue<string>() == "SUGGESTED", "foreign suggestion " + market);
    Check(answer["assumptions"]!.AsArray().Any(a => a!["requestedMarket"]?.GetValue<string>() == market), "explicit market attribution " + market);
}
Check(decoder.DecodeVehicle("1HGCM82603A000000", new Context(market: "US")).Short()["fieldStatus"]!["model"]!.GetValue<string>() == "RESOLVED", "matching market");
Check(decoder.DecodeVehicle("bad").Vehicle["make"] is null, "invalid VIN does not guess identity");
var type = HsnTsnLookup.Bundled().LookupVehicle("0603", "BMT").Short();
Check(type["hsn"]!.GetValue<string>() == "0603" && type["vehicle"]!["model"]!.GetValue<string>() == "Golf Sportsvan", "type codes and leading zeros");
Check(type["sources"]!.AsArray().Any(s => s!["license"]?.GetValue<string>() == "dl-de/by-2-0"), "KBA license credit");
var names = typeof(VinDecoder).Assembly.GetManifestResourceNames();
Check(!names.Any(n => n.Contains(".plain.zip") || n.Contains("source.json.gz") || n.Contains("fixtures") || n.Contains("TG-Automobil")), "no raw archives/fixtures packaged");
// Verify every embedded runtime file against the manifest, not just lazily read shards.
using (var stream = typeof(VinDecoder).Assembly.GetManifestResourceStream("orVIN.Data.manifest.tsv")!)
using (var reader = new StreamReader(stream))
{
    var manifestText = reader.ReadToEnd();
    var directoryArg = Array.IndexOf(args, "--bundle-dir");
    if (directoryArg >= 0) Check(manifestText == File.ReadAllText(Path.Combine(args[directoryArg + 1], "manifest.tsv")), "exact compiled manifest");
    var files = manifestText.Split('\n').Where(l => l.StartsWith("F\t", StringComparison.Ordinal)).Select(l => l.Split('\t')[1]).ToList();
    Check(names.Length == files.Count + 1, "exact runtime inventory");
    foreach (var file in files)
    {
        var bytes = Bundle.Default.Read(file);
        var position = Array.IndexOf(args, "--bundle-dir");
        if (position >= 0) Check(bytes.SequenceEqual(File.ReadAllBytes(Path.Combine(args[position + 1], file))), "compiled bytes: " + file);
    }
}
Console.WriteLine("orVIN .NET behavioral checks passed");
