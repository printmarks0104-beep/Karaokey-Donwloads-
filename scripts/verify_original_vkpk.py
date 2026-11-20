#!/usr/bin/env python3
"""Read-only integrity audit; does not decrypt or export songs."""
import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path

EXPECTED_SIZE = 496506044
EXPECTED_SHA = "313cefc83ec4463c922e213c5edb02cd9f39a68964b526ce17017b55683b14e6"
EXPECTED_COUNT = 47997

def inspect(path, expected_size=EXPECTED_SIZE, expected_sha=EXPECTED_SHA):
    path = Path(path)
    if not path.is_file() or path.stat().st_size < 48:
        raise ValueError("Invalid VKPK file")
    size = path.stat().st_size
    with path.open("rb") as stream:
        head = stream.read(48)
        magic, version, flags, reserved, count, index_offset, stored, raw, _nonce, crc = struct.unpack(">4sBBHIQII16sI", head)
        if magic != b"VKPK":
            raise ValueError("Invalid VKPK magic")
        if zlib.crc32(head[:44]) & 0xffffffff != crc:
            raise ValueError("Invalid header CRC32")
        if not (0 < count <= 2000000 and 48 <= index_offset <= size and 0 < stored <= 128000000 and 0 < raw <= 256000000 and stored <= size-index_offset):
            raise ValueError("Invalid index bounds")
        if count != EXPECTED_COUNT:
            raise ValueError("Unexpected declared song count")
        if expected_size is not None and size != expected_size:
            raise ValueError("Unexpected file size")
        sha = hashlib.sha256()
        stream.seek(0)
        for block in iter(lambda: stream.read(4*1024*1024), b""):
            sha.update(block)
        digest = sha.hexdigest()
        if expected_sha is not None and digest != expected_sha:
            raise ValueError("File SHA-256 mismatch")
    return {
        "file": path.name, "size_bytes": size, "sha256": digest,
        "header_version": version, "header_flags": flags,
        "declared_song_count": count, "index_offset": index_offset,
        "stored_index_bytes": stored, "raw_index_bytes": raw,
        "header_crc32_valid": True, "index_bounds_valid": True,
        "all_47997_song_records_decoded": False,
        "android_playback_verified": False, "license_to_redistribute_verified": False,
        "note": "Complete-file integrity does not verify any playable song."
    }

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--pack", required=True)
    p.add_argument("--report", required=True)
    a = p.parse_args()
    result = inspect(a.pack)
    output = Path(a.report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print("PASS: original VKPK integrity, CRC, count and bounds")
    print("Declared songs:", result["declared_song_count"])
    print("SHA-256:", result["sha256"])
    print("MIDI records decoded in this job: 0 (no decryption credential supplied)")
