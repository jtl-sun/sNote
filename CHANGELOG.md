# Changelog

All notable changes are documented here.

## 1.1.5 - 2026-11-16

- Prevent Windows PowerShell 5.1 from treating stderr from a Python dependency check as a fatal NativeCommandError.
- Execute diagnostic and installation subprocesses with redirected files and record complete error details.
- Verify the existing Python environment and PyQt5 GUI import before updating; create a separate repair environment if damaged.
- Keep existing user configuration and previous application releases untouched on installer failure.
- Add detailed diagnostics in `%LOCALAPPDATA%\sNote\install-diagnostics.log`.

## 1.1.4 - 2026-11-16

- Detect missing or incompatible Windows Python and offer to download the official signed
  Python 3.13.17 x64 installer from python.org, with explicit user consent.
- Install Python privately in the current user's sNote application folder without administrator
  rights and without modifying the system Python or system PATH.
- Detect missing, outdated or unusable PyQt5 and automatically install/repair its dependencies
  in sNote's isolated virtual environment.
- Add a local installer log and actionable errors for offline downloads and installation failures.
- Preserve per-user settings, side-by-side upgrades, native PowerShell, and UI behavior.
- Make the GitHub release workflow publish both the portable EXE ZIP and the source auto-installer ZIP.

## 1.1.3 - 2026-09-01

- Fix first-time Windows installation stopping at the PyQt5 availability check.
- Use a silent module probe so an expected missing dependency is not promoted to
  `NativeCommandError` before the installer can install it.
- Preserve the centered 1440 × 900 startup window and native PowerShell half-screen layout.

## 1.1.2 - 2026-08-17

- Set the default sNote window size to approximately 1440 × 900 pixels.
- Center the initial window in the primary monitor's usable desktop area.
- Automatically reduce the size on displays that cannot fit the requested dimensions.

## 1.1.1 - 2026-08-17

- Split the original sNote window area equally when opening PowerShell below it.
- Place sNote in the upper half and PowerShell in the lower half.
- Keep both windows aligned to the same width and horizontal position.
- Reuse the original layout on repeated shortcuts so the windows never shrink progressively.

## 1.1.0 - 2026-08-17

- Remove the integrated-terminal panel from the sNote interface.
- Launch the real Windows PowerShell with `Ctrl+Backtick` in the current document folder.
- Automatically tile the native PowerShell window directly below sNote.
- Keep `Ctrl+Shift+Backtick` for a normal independent terminal window.

## 1.0.11 - 2026-08-17

- Present terminal output and input as one continuous PowerShell-style surface.
- Remove the white border and contrasting background from the active input line.
- Display interactive prompts immediately instead of holding their final characters while waiting
  for the internal completion marker.

## 1.0.10 - 2026-08-17

- Separate terminal output from a dedicated command/input field.
- Fix normal PowerShell commands requiring Enter twice.
- Prevent asynchronous program output from being inserted into typed responses.
- Encode each PowerShell command into a complete single-line execution block.

## 1.0.9 - 2026-08-17

- Fix the integrated terminal becoming input-locked while an interactive program is running.
- Forward menu choices and other line input to the active child program.
- Preserve partially typed input when asynchronous output arrives.
- Limit terminal history to 10,000 lines to prevent slowdowns during long-running commands.

## 1.0.8 - 2026-08-17

- Replace the bundled Korean manual with a complete English user manual.
- Keep the manual available from `Help > sNote Manual` and the `F1` shortcut.

## 1.0.7 - 2026-08-17

- Remove the redundant `Edit JSON File` action from all link menus.
- Keep `Manage links` as the single link-editing interface.

## 1.0.6 - 2026-08-17

- Replace `Open Settings Folder` with `sNote Manual` in the Help menu.
- Add a bundled Korean user manual displayed in a read-only dialog.
- Add `F1` as the manual shortcut.

## 1.0.5 - 2026-08-17

- Deploy updates side by side instead of uninstalling the active package.
- Fix `WinError 32` when the existing `site-packages\\snote` folder is in use.
- Point the desktop and `sn` launchers to the newly deployed release.
- Avoid reinstalling PyQt when it is already available.
- Request a normal close of an older running window, preserving unsaved-document prompts.

## 1.0.4 - 2026-08-17

- Fix `Permission denied ... pythonw.exe` during updates.
- Reuse the existing virtual environment instead of recreating it.
- Keep first-time installation behavior unchanged.

## 1.0.3 - 2026-08-17

- Move the Help menu to the far right, immediately after System Links.

## 1.0.2 - 2026-08-17

- Open sNote centered at approximately 1250 × 950 pixels instead of maximized.
- Make the installed `sn` launcher close the PowerShell or Command Prompt session that launched it.
- Close the calling terminal after successful one-click installation.
- Keep desktop-shortcut launches console-free.

## 1.0.1 - 2026-08-17

- Open sNote maximized on startup.
- Added the one-click `Install-sNote.cmd` and `Uninstall-sNote.cmd` launchers.
- Launch sNote automatically when installation finishes, without a console window.
- Install the `sn` command in the existing WindowsApps PATH so it works immediately.

## 1.0.0 - 2026-08-17

- Reorganized sNote as an installable Python package.
- Moved personal settings and links to a writable per-user configuration folder.
- Added one-time migration of legacy portable `links` data on first launch.
- Added privacy-safe default links; personal paths and recent files are not distributed.
- Added atomic document and JSON saving to reduce corruption after interruption.
- Added `snote` and `sn` terminal launch commands.
- Added Windows installer, uninstaller, PyInstaller build script, tests, and GitHub Actions.
- Added project, security, contribution, and release documentation.
- Preserved the V0.28 editor, Markdown/HTML preview, link hub, and terminal features.
