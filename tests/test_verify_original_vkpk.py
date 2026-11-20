import importlib.util
import pathlib
import struct
import tempfile
import unittest
import zlib

p = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "verify_original_vkpk.py"
spec = importlib.util.spec_from_file_location("inspector", p)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

def fixture(path, corrupt=False):
    data = b"some-own-content"
    h = struct.pack(">4sBBHIQII16s", b"VKPK", 1, 3, 0, 47997, 48, len(data), 20, b"\0"*16)
    crc = zlib.crc32(h) & 0xffffffff
    path.write_bytes(h + struct.pack(">I", crc ^ int(corrupt)) + data)

class Tests(unittest.TestCase):
    def test_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d)/"fixture"
            fixture(f)
            old = f.read_bytes()
            r = app.inspect(f, expected_size=None, expected_sha=None)
            self.assertEqual(f.read_bytes(), old)
            self.assertEqual(r["declared_song_count"], 47997)
            self.assertFalse(r["all_47997_song_records_decoded"])
    def test_bad_crc(self):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d)/"bad"
            fixture(f, corrupt=True)
            with self.assertRaisesRegex(ValueError, "CRC"):
                app.inspect(f, expected_size=None, expected_sha=None)
    def test_wrong_sha(self):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d)/"bad"
            fixture(f)
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                app.inspect(f, expected_size=None, expected_sha="0"*64)
