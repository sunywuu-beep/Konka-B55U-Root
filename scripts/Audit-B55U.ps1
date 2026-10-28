<#
.SYNOPSIS
Only reads device state and saves local audit files. Requires Windows PowerShell 5.1+ and adb.exe.
.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\scripts\Audit-B55U.ps1 -TvIp 192.168.0.210 -AdbPath .\adb.exe
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$TvIp,
    [string]$AdbPath = 'adb.exe',
    [string]$OutputDir = '.\audit-output'
)
$ErrorActionPreference = 'Stop'
$target = '{0}:5555' -f $TvIp
if (-not ($TvIp -match '^\d{1,3}(\.\d{1,3}){3}$')) { throw 'TvIp must be an IPv4 address.' }
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$dir = Join-Path $OutputDir $stamp
New-Item -ItemType Directory -Path $dir -Force | Out-Null
function Run-Adb([string[]]$Parts) {
    $output = & $AdbPath @Parts 2>&1
    if ($LASTEXITCODE -ne 0) { throw ('adb failed: {0}; {1}' -f ($Parts -join ' '), ($output -join ' ')) }
    return (($output | Out-String).Trim())
}
$connection = Run-Adb @('connect',$target)
$connection | Set-Content -Path (Join-Path $dir 'connection.txt') -Encoding UTF8
$id = Run-Adb @('-s',$target,'shell','id')
$id | Set-Content -Path (Join-Path $dir 'id.txt') -Encoding UTF8
if ($id -notmatch 'uid=0\(root\)') { throw 'Not root ADB; stop. Check id.txt.' }
$commands = [ordered]@{
  'build-type.txt'='getprop ro.build.type'
  'android-release.txt'='getprop ro.build.version.release'
  'installed-packages.txt'='pm list packages -f'
  'disabled-packages.txt'='pm list packages -d'
  'processes.txt'='ps'
  'meminfo.txt'='cat /proc/meminfo'
  'data-df.txt'='df -h /data'
  'root-hook-status.txt'='ls -l /system/etc/install-recovery.sh'
}
foreach($filename in $commands.Keys) {
   try {
     $value=Run-Adb @('-s',$target,'shell',$commands[$filename])
     $value | Set-Content -Path (Join-Path $dir $filename) -Encoding UTF8
   } catch {
     ('FAILED: ' + $_.Exception.Message) | Set-Content -Path (Join-Path $dir $filename) -Encoding UTF8
   }
}
Write-Host ('Audit saved locally: ' + $dir)
Write-Host 'Review files for personal/device identifiers before sharing.'
