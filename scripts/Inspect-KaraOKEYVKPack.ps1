# KaraOKEy VKPack inspection — metadata only, no execution or extraction.
# Usage:
# powershell -ExecutionPolicy Bypass -File .\Inspect-KaraOKEYVKPack.ps1 -PackPath "C:\Users\Administrator\Downloads\KaraOKEY_songs.vkpack"
param([Parameter(Mandatory=$true)][string]$PackPath)
$ErrorActionPreference='Stop'
$file=Get-Item -LiteralPath $PackPath -ErrorAction Stop
if($file.PSIsContainer){throw 'PackPath must point to the .vkpack file.'}
$reader=[System.IO.File]::OpenRead($file.FullName)
try {
  $magic=New-Object byte[] 64
  $count=$reader.Read($magic,0,$magic.Length)
  $head=[BitConverter]::ToString($magic,0,$count).Replace('-','')
  $text=([Text.Encoding]::ASCII.GetString($magic,0,$count) -replace '[^\x20-\x7e]','.')
}finally{$reader.Dispose()}
$isZip=$count -ge 4 -and $magic[0] -eq 0x50 -and $magic[1] -eq 0x4b -and
 (($magic[2] -eq 3 -and $magic[3] -eq 4) -or ($magic[2] -eq 5 -and $magic[3] -eq 6))
$isSqlite=$text.StartsWith('SQLite format 3')
$kind=if($isZip){'zip-compatible'}elseif($isSqlite){'sqlite-database'}else{'custom-binary-or-encrypted'}
$report=[ordered]@{
  file=$file.Name;size_bytes=[long]$file.Length;sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  kind=$kind;header_hex=$head;header_ascii=$text
  entry_count=$null;extension_counts=@{};sample_paths=@()
  warning='Inspection only; does not establish music rights, playability or soundfont compatibility.'
}
if($isZip){
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $zip=[IO.Compression.ZipFile]::OpenRead($file.FullName)
  try{
    $report.entry_count=$zip.Entries.Count
    $extensions=@{}
    $sample=New-Object System.Collections.Generic.List[string]
    foreach($e in $zip.Entries){
      $name=$e.FullName.Replace('\','/')
      if($name.StartsWith('/') -or $name -match '^[a-zA-Z]:' -or ($name.Split('/') -contains '..')){throw "Unsafe entry path $name"}
      $ext=[IO.Path]::GetExtension($name).ToLowerInvariant()
      if(-not $ext){$ext='(none)'}
      if($extensions.ContainsKey($ext)){$extensions[$ext]++}else{$extensions[$ext]=1}
      if($sample.Count -lt 100){[void]$sample.Add($name)}
    }
    $report.extension_counts=$extensions
    $report.sample_paths=@($sample.ToArray())
  }finally{$zip.Dispose()}
}
$output=Join-Path $file.DirectoryName 'KaraOKEY_vkp_inspection.json'
$report|ConvertTo-Json -Depth 7|Set-Content -LiteralPath $output -Encoding UTF8
Write-Host "File format detected: $kind"
Write-Host "Files (ZIP entries, if applicable): $($report.entry_count)"
Write-Host "SHA-256: $($report.sha256)"
Write-Host "Inspection report: $output"
Write-Host 'Share the JSON report to enable building a compatible importer. Your actual song pack remains local/private.'
