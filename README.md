# sNote

**sNote is a lightweight desktop editor and personal work hub.** It combines fast text and
Markdown editing with frequently used files, programs, websites, system tools, and a terminal
that follows the current document's folder.

The project began with a practical goal: reduce the time spent moving between Notepad, File
Explorer, browser bookmarks, application shortcuts, and PowerShell while working with many
small text files.

## What sNote does

- Opens multiple text, Markdown, HTML, Python, CSV, and JSON files in tabs.
- Creates plain-text, Markdown, and HTML documents.
- Shows line numbers, cursor position, file path, and unsaved status.
- Provides light and dark themes, font selection, and zoom controls.
- Finds, replaces, replaces all, and jumps to a line.
- Converts rich clipboard content to Markdown with `Ctrl+Shift+V`.
- Shows a live Markdown or HTML preview.
- Keeps configurable menus for memo files, programs, websites, and system utilities.
- Opens an integrated terminal in the current document's folder.
- Opens an external terminal in the same working folder.
- Saves documents and JSON settings atomically to reduce file corruption.

## Privacy

sNote is a local desktop application. It does not send note content to a server.

Personal link lists, settings, crash logs, and recent-file history are stored separately from the
application:

- Windows: `%APPDATA%\sNote`
- macOS: `~/Library/Application Support/sNote`
- Linux: `${XDG_CONFIG_HOME:-~/.config}/snote`

The repository contains only privacy-safe defaults. Do not commit a personal `links` folder,
recent-file list, or note archive.

## Install on Windows

### Easy installation — double-click

1. Download and extract the ZIP. Do not run the installer inside the ZIP preview.
2. Double-click **`Install-sNote.cmd`**.
3. Wait for the installation to finish. The installer window closes automatically and only
   sNote remains open.

The installer creates a desktop shortcut and the `sn` command. It can also update an existing
installation by double-clicking the same file again. Updates are deployed to a new versioned
folder and never uninstall or overwrite the release currently in use. The installer asks a running
sNote window to close normally, allowing its unsaved-document prompt to appear, and never
force-kills it. Python 3.10 or newer and an internet connection are required for the first
installation.

Windows may display a SmartScreen message for a downloaded command file. Select **More info** and
**Run anyway** only when the ZIP was downloaded from the official project release.

To uninstall the application while keeping personal settings, double-click:

```text
Uninstall-sNote.cmd
```

After installation, sNote can be opened from the desktop icon or from any terminal:

```powershell
sn
```

The `sn` command starts the GUI and then closes the PowerShell or Command Prompt session that
launched it, leaving only sNote open. The desktop shortcut never opens a terminal window.

By default, sNote opens centered at approximately **1250 × 950 pixels**. On a smaller display it
automatically reduces the size to remain within the usable desktop area.

### Advanced PowerShell installation

The same installer can be run manually when troubleshooting:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_windows.ps1
```

### Option B — portable Windows build

Download the Windows artifact from GitHub Actions or a release, extract the ZIP, and run
`sNote.exe`. Keep the executable and its `_internal` folder together.

## Install on Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pyqt5
python3 -m venv --system-site-packages .venv
. .venv/bin/activate
python -m pip install -e . --no-deps
snote
```

If PyQt5 is available from PyPI for your system, a normal virtual environment also works:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
snote
```

## Developer setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check .
pytest
python -m snote
```

Build the portable Windows ZIP from PowerShell:

```powershell
.\scripts\build_windows.ps1
```

GitHub Actions runs lint and tests on Windows and Ubuntu with Python 3.10 and 3.12. It also
produces a downloadable Windows x64 artifact.

## Main shortcuts

| Action | Shortcut |
| --- | --- |
| New text document | `Ctrl+N` |
| New Markdown document | `Ctrl+Alt+N` |
| New HTML document | `Ctrl+Alt+H` |
| Open file | `Ctrl+O` |
| Save / Save as | `Ctrl+S` / `Ctrl+Shift+S` |
| Find / Replace | `Ctrl+F` / `Ctrl+H` |
| Find next / previous | `F3` / `Shift+F3` |
| Go to line | `Ctrl+G` |
| Paste as Markdown | `Ctrl+Shift+V` |
| Toggle preview | `Ctrl+Shift+M` |
| Toggle line numbers | `Ctrl+L` |
| Integrated terminal | <kbd>Ctrl</kbd> + <kbd>&#96;</kbd> |
| External terminal | <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>&#96;</kbd> |

The first ten items in each link menu receive number shortcuts:

- Memo links: `Ctrl+1` … `Ctrl+0`
- Program links: `Ctrl+Alt+1` … `Ctrl+Alt+0`
- Web links: `Alt+1` … `Alt+0`
- System links: `Ctrl+Shift+1` … `Ctrl+Shift+0`

## Link menus

Use **Manage links** inside any link menu to add, remove, rename, browse for, or reorder items.
The menu can open editable text files inside sNote and other files with their default application.
URLs open in the default browser.

## Integrated terminal

On Windows, sNote uses Windows PowerShell. On Linux and macOS, it uses Bash or the available
system shell. The terminal starts in the current file's folder; a new unsaved document uses the
application folder.

Simple `cp`, `mv`, `rm`, and `mkdir` commands are handled directly. Complex commands containing
pipes, redirection, command chaining, or scripts are passed to the shell. Terminal commands have
the same permissions as the current user. Review recursive delete commands carefully.

## Project layout

```text
src/snote/app.py                 PyQt desktop application
src/snote/core.py                Markdown and safe JSON helpers
src/snote/resources/             Icons and privacy-safe defaults
tests/                           Core and privacy regression tests
scripts/install_windows.ps1      Windows source installer
scripts/build_windows.ps1        Portable Windows build
.github/workflows/ci.yml         Automated tests and Windows packaging
```

## 한국어 안내

sNote는 여러 메모 파일을 빠르게 편집하면서 자주 쓰는 메모, 프로그램, 웹사이트,
Windows 시스템 도구와 터미널을 한곳에서 실행하기 위한 개인 작업 허브입니다.

GitHub 공개판에는 개인 메모, 개인 프로그램 경로와 최근 파일 기록이 포함되지 않습니다.
처음 실행하면 사용자 설정 폴더에 안전한 기본 설정이 생성되며, 이후 Link Manager에서
필요한 경로와 웹사이트를 직접 등록할 수 있습니다. V0.28 휴대용 버전의 실행 파일 옆에
기존 `links` 폴더가 있으면 첫 실행 때 해당 설정을 자동으로 가져옵니다.

Windows에서는 ZIP의 압축을 푼 뒤 `Install-sNote.cmd`를 더블클릭하면 됩니다. 설치가 끝나면
설치 창은 자동으로 닫히고 SNote만 실행됩니다. 이후에는 바탕화면의 `sNote` 아이콘이나
`sn` 명령으로 실행할 수 있습니다. `sn`으로 실행하면 SNote를 실행한 PowerShell 또는 CMD도
종료됩니다. SNote의 기본 창은 화면 중앙에 약 1250 × 950 크기로 열립니다. Python 없이
사용하는 배포본은 GitHub Actions가 만든 Windows ZIP을 내려받아 `sNote.exe`를 실행하면 됩니다.

## License

MIT License. See [LICENSE](LICENSE).
