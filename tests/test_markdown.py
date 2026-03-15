from __future__ import annotations

import unittest

from staticnest.markdown import (
    Heading,
    RenderedPage,
    highlight_bash_line,
    highlight_code,
    highlight_config_line,
    highlight_json_line,
    highlight_markdown_line,
    highlight_pythonish_line,
    render_code_block,
    render_inline,
    render_markdown,
    slugify,
    split_comment_outside_quotes,
    summarize,
    wrap_token,
)


class SlugifyTests(unittest.TestCase):
    def test_lowercase_words(self) -> None:
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_special_characters_replaced(self) -> None:
        self.assertEqual(slugify("Getting Started!"), "getting-started")

    def test_numbers_preserved(self) -> None:
        self.assertEqual(slugify("Step 1: Setup"), "step-1-setup")

    def test_empty_string_returns_section(self) -> None:
        self.assertEqual(slugify(""), "section")

    def test_only_special_chars_returns_section(self) -> None:
        self.assertEqual(slugify("!!!"), "section")

    def test_leading_trailing_hyphens_stripped(self) -> None:
        self.assertEqual(slugify("-Title-"), "title")


class RenderInlineTests(unittest.TestCase):
    def test_plain_text_passthrough(self) -> None:
        self.assertEqual(render_inline("hello world"), "hello world")

    def test_link_rendered(self) -> None:
        result = render_inline("[Click me](https://example.com)")
        self.assertIn('<a href="https://example.com">Click me</a>', result)

    def test_inline_code(self) -> None:
        result = render_inline("run `pip install` now")
        self.assertIn("<code>pip install</code>", result)

    def test_bold(self) -> None:
        result = render_inline("this is **bold** text")
        self.assertIn("<strong>bold</strong>", result)

    def test_italic(self) -> None:
        result = render_inline("this is *italic* text")
        self.assertIn("<em>italic</em>", result)

    def test_html_characters_escaped(self) -> None:
        result = render_inline("a < b & c > d")
        self.assertIn("&lt;", result)
        self.assertIn("&amp;", result)
        self.assertIn("&gt;", result)

    def test_combined_formatting(self) -> None:
        result = render_inline("**bold** and `code`")
        self.assertIn("<strong>bold</strong>", result)
        self.assertIn("<code>code</code>", result)


class SummarizeTests(unittest.TestCase):
    def test_returns_first_non_heading_line(self) -> None:
        lines = ["# Title", "", "This is a description."]
        self.assertEqual(summarize(lines), "This is a description.")

    def test_skips_headings(self) -> None:
        lines = ["# Heading", "## Sub", "Some content"]
        self.assertEqual(summarize(lines), "Some content")

    def test_truncates_long_lines(self) -> None:
        long_line = "word " * 50  # > 180 chars
        result = summarize([long_line])
        self.assertTrue(result.endswith("..."))
        self.assertLessEqual(len(result), 180)

    def test_empty_lines_skipped(self) -> None:
        lines = ["", "   ", "First paragraph."]
        self.assertEqual(summarize(lines), "First paragraph.")

    def test_empty_returns_empty_string(self) -> None:
        self.assertEqual(summarize([]), "")

    def test_only_headings_returns_empty(self) -> None:
        self.assertEqual(summarize(["# Heading", "## Sub"]), "")


class WrapTokenTests(unittest.TestCase):
    def test_wraps_with_correct_class(self) -> None:
        result = wrap_token("keyword", "def")
        self.assertEqual(result, '<span class="tok-keyword">def</span>')

    def test_escapes_html_in_value(self) -> None:
        result = wrap_token("string", '"hello"')
        self.assertIn("&quot;", result)


class SplitCommentOutsideQuotesTests(unittest.TestCase):
    def test_comment_outside_quotes(self) -> None:
        code, comment = split_comment_outside_quotes('x = 1  # a comment')
        self.assertEqual(code, 'x = 1  ')
        self.assertEqual(comment, '# a comment')

    def test_hash_inside_string_not_a_comment(self) -> None:
        code, comment = split_comment_outside_quotes('x = "url#anchor"')
        self.assertEqual(code, 'x = "url#anchor"')
        self.assertEqual(comment, '')

    def test_no_comment(self) -> None:
        code, comment = split_comment_outside_quotes('x = 42')
        self.assertEqual(code, 'x = 42')
        self.assertEqual(comment, '')

    def test_hash_in_single_quoted_string(self) -> None:
        code, comment = split_comment_outside_quotes("x = 'hello#world'")
        self.assertEqual(code, "x = 'hello#world'")
        self.assertEqual(comment, "")


class HighlightJsonLineTests(unittest.TestCase):
    def test_highlights_string_value(self) -> None:
        result = highlight_json_line('"key": "value"')
        self.assertIn('tok-key', result)
        self.assertIn('tok-string', result)

    def test_highlights_number(self) -> None:
        result = highlight_json_line('42')
        self.assertIn('tok-number', result)

    def test_highlights_boolean(self) -> None:
        result = highlight_json_line('true')
        self.assertIn('tok-keyword', result)

    def test_highlights_null(self) -> None:
        result = highlight_json_line('null')
        self.assertIn('tok-keyword', result)

    def test_highlights_punctuation(self) -> None:
        result = highlight_json_line('{')
        self.assertIn('tok-punct', result)


class HighlightConfigLineTests(unittest.TestCase):
    def test_yaml_key_value(self) -> None:
        result = highlight_config_line('title: My Docs', ':')
        self.assertIn('tok-key', result)

    def test_toml_key_value(self) -> None:
        result = highlight_config_line('name = "nest"', '=')
        self.assertIn('tok-key', result)

    def test_comment_line(self) -> None:
        result = highlight_config_line('# This is a comment', ':')
        self.assertIn('tok-comment', result)

    def test_empty_line_returns_empty(self) -> None:
        self.assertEqual(highlight_config_line('', ':'), '')

    def test_comment_after_value(self) -> None:
        result = highlight_config_line('port: 8080  # default', ':')
        self.assertIn('tok-key', result)
        self.assertIn('tok-comment', result)


class HighlightMarkdownLineTests(unittest.TestCase):
    def test_heading_line(self) -> None:
        result = highlight_markdown_line('# Hello')
        self.assertIn('tok-keyword', result)

    def test_list_item(self) -> None:
        result = highlight_markdown_line('- item')
        self.assertIn('tok-punct', result)

    def test_plain_line_escaped(self) -> None:
        result = highlight_markdown_line('plain text <b>')
        self.assertIn('&lt;b&gt;', result)
        self.assertNotIn('tok-', result)


class HighlightBashLineTests(unittest.TestCase):
    def test_comment_line(self) -> None:
        result = highlight_bash_line('# comment')
        self.assertIn('tok-comment', result)

    def test_command_highlighted(self) -> None:
        result = highlight_bash_line('pip install foo')
        self.assertIn('tok-command', result)

    def test_flag_highlighted(self) -> None:
        result = highlight_bash_line('pip install --upgrade foo')
        self.assertIn('tok-flag', result)

    def test_variable_highlighted(self) -> None:
        result = highlight_bash_line('echo $HOME')
        self.assertIn('tok-variable', result)

    def test_string_highlighted(self) -> None:
        result = highlight_bash_line('echo "hello world"')
        self.assertIn('tok-string', result)

    def test_empty_line_returns_empty(self) -> None:
        self.assertEqual(highlight_bash_line(''), '')


class HighlightPythonishLineTests(unittest.TestCase):
    def test_keyword_highlighted(self) -> None:
        result = highlight_pythonish_line('def foo():')
        self.assertIn('tok-keyword', result)

    def test_string_highlighted(self) -> None:
        result = highlight_pythonish_line('x = "hello"')
        self.assertIn('tok-string', result)

    def test_number_highlighted(self) -> None:
        result = highlight_pythonish_line('x = 42')
        self.assertIn('tok-number', result)

    def test_comment_highlighted(self) -> None:
        result = highlight_pythonish_line('# comment')
        self.assertIn('tok-comment', result)

    def test_operator_highlighted(self) -> None:
        result = highlight_pythonish_line('x == y')
        self.assertIn('tok-operator', result)


class HighlightCodeTests(unittest.TestCase):
    def test_python_language(self) -> None:
        result = highlight_code('python', 'def foo(): pass')
        self.assertIn('tok-keyword', result)

    def test_bash_language(self) -> None:
        result = highlight_code('bash', '# comment')
        self.assertIn('tok-comment', result)

    def test_yaml_language(self) -> None:
        result = highlight_code('yaml', 'key: value')
        self.assertIn('tok-key', result)

    def test_toml_language(self) -> None:
        result = highlight_code('toml', 'name = "nest"')
        self.assertIn('tok-key', result)

    def test_json_language(self) -> None:
        result = highlight_code('json', '"key": true')
        self.assertIn('tok-keyword', result)

    def test_markdown_language(self) -> None:
        result = highlight_code('markdown', '# Heading')
        self.assertIn('tok-keyword', result)

    def test_unknown_language_returns_escaped(self) -> None:
        result = highlight_code('unknown-xyz', '<b>bold</b>')
        self.assertIn('&lt;b&gt;', result)
        self.assertNotIn('<b>', result)

    def test_sh_alias(self) -> None:
        result = highlight_code('sh', '# comment')
        self.assertIn('tok-comment', result)

    def test_py_alias(self) -> None:
        result = highlight_code('py', 'return x')
        self.assertIn('tok-keyword', result)

    def test_multiline_code(self) -> None:
        result = highlight_code('python', 'def foo():\n    return 1')
        self.assertIn('\n', result)


class RenderCodeBlockTests(unittest.TestCase):
    def test_contains_code_block_wrapper(self) -> None:
        result = render_code_block('python', ['x = 1'])
        self.assertIn('class="code-block"', result)

    def test_contains_copy_button(self) -> None:
        result = render_code_block('python', ['x = 1'])
        self.assertIn('data-code-copy', result)

    def test_language_badge_shown(self) -> None:
        result = render_code_block('bash', ['echo hi'])
        self.assertIn('bash', result)

    def test_empty_language_shows_text_badge(self) -> None:
        result = render_code_block('', ['some text'])
        self.assertIn('>text<', result)

    def test_language_class_on_code_element(self) -> None:
        result = render_code_block('python', ['x = 1'])
        self.assertIn('class="language-python"', result)

    def test_multiline_code_preserved(self) -> None:
        result = render_code_block('python', ['a = 1', 'b = 2'])
        self.assertIn('\n', result)


class RenderMarkdownTests(unittest.TestCase):
    def test_h1_extracted_as_title(self) -> None:
        page = render_markdown("# Hello World\n\nSome text.")
        self.assertEqual(page.title, "Hello World")

    def test_h1_not_in_html_output(self) -> None:
        page = render_markdown("# Hello World\n\nSome text.")
        self.assertNotIn("<h1", page.html)

    def test_headings_in_list(self) -> None:
        page = render_markdown("# Title\n\n## Section\n\nText")
        slugs = [h.slug for h in page.headings]
        self.assertIn("section", slugs)

    def test_paragraph_rendered(self) -> None:
        page = render_markdown("Just a paragraph.")
        self.assertIn("<p>", page.html)

    def test_unordered_list(self) -> None:
        page = render_markdown("- item one\n- item two")
        self.assertIn("<ul>", page.html)
        self.assertIn("<li>", page.html)

    def test_ordered_list(self) -> None:
        page = render_markdown("1. first\n2. second")
        self.assertIn("<ol>", page.html)

    def test_blockquote(self) -> None:
        page = render_markdown("> This is a quote")
        self.assertIn("<blockquote>", page.html)

    def test_horizontal_rule(self) -> None:
        page = render_markdown("---")
        self.assertIn("<hr />", page.html)

    def test_fenced_code_block(self) -> None:
        page = render_markdown("```python\nx = 1\n```")
        self.assertIn("code-block", page.html)

    def test_summary_extracted(self) -> None:
        page = render_markdown("# Title\n\nThis is the summary sentence.")
        self.assertEqual(page.summary, "This is the summary sentence.")

    def test_untitled_when_no_h1(self) -> None:
        page = render_markdown("Just text, no heading.")
        self.assertEqual(page.title, "Untitled")

    def test_inline_link_in_paragraph(self) -> None:
        page = render_markdown("See [docs](https://example.com) for info.")
        self.assertIn('<a href="https://example.com">', page.html)

    def test_unclosed_code_block_still_renders(self) -> None:
        page = render_markdown("```python\nx = 1\n")
        self.assertIn("code-block", page.html)

    def test_returns_rendered_page_type(self) -> None:
        page = render_markdown("# Title\n")
        self.assertIsInstance(page, RenderedPage)

    def test_toc_only_includes_h2_and_h3(self) -> None:
        page = render_markdown("# H1\n\n## H2\n\n### H3\n\n#### H4")
        h2 = next((h for h in page.headings if h.level == 2), None)
        h3 = next((h for h in page.headings if h.level == 3), None)
        h4 = next((h for h in page.headings if h.level == 4), None)
        self.assertIsNotNone(h2)
        self.assertIsNotNone(h3)
        self.assertIsNotNone(h4)

    def test_h2_appears_in_html(self) -> None:
        page = render_markdown("# Title\n\n## Sub-section\n\nText")
        self.assertIn("<h2", page.html)


if __name__ == "__main__":
    unittest.main()
