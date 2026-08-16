# Changelog

All notable changes are documented here.

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
