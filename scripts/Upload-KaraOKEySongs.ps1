# KaraOKEy songs release uploader for Windows PowerShell 5.1+
# Uses GitHub CLI; never puts a large song pack in Git history.
param(
 [string]$PackPath="$env:USERPROFILE\Downloads\KaraOKEY_songs.vkpack",
 [string]$Repository="printmarks0104-beep/Karaokey-Donwloads-",
 [string]$ReleaseTag="songs-v1",
 [switch]$ConfirmRights
)
$ErrorActionPreference="Stop"
if(-not $ConfirmRights){throw "Pass -ConfirmRights only if you have the rights needed to distribute the songs."}
if(-not (Get-Command gh -ErrorAction SilentlyContinue)){throw "Install GitHub CLI: winget install --id GitHub.cli -e"}
$file=Get-Item -LiteralPath $PackPath -ErrorAction Stop
if($file.PSIsContainer -or $file.Extension.ToLowerInvariant() -ne ".vkpack"){throw "Expected a .vkpack file."}
$visibility=& gh repo view $Repository --json visibility --jq ".visibility"
if($LASTEXITCODE -ne 0){throw "Cannot read repository. Use gh auth login and check the repository name."}
if(($visibility|Out-String).Trim().ToUpperInvariant() -ne "PRIVATE"){throw "Refusing to publish into a public repository before rights and format review."}
$size=[long]$file.Length
if($size -le 0 -or $size -ge 2147483648){throw "Pack must be under the 2 GiB Release asset limit."}
$sha=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
$stream=[IO.File]::OpenRead($file.FullName)
try{$head=New-Object byte[] 16;$len=$stream.Read($head,0,16)}finally{$stream.Dispose()}
$magic=[BitConverter]::ToString($head,0,$len).Replace("-","")
$zipLike=$len -ge 4 -and $head[0] -eq 0x50 -and $head[1] -eq 0x4b -and
 (($head[2] -eq 3 -and $head[3] -eq 4) -or ($head[2] -eq 5 -and $head[3] -eq 6))
$detected=if($zipLike){"zip-compatible"}elseif($magic.StartsWith("53514C69746520666F726D61742033")){"sqlite"}else{"unknown-or-encrypted"}
$inspection=[ordered]@{
 filename=$file.Name;size_bytes=$size;sha256=$sha;first_16_bytes_hex=$magic
 detected_format=$detected;entry_count=$null;extensions=@{};sample_entries=@()
 format_verified_for_android=$false;license_audit_completed=$false
}
if($zipLike){
 try{
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $archive=[IO.Compression.ZipFile]::OpenRead($file.FullName)
  try{
   $inspection.entry_count=$archive.Entries.Count
   $extensions=@{};$names=New-Object 'System.Collections.Generic.List[string]'
   foreach($e in $archive.Entries){
    $name=$e.FullName.Replace('\','/')
    if($name.StartsWith('/') -or $name -match '^[A-Za-z]:' -or ($name.Split('/') -contains '..')){throw "Unsafe ZIP path detected: $name"}
    if($names.Count -lt 80){[void]$names.Add($name)}
    $ext=[IO.Path]::GetExtension($name).ToLowerInvariant()
    if(-not $ext){$ext="(none)"}
    if($extensions.ContainsKey($ext)){$extensions[$ext]++}else{$extensions[$ext]=1}
   }
   $inspection.extensions=$extensions;$inspection.sample_entries=@($names.ToArray())
  }finally{$archive.Dispose()}
 }catch{throw "ZIP inspection failed. No asset uploaded: $($_.Exception.Message)"}
}
$reportDir=Join-Path $file.DirectoryName "KaraOKEy-Songs-Report"
New-Item -ItemType Directory -Path $reportDir -Force|Out-Null
$reportPath=Join-Path $reportDir "vkpack-inspection.json"
$manifestPath=Join-Path $reportDir "vkpack-manifest.json"
$checksumPath=Join-Path $reportDir "KaraOKEY_songs.vkpack.sha256"
$manifest=[ordered]@{
 schema=1;pack_id="karaokey-songs-v1";release_tag=$ReleaseTag
 asset=[ordered]@{name=$file.Name;size_bytes=$size;sha256=$sha;detected_format=$detected}
 private_repository=$Repository;secure_download_gateway_required=$true
 auto_install_approved=$false;importer_verified=$false
 open_screen_after_successful_import="stage"
}
($inspection|ConvertTo-Json -Depth 7)|Set-Content -LiteralPath $reportPath -Encoding UTF8
($manifest|ConvertTo-Json -Depth 7)|Set-Content -LiteralPath $manifestPath -Encoding UTF8
"$sha  $($file.Name)"|Set-Content -LiteralPath $checksumPath -Encoding ASCII
Write-Host "Local inspection report: $reportPath"
Write-Host "Format: $detected; Size: $size bytes; SHA256: $sha"
$existing=& gh release view $ReleaseTag --repo $Repository --json assets --jq ".assets[].name" 2>$null
$releaseFound=($LASTEXITCODE -eq 0)
if($releaseFound){
 if(@($existing) -contains $file.Name){throw "Asset already exists under this tag. Use a new immutable release tag."}
 $argsList=@("release","upload",$ReleaseTag,$file.FullName,$checksumPath,$manifestPath,$reportPath,"--repo",$Repository)
}else{
 $argsList=@("release","create",$ReleaseTag,$file.FullName,$checksumPath,$manifestPath,$reportPath,
             "--repo",$Repository,"--title","KaraOKEy songs v1 (format review pending)",
             "--notes","Private song pack; format and redistribution rights must be verified before enabling APK installation.","--draft")
}
& gh @argsList
if($LASTEXITCODE -ne 0){throw "GitHub upload failed; inspect CLI output."}
$foundAssets=& gh release view $ReleaseTag --repo $Repository --json assets --jq ".assets[].name"
if($LASTEXITCODE -ne 0 -or -not (@($foundAssets) -contains $file.Name)){throw "Upload verification failed"}
Write-Host "SUCCESS: $($file.Name) uploaded to private Release $ReleaseTag"
Write-Host "https://github.com/$Repository/releases/tag/$ReleaseTag"
Write-Host "NOTE: The Android app cannot use a private Release until its secure gateway and pack importer are configured."
