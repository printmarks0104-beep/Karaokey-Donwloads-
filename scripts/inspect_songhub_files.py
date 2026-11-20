#!/usr/bin/env python3
"""Read-only inspection for shubidx/shubblob. No song extraction or decryption."""
import argparse
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SIGNATURES = {
    "standard_midi_mthd": b"MThd",
    "riff_container": b"RIFF",
    "zip_local_header": b"PK\x03\x04",
    "mp3_id3": b"ID3",
    "ogg_container": b"OggS",
    "sqlite_database": b"SQLite format 3\x00",
    "flac_audio": b"fLaC",
}
EXPECTED_BYTES = {"index": 1797052, "blob": 606828544}
BLOCK_BYTES = 4 * 1024 * 1024
MAX_OFFSETS = 8


def entropy(data):
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return round(-sum((c/n) * math.log2(c/n) for c in counts.values()), 4)


def classify(head):
    for prefix, kind in (
        (b"MThd", "standard-midi"),
        (b"RIFF", "riff-container"),
        (b"PK\x03\x04", "zip-container"),
        (b"SQLite format 3\x00", "sqlite-database"),
        (b"ID3", "mp3-id3"),
        (b"OggS", "ogg-container"),
        (b"fLaC", "flac-audio"),
    ):
        if head.startswith(prefix):
            return kind
    return "unknown-custom-binary"


def inspect(path, role):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError("Missing " + role + ": " + str(path))
    size = path.stat().st_size
    sha256 = hashlib.sha256()
    hits = {name: {"count": 0, "first_offsets": []} for name in SIGNATURES}
    sample = bytearray()
    carry = b""
    position = 0
    with path.open("rb") as stream:
        while True:
            block = stream.read(BLOCK_BYTES)
            if not block:
                break
            sha256.update(block)
            if len(sample) < 65536:
                sample.extend(block[:65536-len(sample)])
            combined = carry + block
            base = position-len(carry)
            for name, pattern in SIGNATURES.items():
                cursor = 0
                while True:
                    found = combined.find(pattern, cursor)
                    if found < 0:
                        break
                    offset = base+found
                    if offset >= position-len(pattern)+1:
                        hits[name]["count"] += 1
                        if len(hits[name]["first_offsets"]) < MAX_OFFSETS:
                            hits[name]["first_offsets"].append(offset)
                    cursor = found+1
            carry = combined[-15:]
            position += len(block)
    samp = bytes(sample)
    return {
        "file_name": path.name,
        "role": role,
        "bytes": size,
        "matches_songhub_release_size": size == EXPECTED_BYTES[role],
        "sha256": sha256.hexdigest(),
        "leading_format_classification": classify(samp[:16]),
        "sample_entropy_bits_per_byte": entropy(samp),
        "sample_nul_ratio": round(samp.count(0)/max(1, len(samp)), 4),
        "sample_printable_ascii_ratio": round(sum(32 <= b <= 126 for b in samp)/max(1, len(samp)), 4),
        "signature_hits": hits,
    }


def markdown(report):
    out = [
        "# SING'OKEY — SongHub format-only inspection", "",
        "Read-only metadata. No song extraction, decoding or DRM bypass.", "",
        "| File | Bytes | SHA-256 | Leading format |",
        "|---|---:|---|---|",
    ]
    for role in ("index", "blob"):
        a = report["assets"][role]
        out.append("| {file_name} | {bytes:,} | {sha256} | {leading_format_classification} |".format(**a))
    out.extend(["", "## Possible file signatures", ""])
    for role in ("index", "blob"):
        a = report["assets"][role]
        out.append("**{}** (sample entropy: {} bits/byte)".format(role, a["sample_entropy_bits_per_byte"]))
        found = False
        for name, hit in a["signature_hits"].items():
            if hit["count"]:
                found = True
                out.append("- {}: {} possible occurrences; first offsets {}".format(name, hit["count"], hit["first_offsets"]))
        if not found:
            out.append("- No recognized signatures found")
    out.extend([
        "", "## Verdict", "",
        "**Playable in SING'OKEY: NOT YET VERIFIED.**",
        "Signature matches alone do not prove valid MIDI tracks. Absence of matches does not exclude compressed or encrypted MIDI.",
        "Matching file sizes do not establish byte-for-byte identity, licensing or permission to reuse SongHub songs.",
        "This inspector never exports songs, lyrics, private keys, or original file bytes.", "",
    ])
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--index", required=True, type=Path)
    p.add_argument("--blob", required=True, type=Path)
    p.add_argument("--output-dir", type=Path, default=Path("."))
    args = p.parse_args()
    report = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "read-only-metadata-no-extraction",
        "assets": {"index": inspect(args.index, "index"), "blob": inspect(args.blob, "blob")},
        "playable_in_singokey_verified": False,
        "song_content_extracted": False,
        "song_index_decoded": False,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/"songhub-inspection.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    (args.output_dir/"songhub-inspection.md").write_text(markdown(report), encoding="utf-8")
    print(markdown(report))


if __name__ == "__main__":
    main()
