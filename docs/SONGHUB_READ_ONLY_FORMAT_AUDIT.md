# Read-only shubidx/shubblob format audit

The requirements-v1 private release includes shubidx and shubblob. The Python script under scripts/ inspects file sizes, hashes, sampled entropy and signatures. It does not decode, decrypt, export or play songs.

A same-repository PR triggers the separate GitHub Actions scanner; the GITHUB_TOKEN stays in the runner. Only small JSON/Markdown metadata is retained as a workflow artifact for seven days. Private song binaries remain unchanged in GitHub Releases, and all analysis is read-only. No changes to SING'OKEY player code or existing VKPack files.

Matching the original SongHub release asset sizes does not establish byte-for-byte identity, licensing or song compatibility. The original release disallows unauthorized extraction and cross-app redistribution. Only implement an importer for content licensed and authorized for SING'OKEY. The next step after this report is testing a separately owned MIDI/KAR fixture on the current SING'OKEY audio and lyrics engine.
