import json

from snote.core import atomic_write_json, html_to_markdown, link_file_name


def test_html_to_markdown_converts_common_rich_text():
    html = "<h2>Title</h2><p><strong>Bold</strong> and <a href='https://example.com'>link</a></p>"
    assert html_to_markdown(html) == "## Title\n\n**Bold** and [link](https://example.com)"


def test_html_to_markdown_ignores_script_content():
    assert html_to_markdown("<p>Safe</p><script>alert(1)</script>") == "Safe"


def test_link_file_name_is_stable():
    assert link_file_name("Memo links") == "memo_links.json"


def test_atomic_write_json_replaces_complete_document(tmp_path):
    destination = tmp_path / "settings.json"
    atomic_write_json(destination, {"theme": "dark", "items": [1, 2]})
    assert json.loads(destination.read_text(encoding="utf-8")) == {
        "theme": "dark",
        "items": [1, 2],
    }
