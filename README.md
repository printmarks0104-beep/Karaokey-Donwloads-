# KaraOKEy Downloads — current assets

Developer: **MJ Ranuda**. Current PRIVATE GitHub Release: **requirements-v1**.

**The old VideoKey.zip was replaced. The Release currently contains:**
- KaraOKEY_songs.vkpack — 496,506,044 bytes, SHA-256 313cefc83ec4463c922e213c5edb02cd9f39a68964b526ce17017b55683b14e6
- Dream.SAM2634.ver.2.1.sf2 — 141,454,402 bytes, SHA-256 795e72be5fd0ac531adb47b2b5cd6b482f2410e3c7e12ea5482c7e6038c97795
- mega.sf2 — 98,574,116 bytes, SHA-256 d63de87525cce532591d91c394fdd1f356aeb970491fb3472aa3a28a266825fd
- DRONE_SHOOT.mp4 — 213,832,090 bytes, SHA-256 83f87dec7fd89c668edf6917f8763a5db0a26b7c55f1181cf3f538bf31e515c7

Total 950,366,652 bytes. Verified exact release metadata is in [release-manifest.json](release-manifest.json).

The songs VKPack format is not yet inspected and is **not automatically playable**. SoundFonts require a MIDI engine that can load .sf2, and app-private background video needs a safe media bridge. All four files are stored privately pending format and distribution-rights review.

For the song pack, use the [local format inspector](scripts/Inspect-KaraOKEYVKPack.ps1) and share its JSON report. It performs metadata-only inspection and does not extract the actual songs.

Android devices cannot access these PRIVATE Release assets by anonymous GitHub URLs. Only an authorized HTTPS streaming download gateway with byte-range support may be configured. **Never bundle a GitHub token inside the APK.**

---

## Earlier setup notes (obsolete source archive)

# KaraOKEy Content Downloads

**Developer:** MJ Ranuda

This is the PRIVATE source repository for large optional KaraOKEy runtime assets, separate from the Android application's source. The original ZIP remains in Google Drive until a release transfer succeeds.

## Source archive

- File: `VideoKey.zip`
- Google Drive file ID: `1ipljZ2UvYG-Rum_1yZs8a7qxYSS0kQWO`
- Expected size: **915,280,957 bytes**
- Original Google Drive URL: https://drive.google.com/file/d/1ipljZ2UvYG-Rum_1yZs8a7qxYSS0kQWO/view
- Access: owned by the user. File contents are **not yet audited**.

## Move archive to a GitHub Release without ChatGPT's 256 MB connector limit

Run the **Import authorized ZIP from Google Drive** workflow in this repository's **Actions** tab. The workflow uses a GitHub runner to fetch the file from Drive and verifies its size, integrity, and ZIP entry safety. It calculates SHA-256 and uploads an asset to a versioned **private GitHub Release** only when you acknowledge that you own, or are licensed to distribute, the contents. There is no routine source Git commit of a 915 MB binary.

**Do not make the repository public or redistribute copyrighted tracks, BASS binaries, protected Android application code, or other licensed files until their licenses and rights have been reviewed.** The workflow's acknowledgement is not a substitute for license verification.

### Private Release delivery limitation

A normal installed Android app **cannot anonymously download private GitHub Release assets**. Never embed a personal access token or GITHUB_TOKEN into an APK. To provide private assets to buyers, use a secure backend to authenticate devices and issue temporary download URLs via a storage service supporting HTTPS Range requests. Alternatively, use an explicitly approved public release of individually cleared, redistributable files. No runtime download is enabled yet.

### First-install downloader requirements

- Signed release manifest (SHA-256 and size for each immutable asset)
- Download to temp files using HTTP Range / If-Range with ETag
- Retry/backoff and partial resume after network loss
- Background work and foreground notification on Android
- Verify full content SHA-256 before atomic install
- Check free space, allow cancellation, and safe exit (never lock the user's phone)
- Restrict server URLs; never accept arbitrary shell commands or executables from a manifest

See `manifest.example.json` for the proposed schema.

## Important Google Drive sharing precaution

The source ZIP currently has a Drive permission described as **anyone: writer**. For safety, change it to **Viewer** or **Restricted** after the controlled import, so strangers with the link cannot edit or replace the ZIP.
