import json

from snote.core import (
    atomic_write_json,
    html_to_markdown,
    link_file_name,
    terminal_command_payload,
    terminal_safe_output_length,
)


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


def test_powershell_payload_parses_marker_before_interactive_command_runs():
    payload = terminal_command_payload("powershell", "xget", "__DONE__", "\r\n")
    assert "FromBase64String('eGdldA==')" in payload
    assert "Invoke-Expression $__snoteCommand" in payload
    assert "Write-Output ('__DONE__'" in payload
    assert "\n" not in payload.rstrip("\r\n")


def test_posix_payload_keeps_marker_in_the_same_parsed_group():
    payload = terminal_command_payload("posix", "menu-tool", "__DONE__", "\n")
    assert payload == "{\nmenu-tool\nprintf '%s\\n' '__DONE__'\n}\n"


def test_terminal_only_holds_a_suffix_that_could_be_a_split_marker():
    marker = "__SNOTE_DONE__"
    assert terminal_safe_output_length("Press Enter", marker) == len("Press Enter")
    assert terminal_safe_output_length("result\n__SNO", marker) == len("result\n")
    assert terminal_safe_output_length("ordinary output.", marker) == len("ordinary output.")
