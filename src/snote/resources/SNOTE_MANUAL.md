# sNote User Manual

Version: {APP_VERSION}

sNote is a lightweight desktop editor that brings note-taking, Markdown and HTML previews,
frequently used files, programs, websites, and terminal tools into one place.

## 1. Installation and Launch

- Extract the downloaded ZIP file, then double-click `Install-sNote.cmd` to install or update sNote.
- After installation, open sNote from the **sNote** desktop shortcut.
- You can also enter `sn` in a terminal to launch it.
- Personal settings and links are stored in `%APPDATA%\sNote`.

## 2. File Editing

- New text document: `Ctrl+N`
- New Markdown document: `Ctrl+Alt+N`
- New HTML document: `Ctrl+Alt+H`
- Open a file: `Ctrl+O`
- Save: `Ctrl+S`
- Save As: `Ctrl+Shift+S`
- Quit: `Ctrl+Q`

sNote can open TXT, Markdown, HTML, Python, CSV, and JSON files in multiple tabs. Modified tabs
display an asterisk. If you try to close a modified document, sNote asks whether to save it.

## 3. Find and Edit

- Find: `Ctrl+F`
- Replace: `Ctrl+H`
- Find next: `F3`
- Find previous: `Shift+F3`
- Go to line: `Ctrl+G`
- Undo/Redo: `Ctrl+Z` / `Ctrl+Y`
- Cut/Copy/Paste: `Ctrl+X` / `Ctrl+C` / `Ctrl+V`

## 4. Markdown and HTML

- Preview Markdown or HTML: `Ctrl+Shift+M`
- Paste formatted web content as Markdown: `Ctrl+Shift+V`
- The preview supports Markdown headings, lists, links, images, quotes, and code blocks.
- HTML preview is intended for document inspection and does not run JavaScript.

## 5. Display Settings

- Show or hide line numbers: `Ctrl+L`
- Zoom in/out: `Ctrl++` / `Ctrl+-`
- Reset the font size: `Ctrl+0`
- Select White Mode or Dark Mode from the `View` menu.
- Change the editor font from the `Font` menu.

## 6. Link Menus

sNote provides four link menus:

- Memo Links: frequently used note files
- Program Links: applications and executable files
- Web Links: websites
- System Links: system tools such as Calculator and PowerShell

Use **Manage links** in each menu to add, remove, edit, or reorder entries.

Shortcuts are automatically assigned to the first ten entries:

- Memo Links: `Ctrl+1` through `Ctrl+0`
- Program Links: `Ctrl+Alt+1` through `Ctrl+Alt+0`
- Web Links: `Alt+1` through `Alt+0`
- System Links: `Ctrl+Shift+1` through `Ctrl+Shift+0`

## 7. Terminal

- Show or hide the built-in terminal: <kbd>Ctrl</kbd> + <kbd>&#96;</kbd>
- Open an external terminal: <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>&#96;</kbd>
- For a saved document, the terminal starts in that document's folder.
- For a new document, the sNote program folder is used as the working directory.
- Run a command: `Enter`
- Insert a line break while typing a command: `Shift+Enter`
- Previous/next command: Up/Down Arrow
- Clear the terminal: `clear` or `cls`

Basic file commands such as `cp`, `mv`, `rm`, and `mkdir` are available. Be careful with `rm -r`,
because it deletes a folder and its contents. Always verify the target path first.

## 8. Personal Settings and Backup

On Windows, your personal configuration folder is:

```text
%APPDATA%\sNote
```

This folder stores the theme, line-number preference, recent files, and link lists. Uninstalling
sNote does not automatically remove these personal settings. To make a backup, copy the entire
folder to a safe location.

## 9. Updating sNote

Extract the new ZIP file and double-click `Install-sNote.cmd` again. You do not need to uninstall
the previous version first, and your settings and links are preserved. If sNote is running, the
installer requests a normal close, so a prompt may appear for any unsaved documents.

## 10. Troubleshooting

- If the `sn` command is not recognized, use the sNote desktop shortcut.
- If installation fails, capture the error screen for troubleshooting.
- Crash details are written to `%APPDATA%\sNote\crash.log`.
- Check the installed version from `Help > About sNote`.

You can reopen this manual at any time from `Help > sNote Manual` or by pressing `F1`.
