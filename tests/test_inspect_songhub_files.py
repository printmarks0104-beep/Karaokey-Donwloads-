import importlib.util
import pathlib
import tempfile
import unittest

FILE = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "inspect_songhub_files.py"
spec = importlib.util.spec_from_file_location("shub_scanner", FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class InspectorTests(unittest.TestCase):
    def test_magic(self):
        self.assertEqual(mod.classify(b"MThd" + bytes(12)), "standard-midi")
        self.assertEqual(mod.classify(b"SQLite format 3\x00"), "sqlite-database")
        self.assertEqual(mod.classify(b"private"), "unknown-custom-binary")

    def test_no_changes_and_offsets(self):
        with tempfile.TemporaryDirectory() as directory:
            p = pathlib.Path(directory)/"sample-shubblob"
            original = b"XXXXMThd" + b"0"*180 + b"RIFF" + b"Q"*30
            p.write_bytes(original)
            a = mod.inspect(p, "blob")
            self.assertEqual(p.read_bytes(), original)
            self.assertEqual(a["signature_hits"]["standard_midi_mthd"]["first_offsets"], [4])
            self.assertEqual(a["signature_hits"]["riff_container"]["first_offsets"], [188])
            self.assertFalse(a["matches_songhub_release_size"])
            self.assertNotIn("song_bytes", a)

    def test_empty_file(self):
        with tempfile.TemporaryDirectory() as directory:
            p = pathlib.Path(directory)/"empty"
            p.write_bytes(b"")
            a = mod.inspect(p, "index")
            self.assertEqual(a["sample_entropy_bits_per_byte"], 0)
            self.assertEqual(a["signature_hits"]["standard_midi_mthd"]["count"], 0)


if __name__ == "__main__":
    unittest.main()
