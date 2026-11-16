# sNote 1.1.6: Windows installation and update

This guide applies to Windows 11, 64-bit. No administrator account is needed for the auto-installer.

## Option 1: easy auto-installer (source package)

1. Extract **sNote-1.1.6-source-auto-install.zip** to a normal folder.
2. Double-click **Install-sNote.cmd**. Do not run the CMD directly from within ZIP preview.
3. If a compatible 64-bit Python 3.10–3.13 is available, the installer uses it only to create an
   isolated sNote virtual environment. Python used by other programs is not modified.
4. If no compatible Python is found, the installer offers to download Python 3.13.17 (x64)
   from the official python.org site. Press **Y** or **Enter** to consent, **N** to cancel.
   The download is checked for a valid **Python Software Foundation** code signature
   before it is run. The private runtime is installed in `%LOCALAPPDATA%\sNote\python`.
5. If pip is missing, it is restored locally. If PyQt5 is missing, outdated, or fails to import,
   the installer downloads and installs it
   into `%LOCALAPPDATA%\sNote\venv` (or a new `%LOCALAPPDATA%\sNote\envs\repair-*` folder when repairing a damaged existing environment). No system-wide pip package is altered.
6. During environment creation or PyQt5 installation, the installer displays a rotating
   `/ - \ |` symbol, elapsed seconds and **approximate stage progress**, such as `[~42%]`.
   The percentage is a phase estimate, **not** a measured percentage of downloaded bytes.
   A steady percentage with a moving spinner means the installer is still waiting for a process.
7. When installation completes, sNote starts and a desktop shortcut appears.

The installer needs internet access **only when components are missing**. If the automatic
Python download is blocked by a proxy, antivirus or workplace policy, use the portable option
below or install official Python manually and rerun Install-sNote.cmd.

## Option 2: portable Windows app (no Python installation)

Download the **sNote-1.1.6-windows-x64.zip** release artifact when it has been published.
Extract it, and run `sNote.exe` in the extracted folder. Keep `_internal` together with
`sNote.exe`. Python and PyQt5 are bundled inside this PyInstaller build.

The portable build must be generated on Windows; the source installer ZIP does not include
an executable or pre-downloaded Python files.

## Where files are stored

- Application: `%LOCALAPPDATA%\sNote\app\<version>-<timestamp>`
- Isolated environment: `%LOCALAPPDATA%\sNote\venv`
- Managed Python, when needed: `%LOCALAPPDATA%\sNote\python`
- Personal settings and link lists: `%APPDATA%\sNote` (preserved during updates/uninstall)
- Installer troubleshooting log: `%LOCALAPPDATA%\sNote\install.log`
- Detailed dependency errors: `%LOCALAPPDATA%\sNote\install-diagnostics.log`

The installer keeps the installed version it is replacing until the update is complete.
If sNote is open, the editor can prompt to save changes before closing. If you cancel that
prompt, simply exit and reopen sNote when ready.

## Troubleshooting

- **Download failed:** Check the internet connection and HTTPS/proxy access to `www.python.org`
  and the Python package index (PyPI); retry or use the portable Windows release.
- **Python signature verification failed:** Do not bypass this check. Download Python directly
  from `https://www.python.org/downloads/windows/` or use a verified portable build.
- **PyQt5 install failed:** Check Windows security software, network permissions, and
  `%LOCALAPPDATA%\sNote\install.log`.
- **Existing sNote environment is damaged:** Close sNote and review the install log. Do not
  delete `%APPDATA%\sNote` because it contains your notes-related settings and links.
- **Program won't open:** Use the desktop shortcut, then review
  `%APPDATA%\sNote\crash.log` (if present) and the installer log.

To uninstall the application (while preserving personal settings), run `Uninstall-sNote.cmd`.

## For developers

GitHub Actions on Windows builds both ZIP types for a tagged `v1.1.6` release:
`scripts/build_windows.ps1` produces a portable PyInstaller EXE bundle, and
`scripts/build_source_zip.ps1` produces the automatic dependency installer source ZIP.
Do not publish a version tag until Windows CI and a clean-machine install are verified.
