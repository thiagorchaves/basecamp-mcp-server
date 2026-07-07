from __future__ import annotations

import html
import re


def markdown_to_basecamp_html(markdown: str) -> str:
    """Convert a small, predictable Markdown subset into Basecamp-safe HTML.

    Supports headings, unordered lists, fenced code blocks, horizontal rules,
    bold, italic, inline code, and paragraphs.
    """
    lines = markdown.strip().splitlines()
    out: list[str] = []
    in_ul = False
    in_pre = False
    code_buffer: list[str] = []

    def close_ul() -> None:
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    def flush_code() -> None:
        nonlocal in_pre, code_buffer
        escaped = html.escape("\n".join(code_buffer))
        out.append(f"<pre><code>{escaped}</code></pre>")
        code_buffer = []
        in_pre = False

    for raw_line in lines:
        line = raw_line.rstrip()

        if line.strip().startswith("```"):
            if in_pre:
                flush_code()
            else:
                close_ul()
                in_pre = True
                code_buffer = []
            continue

        if in_pre:
            code_buffer.append(line)
            continue

        if not line.strip():
            close_ul()
            continue

        if line.strip() == "---":
            close_ul()
            out.append("<hr>")
        elif line.startswith("### "):
            close_ul()
            out.append(f"<h3>{_inline(line[4:])}</h3>")
        elif line.startswith("## "):
            close_ul()
            out.append(f"<h2>{_inline(line[3:])}</h2>")
        elif line.startswith("# "):
            close_ul()
            out.append(f"<h1>{_inline(line[2:])}</h1>")
        elif line.lstrip().startswith(("- ", "* ")):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            item = line.lstrip()[2:]
            out.append(f"<li>{_inline(item)}</li>")
        else:
            close_ul()
            out.append(f"<p>{_inline(line)}</p>")

    close_ul()
    if in_pre:
        flush_code()
    return "\n".join(out)


def _inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    escaped = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"<em>\1</em>", escaped)
    return escaped
