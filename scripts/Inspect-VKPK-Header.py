#!/usr/bin/env python3
"""Read the unencrypted VKPK header; never decrypt or extract song contents.

Usage (Windows):
  python scripts/Inspect-VKPK-Header.py "C:\Users\Administrator\Downloads\KaraOKEY_songs.vkpack"

Writes a small *.header.json report beside the original song pack.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

EXPECTED_HASH="313cefc83ec4463c922e213c5edb02cd9f39a68964b526ce17017b55683b14e6"
EXPECTED_BYTES=496506044

def inspect(path: Path):
    if not path.is_file():
        raise SystemExit(f"Cannot find pack: {path}")
    size=path.stat().st_size
    with path.open("rb") as f:
        header=f.read(48)
    if len(header)!=48:
        raise SystemExit("Incomplete VKPK header")
    if header[:4]!=b"VKPK":
        raise SystemExit(
            "Not a VKPK song container. Signature: "+
            repr(header[:8])+
            ". Do not assume it is a ZIP archive."
        )
    magic,version,flags,reserved,count,index_offset,packed_bytes,plain_bytes,nonce,crc=struct.unpack(">4sBBHiqii16sI",header)
    calculated=zlib.crc32(header[:44])&0xffffffff
    if crc!=calculated:
        raise SystemExit(f"Header CRC mismatch: expected {crc:08x}, got {calculated:08x}")
    if not 1<=count<=2_000_000:
        raise SystemExit(f"Invalid VKPK song count: {count}")
    if index_offset<48 or packed_bytes<=0 or plain_bytes<=0 or index_offset+packed_bytes>size:
        raise SystemExit("VKPK encrypted index does not fit inside the file")
    digest=hashlib.sha256()
    with path.open("rb") as f:
        while chunk:=f.read(4*1024*1024):
            digest.update(chunk)
    sha=digest.hexdigest()
    report={
      "file":path.name,
      "bytes":size,
      "sha256":sha,
      "matches_uploaded_release":size==EXPECTED_BYTES and sha==EXPECTED_HASH,
      "container":"VKPK",
      "version":version,
      "flags":flags,
      "header_crc32_valid":True,
      "song_count_reported_by_header":count,
      "encrypted_index_offset":index_offset,
      "encrypted_index_length":packed_bytes,
      "index_uncompressed_length":plain_bytes,
      "contents_decrypted":False,
      "songs_playable":False,
      "next_step":"Requires an authorized compatible pack-key provider and a licensed MIDI/SoundFont playback engine. No protected app key was extracted.",
    }
    out=path.with_name(path.name+".header.json")
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    print("Report saved:",out)
    return report

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit('Usage: python Inspect-VKPK-Header.py "path_to_KaraOKEY_songs.vkpack"')
    inspect(Path(sys.argv[1]))
