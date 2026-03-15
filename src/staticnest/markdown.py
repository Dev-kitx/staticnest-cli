from __future__ import annotations

from dataclasses import dataclass
from html import escape
import re


HEADING_SLUG_RE = re.compile(r"[^a-z0-9]+")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
GENERIC_KEYWORDS = {
    "def", "class", "return", "if", "else", "elif", "for", "while", "in",
    "import", "from", "try", "except", "finally", "with", "as", "true",
    "false", "none", "null",
}


@dataclass
class Heading:
    level: int
    text: str
    slug: str


@dataclass
class RenderedPage:
    html: str
    headings: list[Heading]
    title: str
    summary: str


def slugify(value: str) -> str:
    slug = HEADING_SLUG_RE.sub("-", value.lower()).strip("-")
    return slug or "section"


def render_inline(text: str) -> str:
    escaped = escape(text)
    escaped = LINK_RE.sub(lambda m: f'<a href="{escape(m.group(2), quote=True)}">{m.group(1)}</a>', escaped)
    escaped = INLINE_CODE_RE.sub(lambda m: f"<code>{m.group(1)}</code>", escaped)
    escaped = BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", escaped)
    escaped = ITALIC_RE.sub(lambda m: f"<em>{m.group(1)}</em>", escaped)
    return escaped


def summarize(lines: list[str]) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            if len(stripped) <= 180:
                return stripped
            trimmed = stripped[:177].rsplit(" ", 1)[0].rstrip(" ,.")
            return f"{trimmed}..."
    return ""


def wrap_token(token_type: str, value: str) -> str:
    return f'<span class="tok-{token_type}">{escape(value)}</span>'


def split_comment_outside_quotes(line: str) -> tuple[str, str]:
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if char == "#" and not in_single and not in_double:
            return line[:index], line[index:]
    return line, ""


def highlight_json_line(line: str) -> str:
    result: list[str] = []
    index = 0
    key_match = re.match(r'^(\s*)"([^"]+)"(\s*:\s*)', line)
    if key_match:
        result.append(escape(key_match.group(1)))
        result.append(wrap_token("key", f'"{key_match.group(2)}"'))
        result.append(escape(key_match.group(3)))
        index = key_match.end()
    while index < len(line):
        remaining = line[index:]
        for token_type, pattern in (
            ("string", r'^"([^"\\]|\\.)*"'),
            ("number", r"^-?\d+(\.\d+)?"),
            ("keyword", r"^(true|false|null)\b"),
            ("punct", r"^[{}\[\],:]"),
        ):
            match = re.match(pattern, remaining)
            if match:
                result.append(wrap_token(token_type, match.group(0)))
                index += len(match.group(0))
                break
        else:
            result.append(escape(line[index]))
            index += 1
    return "".join(result)


def highlight_config_line(line: str, separator: str) -> str:
    if not line.strip():
        return ""
    content, comment_raw = split_comment_outside_quotes(line)
    comment = wrap_token("comment", comment_raw) if comment_raw else ""

    key_match = re.match(rf"^(\s*)([A-Za-z0-9_.-]+)(\s*{re.escape(separator)}\s*)(.*)$", content)
    if not key_match:
        return escape(content) + comment

    prefix, key, divider, value = key_match.groups()
    highlighted_value = highlight_code_inline(value)
    return "".join(
        [
            escape(prefix),
            wrap_token("key", key),
            escape(divider),
            highlighted_value,
            comment,
        ]
    )


def highlight_code_inline(value: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(value):
        remaining = value[index:]
        for token_type, pattern in (
            ("string", r'^"([^"\\]|\\.)*"'),
            ("string", r"^'([^'\\]|\\.)*'"),
            ("number", r"^-?\d+(\.\d+)?"),
            ("keyword", r"^(true|false|null|none)\b"),
            ("operator", r"^[=\[\]{}(),]"),
        ):
            match = re.match(pattern, remaining, flags=re.IGNORECASE)
            if match:
                result.append(wrap_token(token_type, match.group(0)))
                index += len(match.group(0))
                break
        else:
            result.append(escape(value[index]))
            index += 1
    return "".join(result)


def highlight_markdown_line(line: str) -> str:
    if re.match(r"^\s*#{1,6}\s", line):
        hashes, rest = re.match(r"^(\s*#{1,6}\s)(.*)$", line).groups()
        return wrap_token("keyword", hashes) + escape(rest)
    if re.match(r"^\s*[-*]\s", line):
        bullet, rest = re.match(r"^(\s*[-*]\s)(.*)$", line).groups()
        return wrap_token("punct", bullet) + escape(rest)
    return escape(line)


def highlight_bash_line(line: str) -> str:
    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]
    if not stripped:
        return ""
    if stripped.startswith("#"):
        return escape(indent) + wrap_token("comment", stripped)

    result = [escape(indent)]
    index = 0
    command_highlighted = False
    while index < len(stripped):
        remaining = stripped[index:]
        for token_type, pattern in (
            ("comment", r"^#.*$"),
            ("string", r'^"([^"\\]|\\.)*"'),
            ("string", r"^'([^'\\]|\\.)*'"),
            ("variable", r"^\$[A-Za-z_][A-Za-z0-9_]*"),
            ("flag", r"^--?[A-Za-z0-9_-]+"),
            ("operator", r"^(\|\||&&|[|=])"),
            ("number", r"^\d+"),
        ):
            match = re.match(pattern, remaining)
            if match:
                result.append(wrap_token(token_type, match.group(0)))
                index += len(match.group(0))
                break
        else:
            word = re.match(r"^[A-Za-z0-9_./:-]+", remaining)
            if word:
                token = word.group(0)
                token_type = "command" if not command_highlighted else "text"
                result.append(wrap_token(token_type, token) if token_type != "text" else escape(token))
                command_highlighted = True
                index += len(token)
            else:
                result.append(escape(stripped[index]))
                index += 1
    return "".join(result)


def highlight_pythonish_line(line: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(line):
        remaining = line[index:]
        for token_type, pattern in (
            ("comment", r"^#.*$"),
            ("string", r'^"([^"\\]|\\.)*"'),
            ("string", r"^'([^'\\]|\\.)*'"),
            ("number", r"^-?\d+(\.\d+)?"),
            ("keyword", r"^(def|class|return|if|else|elif|for|while|in|import|from|try|except|finally|with|as)\b"),
            ("operator", r"^(==|!=|<=|>=|=|\+|-|\*|/|:|->)"),
        ):
            match = re.match(pattern, remaining)
            if match:
                result.append(wrap_token(token_type, match.group(0)))
                index += len(match.group(0))
                break
        else:
            word = re.match(r"^[A-Za-z_][A-Za-z0-9_]*", remaining)
            if word:
                token = word.group(0)
                result.append(
                    wrap_token("keyword", token) if token.lower() in GENERIC_KEYWORDS else escape(token)
                )
                index += len(token)
            else:
                result.append(escape(line[index]))
                index += 1
    return "".join(result)


def highlight_code(language: str, code: str) -> str:
    normalized = language.strip().lower()
    highlighter = {
        "bash": highlight_bash_line,
        "sh": highlight_bash_line,
        "shell": highlight_bash_line,
        "yaml": lambda line: highlight_config_line(line, ":"),
        "yml": lambda line: highlight_config_line(line, ":"),
        "toml": lambda line: highlight_config_line(line, "="),
        "json": highlight_json_line,
        "md": highlight_markdown_line,
        "markdown": highlight_markdown_line,
        "python": highlight_pythonish_line,
        "py": highlight_pythonish_line,
    }.get(normalized, highlight_pythonish_line if normalized in {"txt", "text"} else None)

    if highlighter is None:
        return escape(code)
    return "\n".join(highlighter(line) for line in code.splitlines())


def render_code_block(language: str, code_lines: list[str]) -> str:
    raw_code = "\n".join(code_lines)
    code_html = highlight_code(language, raw_code)
    language_value = language.strip()
    language_class = f' class="language-{escape(language_value, quote=True)}"' if language_value else ""
    language_badge = escape(language_value) if language_value else "text"
    return (
        '<div class="code-block">'
        '<div class="code-block-header">'
        f'<span class="code-block-language">{language_badge}</span>'
        '<button class="code-copy-button" type="button" data-code-copy>Copy</button>'
        "</div>"
        f"<pre><code{language_class}>{code_html}</code></pre>"
        "</div>"
    )


def render_markdown(text: str) -> RenderedPage:
    lines = text.splitlines()
    headings: list[Heading] = []
    blocks: list[str] = []
    paragraph: list[str] = []
    list_buffer: list[str] = []
    list_kind: str | None = None
    in_code = False
    code_language = ""
    code_lines: list[str] = []
    title = "Untitled"
    primary_heading_rendered = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            blocks.append(f"<p>{render_inline(' '.join(paragraph))}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_buffer, list_kind
        if list_buffer and list_kind:
            inner = "".join(f"<li>{render_inline(item)}</li>" for item in list_buffer)
            blocks.append(f"<{list_kind}>{inner}</{list_kind}>")
        list_buffer = []
        list_kind = None

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            if in_code:
                blocks.append(render_code_block(code_language, code_lines))
                code_lines = []
                code_language = ""
                in_code = False
            else:
                in_code = True
                code_language = stripped.removeprefix("```").strip()
            continue

        if in_code:
            code_lines.append(raw_line)
            continue

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        if stripped == "---":
            flush_paragraph()
            flush_list()
            blocks.append("<hr />")
            continue

        if stripped.startswith("> "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<blockquote>{render_inline(stripped[2:])}</blockquote>")
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            flush_paragraph()
            flush_list()
            level = len(heading_match.group(1))
            text_value = heading_match.group(2).strip()
            slug = slugify(text_value)
            headings.append(Heading(level=level, text=text_value, slug=slug))
            if title == "Untitled" and level == 1:
                title = text_value
                if not primary_heading_rendered:
                    primary_heading_rendered = True
                    continue
            blocks.append(f'<h{level} id="{slug}">{render_inline(text_value)}</h{level}>')
            continue

        unordered_match = re.match(r"^[-*]\s+(.*)$", stripped)
        ordered_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if unordered_match:
            flush_paragraph()
            if list_kind not in (None, "ul"):
                flush_list()
            list_kind = "ul"
            list_buffer.append(unordered_match.group(1))
            continue
        if ordered_match:
            flush_paragraph()
            if list_kind not in (None, "ol"):
                flush_list()
            list_kind = "ol"
            list_buffer.append(ordered_match.group(1))
            continue

        paragraph.append(stripped)

    flush_paragraph()
    flush_list()

    if in_code:
        blocks.append(render_code_block(code_language, code_lines))

    return RenderedPage(
        html="\n".join(blocks),
        headings=headings,
        title=title,
        summary=summarize(lines),
    )
