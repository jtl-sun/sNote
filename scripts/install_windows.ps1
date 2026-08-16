$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$InstallRoot = Join-Path $env:LOCALAPPDATA "sNote"
$VenvRoot = Join-Path $InstallRoot "venv"
$BinRoot = Join-Path $InstallRoot "bin"
$AppsRoot = Join-Path $InstallRoot "app"
$Python = Join-Path $VenvRoot "Scripts/python.exe"
$Pythonw = Join-Path $VenvRoot "Scripts/pythonw.exe"

New-Item -ItemType Directory -Force -Path $InstallRoot, $BinRoot, $AppsRoot | Out-Null

# Create Python only on the first installation. Updates never modify or remove
# the active environment, so a running sNote process cannot lock the update.
$FreshInstall = -not (Test-Path $Python)
if ($FreshInstall) {
    Write-Host "Creating the sNote environment..."
    python -m venv $VenvRoot
    if ($LASTEXITCODE -ne 0) { throw "Could not create the Python environment." }
    & $Python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Could not update pip." }
} else {
    Write-Host "Existing sNote installation found. Preparing a side-by-side update..."
    & $Python --version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "The existing sNote environment is damaged. Close sNote, uninstall it, and install again."
    }
}

# Install PyQt only when missing. Do not ask pip to uninstall the running sNote
# package; application updates are deployed to a new versioned folder below.
& $Python -c "import PyQt5" 2>$null
if ($LASTEXITCODE -ne 0) {
    & $Python -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
    if ($LASTEXITCODE -ne 0) { throw "Could not install sNote requirements." }
}

$VersionText = Get-Content (Join-Path $ProjectRoot "src/snote/__init__.py") -Raw
if ($VersionText -notmatch '__version__\s*=\s*"([^"]+)"') {
    throw "Could not determine the sNote version."
}
$Version = $Matches[1]
$ReleaseId = "$Version-$(Get-Date -Format 'yyyyMMddHHmmss')"
$ReleaseRoot = Join-Path $AppsRoot $ReleaseId
New-Item -ItemType Directory -Force -Path $ReleaseRoot | Out-Null
Copy-Item (Join-Path $ProjectRoot "src/snote") (Join-Path $ReleaseRoot "snote") -Recurse -Force
[System.IO.File]::WriteAllText(
    (Join-Path $InstallRoot "current_release.txt"),
    $ReleaseRoot,
    [System.Text.Encoding]::UTF8
)

$LauncherScript = Join-Path $InstallRoot "start_snote_and_close.ps1"
Copy-Item (Join-Path $ProjectRoot "scripts/start_snote_and_close.ps1") $LauncherScript -Force
$CommandFile = Join-Path $BinRoot "sn.cmd"
$CommandText = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$LauncherScript`" -Pythonw `"$Pythonw`" -WorkingDirectory `"$InstallRoot`" -AppPath `"$ReleaseRoot`"`r`n"
[System.IO.File]::WriteAllText($CommandFile, $CommandText, [System.Text.Encoding]::ASCII)
$InstalledIcon = Join-Path $InstallRoot "snote.ico"
Copy-Item (Join-Path $ProjectRoot "src/snote/resources/snote.ico") $InstalledIcon -Force

# A VBS launcher keeps desktop launches completely console-free while setting
# PYTHONPATH to the newly deployed side-by-side release.
$GuiLauncher = Join-Path $InstallRoot "start_snote.vbs"
$GuiLauncherText = @"
Set shell = CreateObject("WScript.Shell")
shell.Environment("PROCESS")("PYTHONPATH") = "$ReleaseRoot"
shell.Run Chr(34) & "$Pythonw" & Chr(34) & " -m snote", 0, False
"@
[System.IO.File]::WriteAllText($GuiLauncher, $GuiLauncherText, [System.Text.Encoding]::ASCII)

# WindowsApps is already on the normal Windows user PATH, so `sn` works
# immediately without reopening Windows Terminal.
$WindowsApps = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps"
if (Test-Path $WindowsApps) {
    $ImmediateCommand = Join-Path $WindowsApps "sn.cmd"
    [System.IO.File]::WriteAllText($ImmediateCommand, $CommandText, [System.Text.Encoding]::ASCII)
}

$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$PathItems = @($UserPath -split ";" | Where-Object { $_ })
if ($PathItems -notcontains $BinRoot) {
    $NewPath = (($PathItems + $BinRoot) -join ";")
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
}

$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "sNote.lnk"
$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = Join-Path $env:WINDIR "System32\wscript.exe"
$Shortcut.Arguments = "`"$GuiLauncher`""
$Shortcut.WorkingDirectory = $InstallRoot
$Shortcut.IconLocation = $InstalledIcon
$Shortcut.Save()

# Import portable V0.28 link files only when no user settings exist yet.
$LegacyLinks = Join-Path $ProjectRoot "links"
$UserSettings = Join-Path $env:APPDATA "sNote"
if ((Test-Path $LegacyLinks) -and -not (Test-Path $UserSettings)) {
    New-Item -ItemType Directory -Force -Path $UserSettings | Out-Null
    Copy-Item (Join-Path $LegacyLinks "*.json") $UserSettings -Force
}

Write-Host "sNote installation completed."
Write-Host "The installer will close and sNote will open now."

# Ask an older running sNote window to close normally. Its closeEvent can still
# prompt the user to save modified documents. Never force-kill it.
$RunningSNote = @(
    Get-CimInstance Win32_Process | Where-Object {
        $_.ExecutablePath -ieq $Pythonw -and $_.CommandLine -match '-m\s+snote'
    }
)
foreach ($RunningItem in $RunningSNote) {
    $Process = Get-Process -Id $RunningItem.ProcessId -ErrorAction SilentlyContinue
    if ($null -ne $Process) { [void]$Process.CloseMainWindow() }
}
foreach ($RunningItem in $RunningSNote) {
    Wait-Process -Id $RunningItem.ProcessId -Timeout 30 -ErrorAction SilentlyContinue
}

$StillRunning = @(
    Get-CimInstance Win32_Process | Where-Object {
        $_.ExecutablePath -ieq $Pythonw -and $_.CommandLine -match '-m\s+snote'
    }
)
if ($StillRunning.Count -eq 0) {
    $env:PYTHONPATH = $ReleaseRoot
    Start-Process -FilePath $Pythonw -ArgumentList "-m", "snote" -WorkingDirectory $InstallRoot
} else {
    Write-Host "Update installed. Close and reopen the existing sNote window to use the new version."
}
