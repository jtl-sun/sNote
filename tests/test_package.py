import ast
from pathlib import Path


def test_application_source_is_valid_python():
    source = Path("src/snote/app.py").read_text(encoding="utf-8")
    ast.parse(source)


def test_default_json_files_are_privacy_safe():
    resources = Path("src/snote/resources/links")
    combined = "\n".join(path.read_text(encoding="utf-8") for path in resources.glob("*.json"))
    forbidden = ("C:\\Users\\", "S:\\", "D:\\", "F:\\")
    assert not any(value in combined for value in forbidden)


def test_requested_startup_size_and_terminal_closer_are_packaged():
    app_source = Path("src/snote/app.py").read_text(encoding="utf-8")
    closer = Path("scripts/start_snote_and_close.ps1").read_text(encoding="utf-8")
    assert "window.showNormal()" in app_source
    assert "min(1440" in app_source
    assert "min(900" in app_source
    assert "screen = app.primaryScreen()" in app_source
    assert "Stop-Process" in closer


def test_updater_reuses_existing_environment():
    installer = Path("scripts/install_windows.ps1").read_text(encoding="utf-8")
    assert "$FreshInstall = -not (Test-Path $Python)" in installer
    assert "if ($FreshInstall)" in installer
    assert "$ReleaseRoot = Join-Path $AppsRoot $ReleaseId" in installer
    assert "pip install --upgrade $ProjectRoot" not in installer
    assert "CloseMainWindow" in installer


def test_pyqt_probe_does_not_emit_an_expected_import_traceback():
    installer = Path("scripts/install_windows.ps1").read_text(encoding="utf-8")
    assert 'from PyQt5.QtWidgets import QApplication' in installer
    assert 'except Exception:' in installer
    assert 'return ($Process.ExitCode -eq 0)' in installer
    assert '-c "import PyQt5"' not in installer


def test_help_menu_opens_bundled_manual():
    app_source = Path("src/snote/app.py").read_text(encoding="utf-8")
    manual = Path("src/snote/resources/SNOTE_MANUAL.md")
    assert 'QAction("sNote &Manual"' in app_source
    assert "Open Settings &Folder" not in app_source
    assert "def show_manual(self):" in app_source
    manual_text = manual.read_text(encoding="utf-8")
    assert manual.exists() and "sNote User Manual" in manual_text
    assert "sNote 사용자 매뉴얼" not in manual_text


def test_link_menus_do_not_expose_raw_json_editor():
    app_source = Path("src/snote/app.py").read_text(encoding="utf-8")
    assert "Manage links" in app_source
    assert "Edit JSON File" not in app_source


def test_internal_terminal_is_replaced_by_native_powershell():
    app_source = Path("src/snote/app.py").read_text(encoding="utf-8")
    assert "self.embedded_terminal" not in app_source
    assert "self.terminal_dock" not in app_source
    assert 'QAction("Open &PowerShell Below sNote"' in app_source
    assert "subprocess.CREATE_NEW_CONSOLE" in app_source
    assert "def position_powershell_below(self):" in app_source
    assert "user32.SetWindowPos" in app_source
    assert "total_height = min(layout_rect.height()" in app_source
    assert "note_height = total_height // 2" in app_source
    assert "terminal_height = total_height - note_height" in app_source
    assert "wintypes.HWND(int(self.winId()))" in app_source
    assert "self.powershell_layout_rect = QRect(self.frameGeometry())" in app_source
