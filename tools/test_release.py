"""Prevent mixed versions or malformed tags from reaching release publication."""
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

import release


class ReleaseTest(unittest.TestCase):
    def test_only_stable_release_tags_are_accepted(self):
        self.assertEqual("0.1.0", release.version_from_tag("v0.1.0"))
        self.assertEqual("12.34.56", release.version_from_tag("v12.34.56"))
        for tag in ("main", "0.1.0", "v01.2.3", "v1.2.3-rc1", "v1.2.3\n", "v1.2.3/other", "v1.2.$(command)"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                release.version_from_tag(tag)

    def test_preparation_updates_all_versions_but_preserves_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            java = root / "libs/java/pom.xml"
            python = root / "libs/python/pyproject.toml"
            dotnet = root / "libs/dotnet/ORvin/ORvin.csproj"
            dotnet.parent.mkdir(parents=True)
            dotnet.write_text("<Project><PropertyGroup><Version>0.3.0-dev</Version></PropertyGroup></Project>")
            java.parent.mkdir(parents=True)
            python.parent.mkdir(parents=True)
            original = '''<project xmlns="http://maven.apache.org/POM/4.0.0">
<version>0.1.0-SNAPSHOT</version><scm><tag>HEAD</tag></scm>
<dependencies><dependency><version>0.1.0-SNAPSHOT</version></dependency></dependencies></project>'''
            java.write_text(original)
            python.write_text('[project]\nname = "orvin"\nversion = "0.1.0.dev0"\n')
            release.prepare("v2.3.4", root)
            self.assertEqual("2.3.4", ET.fromstring(dotnet.read_text()).findtext("PropertyGroup/Version"))
            pom = ET.fromstring(java.read_text())
            self.assertEqual("2.3.4", pom.findtext("m:version", namespaces=release.NS))
            self.assertEqual("v2.3.4", pom.findtext("m:scm/m:tag", namespaces=release.NS))
            self.assertEqual("0.1.0-SNAPSHOT", pom.findtext("m:dependencies/m:dependency/m:version", namespaces=release.NS))
            self.assertEqual('[project]\nname = "orvin"\nversion = "2.3.4"\n', python.read_text())
            java.write_text(original)
            python.write_text('[project]\nname = "orvin"\n')
            with self.assertRaisesRegex(ValueError, "Python project version"):
                release.prepare("v2.3.4", root)
            self.assertEqual(original, java.read_text())

    def test_packaged_metadata_must_match_the_tag_and_coordinates(self):
        pom = b'<project xmlns="http://maven.apache.org/POM/4.0.0"><groupId>com.openresearch</groupId><artifactId>orvin</artifactId><version>1.2.3</version></project>'
        release.check_pom(pom, "1.2.3")
        release.check_python_metadata(b"Name: orvin\nVersion: 1.2.3\n", "1.2.3")
        for schema in ("2012/06", "2013/05"):
            nuspec = f'<package xmlns="http://schemas.microsoft.com/packaging/{schema}/nuspec.xsd"><metadata><id>OpenResearch.ORvin</id><version>1.2.3</version></metadata></package>'.encode()
            release.check_nuget_metadata(nuspec, "1.2.3")
            with self.assertRaisesRegex(ValueError, "differs"):
                release.check_nuget_metadata(nuspec, "1.2.4")
            with self.assertRaisesRegex(ValueError, "differs"):
                release.check_nuget_metadata(nuspec.replace(b"OpenResearch.ORvin", b"another-package"), "1.2.3")
        with self.assertRaisesRegex(ValueError, "version"):
            release.check_pom(pom, "1.2.4")
        with self.assertRaisesRegex(ValueError, "artifactId"):
            release.check_pom(pom.replace(b"orvin", b"different"), "1.2.3")
        with self.assertRaisesRegex(ValueError, "differs"):
            release.check_python_metadata(b"Name: orvin\nVersion: 1.2.3\n", "1.2.4")


if __name__ == "__main__":
    unittest.main()
