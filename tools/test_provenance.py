"""Regression boundaries for missing attribution and silently changed source bytes."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

import provenance


class ProvenanceTest(unittest.TestCase):
    def test_changed_and_missing_snapshot_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "source.json"
            path.write_bytes(b'{"fact":1}')
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            provenance.snapshot(root, "source.json", digest)
            path.write_bytes(b'{"fact":2}')
            with self.assertRaisesRegex(ValueError, "changed source file"):
                provenance.snapshot(root, "source.json", digest)
            path.unlink()
            with self.assertRaisesRegex(ValueError, "Missing"):
                provenance.snapshot(root, "source.json", digest)

    def test_missing_and_unresolved_rule_sources_are_rejected(self):
        tesla = provenance.read(provenance.ROOT / "data/europe/tesla-model-y.json")
        volkswagen = provenance.read(provenance.ROOT / "data/europe/vw-golf-1k-2005.json")
        provenance.oem_sources(tesla, volkswagen)
        changed = copy.deepcopy(volkswagen)
        del changed["fieldSources"]["ModelYear"]
        with self.assertRaisesRegex(ValueError, "field source mapping"):
            provenance.oem_sources(tesla, changed)
        changed = copy.deepcopy(volkswagen)
        changed["fieldSources"]["PlantCity"] = ["unrecorded-source"]
        with self.assertRaisesRegex(ValueError, "Unknown/duplicate source"):
            provenance.oem_sources(tesla, changed)
        changed["fieldSources"]["PlantCity"] = []
        with self.assertRaisesRegex(ValueError, "Missing source references"):
            provenance.oem_sources(tesla, changed)

    def test_missing_document_locator_and_unexplained_hash_absence_are_rejected(self):
        tesla = provenance.read(provenance.ROOT / "data/europe/tesla-model-y.json")
        volkswagen = provenance.read(provenance.ROOT / "data/europe/vw-golf-1k-2005.json")
        changed = copy.deepcopy(tesla)
        changed["source"]["section"] = ""
        with self.assertRaisesRegex(ValueError, "missing section"):
            provenance.oem_sources(changed, volkswagen)
        changed = copy.deepcopy(tesla)
        del changed["source"]["inspectedSha256"]
        with self.assertRaisesRegex(ValueError, "hash explanation"):
            provenance.oem_sources(changed, volkswagen)

    def test_new_data_files_cannot_escape_the_provenance_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "known.json").write_text("{}")
            provenance.inventory(root, {"known.json"})
            (root / "new-unsourced.csv").write_text("manufacturer,plant")
            with self.assertRaisesRegex(ValueError, "new-unsourced.csv"):
                provenance.inventory(root, {"known.json"})
