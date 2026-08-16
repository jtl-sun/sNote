"""Dependency-free helpers used by the sNote desktop application."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


class HtmlToMarkdownParser(HTMLParser):
    """Convert common rich clipboard HTML into readable Markdown."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.list_stack: list[dict[str, Any]] = []
        self.link_stack: list[str] = []
        self.skip_depth = 0
        self.in_pre = False

    def add(self, text: str) -> None:
        if text:
            self.parts.append(text)

    def newline(self, count: int = 1) -> None:
        current = "".join(self.parts)
        existing = len(current) - len(current.rstrip("\n"))
        if existing < count:
            self.add("\n" * (count - existing))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attributes = dict(attrs)
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in {"p", "div", "section", "article", "header", "footer"}:
            self.newline(2)
        elif tag == "br":
            self.newline()
        elif tag in {"strong", "b"}:
            self.add("**")
        elif tag in {"em", "i"}:
            self.add("*")
        elif tag == "del":
            self.add("~~")
        elif tag == "code" and not self.in_pre:
            self.add("`")
        elif tag == "pre":
            self.newline(2)
            self.add("```\n")
            self.in_pre = True
        elif tag in {"ul", "ol"}:
            self.list_stack.append({"tag": tag, "number": 0})
            self.newline()
        elif tag == "li":
            self.newline()
            indent = "  " * max(0, len(self.list_stack) - 1)
            if self.list_stack and self.list_stack[-1]["tag"] == "ol":
                self.list_stack[-1]["number"] += 1
                marker = f'{self.list_stack[-1]["number"]}. '
            else:
                marker = "- "
            self.add(indent + marker)
        elif tag in {f"h{i}" for i in range(1, 7)}:
            self.newline(2)
            self.add("#" * int(tag[1]) + " ")
        elif tag == "blockquote":
            self.newline(2)
            self.add("> ")
        elif tag == "a":
            self.add("[")
            self.link_stack.append(attributes.get("href") or "")
        elif tag == "img":
            src = attributes.get("src") or ""
            if src:
                self.add(f'![{attributes.get("alt") or ""}]({src})')
        elif tag == "hr":
            self.newline(2)
            self.add("---")
            self.newline(2)
        elif tag in {"td", "th"}:
            self.add(" | ")
        elif tag == "tr":
            self.newline()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag in {"strong", "b"}:
            self.add("**")
        elif tag in {"em", "i"}:
            self.add("*")
        elif tag == "del":
            self.add("~~")
        elif tag == "code" and not self.in_pre:
            self.add("`")
        elif tag == "pre":
            self.newline()
            self.add("```")
            self.newline(2)
            self.in_pre = False
        elif tag in {"ul", "ol"}:
            if self.list_stack:
                self.list_stack.pop()
            self.newline(2 if not self.list_stack else 1)
        elif tag in {"p", "div", "section", "article", "blockquote"}:
            self.newline(2)
        elif tag in {f"h{i}" for i in range(1, 7)}:
            self.newline(2)
        elif tag == "a":
            href = self.link_stack.pop() if self.link_stack else ""
            self.add(f"]({href})" if href else "]")

    def handle_data(self, data: str) -> None:
        if self.skip_depth or not data:
            return
        if self.in_pre:
            self.add(data)
            return
        text = re.sub(r"\s+", " ", data)
        if text == " ":
            current = "".join(self.parts)
            if not current or current.endswith((" ", "\n")):
                return
        self.add(text)

    def markdown(self) -> str:
        text = "".join(self.parts).replace("\xa0", " ")
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def html_to_markdown(html: str) -> str:
    parser = HtmlToMarkdownParser()
    try:
        parser.feed(html)
        parser.close()
        return parser.markdown()
    except Exception:
        return ""


def link_file_name(category: str) -> str:
    return f'{category.lower().replace(" ", "_")}.json'


def user_config_directory() -> Path:
    """Return a writable per-user configuration folder on each OS."""
    if sys.platform.startswith("win"):
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return root / "sNote"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "sNote"
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "snote"


def read_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return default


def atomic_write_json(path: Path, value: Any) -> None:
    """Write JSON without leaving a half-written settings file after a crash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", text=True
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
