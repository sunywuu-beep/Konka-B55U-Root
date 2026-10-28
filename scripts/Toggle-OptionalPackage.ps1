<#
.SYNOPSIS
Single-package trial disable and exact restore with local recorded state.
Protection-first: no bulk changes, no core package toggles, root ADB required.
.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\scripts\Toggle-OptionalPackage.ps1 -TvIp 192.168.0.210 -AdbPath .\adb.exe -Mode Disable -Package com.konka.gameassistant
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$TvIp,
  [Parameter(Mandatory=$true)][ValidateSet('Disable','Restore','Status')][string]$Mode,
  [Parameter(Mandatory=$true)][string]$Package,
  [string]$AdbPath='adb.exe',
  [string]$StateDir='.\package-state'
)
$ErrorActionPreference='Stop'
# These were observed in the study, but are NOT proven safe across other firmware.
$optional=@(
 'com.konka.gameassistant',
 'com.konka.hotelmenu',
 'com.konka.apkhall.edu',
 'com.konka.tv.pay',
 'com.yunos.tv.yingshi.boutique',
 'com.lz.smart.music',
 'com.gitvdemokonka.video',
 'com.cibn.tv'
)
if ($optional -notcontains $Package) { throw 'Package is outside the small explicit optional allowlist. No change made.' }
if (-not ($TvIp -match '^\d{1,3}(\.\d{1,3}){3}$')) { throw 'TvIp must be an IPv4 address.' }
$target=('{0}:5555' -f $TvIp)
function ADB([string[]]$Parts) {
 $result = & $AdbPath @Parts 2>&1
 if ($LASTEXITCODE -ne 0) { throw ('ADB command failed: '+($Parts -join ' ')+': '+($result -join ' ')) }
 return (($result | Out-String).Trim())
}
[void](ADB @('connect',$target))
$id=ADB @('-s',$target,'shell','id')
if($id -notmatch 'uid=0\(root\)') { throw 'Root ADB not available. No changes made.' }
$all=ADB @('-s',$target,'shell','pm list packages')
if (@($all -split "`n" | ForEach-Object {$_.Trim()}) -notcontains ('package:'+$Package)) {
 throw 'Target package not installed. No changes made.'
}
$disabled=ADB @('-s',$target,'shell','pm list packages -d')
$isDisabled=(@($disabled -split "`n" | ForEach-Object {$_.Trim()}) -contains ('package:'+$Package))
if($Mode -eq 'Status') { Write-Host ($Package+' => '+$(if($isDisabled){'DISABLED'}else{'ENABLED'})); exit 0 }
New-Item -ItemType Directory -Path $StateDir -Force | Out-Null
$marker=Join-Path $StateDir ($Package+'.disabled-by-project.txt')
if($Mode -eq 'Disable') {
 if($isDisabled) { Write-Host 'Already disabled before this action. Leave unchanged.'; exit 0 }
 $go = Read-Host ('Type YES to test disabling '+$Package+' (other response cancels)')
 if($go -cne 'YES') { Write-Host 'Canceled'; exit 0 }
 $output=ADB @('-s',$target,'shell',('pm disable '+$Package))
 $after=ADB @('-s',$target,'shell','pm list packages -d')
 if (@($after -split "`n" | ForEach-Object {$_.Trim()}) -notcontains ('package:'+$Package)) {throw ('Disable not verified. '+$output)}
 ('time='+ (Get-Date -Format o)+"`npackage="+$Package+"`ntarget="+$target) | Set-Content -Path $marker -Encoding UTF8
 Write-Host ('DISABLED: '+$Package+'; restore only after checking TV functions.')
} elseif($Mode -eq 'Restore') {
 if(-not (Test-Path $marker)) { throw 'No record that THIS script disabled the package. Refusing to change baseline state.' }
 if(-not $isDisabled) { Remove-Item $marker; Write-Host 'Package already enabled. Local marker removed.'; exit 0 }
 $output=ADB @('-s',$target,'shell',('pm enable '+$Package))
 $after=ADB @('-s',$target,'shell','pm list packages -d')
 if (@($after -split "`n" | ForEach-Object {$_.Trim()}) -contains ('package:'+$Package)) {throw ('Restore not verified. '+$output)}
 Remove-Item $marker
 Write-Host ('RESTORED: '+$Package)
}
