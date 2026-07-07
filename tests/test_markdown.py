from basecamp_mcp.markdown import markdown_to_basecamp_html


def test_markdown_is_escaped_and_formatted() -> None:
    result = markdown_to_basecamp_html(
        "# Report\n\n- **safe** <script>\n- *italic*\n\n---\n\n`code`"
    )

    assert "<h1>Report</h1>" in result
    assert "<strong>safe</strong> &lt;script&gt;" in result
    assert "<em>italic</em>" in result
    assert "<hr>" in result
    assert "<code>code</code>" in result
    assert "<script>" not in result


def test_fenced_code_preserves_content_without_rendering_html() -> None:
    result = markdown_to_basecamp_html("```\n<a>unsafe</a>\n```")

    assert result == "<pre><code>&lt;a&gt;unsafe&lt;/a&gt;</code></pre>"
