# sNote 1.1.5 Windows installer: Python 3.10-3.13 (x64) and PyQt5 are installed
# automatically when required. All managed dependencies are per-user.
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$InstallRoot = Join-Path $env:LOCALAPPDATA "sNote"
$VenvRoot = Join-Path $InstallRoot "venv"
$RuntimeRoot = Join-Path $InstallRoot "python"
$BinRoot = Join-Path $InstallRoot "bin"
$AppsRoot = Join-Path $InstallRoot "app"
$Python = Join-Path $VenvRoot "Scripts/python.exe"
$Pythonw = Join-Path $VenvRoot "Scripts/pythonw.exe"
$InstallerLog = Join-Path $InstallRoot "install.log"
$DiagnosticsLog = Join-Path $InstallRoot "install-diagnostics.log"

New-Item -ItemType Directory -Force -Path $InstallRoot, $BinRoot, $AppsRoot | Out-Null

# Keep a local log for troubleshooting installations on another computer.
try { Start-Transcript -Path $InstallerLog -Append -ErrorAction Stop | Out-Null } catch {
    Write-Host "Note: installer log could not be opened: $($_.Exception.Message)"
}

# Do not call native Python with 2>$null under Windows PowerShell 5.1 and
# $ErrorActionPreference=Stop. That combination can surface only the first
# traceback line as a NativeCommandError and abort an otherwise safe update.
# An external process with redirected files is immune to that behavior.
function Add-InstallerDiagnostic {
    param([string]$Message)
    try {
        Add-Content -LiteralPath $DiagnosticsLog -Value ("$(Get-Date -Format o) $Message") -Encoding UTF8 -ErrorAction Stop
    } catch { }
}

function Invoke-PythonProbe {
    param([string]$Executable, [string]$Script, [string[]]$Prefix = @(), [string]$Label = "Python probe")
    $Id = [guid]::NewGuid().ToString('N')
    $ScriptFile = Join-Path $env:TEMP "snote-probe-$Id.py"
    $Stdout = Join-Path $env:TEMP "snote-probe-$Id.stdout"
    $Stderr = Join-Path $env:TEMP "snote-probe-$Id.stderr"
    try {
        [System.IO.File]::WriteAllText($ScriptFile, $Script, (New-Object System.Text.UTF8Encoding($false)))
        $ArgList = ((@($Prefix) + @("`"$ScriptFile`"")) -join ' ')
        $Process = Start-Process -FilePath $Executable -ArgumentList $ArgList -Wait -PassThru -WindowStyle Hidden `
            -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -ErrorAction Stop
        if ($Process.ExitCode -ne 0) {
            $ErrorText = if (Test-Path $Stderr) { Get-Content $Stderr -Raw -ErrorAction SilentlyContinue } else { "" }
            Add-InstallerDiagnostic "$Label failed (exit $($Process.ExitCode)): $ErrorText"
        }
        return ($Process.ExitCode -eq 0)
    } catch {
        Add-InstallerDiagnostic "$Label could not execute: $($_ | Out-String)"
        return $false
    } finally {
        Remove-Item -Path @($ScriptFile, $Stdout, $Stderr) -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-PythonSetup {
    param([string]$Executable, [string[]]$Arguments, [string]$Label)
    $Id = [guid]::NewGuid().ToString('N')
    $Stdout = Join-Path $env:TEMP "snote-setup-$Id.stdout"
    $Stderr = Join-Path $env:TEMP "snote-setup-$Id.stderr"
    try {
        Write-Host "$Label ..."
        $Process = Start-Process -FilePath $Executable -ArgumentList ($Arguments -join ' ') -Wait -PassThru `
            -WindowStyle Hidden -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -ErrorAction Stop
        $OutText = if (Test-Path $Stdout) { Get-Content $Stdout -Raw -ErrorAction SilentlyContinue } else { "" }
        $ErrText = if (Test-Path $Stderr) { Get-Content $Stderr -Raw -ErrorAction SilentlyContinue } else { "" }
        if ($OutText) { Write-Host $OutText.TrimEnd() }
        if ($Process.ExitCode -ne 0) {
            Add-InstallerDiagnostic "$Label failed (exit $($Process.ExitCode)):`nSTDOUT: $OutText`nSTDERR: $ErrText"
            if ($ErrText) { Write-Host ($ErrText -split "`n" | Select-Object -Last 12) -ForegroundColor Yellow }
        } elseif ($ErrText) {
            Add-InstallerDiagnostic "$Label completed with warnings: $ErrText"
        }
        return [int]$Process.ExitCode
    } catch {
        Add-InstallerDiagnostic "$Label failed to start: $($_ | Out-String)"
        throw "Unable to run $Label. See $DiagnosticsLog. $($_.Exception.Message)"
    } finally {
        Remove-Item -Path @($Stdout, $Stderr) -Force -ErrorAction SilentlyContinue
    }
}

function Test-PythonVersion {
    param([string]$Executable, [string[]]$Prefix = @())
    $Probe = 'import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] < (3,14) and sys.maxsize > 2**32 else 1)'
    return (Invoke-PythonProbe -Executable $Executable -Script $Probe -Prefix $Prefix -Label "Python version check")
}

function Find-AvailablePython {
    # Prefer a local sNote runtime over altering a machine-wide Python install.
    $ManagedPython = Join-Path $RuntimeRoot "python.exe"
    if ((Test-Path $ManagedPython) -and (Test-PythonVersion $ManagedPython)) {
        return @{ Executable = $ManagedPython; Prefix = @(); Source = "sNote private Python" }
    }

    $PythonCmd = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($null -ne $PythonCmd -and (Test-PythonVersion $PythonCmd.Source)) {
        return @{ Executable = $PythonCmd.Source; Prefix = @(); Source = "installed Python" }
    }

    $Launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($null -ne $Launcher) {
        foreach ($Version in @("-3.12", "-3.13", "-3.11", "-3.10")) {
            if (Test-PythonVersion $Launcher.Source @($Version)) {
                return @{ Executable = $Launcher.Source; Prefix = @($Version); Source = "Python launcher ($Version)" }
            }
        }
    }
    return $null
}

function Install-PrivatePython {
    Write-Host ""
    Write-Host "A compatible 64-bit Python (3.10-3.13) was not found."
    Write-Host "sNote can download the official Python 3.13.17 installer from python.org."
    Write-Host "Python will be installed ONLY under: $RuntimeRoot"
    Write-Host "Administrator privileges and system PATH changes are not required."
    Write-Host "An internet connection is required to download Python and PyQt5."
    $Reply = Read-Host "Download and install Python for sNote now? [Y/n]"
    if ($Reply -notin @("", "y", "Y", "yes", "YES", "Yes")) {
        throw "Python setup was declined. You can instead use a portable sNote.exe release."
    }

    if (-not [Environment]::Is64BitOperatingSystem) {
        throw "This installer supports 64-bit Windows only."
    }

    # Official python.org 64-bit Windows installer, not an untrusted mirror.
    $Url = "https://www.python.org/ftp/python/3.13.17/python-3.13.17-amd64.exe"
    $Download = Join-Path $env:TEMP ("snote-python-" + [guid]::NewGuid().ToString("N") + ".exe")
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
        Write-Host "Downloading official Python installer..."
        try {
            Invoke-WebRequest -Uri $Url -OutFile $Download -UseBasicParsing -ErrorAction Stop
        } catch {
            throw "Python download failed. Check internet access or use the portable sNote.exe release. Details: $($_.Exception.Message)"
        }

        # Never execute a downloaded installer unless its Windows signature is trusted.
        $Signature = Get-AuthenticodeSignature -FilePath $Download
        $Publisher = if ($null -ne $Signature.SignerCertificate) { $Signature.SignerCertificate.Subject } else { "" }
        if ($Signature.Status -ne "Valid" -or $Publisher -notmatch 'Python Software Foundation') {
            throw "Official Python installer failed Windows signature verification (status: $($Signature.Status)). No downloaded code was executed."
        }

        Write-Host "Verified digital signature: Python Software Foundation"
        Write-Host "Installing private Python runtime..."
        $Arguments = @(
            "/quiet", "InstallAllUsers=0", "Include_pip=1", "Include_launcher=0",
            "PrependPath=0", "Include_test=0", "Include_doc=0", "Include_dev=0",
            "TargetDir=`"$RuntimeRoot`""
        )
        $Process = Start-Process -FilePath $Download -ArgumentList $Arguments -Wait -PassThru
        if ($Process.ExitCode -ne 0) {
            throw "Python installation failed (exit code $($Process.ExitCode)). Check Windows policies or use the portable release."
        }
        $ManagedPython = Join-Path $RuntimeRoot "python.exe"
        if (-not (Test-Path $ManagedPython) -or -not (Test-PythonVersion $ManagedPython)) {
            throw "Python installation finished, but its interpreter is missing or incompatible at $ManagedPython."
        }
        return @{ Executable = $ManagedPython; Prefix = @(); Source = "sNote private Python" }
    } finally {
        if (Test-Path $Download) { Remove-Item $Download -Force -ErrorAction SilentlyContinue }
    }
}

function Test-PyQt5 {
    param([string]$Executable)
    # Import the real GUI Qt widgets, rather than checking for a folder name.
    $Probe = @'
import sys
try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import PYQT_VERSION_STR
    parts = tuple(int(n) for n in PYQT_VERSION_STR.split('.')[:3])
    sys.exit(0 if (5, 15, 10) <= parts < (6, 0, 0) else 1)
except Exception:
    sys.exit(1)
'@
    return (Invoke-PythonProbe -Executable $Executable -Script $Probe -Label "PyQt5 GUI import check")
}

try {
    $FreshInstall = -not (Test-Path $Python)
    if (-not $FreshInstall) {
        Write-Host "Existing sNote installation found. Preparing a side-by-side update..."
        if (-not (Test-PythonVersion $Python) -or -not (Test-Path $Pythonw)) {
            Write-Host "The existing virtual environment is not healthy. Rebuilding in a NEW directory."
            Add-InstallerDiagnostic "Old venv is unusable; preserving it and creating a replacement."
            $VenvRoot = Join-Path $InstallRoot ("envs\repair-" + (Get-Date -Format 'yyyyMMddHHmmss'))
            $Python = Join-Path $VenvRoot 'Scripts\python.exe'
            $Pythonw = Join-Path $VenvRoot 'Scripts\pythonw.exe'
            $FreshInstall = $true
        } elseif (-not (Test-PyQt5 $Python)) {
            # Never modify packages or DLLs held open by a running sNote instance.
            Write-Host "Existing PyQt5 is missing or damaged. Creating an isolated repair environment."
            Add-InstallerDiagnostic "Existing PyQt5 probe failed; preserving the old venv."
            $VenvRoot = Join-Path $InstallRoot ("envs\repair-" + (Get-Date -Format 'yyyyMMddHHmmss'))
            $Python = Join-Path $VenvRoot 'Scripts\python.exe'
            $Pythonw = Join-Path $VenvRoot 'Scripts\pythonw.exe'
            $FreshInstall = $true
        }
    }

    if ($FreshInstall) {
        Write-Host "Checking for a compatible Python runtime..."
        $Interpreter = Find-AvailablePython
        if ($null -eq $Interpreter) { $Interpreter = Install-PrivatePython }
        Write-Host "Using $($Interpreter.Source). Creating an isolated sNote environment..."
        $SelectedPython = [string]$Interpreter.Executable
        $PythonArgs = @($Interpreter.Prefix) + @('-m', 'venv', "`"$VenvRoot`"")
        $Code = Invoke-PythonSetup -Executable $SelectedPython -Arguments $PythonArgs -Label "Creating virtual environment"
        if ($Code -ne 0 -or -not (Test-Path $Python)) {
            throw "Could not create the sNote Python environment. See $DiagnosticsLog."
        }
    }

    if (-not (Test-Path $Pythonw)) {
        throw "The Python GUI launcher (pythonw.exe) is missing from the environment. See $DiagnosticsLog."
    }

    # Check installed GUI before pip. A healthy existing installation must never
    # fail merely because its pip package is missing or damaged.
    if (-not (Test-PyQt5 $Python)) {
        $PipProbe = 'import importlib.util,sys; sys.exit(0 if importlib.util.find_spec("pip") else 1)'
        if (-not (Invoke-PythonProbe -Executable $Python -Script $PipProbe -Label "pip availability check")) {
            Write-Host "pip is missing. Restoring pip inside the isolated environment..."
            $Code = Invoke-PythonSetup -Executable $Python -Arguments @('-m', 'ensurepip', '--upgrade') -Label "Restoring pip"
            if ($Code -ne 0) { throw "Could not restore pip. See $DiagnosticsLog." }
        }
        Write-Host "PyQt5 is missing, outdated or damaged. Installing its required packages..."
        $Requirements = Join-Path $ProjectRoot "requirements.txt"
        $Code = Invoke-PythonSetup -Executable $Python -Arguments @('-m', 'pip', 'install', '-r', "`"$Requirements`"", '--upgrade') -Label "Installing PyQt5"
        if ($Code -ne 0) { throw "Could not install PyQt5. Check network/proxy settings and $DiagnosticsLog." }
        if (-not (Test-PyQt5 $Python)) {
            throw "PyQt5 still cannot be loaded after installation. See $DiagnosticsLog."
        }
    } else {
        Write-Host "PyQt5 is installed and working."
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

    $LauncherScript = Join-Path $InstallRoot "start_snote_and_close.ps1"
    Copy-Item (Join-Path $ProjectRoot "scripts/start_snote_and_close.ps1") $LauncherScript -Force
    $CommandFile = Join-Path $BinRoot "sn.cmd"
    $CommandText = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$LauncherScript`" -Pythonw `"$Pythonw`" -WorkingDirectory `"$InstallRoot`" -AppPath `"$ReleaseRoot`"`r`n"
    [System.IO.File]::WriteAllText($CommandFile, $CommandText, [System.Text.Encoding]::ASCII)
    $InstalledIcon = Join-Path $InstallRoot "snote.ico"
    Copy-Item (Join-Path $ProjectRoot "src/snote/resources/snote.ico") $InstalledIcon -Force

    # The desktop shortcut uses pythonw.exe: no visible console window.
    $GuiLauncher = Join-Path $InstallRoot "start_snote.vbs"
    $GuiLauncherText = @"
Set shell = CreateObject("WScript.Shell")
shell.Environment("PROCESS")("PYTHONPATH") = "$ReleaseRoot"
shell.Run Chr(34) & "$Pythonw" & Chr(34) & " -m snote", 0, False
"@
    [System.IO.File]::WriteAllText($GuiLauncher, $GuiLauncherText, [System.Text.Encoding]::Unicode)

    # WindowsApps is an optional convenience. Some machines block writing there.
    $WindowsApps = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps"
    if (Test-Path $WindowsApps) {
        try {
            $ImmediateCommand = Join-Path $WindowsApps "sn.cmd"
            [System.IO.File]::WriteAllText($ImmediateCommand, $CommandText, [System.Text.Encoding]::ASCII)
        } catch {
            Write-Host "WindowsApps shortcut could not be created. The standard sn command is still installed."
        }
    }

    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $PathItems = @($UserPath -split ";" | Where-Object { $_ })
    if ($PathItems -notcontains $BinRoot) {
        [Environment]::SetEnvironmentVariable("Path", (($PathItems + $BinRoot) -join ";"), "User")
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

    # Import V0.28 portable settings only when the user's settings do not exist.
    $LegacyLinks = Join-Path $ProjectRoot "links"
    $UserSettings = Join-Path $env:APPDATA "sNote"
    if ((Test-Path $LegacyLinks) -and -not (Test-Path $UserSettings)) {
        New-Item -ItemType Directory -Force -Path $UserSettings | Out-Null
        Copy-Item (Join-Path $LegacyLinks "*.json") $UserSettings -Force
    }

    # Switch to the new release only after dependencies and launchers succeed.
    [System.IO.File]::WriteAllText(
        (Join-Path $InstallRoot "current_release.txt"), $ReleaseRoot, [System.Text.Encoding]::UTF8
    )

    Write-Host "sNote $Version installed successfully."
    Write-Host "Installer log: $InstallerLog"
    Write-Host "Starting sNote..."

    # Do not kill a running editor: allow the normal Save/Discard/Cancel prompt.
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
        Write-Host "Update installed. Close and reopen sNote to use the new version."
    }
} catch {
    $Failure = ($_ | Out-String)
    $FailureLine = $_.InvocationInfo.ScriptLineNumber
    Add-InstallerDiagnostic "Installer failure at line $FailureLine : $Failure"
    Write-Host "" -ForegroundColor Red
    Write-Host "sNote installation FAILED at script line $FailureLine : $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Installer log: $InstallerLog" -ForegroundColor Yellow
    Write-Host "Detailed error log: $DiagnosticsLog" -ForegroundColor Yellow
    Write-Host "No existing notes, settings or old release were deleted." -ForegroundColor Yellow
    exit 1
} finally {
    try { Stop-Transcript | Out-Null } catch { }
}
