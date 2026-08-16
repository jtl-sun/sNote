"""sNote desktop application."""

import sys
import re
from pathlib import Path

from . import __version__
from .core import (
    atomic_write_json,
    html_to_markdown,
    link_file_name,
    read_json,
    user_config_directory,
)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QAction, QFileDialog,
    QFontDialog, QInputDialog, QMessageBox, QVBoxLayout, QWidget,
    QLineEdit, QPushButton, QLabel, QHBoxLayout, QTabWidget,
    QPlainTextEdit, QActionGroup, QDialog, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextBrowser, QDockWidget,
    QSplashScreen
)
from PyQt5.QtGui import (
    QKeySequence, QFont, QPainter, QTextFormat, QColor, QTextDocument, QTextCursor,
    QTextCharFormat, QPalette, QPixmap, QIcon
)
from PyQt5.QtCore import (
    Qt, QSize, QRect, QUrl, QProcess, QTimer, pyqtSignal, QSaveFile, QIODevice
)


APP_VERSION = __version__
EDITABLE_SUFFIXES = {".txt", ".md", ".markdown", ".html", ".htm", ".py", ".csv", ".json"}
FILE_DIALOG_FILTER = (
    "Editable Files (*.txt *.md *.markdown *.html *.htm *.py *.csv *.json);;"
    "HTML Files (*.html *.htm);;"
    "Markdown Files (*.md *.markdown);;"
    "Python Files (*.py);;"
    "CSV Files (*.csv);;"
    "JSON Files (*.json);;"
    "Text/Markdown Files (*.txt *.md);;"
    "All Files (*)"
)
LINK_CATEGORIES = ["Memo links", "Program links", "Web links", "System links"]


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = None
        self.current_file = "Untitled"
        self.theme = "light"
        
        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.line_numbers_visible = True
        self.line_number_bg = QColor("#f0f0f0")
        self.line_number_text = QColor("#787878")
        self.current_line_bg = QColor("#eef2f7")

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def is_markdown_document(self):
        name = self.file_path or self.current_file or ""
        return Path(name).suffix.lower() in {".md", ".markdown"}

    def is_html_document(self):
        name = self.file_path or self.current_file or ""
        return Path(name).suffix.lower() in {".html", ".htm"}

    def insertFromMimeData(self, source):
        """Ctrl+V converts rich web clipboard content in Markdown documents."""
        if self.is_markdown_document() and source.hasHtml():
            markdown = html_to_markdown(source.html())
            if markdown:
                self.textCursor().insertText(markdown)
                return
        super().insertFromMimeData(source)

    def paste_as_markdown(self):
        mime = QApplication.clipboard().mimeData()
        if mime.hasHtml():
            markdown = html_to_markdown(mime.html())
            if markdown:
                self.textCursor().insertText(markdown)
                return True
        if mime.hasText():
            self.textCursor().insertText(mime.text())
            return True
        return False

    def setLineNumbersVisible(self, visible):
        self.line_numbers_visible = visible
        self.lineNumberArea.setVisible(visible)
        if visible:
            self.updateLineNumberAreaWidth(0)
        else:
            self.setViewportMargins(0, 0, 0, 0)

    def setTheme(self, theme):
        self.theme = theme
        if theme == "dark":
            self.line_number_bg = QColor("#2d2d2d")
            self.line_number_text = QColor("#858585")
            self.current_line_bg = QColor("#2c313c")
        else:
            self.line_number_bg = QColor("#f0f0f0")
            self.line_number_text = QColor("#787878")
            self.current_line_bg = QColor("#eef2f7")
        self.highlightCurrentLine()
        self.lineNumberArea.update()

    def lineNumberAreaWidth(self):
        if not self.line_numbers_visible:
            return 0
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        if self.line_numbers_visible:
            self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)
        else:
            self.setViewportMargins(0, 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        if not self.line_numbers_visible:
            return
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), self.line_number_bg)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(self.line_number_text)
                painter.drawText(0, top, self.lineNumberArea.width() - 3, self.fontMetrics().height(),
                                 Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(self.current_line_bg)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)


class TerminalConsole(QPlainTextEdit):
    commandSubmitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = []
        self.history_index = 0
        self.input_start = 0
        self.accepting_input = False
        self.setUndoRedoEnabled(False)
        self.setFont(QFont("Consolas", 11))
        self.setToolTip("Enter: run command / Shift+Enter: new line")

    def remember(self, command):
        if command and (not self.history or self.history[-1] != command):
            self.history.append(command)
        self.history_index = len(self.history)

    def append_output(self, text):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        output_format = QTextCharFormat()
        output_format.setForeground(self.palette().color(QPalette.Text))
        output_format.setFontWeight(QFont.Normal)
        cursor.insertText(text, output_format)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def show_prompt(self, prompt):
        if self.toPlainText() and not self.toPlainText().endswith("\n"):
            self.append_output("\n")
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        prompt_format = QTextCharFormat()
        prompt_format.setForeground(QColor("#32CD32"))
        prompt_format.setFontWeight(QFont.Bold)
        cursor.insertText(prompt, prompt_format)
        input_format = QTextCharFormat()
        input_format.setForeground(self.palette().color(QPalette.Text))
        input_format.setFontWeight(QFont.Normal)
        cursor.setCharFormat(input_format)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        self.input_start = self.document().characterCount() - 1
        self.accepting_input = True
        self.setFocus(Qt.OtherFocusReason)

    def current_command(self):
        return self.toPlainText()[self.input_start:]

    def replace_current_command(self, command):
        cursor = self.textCursor()
        cursor.setPosition(self.input_start)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cursor.insertText(command)
        self.setTextCursor(cursor)

    def move_to_input_end(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

    def keyPressEvent(self, event):
        if (
            event.key() in (Qt.Key_Return, Qt.Key_Enter)
            and not (event.modifiers() & Qt.ShiftModifier)
        ):
            if self.accepting_input:
                command = self.current_command().strip()
                if command:
                    self.remember(command)
                self.move_to_input_end()
                super().keyPressEvent(event)
                self.accepting_input = False
                self.commandSubmitted.emit(command)
            event.accept()
            return
        if not self.accepting_input:
            if event.matches(QKeySequence.Copy):
                super().keyPressEvent(event)
            return
        if event.key() == Qt.Key_Up and self.history and not (event.modifiers() & Qt.ShiftModifier):
            self.history_index = max(0, self.history_index - 1)
            self.replace_current_command(self.history[self.history_index])
            return
        if event.key() == Qt.Key_Down and self.history and not (event.modifiers() & Qt.ShiftModifier):
            self.history_index = min(len(self.history), self.history_index + 1)
            self.replace_current_command(
                "" if self.history_index == len(self.history) else self.history[self.history_index]
            )
            return
        if event.key() in (Qt.Key_Backspace, Qt.Key_Left):
            if self.textCursor().position() <= self.input_start:
                return
        if event.key() == Qt.Key_Home:
            cursor = self.textCursor()
            cursor.setPosition(self.input_start)
            self.setTextCursor(cursor)
            return
        if self.textCursor().position() < self.input_start and event.text():
            self.move_to_input_end()
        super().keyPressEvent(event)


class EmbeddedTerminal(QWidget):
    """A small persistent shell embedded in a dock widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
        self.working_directory = None
        self.shell_kind = None
        self.output_decoder = None
        self.command_number = 0
        self.pending_marker = None
        self.output_buffer = ""
        self.current_shell_directory = None
        self.restart_request_id = 0
        self.start_serial = 0
        self.intentional_process_stop = False
        self.create_process()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        toolbar = QHBoxLayout()
        self.location_label = QLabel("Terminal is not running", self)
        toolbar.addWidget(self.location_label, 1)
        clear_button = QPushButton("Clear", self)
        clear_button.clicked.connect(self.clear)
        toolbar.addWidget(clear_button)
        self.restart_button = QPushButton("Restart", self)
        self.restart_button.clicked.connect(self.restart)
        toolbar.addWidget(self.restart_button)
        layout.addLayout(toolbar)

        self.console = TerminalConsole(self)
        self.console.setPlaceholderText("PowerShell starts here.")
        self.console.commandSubmitted.connect(self.run_command)
        layout.addWidget(self.console, 1)
        self.setFocusProxy(self.console)

    def create_process(self):
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.started.connect(self.process_started)
        self.process.finished.connect(self.process_finished)
        self.process.errorOccurred.connect(self.process_error)

    def focus_command_input(self):
        self.console.setFocus(Qt.OtherFocusReason)
        self.console.activateWindow()

    def start(self, working_directory):
        import codecs
        import shutil

        working_directory = Path(working_directory).resolve()
        self.working_directory = working_directory
        self.current_shell_directory = working_directory
        self.location_label.setText(str(working_directory))
        if self.process.state() != QProcess.NotRunning:
            return

        self.start_serial += 1

        self.process.setWorkingDirectory(str(working_directory))
        self.output_decoder = None
        if sys.platform.startswith("win"):
            powershell = shutil.which("powershell.exe") or shutil.which("powershell")
            self.shell_kind = "powershell"
            self.output_decoder = codecs.getincrementaldecoder("utf-8")("replace")
            program = powershell or "powershell.exe"
            arguments = ["-NoLogo", "-NoProfile", "-NoExit", "-Command", "-"]
        else:
            self.shell_kind = "posix"
            self.output_decoder = codecs.getincrementaldecoder("utf-8")("replace")
            program = shutil.which("bash") or shutil.which("sh") or "/bin/sh"
            arguments = ["-i"]

        self.append_text(f"Starting terminal in {working_directory}\n")
        self.console.accepting_input = False
        self.process.start(program, arguments)
        if not self.process.waitForStarted(1500):
            self.append_text("Could not start the terminal process.\n")
            self.restart_button.setEnabled(True)
        QTimer.singleShot(0, self.focus_command_input)

    def restart(self):
        directory = self.working_directory or Path(__file__).resolve().parent
        self.restart_request_id += 1
        request_id = self.restart_request_id
        self.restart_button.setEnabled(False)
        self.start_serial += 1
        self.console.accepting_input = False
        self.pending_marker = None
        self.output_buffer = ""
        self.dispose_process()
        self.create_process()
        QTimer.singleShot(75, lambda: self.finish_restart(request_id, directory))

    def finish_restart(self, request_id, directory):
        if request_id != self.restart_request_id:
            return
        if self.process.state() == QProcess.NotRunning:
            self.start(directory)
        else:
            self.restart_button.setEnabled(True)

    def stop(self):
        if self.process is None or self.process.state() == QProcess.NotRunning:
            return
        self.dispose_process()

    def dispose_process(self):
        """Stop and detach the old shell without leaking late crash signals."""
        old_process = self.process
        if old_process is None:
            return
        self.intentional_process_stop = True
        old_process.blockSignals(True)
        if old_process.state() != QProcess.NotRunning:
            old_process.write(("exit" + self.line_ending()).encode(self.shell_encoding()))
            if not old_process.waitForFinished(250):
                old_process.terminate()
            if not old_process.waitForFinished(350):
                old_process.kill()
                old_process.waitForFinished(350)
        old_process.deleteLater()
        self.process = None
        self.output_decoder = None
        self.intentional_process_stop = False

    def run_command(self, command):
        if self.process.state() == QProcess.NotRunning:
            self.append_text("[Cannot run command: terminal is not running]\n")
            return
        if not command.strip():
            self.console.show_prompt(self.prompt_text())
            return
        if command.strip().lower() in {"clear", "cls", "clear-host"}:
            self.console.clear()
            self.console.show_prompt(self.prompt_text())
            return
        if self.try_run_internal_file_command(command):
            QTimer.singleShot(0, self.show_command_prompt)
            return
        self.command_number += 1
        self.pending_marker = f"__SNOTE_COMMAND_DONE_{self.command_number}__"
        if self.shell_kind == "powershell":
            marker_command = (
                f"Write-Output ('{self.pending_marker}' + (Get-Location).Path)"
            )
        elif self.shell_kind == "cmd":
            marker_command = f"echo {self.pending_marker}%CD%"
        else:
            marker_command = f"printf '%s\\n' '{self.pending_marker}'"
        payload = command + self.line_ending() + marker_command + self.line_ending()
        self.process.write(payload.encode(self.shell_encoding(), errors="replace"))

    def try_run_internal_file_command(self, command):
        parsed = self.parse_internal_file_command(command)
        if not parsed:
            return False
        action, options, paths = parsed
        try:
            message = self.execute_internal_file_command(action, options, paths)
        except Exception as error:
            self.append_text(f"[sNote file command error] {error}\n")
            return True
        if message:
            self.append_text(message + "\n")
        return True

    def parse_internal_file_command(self, command):
        import shlex

        command = command.strip()
        if not command or any(token in command for token in ("|", ";", "&&", "||", ">", "<", "`", "$(")):
            return None
        try:
            parts = shlex.split(command, posix=False)
        except ValueError:
            return None
        parts = [self.unquote_token(part) for part in parts if part.strip()]
        if not parts:
            return None

        aliases = {
            "cp": "copy",
            "copy": "copy",
            "copy-item": "copy",
            "mv": "move",
            "move": "move",
            "move-item": "move",
            "rm": "remove",
            "del": "remove",
            "erase": "remove",
            "remove-item": "remove",
            "mkdir": "mkdir",
            "md": "mkdir",
            "new-item": "mkdir",
        }
        action = aliases.get(parts[0].lower())
        if not action:
            return None

        options = set()
        paths = []
        for part in parts[1:]:
            lower = part.lower()
            if lower in {"-r", "-recurse", "-recursive"}:
                options.add("recursive")
            elif lower in {"-f", "-force", "-p"}:
                options.add("force")
            elif lower in {"-i", "-itemtype", "-type"}:
                return None
            elif part.startswith("-"):
                return None
            else:
                paths.append(part)

        required_paths = 1 if action in {"remove", "mkdir"} else 2
        if len(paths) < required_paths:
            return None
        if action in {"copy", "move"} and len(paths) != 2:
            return None
        return action, options, paths

    def unquote_token(self, token):
        if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
            return token[1:-1]
        return token

    def resolve_terminal_path(self, value):
        path = Path(value).expanduser()
        if not path.is_absolute():
            base = self.current_shell_directory or self.working_directory or Path.cwd()
            path = Path(base) / path
        return path.resolve()

    def execute_internal_file_command(self, action, options, paths):
        import shutil

        if action == "mkdir":
            created = []
            for raw_path in paths:
                target = self.resolve_terminal_path(raw_path)
                target.mkdir(parents=True, exist_ok="force" in options)
                created.append(str(target))
            return "[sNote file command] created " + ", ".join(created)

        if action == "remove":
            removed = []
            for raw_path in paths:
                target = self.resolve_terminal_path(raw_path)
                if not target.exists():
                    if "force" in options:
                        continue
                    raise FileNotFoundError(str(target))
                if target.is_dir():
                    if "recursive" not in options:
                        raise IsADirectoryError(f"{target} is a directory. Use rm -r to remove it.")
                    shutil.rmtree(target)
                else:
                    target.unlink()
                removed.append(str(target))
            return "[sNote file command] removed " + ", ".join(removed) if removed else "[sNote file command] nothing to remove"

        source = self.resolve_terminal_path(paths[0])
        destination = self.resolve_terminal_path(paths[1])
        if not source.exists():
            raise FileNotFoundError(str(source))

        if action == "copy":
            final_destination = destination / source.name if destination.exists() and destination.is_dir() else destination
            if source.is_dir():
                if "recursive" not in options:
                    raise IsADirectoryError(f"{source} is a directory. Use cp -r to copy it.")
                if final_destination.exists() and "force" in options:
                    if final_destination.is_dir():
                        shutil.rmtree(final_destination)
                    else:
                        final_destination.unlink()
                shutil.copytree(source, final_destination)
            else:
                final_destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, final_destination)
            return f"[sNote file command] copied {source} -> {final_destination}"

        if action == "move":
            final_destination = destination / source.name if destination.exists() and destination.is_dir() else destination
            final_destination.parent.mkdir(parents=True, exist_ok=True)
            if final_destination.exists() and "force" in options:
                if final_destination.is_dir():
                    shutil.rmtree(final_destination)
                else:
                    final_destination.unlink()
            shutil.move(str(source), str(final_destination))
            return f"[sNote file command] moved {source} -> {final_destination}"

        return ""

    def change_directory(self, working_directory):
        working_directory = Path(working_directory).resolve()
        self.working_directory = working_directory
        self.location_label.setText(str(working_directory))
        if self.process.state() == QProcess.NotRunning:
            self.start(working_directory)
            return
        if self.shell_kind == "powershell":
            escaped = str(working_directory).replace("'", "''")
            command = f"Set-Location -LiteralPath '{escaped}'"
        elif sys.platform.startswith("win"):
            command = f'cd /d "{working_directory}"'
        else:
            escaped = str(working_directory).replace("'", "'\\''")
            command = f"cd '{escaped}'"
        self.process.write((command + self.line_ending()).encode(self.shell_encoding(), errors="replace"))
        QTimer.singleShot(0, self.focus_command_input)

    def shell_encoding(self):
        if self.shell_kind in ("powershell", "cmd"):
            return "utf-8"
        import locale
        return locale.getpreferredencoding(False) if sys.platform.startswith("win") else "utf-8"

    def line_ending(self):
        return "\r\n" if sys.platform.startswith("win") else "\n"

    def read_output(self):
        raw = bytes(self.process.readAllStandardOutput())
        if self.output_decoder is not None:
            # Preserve incomplete multi-byte Korean characters between QProcess
            # output chunks instead of decoding each chunk independently.
            text = self.output_decoder.decode(raw, final=False)
        else:
            for encoding in (self.shell_encoding(), "utf-8", "cp949", "mbcs"):
                try:
                    text = raw.decode(encoding)
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            else:
                text = raw.decode("utf-8", errors="replace")
        text = text.replace("\x08", "").replace("\r\r\n", "\n").replace("\r\n", "\n")
        if self.shell_kind == "cmd":
            text = re.sub(r"(?m)^[ \t]+(?:\n|$)", "", text)
        if not self.pending_marker:
            self.append_text(text)
            return

        self.output_buffer += text
        marker_index = self.output_buffer.find(self.pending_marker)
        if marker_index >= 0:
            self.append_text(self.output_buffer[:marker_index])
            remainder = self.output_buffer[marker_index + len(self.pending_marker):]
            if self.shell_kind in ("powershell", "cmd"):
                directory_line, separator, remaining_output = remainder.partition("\n")
                if directory_line.strip():
                    self.current_shell_directory = Path(directory_line.strip())
                remainder = remaining_output if separator else ""
            self.output_buffer = ""
            self.pending_marker = None
            self.append_text(remainder.lstrip("\n"))
            QTimer.singleShot(100, self.show_command_prompt)
            return

        safe_length = max(0, len(self.output_buffer) - len(self.pending_marker) - 2)
        if safe_length:
            self.append_text(self.output_buffer[:safe_length])
            self.output_buffer = self.output_buffer[safe_length:]

    def append_text(self, text):
        self.console.append_output(text)

    def prompt_text(self):
        if self.shell_kind == "powershell":
            directory = self.current_shell_directory or self.working_directory
            return f"PS {directory}> "
        if self.shell_kind == "cmd":
            directory = self.current_shell_directory or self.working_directory
            return f"{directory}> "
        return "> "

    def show_command_prompt(self, start_serial=None):
        if start_serial is not None and start_serial != self.start_serial:
            return
        if self.process.state() != QProcess.NotRunning and not self.pending_marker:
            self.console.show_prompt(self.prompt_text())
            self.focus_command_input()

    def clear(self):
        self.console.clear()
        if self.process.state() != QProcess.NotRunning and not self.pending_marker:
            self.console.show_prompt(self.prompt_text())

    def process_started(self):
        self.configure_shell_encoding()
        if self.shell_kind == "powershell":
            shell_name = "PowerShell"
        elif self.shell_kind == "cmd":
            shell_name = "Command Prompt"
        else:
            shell_name = "Shell"
        self.append_text(f"[{shell_name} ready]\n")
        serial = self.start_serial
        self.restart_button.setEnabled(True)
        QTimer.singleShot(150, lambda: self.show_command_prompt(serial))

    def configure_shell_encoding(self):
        if self.shell_kind == "powershell":
            # Windows PowerShell 5 defaults to legacy encodings for the console
            # and BOM-less text files. Keep the whole embedded pipeline UTF-8.
            setup = (
                "chcp 65001 > $null; "
                "$utf8 = New-Object System.Text.UTF8Encoding($false); "
                "[Console]::InputEncoding = $utf8; "
                "[Console]::OutputEncoding = $utf8; "
                "$OutputEncoding = $utf8; "
                "$PSDefaultParameterValues['*:Encoding'] = 'utf8'; "
                "$env:PYTHONIOENCODING = 'utf-8'; "
                "$env:PYTHONUTF8 = '1'; "
                "function global:grep { "
                "param([string]$Pattern, "
                "[Parameter(ValueFromRemainingArguments=$true)][string[]]$Path); "
                "if (-not $Pattern -or -not $Path -or $Path.Count -eq 0) { "
                "Write-Output 'Usage: grep <pattern> <file>'; return }; "
                "Select-String -Pattern $Pattern -Path $Path }; "
                "function global:find { Get-ChildItem -Recurse @args }; "
                "function global:env { Get-ChildItem Env: @args }; "
                "function global:which { Get-Command @args }; "
                "function global:ll { Get-ChildItem -Force @args }; "
                "function global:touch { "
                "param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Path); "
                "foreach ($item in $Path) { "
                "if (Test-Path -LiteralPath $item) { "
                "(Get-Item -LiteralPath $item).LastWriteTime = Get-Date "
                "} else { New-Item -ItemType File -Path $item | Out-Null } "
                "} }"
            )
            self.process.write((setup + self.line_ending()).encode("utf-8"))
        elif self.shell_kind == "cmd":
            setup = (
                "chcp 65001 > nul\r\n"
                "set PYTHONIOENCODING=utf-8\r\n"
                "set PYTHONUTF8=1\r\n"
            )
            self.process.write(setup.encode("utf-8"))

    def process_finished(self, exit_code, _exit_status):
        if self.process.state() != QProcess.NotRunning:
            return
        if self.output_decoder is not None:
            remaining = self.output_decoder.decode(b"", final=True)
            if remaining:
                self.append_text(remaining)
            self.output_decoder = None
        self.append_text(f"\n[Terminal exited: {exit_code}]\n")
        self.console.accepting_input = False

    def process_error(self, _error):
        if self.intentional_process_stop:
            return
        self.append_text(f"\n[Terminal error: {self.process.errorString()}]\n")


class EnhancedSimpleNotePad(QMainWindow):
    def __init__(self):
        super().__init__()
        self.last_find_text = ""
        self.line_numbers_visible = True
        self.current_theme = "light"
        self.recent_files = []
        self.find_dialog = None
        self.links_dir = self.resolve_links_directory()

        self.load_settings()
        self.init_ui()
        self.update_title()

    def resolve_links_directory(self):
        """Initialize writable settings from privacy-safe bundled defaults."""
        import shutil

        user_links = user_config_directory()
        source_links = Path(__file__).resolve().parent / "resources" / "links"
        user_links.mkdir(parents=True, exist_ok=True)
        legacy_links = (
            Path(sys.executable).resolve().parent / "links"
            if getattr(sys, "frozen", False)
            else Path.cwd() / "links"
        )
        for name in (
            "editor_settings.json", "memo_links.json", "program_links.json",
            "web_links.json", "system_links.json", "recent_files.json",
        ):
            destination = user_links / name
            legacy = legacy_links / name
            source = source_links / name
            if destination.exists():
                continue
            if legacy.exists() and legacy.resolve() != destination.resolve():
                shutil.copy2(legacy, destination)
            elif source.exists():
                shutil.copy2(source, destination)
        return user_links

    # ---------- UI & Menus ----------
    def init_ui(self):
        # Create Tabbed Interface
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.tab_changed)
        self.setCentralWidget(self.tab_widget)

        # Live Markdown preview panel (hidden until requested).
        self.markdown_preview = QTextBrowser(self)
        self.markdown_preview.setOpenExternalLinks(True)
        self.markdown_preview.setPlaceholderText("Open a Markdown or HTML file to preview it here.")
        self.preview_dock = QDockWidget("Markdown / HTML Preview", self)
        self.preview_dock.setObjectName("markdownPreviewDock")
        self.preview_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.preview_dock.setWidget(self.markdown_preview)
        self.addDockWidget(Qt.RightDockWidgetArea, self.preview_dock)
        self.preview_dock.hide()

        # Integrated terminal panel at the bottom (hidden until requested).
        self.embedded_terminal = EmbeddedTerminal(self)
        self.terminal_dock = QDockWidget("Terminal", self)
        self.terminal_dock.setObjectName("terminalDock")
        self.terminal_dock.setAllowedAreas(Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)
        self.terminal_dock.setWidget(self.embedded_terminal)
        self.terminal_dock.setMinimumHeight(180)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.terminal_dock)
        self.terminal_dock.hide()

        # Menus
        file_menu = self.menuBar().addMenu("&File")
        self.create_file_menu(file_menu)

        edit_menu = self.menuBar().addMenu("&Edit")
        self.create_edit_menu(edit_menu)

        font_menu = self.menuBar().addMenu("F&ont")
        self.create_font_size_menu(font_menu)

        view_menu = self.menuBar().addMenu("&View")
        self.create_view_menu(view_menu)

        terminal_menu = self.menuBar().addMenu("&Terminal")
        self.create_terminal_menu(terminal_menu)

        # Link menus
        self.link_menus = {}
        self.link_data = {}
        for category in LINK_CATEGORIES:
            self.link_menus[category] = self.menuBar().addMenu(category)
            self.load_link_data(category)

        self.update_link_menus()

        # Help stays at the far right, after System Links.
        help_menu = self.menuBar().addMenu("&Help")
        self.create_help_menu(help_menu)

        # Status bar: path + cursor + modified
        self.status_path = QLabel("")
        self.status_pos = QLabel("Ln 1, Col 1")
        self.status_modified = QLabel("")
        self.statusBar().addPermanentWidget(self.status_path, 1)
        self.statusBar().addPermanentWidget(self.status_pos)
        self.statusBar().addPermanentWidget(self.status_modified)

        # Add initial empty tab
        self.add_new_tab()
        self.apply_theme(self.current_theme)

        # Ctrl+= is an additional zoom shortcut not provided by the menu action.
        # The other zoom shortcuts live on their menu actions to avoid ambiguity.
        self.add_sc(QKeySequence("Ctrl+="), self.zoom_in)

    def add_sc(self, seq, slot):
        act = QAction(self)
        act.setShortcut(seq)
        act.setShortcutContext(Qt.ApplicationShortcut)
        act.triggered.connect(slot)
        self.addAction(act)

    def get_current_editor(self):
        return self.tab_widget.currentWidget()

    def update_title(self):
        editor = self.get_current_editor()
        if not editor:
            self.setWindowTitle(f"sNote {APP_VERSION}")
            return
        name = editor.current_file if editor.file_path is None else Path(editor.file_path).name
        modified_flag = "[*]" if editor.document().isModified() else ""
        self.setWindowTitle(f"sNote {APP_VERSION}{modified_flag} — {name}")
        self.setToolTip(editor.file_path if editor.file_path else "(unsaved)")
        self.update_status_path()

    def update_status_path(self):
        editor = self.get_current_editor()
        if editor:
            self.status_path.setText(editor.file_path if editor.file_path else "(unsaved)")
        else:
            self.status_path.setText("")
        self.update_modified_label()

    def update_modified_label(self):
        editor = self.get_current_editor()
        if editor:
            self.status_modified.setText("● Modified" if editor.document().isModified() else "")
        else:
            self.status_modified.setText("")

    def update_cursor_pos(self):
        editor = self.get_current_editor()
        if not editor:
            self.status_pos.setText("Ln 1, Col 1")
            return
        cur = editor.textCursor()
        line = cur.blockNumber() + 1
        col = cur.columnNumber() + 1
        self.status_pos.setText(f"Ln {line}, Col {col}")

    # ---------- Tab Management ----------
    def add_new_tab(self, file_path=None, content=""):
        editor = CodeEditor(self)
        
        # Inherit current font size
        if self.tab_widget.count() > 0:
            current_editor = self.get_current_editor()
            if current_editor:
                editor.setFont(current_editor.font())
        else:
            editor.setFont(QFont("Arial", 16))

        editor.setTheme(self.current_theme)
        editor.setLineNumbersVisible(self.line_numbers_visible)

        # Connect signals
        editor.document().modificationChanged.connect(self.update_tab_title_and_modified)
        editor.cursorPositionChanged.connect(self.update_cursor_pos)
        editor.textChanged.connect(self.update_markdown_preview)

        if content:
            editor.setPlainText(content)

        editor.document().setModified(False)

        # Tab title
        if file_path:
            title = Path(file_path).name
        else:
            title = "Untitled"

        editor.file_path = file_path
        editor.current_file = file_path if file_path else "Untitled"

        tab_index = self.tab_widget.addTab(editor, title)
        self.tab_widget.setCurrentIndex(tab_index)
        self.update_title()
        if editor.is_html_document():
            self.preview_dock.show()
            self.update_markdown_preview()
        return editor

    def add_new_markdown_tab(self):
        editor = self.add_new_tab()
        editor.current_file = "Untitled.md"
        index = self.tab_widget.indexOf(editor)
        self.tab_widget.setTabText(index, "Untitled.md")
        self.update_title()
        return editor

    def add_new_html_tab(self):
        editor = self.add_new_tab()
        editor.current_file = "Untitled.html"
        index = self.tab_widget.indexOf(editor)
        self.tab_widget.setTabText(index, "Untitled.html")
        self.preview_dock.show()
        self.update_title()
        self.update_markdown_preview()
        return editor

    def close_tab(self, index):
        editor = self.tab_widget.widget(index)
        if editor.document().isModified():
            ret = QMessageBox.warning(
                self, "Unsaved changes",
                f"The document '{editor.current_file}' has been modified.\nDo you want to save your changes?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if ret == QMessageBox.Save:
                self.tab_widget.setCurrentIndex(index)
                if not self.save_file():
                    return False
            elif ret == QMessageBox.Cancel:
                return False

        self.tab_widget.removeTab(index)
        if self.tab_widget.count() == 0:
            self.add_new_tab()
        return True

    def tab_changed(self, index):
        if index >= 0:
            self.update_title()
            self.update_cursor_pos()
            self.update_markdown_preview()

    def update_tab_title_and_modified(self, _=None):
        editor = self.get_current_editor()
        if not editor:
            return
        idx = self.tab_widget.indexOf(editor)
        if idx >= 0:
            name = Path(editor.file_path).name if editor.file_path else "Untitled"
            modified_star = "*" if editor.document().isModified() else ""
            self.tab_widget.setTabText(idx, f"{name}{modified_star}")
        self.update_title()

    # ---------- File Menu ----------
    def create_file_menu(self, menu):
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(lambda: self.add_new_tab())
        menu.addAction(new_action)

        new_markdown_action = QAction("New &Markdown", self)
        new_markdown_action.setShortcut("Ctrl+Alt+N")
        new_markdown_action.triggered.connect(self.add_new_markdown_tab)
        menu.addAction(new_markdown_action)

        new_html_action = QAction("New &HTML", self)
        new_html_action.setShortcut("Ctrl+Alt+H")
        new_html_action.triggered.connect(self.add_new_html_tab)
        menu.addAction(new_html_action)

        open_action = QAction("&Open…", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)
        menu.addAction(save_action)

        save_as_action = QAction("Save &As…", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        menu.addAction(save_as_action)

        self.recent_files_menu = menu.addMenu("Recent &Files")
        self.load_recent_files()

        menu.addSeparator()

        show_in_folder = QAction("Show in &Folder", self)
        show_in_folder.setShortcut("Ctrl+Shift+O")
        show_in_folder.triggered.connect(self.reveal_in_explorer)
        menu.addAction(show_in_folder)

        copy_path = QAction("&Copy File Path", self)
        copy_path.setShortcut("Ctrl+Alt+C")
        copy_path.triggered.connect(self.copy_file_path)
        menu.addAction(copy_path)

        menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)

    # ---------- Edit Menu ----------
    def create_edit_menu(self, menu):
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.undo)
        menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self.redo)
        menu.addAction(redo_action)

        menu.addSeparator()

        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.cut)
        menu.addAction(cut_action)

        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy)
        menu.addAction(copy_action)

        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste)
        menu.addAction(paste_action)

        paste_markdown_action = QAction("Paste as &Markdown", self)
        paste_markdown_action.setShortcut("Ctrl+Shift+V")
        paste_markdown_action.triggered.connect(self.paste_as_markdown)
        menu.addAction(paste_markdown_action)

        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_all_action.triggered.connect(self.select_all)
        menu.addAction(select_all_action)

        menu.addSeparator()

        find_action = QAction("&Find…", self)
        find_action.setShortcut(QKeySequence.Find)  # Ctrl+F
        find_action.triggered.connect(self.find_text)
        menu.addAction(find_action)

        replace_action = QAction("&Replace…", self)
        replace_action.setShortcut("Ctrl+H")
        replace_action.triggered.connect(self.replace_text)
        menu.addAction(replace_action)

        find_next_action = QAction("Find &Next", self)
        find_next_action.setShortcut(QKeySequence("F3"))
        find_next_action.triggered.connect(lambda: self.find_next(backward=False))
        menu.addAction(find_next_action)

        find_prev_action = QAction("Find &Previous", self)
        find_prev_action.setShortcut(QKeySequence("Shift+F3"))
        find_prev_action.triggered.connect(lambda: self.find_next(backward=True))
        menu.addAction(find_prev_action)

        goto_line_action = QAction("&Go To Line…", self)
        goto_line_action.setShortcut("Ctrl+G")
        goto_line_action.triggered.connect(self.go_to_line)
        menu.addAction(goto_line_action)

    # ---------- Font Menu ----------
    def create_font_size_menu(self, menu):
        change_font_action = QAction("&Change Font…", self)
        change_font_action.setShortcut("Ctrl+T")
        change_font_action.triggered.connect(self.change_font_size)
        menu.addAction(change_font_action)

        menu.addSeparator()

        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self.zoom_in)
        menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.zoom_out)
        menu.addAction(zoom_out_action)

        zoom_reset_action = QAction("&Reset Zoom", self)
        zoom_reset_action.setShortcut("Ctrl+0")
        zoom_reset_action.triggered.connect(self.zoom_reset)
        menu.addAction(zoom_reset_action)

    # ---------- View Menu ----------
    def create_view_menu(self, menu):
        preview_action = self.preview_dock.toggleViewAction()
        preview_action.setText("Markdown / HTML &Preview")
        preview_action.setShortcut("Ctrl+Shift+M")
        menu.addAction(preview_action)
        self.preview_dock.visibilityChanged.connect(self.update_markdown_preview)
        menu.addSeparator()

        self.line_num_action = QAction("Show &Line Numbers", self, checkable=True)
        self.line_num_action.setChecked(self.line_numbers_visible)
        self.line_num_action.setShortcut("Ctrl+L")
        self.line_num_action.triggered.connect(self.toggle_line_numbers)
        menu.addAction(self.line_num_action)

        menu.addSeparator()

        self.theme_group = QActionGroup(self)
        self.light_theme_action = QAction("&White Mode", self, checkable=True)
        self.dark_theme_action = QAction("&Dark Mode", self, checkable=True)

        self.theme_group.addAction(self.light_theme_action)
        self.theme_group.addAction(self.dark_theme_action)

        if self.current_theme == "dark":
            self.dark_theme_action.setChecked(True)
        else:
            self.light_theme_action.setChecked(True)

        self.light_theme_action.triggered.connect(lambda: self.set_theme("light"))
        self.dark_theme_action.triggered.connect(lambda: self.set_theme("dark"))

        menu.addAction(self.light_theme_action)
        menu.addAction(self.dark_theme_action)

    # ---------- Terminal Menu ----------
    def create_terminal_menu(self, menu):
        self.toggle_terminal_action = self.terminal_dock.toggleViewAction()
        self.toggle_terminal_action.setText("Show &Integrated Terminal")
        self.toggle_terminal_action.setShortcut(QKeySequence("Ctrl+`"))
        self.toggle_terminal_action.setStatusTip("Show the terminal panel below the editor")
        menu.addAction(self.toggle_terminal_action)
        self.terminal_dock.visibilityChanged.connect(self.terminal_visibility_changed)

        menu.addSeparator()
        open_external_action = QAction("Open &External Terminal", self)
        open_external_action.setShortcut(QKeySequence("Ctrl+Shift+`"))
        open_external_action.setStatusTip("Open a separate terminal window")
        open_external_action.triggered.connect(self.open_terminal)
        menu.addAction(open_external_action)

    def create_help_menu(self, menu):
        manual_action = QAction("sNote &Manual", self)
        manual_action.setShortcut(QKeySequence("F1"))
        manual_action.triggered.connect(self.show_manual)
        menu.addAction(manual_action)

        menu.addSeparator()
        about_action = QAction("&About sNote", self)
        about_action.triggered.connect(
            lambda: QMessageBox.about(
                self,
                "About sNote",
                f"<h3>sNote {APP_VERSION}</h3>"
                "<p>A focused editor and personal work hub for text, Markdown, "
                "links, programs, and terminal tasks.</p>"
                "<p>Settings are stored separately from the application.</p>",
            )
        )
        menu.addAction(about_action)

    def show_manual(self):
        """Display the bundled manual in a read-only sNote dialog."""
        manual_path = Path(__file__).resolve().parent / "resources" / "SNOTE_MANUAL.md"
        try:
            manual_text = manual_path.read_text(encoding="utf-8")
        except OSError as error:
            QMessageBox.warning(self, "sNote Manual", f"Could not open the manual:\n{error}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"sNote {APP_VERSION} Manual")
        dialog.resize(900, 720)
        layout = QVBoxLayout(dialog)

        viewer = QTextBrowser(dialog)
        viewer.setOpenExternalLinks(True)
        manual_text = manual_text.replace("{APP_VERSION}", APP_VERSION)
        if hasattr(viewer, "setMarkdown"):
            viewer.setMarkdown(manual_text)
        else:
            viewer.setPlainText(manual_text)
        layout.addWidget(viewer, 1)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        close_button = QPushButton("Close", dialog)
        close_button.clicked.connect(dialog.accept)
        button_row.addWidget(close_button)
        layout.addLayout(button_row)

        dialog.exec_()

    def terminal_visibility_changed(self, visible):
        if not visible:
            return
        working_dir = self.terminal_working_directory()
        if self.embedded_terminal.process.state() == QProcess.NotRunning:
            self.embedded_terminal.start(working_dir)
        else:
            self.embedded_terminal.change_directory(working_dir)
        QTimer.singleShot(0, self.embedded_terminal.focus_command_input)

    def terminal_working_directory(self):
        """Use the current file's folder, or the sNote folder for a new document."""
        editor = self.get_current_editor()
        if editor and editor.file_path:
            file_path = Path(editor.file_path).expanduser()
            try:
                return file_path.resolve().parent
            except OSError:
                return file_path.absolute().parent
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent

    def open_terminal(self):
        import shutil
        import subprocess

        working_dir = self.terminal_working_directory()
        try:
            if sys.platform.startswith("win"):
                windows_terminal = shutil.which("wt.exe") or shutil.which("wt")
                if windows_terminal:
                    subprocess.Popen(
                        [windows_terminal, "-d", str(working_dir)],
                        cwd=str(working_dir)
                    )
                else:
                    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
                    if not powershell:
                        raise FileNotFoundError("Windows Terminal and PowerShell were not found.")
                    subprocess.Popen(
                        [powershell, "-NoExit"],
                        cwd=str(working_dir),
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-a", "Terminal", str(working_dir)])
            else:
                terminal = next(
                    (shutil.which(name) for name in (
                        "x-terminal-emulator", "gnome-terminal", "konsole", "xfce4-terminal"
                    ) if shutil.which(name)),
                    None
                )
                if not terminal:
                    raise FileNotFoundError("No supported terminal application was found.")
                subprocess.Popen([terminal], cwd=str(working_dir))

            self.statusBar().showMessage(f"Terminal opened: {working_dir}", 2500)
        except Exception as error:
            QMessageBox.warning(
                self,
                "Open Terminal",
                f"Could not open a terminal in:\n{working_dir}\n\n{error}"
            )

    # ---------- Edit Actions Helpers ----------
    def undo(self):
        editor = self.get_current_editor()
        if editor: editor.undo()

    def redo(self):
        editor = self.get_current_editor()
        if editor: editor.redo()

    def cut(self):
        editor = self.get_current_editor()
        if editor: editor.cut()

    def copy(self):
        editor = self.get_current_editor()
        if editor: editor.copy()

    def paste(self):
        editor = self.get_current_editor()
        if editor: editor.paste()

    def paste_as_markdown(self):
        editor = self.get_current_editor()
        if editor and editor.paste_as_markdown():
            self.statusBar().showMessage("Pasted as Markdown", 1500)

    def select_all(self):
        editor = self.get_current_editor()
        if editor: editor.selectAll()

    # ---------- Font helpers ----------
    def change_font_size(self):
        current_editor = self.get_current_editor()
        if not current_editor:
            return
        font, ok = QFontDialog.getFont(current_editor.font(), self, "Choose Font")
        if ok:
            for i in range(self.tab_widget.count()):
                self.tab_widget.widget(i).setFont(font)

    def zoom_in(self):
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            f = editor.font()
            f.setPointSize(max(1, f.pointSize() + 1))
            editor.setFont(f)

    def zoom_out(self):
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            f = editor.font()
            f.setPointSize(max(1, f.pointSize() - 1))
            editor.setFont(f)

    def zoom_reset(self):
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            f = editor.font()
            f.setPointSize(16)
            editor.setFont(f)

    # ---------- View helpers ----------
    def toggle_line_numbers(self):
        self.line_numbers_visible = self.line_num_action.isChecked()
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            editor.setLineNumbersVisible(self.line_numbers_visible)
        self.save_settings()

    def update_markdown_preview(self, _=None):
        if not hasattr(self, "markdown_preview") or not self.preview_dock.isVisible():
            return
        editor = self.get_current_editor()
        if not editor:
            self.markdown_preview.clear()
            return
        if not editor.is_markdown_document() and not editor.is_html_document():
            self.markdown_preview.setHtml(
                "<p style='color:#777'>Preview is available for Markdown and HTML files.</p>"
            )
            return
        document = QTextDocument(self.markdown_preview)
        document.setDefaultFont(editor.font())
        if editor.file_path:
            base_directory = Path(editor.file_path).resolve().parent
            document.setBaseUrl(QUrl.fromLocalFile(str(base_directory) + "/"))
        if editor.is_html_document():
            document.setHtml(editor.toPlainText())
        elif hasattr(document, "setMarkdown"):
            document.setMarkdown(editor.toPlainText())
        else:
            document.setPlainText(editor.toPlainText())
        self.markdown_preview.setDocument(document)

    def set_theme(self, theme_name):
        self.current_theme = theme_name
        self.apply_theme(theme_name)
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            editor.setTheme(theme_name)
        self.save_settings()

    def apply_theme(self, theme):
        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                }
                QPlainTextEdit {
                    background-color: #1e1e1e;
                    color: #efefef;
                    border: none;
                }
                QMenuBar {
                    background-color: #2b2b2b;
                    color: #efefef;
                }
                QMenuBar::item:selected {
                    background-color: #3a3a3a;
                }
                QMenu {
                    background-color: #2b2b2b;
                    color: #efefef;
                    border: 1px solid #3a3a3a;
                }
                QMenu::item:selected {
                    background-color: #3a3a3a;
                }
                QStatusBar {
                    background-color: #2b2b2b;
                    color: #efefef;
                }
                QTabWidget::pane {
                    border: 1px solid #3a3a3a;
                    background: #1e1e1e;
                }
                QTabBar::tab {
                    background: #2b2b2b;
                    color: #858585;
                    padding: 8px 12px;
                    border: 1px solid #3a3a3a;
                    border-bottom: none;
                }
                QTabBar::tab:selected {
                    background: #1e1e1e;
                    color: #efefef;
                    border-bottom: none;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f0f0f0;
                }
                QPlainTextEdit {
                    background-color: #ffffff;
                    color: #000000;
                    border: none;
                }
                QMenuBar {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QMenuBar::item:selected {
                    background-color: #e0e0e0;
                }
                QMenu {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #d0d0d0;
                }
                QMenu::item:selected {
                    background-color: #e0e0e0;
                }
                QStatusBar {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QTabWidget::pane {
                    border: 1px solid #d0d0d0;
                    background: #ffffff;
                }
                QTabBar::tab {
                    background: #e0e0e0;
                    color: #555555;
                    padding: 8px 12px;
                    border: 1px solid #d0d0d0;
                    border-bottom: none;
                }
                QTabBar::tab:selected {
                    background: #ffffff;
                    color: #000000;
                    border-bottom: none;
                }
            """)

    # ---------- File ops ----------
    def open_file(self):
        options = QFileDialog.Options()
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Open File(s)", "",
            FILE_DIALOG_FILTER, options=options
        )
        if file_paths:
            for file_path in file_paths:
                content = ""
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'r', encoding='cp949') as file:
                            content = file.read()
                    except Exception as e:
                        QMessageBox.critical(self, "Open Error", f"Could not read {file_path}:\n{e}")
                        continue
                except Exception as e:
                    QMessageBox.critical(self, "Open Error", f"Could not read {file_path}:\n{e}")
                    continue

                current_editor = self.get_current_editor()
                is_empty_untitled = (
                    current_editor and 
                    current_editor.file_path is None and 
                    not current_editor.document().isModified() and 
                    current_editor.toPlainText() == ""
                )

                self.add_new_tab(file_path, content)
                self.add_recent_file(file_path)

                if is_empty_untitled and self.tab_widget.count() > 1:
                    self.tab_widget.removeTab(self.tab_widget.currentIndex() - 1)

    def save_file(self):
        editor = self.get_current_editor()
        if not editor:
            return False
        if not editor.file_path:
            return self.save_file_as()
        try:
            output = QSaveFile(editor.file_path)
            if not output.open(QIODevice.WriteOnly | QIODevice.Text):
                raise OSError(output.errorString())
            if output.write(editor.toPlainText().encode("utf-8")) < 0:
                raise OSError(output.errorString())
            if not output.commit():
                raise OSError(output.errorString())
            editor.document().setModified(False)
            self.update_tab_title_and_modified()
            self.update_status_path()
            self.add_recent_file(editor.file_path)
            self.update_markdown_preview()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))
            return False

    def save_file_as(self):
        editor = self.get_current_editor()
        if not editor:
            return False
        options = QFileDialog.Options()
        suggested_name = editor.current_file if editor.current_file != "Untitled" else ""
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Save File As", suggested_name,
            FILE_DIALOG_FILTER, options=options
        )
        if file_path:
            if not Path(file_path).suffix and (
                editor.is_markdown_document() or "Markdown" in selected_filter
            ):
                file_path += ".md"
            elif not Path(file_path).suffix and (
                editor.is_html_document() or "HTML" in selected_filter
            ):
                file_path += ".html"
            editor.file_path = file_path
            editor.current_file = file_path
            ok = self.save_file()
            if ok:
                idx = self.tab_widget.indexOf(editor)
                self.tab_widget.setTabText(idx, Path(file_path).name)
                self.update_title()
                if editor.is_html_document():
                    self.preview_dock.show()
                self.update_markdown_preview()
            return ok
        return False

    def copy_file_path(self):
        editor = self.get_current_editor()
        if editor and editor.file_path:
            QApplication.clipboard().setText(editor.file_path)
            self.statusBar().showMessage("File path copied", 1500)
        else:
            self.statusBar().showMessage("No file path (unsaved document)", 2000)

    def reveal_in_explorer(self):
        editor = self.get_current_editor()
        if not editor or not editor.file_path:
            QMessageBox.information(self, "Show in Folder", "This file has not been saved yet.")
            return
        p = Path(editor.file_path)
        try:
            if sys.platform.startswith('win'):
                import subprocess
                subprocess.Popen(f'explorer /select,"{str(p)}"')
            elif sys.platform == "darwin":
                import subprocess
                subprocess.run(["open", "-R", str(p)])
            else:
                import subprocess
                subprocess.run(["xdg-open", str(p.parent)])
        except Exception as e:
            QMessageBox.warning(self, "Show in Folder", f"Could not open folder:\n{e}")

    # ---------- Settings Persistence ----------
    def load_settings(self):
        settings_path = self.links_dir / 'editor_settings.json'
        settings = read_json(settings_path, {})
        if isinstance(settings, dict):
            self.line_numbers_visible = bool(settings.get("line_numbers_visible", True))
            theme = settings.get("theme", "light")
            self.current_theme = theme if theme in {"light", "dark"} else "light"

    def save_settings(self):
        settings_path = self.links_dir / 'editor_settings.json'
        try:
            atomic_write_json(settings_path, {
                "line_numbers_visible": self.line_numbers_visible,
                "theme": self.current_theme,
            })
        except OSError as error:
            self.statusBar().showMessage(f"Could not save settings: {error}", 3000)

    # ---------- Recent Files Persistence ----------
    def load_recent_files(self):
        recent_file_path = self.links_dir / 'recent_files.json'
        self.recent_files = read_json(recent_file_path, [])
        if not isinstance(self.recent_files, list):
            self.recent_files = []
        self.recent_files = [str(value) for value in self.recent_files if value]
        self.update_recent_files_menu()

    def save_recent_files(self):
        recent_file_path = self.links_dir / 'recent_files.json'
        try:
            atomic_write_json(recent_file_path, self.recent_files)
        except OSError as error:
            self.statusBar().showMessage(f"Could not save recent files: {error}", 3000)

    def add_recent_file(self, file_path):
        if not file_path:
            return
        file_path = str(Path(file_path).resolve())
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:10]
        self.save_recent_files()
        self.update_recent_files_menu()

    def update_recent_files_menu(self):
        if not hasattr(self, 'recent_files_menu'):
            return
        self.recent_files_menu.clear()
        if not self.recent_files:
            no_recent_action = QAction("No Recent Files", self)
            no_recent_action.setEnabled(False)
            self.recent_files_menu.addAction(no_recent_action)
        else:
            for file_path in self.recent_files:
                path_obj = Path(file_path)
                action = QAction(f"{path_obj.name} ({file_path})", self)
                action.triggered.connect(lambda _, fp=file_path: self.open_recent_file(fp))
                self.recent_files_menu.addAction(action)

            self.recent_files_menu.addSeparator()
            clear_action = QAction("Clear Recent Files List", self)
            clear_action.triggered.connect(self.clear_recent_files)
            self.recent_files_menu.addAction(clear_action)

    def open_recent_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp949') as file:
                    content = file.read()
            except Exception as e:
                QMessageBox.critical(self, "Open Error", f"Could not read file:\n{e}")
                if file_path in self.recent_files:
                    self.recent_files.remove(file_path)
                    self.save_recent_files()
                    self.update_recent_files_menu()
                return
        except Exception as e:
            QMessageBox.critical(self, "Open Error", f"Could not read file:\n{e}")
            return

        current_editor = self.get_current_editor()
        is_empty_untitled = (
            current_editor and 
            current_editor.file_path is None and 
            not current_editor.document().isModified() and 
            current_editor.toPlainText() == ""
        )

        self.add_new_tab(file_path, content)
        self.add_recent_file(file_path)

        if is_empty_untitled and self.tab_widget.count() > 1:
            self.tab_widget.removeTab(self.tab_widget.currentIndex() - 1)

    def clear_recent_files(self):
        self.recent_files = []
        self.save_recent_files()
        self.update_recent_files_menu()

    # ---------- Links ----------
    def get_link_file_path(self, category):
        return self.links_dir / link_file_name(category)

    def load_link_data(self, category):
        file_path = self.get_link_file_path(category)
        loaded_data = read_json(file_path, [])
        if isinstance(loaded_data, dict):
            loaded_data = loaded_data.get("links", [])
        self.link_data[category] = self.normalize_links(loaded_data)
        if not file_path.exists():
            atomic_write_json(file_path, self.link_data[category])

    def normalize_links(self, links):
        normalized = []
        if not isinstance(links, list):
            return normalized
        for link in links:
            if not isinstance(link, dict):
                continue
            name = str(link.get('name', '')).strip()
            url = str(link.get('url', '')).strip()
            if name or url:
                normalized.append({'name': name or url, 'url': url})
        return normalized

    def save_link_data(self, category):
        file_path = self.get_link_file_path(category)
        self.link_data[category] = self.normalize_links(self.link_data.get(category, []))
        atomic_write_json(file_path, self.link_data[category])

    def update_link_menus(self):
        category_prefixes = {
            "Memo links": "Ctrl",
            "Program links": "Ctrl+Alt",
            "Web links": "Alt",
            "System links": "Ctrl+Shift"
        }

        for category, category_menu in self.link_menus.items():
            category_menu.clear()
            self.add_link_management_actions(category)
            prefix = category_prefixes.get(category)
            if category in self.link_data:
                for idx, link in enumerate(self.link_data[category]):
                    action = QAction(link.get('name', 'Unnamed'), self)
                    url = link.get('url', '')
                    action.triggered.connect(lambda _, u=url: self.open_link(u))

                    if prefix and idx < 10:
                        key_char = "0" if idx == 9 else str(idx + 1)
                        shortcut_str = f"{prefix}+{key_char}"
                        action.setShortcut(QKeySequence(shortcut_str))

                    category_menu.addAction(action)

    def open_link(self, url):
        if not url:
            QMessageBox.information(self, "Link", "Empty URL.")
            return

        import os
        import shutil
        import subprocess
        import webbrowser

        target = str(url).strip()
        if len(target) >= 2 and target[0] == target[-1] and target[0] in {'"', "'"}:
            target = target[1:-1].strip()

        try:
            expanded_target = os.path.expandvars(os.path.expanduser(target))
            p = Path(expanded_target)
            if p.exists():
                if p.is_file() and p.suffix.lower() in EDITABLE_SUFFIXES:
                    try:
                        with open(p, 'r', encoding='utf-8') as file:
                            content = file.read()
                    except UnicodeDecodeError:
                        with open(p, 'r', encoding='cp949') as file:
                            content = file.read()

                    current_editor = self.get_current_editor()
                    is_empty_untitled = (
                        current_editor and
                        current_editor.file_path is None and
                        not current_editor.document().isModified() and
                        current_editor.toPlainText() == ""
                    )

                    self.add_new_tab(str(p), content)
                    self.add_recent_file(str(p))

                    if is_empty_untitled and self.tab_widget.count() > 1:
                        self.tab_widget.removeTab(self.tab_widget.currentIndex() - 1)
                elif sys.platform.startswith("win"):
                    os.startfile(str(p))
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(p)])
                else:
                    subprocess.Popen(["xdg-open", str(p)])
                return

            lower_target = target.lower()
            if lower_target.startswith(("http://", "https://", "mailto:", "ftp://", "file://")):
                webbrowser.open(target)
                return

            # System links such as calc, perfmon.exe, and control.exe.
            if not any(sep in target for sep in ("/", "\\")):
                executable = shutil.which(target) or target
                subprocess.Popen([executable])
                return

            # Codex's WindowsApps directory contains a changing version number.
            # Recover the current GUI executable from the stable codex.exe PATH entry.
            if p.name.lower() == "codex.exe" and "openai.codex_" in target.lower():
                codex_cli = shutil.which("codex.exe") or shutil.which("codex")
                if codex_cli:
                    codex_gui = Path(codex_cli).resolve().parent.parent / "Codex.exe"
                    if codex_gui.exists():
                        os.startfile(str(codex_gui))
                        return

            QMessageBox.warning(self, "Open Link", f"Link target was not found:\n{target}")
        except Exception as error:
            QMessageBox.warning(self, "Open Link", f"Could not open link:\n{target}\n\n{error}")

    def add_link_management_actions(self, category):
        manage_link_action = QAction('Manage links', self)
        manage_link_action.triggered.connect(lambda _, cat=category: self.manage_links(cat))
        self.link_menus[category].addAction(manage_link_action)

        self.link_menus[category].addSeparator()

    def manage_links(self, category):
        dialog = LinkManagerDialog(self, category)
        if dialog.exec_() == QDialog.Accepted:
            self.update_link_menus()

    # ---------- Find / Replace ----------
    def find_text(self):
        if self.find_dialog is None:
            self.find_dialog = FindReplaceDialog(self, find_only=True)
        else:
            self.find_dialog.set_find_only(True)
        self.find_dialog.show()
        self.find_dialog.raise_()
        self.find_dialog.activateWindow()

    def replace_text(self):
        if self.find_dialog is None:
            self.find_dialog = FindReplaceDialog(self, find_only=False)
        else:
            self.find_dialog.set_find_only(False)
        self.find_dialog.show()
        self.find_dialog.raise_()
        self.find_dialog.activateWindow()

    def find_next(self, backward=False):
        text = self.last_find_text
        if not text:
            self.find_text()
            return
        editor = self.get_current_editor()
        if not editor:
            return
        flags = QTextDocument.FindFlags()
        if backward:
            flags |= QTextDocument.FindBackward
        cursor = editor.textCursor()
        found = editor.find(text, flags)
        if not found:
            cursor.movePosition(cursor.Start if not backward else cursor.End)
            editor.setTextCursor(cursor)
            if not editor.find(text, flags):
                parent_widget = self.find_dialog if (self.find_dialog and self.find_dialog.isVisible()) else self
                QMessageBox.information(parent_widget, "Find", f"Cannot find '{text}'")

    def go_to_line(self):
        editor = self.get_current_editor()
        if not editor:
            return
        total_lines = editor.document().blockCount()
        dialog = self.create_go_to_line_dialog(
            total_lines,
            editor.textCursor().blockNumber() + 1,
        )
        if dialog.exec_() != QDialog.Accepted:
            return

        block = editor.document().findBlockByNumber(dialog.intValue() - 1)
        if block.isValid():
            editor.setTextCursor(QTextCursor(block))
            editor.centerCursor()
            editor.setFocus()

    def create_go_to_line_dialog(self, total_lines, current_line=1):
        """Create a content-sized, user-resizable line navigation dialog."""
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Go To Line")
        dialog.setLabelText(f"Enter line number (1..{total_lines}):")
        dialog.setInputMode(QInputDialog.IntInput)
        dialog.setIntRange(1, max(1, total_lines))
        dialog.setIntValue(min(max(1, current_line), max(1, total_lines)))
        dialog.setIntStep(1)

        # QInputDialog.getInt() uses a compact native size that can clip the
        # title on Windows.  Calculate a safe width from both visible strings,
        # then leave the dialog resizable for users with larger system fonts.
        metrics = dialog.fontMetrics()
        content_width = max(
            metrics.horizontalAdvance(dialog.windowTitle()) + 190,
            metrics.horizontalAdvance(dialog.labelText()) + 100,
            dialog.sizeHint().width(),
            360,
        )
        dialog.setMinimumWidth(content_width)
        dialog.setMinimumHeight(max(130, dialog.sizeHint().height()))
        dialog.resize(content_width, dialog.minimumHeight())
        dialog.setSizeGripEnabled(True)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMaximizeButtonHint)
        return dialog

    # ---------- Window events ----------
    def closeEvent(self, event):
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            if editor.document().isModified():
                self.tab_widget.setCurrentIndex(i)
                ret = QMessageBox.warning(
                    self, "Unsaved changes",
                    f"The document '{editor.current_file}' has been modified.\nDo you want to save your changes?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                    QMessageBox.Save
                )
                if ret == QMessageBox.Save:
                    if not self.save_file():
                        event.ignore()
                        return
                elif ret == QMessageBox.Cancel:
                    event.ignore()
                    return
        if hasattr(self, "embedded_terminal"):
            self.embedded_terminal.stop()
        event.accept()


class LinkManagerDialog(QDialog):
    def __init__(self, main_win, initial_category):
        super().__init__(main_win)
        self.main_win = main_win
        self.current_category = initial_category
        self.setWindowTitle("Link Manager")
        self.resize(820, 460)

        layout = QVBoxLayout(self)

        category_row = QHBoxLayout()
        category_row.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox(self)
        self.category_combo.addItems(LINK_CATEGORIES)
        self.category_combo.setCurrentText(initial_category)
        self.category_combo.currentTextChanged.connect(self.change_category)
        category_row.addWidget(self.category_combo, 1)
        layout.addLayout(category_row)

        self.table = QTableWidget(0, 2, self)
        self.table.setHorizontalHeaderLabels(["Name", "URL / Path"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table, 1)

        edit_row = QHBoxLayout()
        add_btn = QPushButton("Add Row", self)
        add_btn.clicked.connect(self.add_row)
        edit_row.addWidget(add_btn)

        remove_btn = QPushButton("Remove Row", self)
        remove_btn.clicked.connect(self.remove_selected_rows)
        edit_row.addWidget(remove_btn)

        up_btn = QPushButton("Move Up", self)
        up_btn.clicked.connect(lambda: self.move_selected_row(-1))
        edit_row.addWidget(up_btn)

        down_btn = QPushButton("Move Down", self)
        down_btn.clicked.connect(lambda: self.move_selected_row(1))
        edit_row.addWidget(down_btn)

        browse_btn = QPushButton("Browse File...", self)
        browse_btn.clicked.connect(self.browse_file_for_selected_row)
        edit_row.addWidget(browse_btn)
        edit_row.addStretch(1)
        layout.addLayout(edit_row)

        save_row = QHBoxLayout()
        open_json_btn = QPushButton("Open JSON", self)
        open_json_btn.clicked.connect(self.open_current_json)
        save_row.addWidget(open_json_btn)
        save_row.addStretch(1)

        save_btn = QPushButton("Save", self)
        save_btn.clicked.connect(self.save_current_category)
        save_row.addWidget(save_btn)

        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        save_row.addWidget(close_btn)
        layout.addLayout(save_row)

        self.load_table(initial_category)

    def change_category(self, category):
        self.save_current_category(show_message=False)
        self.current_category = category
        self.load_table(category)

    def load_table(self, category):
        links = self.main_win.link_data.get(category, [])
        self.table.setRowCount(0)
        for link in links:
            self.add_row(link.get('name', ''), link.get('url', ''))

    def add_row(self, name="", url=""):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(name))
        self.table.setItem(row, 1, QTableWidgetItem(url))
        self.table.selectRow(row)

    def remove_selected_rows(self):
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.table.removeRow(row)

    def move_selected_row(self, direction):
        row = self.current_row()
        if row < 0:
            return
        target = row + direction
        if target < 0 or target >= self.table.rowCount():
            return

        row_data = [self.item_text(row, col) for col in range(self.table.columnCount())]
        target_data = [self.item_text(target, col) for col in range(self.table.columnCount())]
        for col, value in enumerate(target_data):
            self.table.setItem(row, col, QTableWidgetItem(value))
        for col, value in enumerate(row_data):
            self.table.setItem(target, col, QTableWidgetItem(value))
        self.table.selectRow(target)

    def browse_file_for_selected_row(self):
        row = self.current_row()
        if row < 0:
            self.add_row()
            row = self.table.rowCount() - 1
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Link Target", "", "All Files (*)"
        )
        if not file_path:
            return
        if not self.item_text(row, 0):
            self.table.setItem(row, 0, QTableWidgetItem(Path(file_path).name))
        self.table.setItem(row, 1, QTableWidgetItem(file_path))

    def open_current_json(self):
        self.save_current_category(show_message=False)
        self.main_win.open_link(str(self.main_win.get_link_file_path(self.current_category)))

    def save_current_category(self, show_message=True):
        links = []
        for row in range(self.table.rowCount()):
            name = self.item_text(row, 0).strip()
            url = self.item_text(row, 1).strip()
            if not name and not url:
                continue
            links.append({'name': name or url, 'url': url})
        self.main_win.link_data[self.current_category] = self.main_win.normalize_links(links)
        self.main_win.save_link_data(self.current_category)
        self.main_win.update_link_menus()
        if show_message:
            QMessageBox.information(self, "Link Manager", "Links saved.")

    def current_row(self):
        indexes = self.table.selectedIndexes()
        return indexes[0].row() if indexes else -1

    def item_text(self, row, col):
        item = self.table.item(row, col)
        return item.text() if item else ""

    def accept(self):
        self.save_current_category(show_message=False)
        super().accept()


class FindReplaceDialog(QWidget):
    def __init__(self, parent=None, find_only=True):
        super().__init__(parent, Qt.Window | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("Find and Replace")
        self.find_only = find_only
        self.main_win = parent

        layout = QVBoxLayout()
        self.find_input = QLineEdit(self)
        self.find_input.setPlaceholderText("Find")
        layout.addWidget(self.find_input)

        btns_row = QHBoxLayout()
        self.find_button = QPushButton("Find")
        self.find_button.clicked.connect(self._find_from_start)
        btns_row.addWidget(self.find_button)

        self.find_next_button = QPushButton("Find Next (F3)")
        self.find_next_button.clicked.connect(lambda: self._find_next(False))
        btns_row.addWidget(self.find_next_button)

        self.find_prev_button = QPushButton("Find Previous (Shift+F3)")
        self.find_prev_button.clicked.connect(lambda: self._find_next(True))
        btns_row.addWidget(self.find_prev_button)
        layout.addLayout(btns_row)

        self.replace_input = QLineEdit(self)
        self.replace_input.setPlaceholderText("Replace")
        layout.addWidget(self.replace_input)

        self.rep_row_widget = QWidget(self)
        rep_row = QHBoxLayout(self.rep_row_widget)
        rep_row.setContentsMargins(0, 0, 0, 0)
        self.replace_button = QPushButton("Replace")
        self.replace_button.clicked.connect(self.replace_once)
        rep_row.addWidget(self.replace_button)

        self.replace_all_button = QPushButton("Replace All")
        self.replace_all_button.clicked.connect(self.replace_all)
        rep_row.addWidget(self.replace_all_button)
        layout.addWidget(self.rep_row_widget)

        self.setLayout(layout)
        self.set_find_only(find_only)

        self.find_input.returnPressed.connect(lambda: self._find_next(False))
        self.replace_input.returnPressed.connect(self.replace_once)

    def set_find_only(self, find_only):
        self.find_only = find_only
        if find_only:
            self.replace_input.hide()
            self.rep_row_widget.hide()
            self.setWindowTitle("Find")
        else:
            self.replace_input.show()
            self.rep_row_widget.show()
            self.setWindowTitle("Find and Replace")
        self.adjustSize()

    def get_current_editor(self):
        return self.main_win.get_current_editor()

    def _sync_find_text(self):
        txt = self.find_input.text()
        self.main_win.last_find_text = txt
        return txt

    def _find_from_start(self):
        text = self._sync_find_text()
        if not text:
            return
        editor = self.get_current_editor()
        if not editor:
            return
        cursor = editor.textCursor()
        cursor.movePosition(cursor.Start)
        editor.setTextCursor(cursor)
        self._find_next(False)

    def _find_next(self, backward=False):
        text = self._sync_find_text()
        if not text:
            return
        self.main_win.find_next(backward=backward)

    def replace_once(self):
        find_text = self._sync_find_text()
        if not find_text:
            return
        editor = self.get_current_editor()
        if not editor:
            return
        replace_text = self.replace_input.text()
        cur = editor.textCursor()
        if cur.hasSelection() and cur.selectedText() == find_text:
            cur.insertText(replace_text)
            editor.setTextCursor(cur)
        self._find_next(False)

    def replace_all(self):
        find_text = self._sync_find_text()
        if not find_text:
            return
        editor = self.get_current_editor()
        if not editor:
            return
        replace_text = self.replace_input.text()
        cur = editor.textCursor()
        cur.beginEditBlock()
        cur.movePosition(cur.Start)
        editor.setTextCursor(cur)
        count = 0
        while editor.find(find_text):
            c = editor.textCursor()
            c.insertText(replace_text)
            count += 1
        cur.endEditBlock()
        QMessageBox.information(self, "Replace All", f"Replaced {count} occurrence(s).")


def create_startup_splash():
    pixmap = QPixmap(420, 180)
    pixmap.fill(QColor("#f6f8fb"))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QColor("#1f2937"))
    title_font = QFont("Segoe UI", 22, QFont.Bold)
    painter.setFont(title_font)
    painter.drawText(QRect(0, 42, 420, 42), Qt.AlignCenter, f"sNote {APP_VERSION}")

    painter.setPen(QColor("#4b5563"))
    body_font = QFont("Segoe UI", 10)
    painter.setFont(body_font)
    painter.drawText(QRect(0, 96, 420, 28), Qt.AlignCenter, "Loading editor...")

    painter.setPen(QColor("#2563eb"))
    painter.setBrush(QColor("#dbeafe"))
    painter.drawRoundedRect(110, 132, 200, 8, 4, 4)
    painter.setBrush(QColor("#2563eb"))
    painter.drawRoundedRect(110, 132, 96, 8, 4, 4)
    painter.end()

    splash = QSplashScreen(pixmap)
    splash.setWindowFlags(Qt.SplashScreen | Qt.WindowStaysOnTopHint)
    splash.showMessage("Starting...", Qt.AlignBottom | Qt.AlignCenter, QColor("#4b5563"))
    return splash


def set_initial_window_geometry(window, app):
    """Open centered at the practical size requested for a desktop workspace."""
    screen = app.primaryScreen()
    if screen is None:
        window.resize(1250, 950)
        return
    available = screen.availableGeometry()
    width = min(1250, max(480, available.width() - 80))
    height = min(950, max(360, available.height() - 80))
    left = available.x() + (available.width() - width) // 2
    top = available.y() + (available.height() - height) // 2
    window.setGeometry(left, top, width, height)


def main():
    """Start the GUI and return its process exit code."""
    import traceback

    crash_log = user_config_directory() / "crash.log"

    def my_excepthook(exception_type, value, tback):
        crash_log.parent.mkdir(parents=True, exist_ok=True)
        with crash_log.open('w', encoding='utf-8') as stream:
            traceback.print_exception(exception_type, value, tback, file=stream)
        sys.__excepthook__(exception_type, value, tback)

    sys.excepthook = my_excepthook

    try:
        app = QApplication(sys.argv)
        app.setApplicationName("sNote")
        app.setApplicationDisplayName("sNote")
        app.setApplicationVersion(APP_VERSION)
        icon_path = Path(__file__).resolve().parent / "resources" / "snote.ico"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        splash = create_startup_splash()
        splash.show()
        app.processEvents()
        splash.showMessage("Preparing editor...", Qt.AlignBottom | Qt.AlignCenter, QColor("#4b5563"))
        app.processEvents()
        window = EnhancedSimpleNotePad()
        set_initial_window_geometry(window, app)
        splash.showMessage("Opening main window...", Qt.AlignBottom | Qt.AlignCenter, QColor("#4b5563"))
        app.processEvents()
        window.showNormal()
        splash.finish(window)
        try:
            return app.exec_()
        except SystemExit:
            return 0
    except Exception:
        crash_log.parent.mkdir(parents=True, exist_ok=True)
        with crash_log.open('a', encoding='utf-8') as stream:
            traceback.print_exc(file=stream)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
