from pathlib import Path


INSTALL = Path('scripts/install_windows.ps1').read_text(encoding='utf-8')
README = Path('README.md').read_text(encoding='utf-8')
RELEASE = Path('.github/workflows/release.yml').read_text(encoding='utf-8')


def test_missing_python_is_detected_and_user_asked_before_installing():
    assert 'function Find-AvailablePython' in INSTALL
    assert 'function Test-PythonVersion' in INSTALL
    assert 'Get-Command python.exe' in INSTALL
    assert 'Get-Command py.exe' in INSTALL
    assert 'Read-Host "Download and install Python for sNote now? [Y/n]"' in INSTALL
    assert 'if ($null -eq $Interpreter) { $Interpreter = Install-PrivatePython }' in INSTALL


def test_python_is_downloaded_from_official_source_and_signed_before_execution():
    assert 'https://www.python.org/ftp/python/3.13.17/python-3.13.17-amd64.exe' in INSTALL
    assert 'Get-AuthenticodeSignature -FilePath $Download' in INSTALL
    assert "-notmatch 'Python Software Foundation'" in INSTALL
    assert INSTALL.index('Get-AuthenticodeSignature -FilePath $Download') < INSTALL.index('Start-Process -FilePath $Download')
    assert 'InstallAllUsers=0' in INSTALL
    assert 'PrependPath=0' in INSTALL
    assert 'Join-Path $InstallRoot "python"' in INSTALL


def test_python_probe_restricts_version_to_supported_64bit_versions():
    assert '(3,10) <= sys.version_info[:2] < (3,14)' in INSTALL
    assert 'sys.maxsize > 2**32' in INSTALL
    assert 'Invoke-PythonSetup -Executable $SelectedPython' in INSTALL
    assert "@('-m', 'venv'" in INSTALL


def test_installer_repairs_pyqt_and_checks_real_qtwidgets_import():
    assert 'function Test-PyQt5' in INSTALL
    assert 'from PyQt5.QtWidgets import QApplication' in INSTALL
    assert '(5, 15, 10) <= parts' in INSTALL
    assert "'-m', 'pip', 'install', '-r'" in INSTALL
    assert "'-m', 'ensurepip', '--upgrade'" in INSTALL
    assert 'if (-not (Test-PyQt5 $Python))' in INSTALL


def test_side_by_side_upgrade_and_personal_settings_are_retained():
    assert '$FreshInstall = -not (Test-Path $Python)' in INSTALL
    assert '$ReleaseRoot = Join-Path $AppsRoot $ReleaseId' in INSTALL
    assert 'Copy-Item (Join-Path $ProjectRoot "src/snote")' in INSTALL
    assert 'CloseMainWindow()' in INSTALL
    assert '-not (Test-Path $UserSettings)' in INSTALL
    assert 'Remove-Item $UserSettings' not in INSTALL


def test_auto_install_instructions_and_logging_present():
    assert 'install.log' in INSTALL
    assert 'Start-Transcript' in INSTALL
    assert 'INSTALL_WINDOWS.md' in README
    assert Path('INSTALL_WINDOWS.md').is_file()


def test_release_provides_both_executable_and_auto_installer():
    assert 'scripts/build_windows.ps1' in RELEASE
    assert 'scripts/build_source_zip.ps1' in RELEASE
    assert 'release/sNote-*-windows-x64.zip' in RELEASE
    assert 'release/sNote-*-source-auto-install.zip' in RELEASE
    source_builder = Path('scripts/build_source_zip.ps1').read_text(encoding='utf-8')
    assert '"Install-sNote.cmd"' in source_builder
    assert '"src"' in source_builder
    assert '"scripts"' in source_builder
    assert '"INSTALL_WINDOWS.md"' in source_builder


def test_probe_failure_does_not_crash_powershell_on_stderr():
    assert 'Start-Process -FilePath $Executable' in INSTALL
    assert '-RedirectStandardError $Stderr' in INSTALL
    assert 'Invoke-PythonProbe' in INSTALL
    assert '2>$null' not in INSTALL.split('function Invoke-PythonProbe {', 1)[1]

def test_damaged_old_environment_is_preserved_for_recovery():
    assert r'envs\repair-' in INSTALL
    assert 'install-diagnostics.log' in INSTALL
    assert 'No existing notes, settings or old release were deleted.' in INSTALL
