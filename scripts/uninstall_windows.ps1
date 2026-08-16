$ErrorActionPreference = "Stop"
$InstallRoot = Join-Path $env:LOCALAPPDATA "sNote"
$BinRoot = Join-Path $InstallRoot "bin"
$DesktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "sNote.lnk"
$ImmediateCommand = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\sn.cmd"

$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$NewPath = (($UserPath -split ";" | Where-Object { $_ -and $_ -ne $BinRoot }) -join ";")
[Environment]::SetEnvironmentVariable("Path", $NewPath, "User")

if (Test-Path $DesktopShortcut) { Remove-Item $DesktopShortcut -Force }
if (Test-Path $ImmediateCommand) { Remove-Item $ImmediateCommand -Force }
if (Test-Path $InstallRoot) { Remove-Item $InstallRoot -Recurse -Force }

Write-Host "sNote application files were removed."
Write-Host "Your settings remain in %APPDATA%\sNote and can be removed manually."
