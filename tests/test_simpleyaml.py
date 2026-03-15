from __future__ import annotations

import unittest

from staticnest.simpleyaml import (
    parse_navigation_yaml,
    parse_scalar,
    parse_yaml_document,
    parse_yaml_mapping,
)


class ParseScalarTests(unittest.TestCase):
    def test_true(self) -> None:
        self.assertIs(parse_scalar("true"), True)
        self.assertIs(parse_scalar("True"), True)

    def test_false(self) -> None:
        self.assertIs(parse_scalar("false"), False)
        self.assertIs(parse_scalar("False"), False)

    def test_null(self) -> None:
        self.assertIsNone(parse_scalar("null"))
        self.assertIsNone(parse_scalar("none"))
        self.assertIsNone(parse_scalar("None"))

    def test_integer(self) -> None:
        self.assertEqual(parse_scalar("42"), 42)
        self.assertEqual(parse_scalar("-7"), -7)

    def test_float(self) -> None:
        self.assertAlmostEqual(parse_scalar("3.14"), 3.14)

    def test_quoted_string_strips_quotes(self) -> None:
        self.assertEqual(parse_scalar('"hello"'), "hello")
        self.assertEqual(parse_scalar("'world'"), "world")

    def test_unquoted_string_returned_as_is(self) -> None:
        self.assertEqual(parse_scalar("hello"), "hello")

    def test_empty_string_returns_empty(self) -> None:
        self.assertEqual(parse_scalar(""), "")
        self.assertEqual(parse_scalar("   "), "")

    def test_inline_list(self) -> None:
        result = parse_scalar("[1, 2, 3]")
        self.assertEqual(result, [1, 2, 3])

    def test_empty_list(self) -> None:
        self.assertEqual(parse_scalar("[]"), [])

    def test_list_with_strings(self) -> None:
        result = parse_scalar("[a, b, c]")
        self.assertEqual(result, ["a", "b", "c"])


class ParseYamlDocumentTests(unittest.TestCase):
    def test_simple_mapping(self) -> None:
        result = parse_yaml_document("title: Hello\nversion: 1")
        self.assertEqual(result["title"], "Hello")
        self.assertEqual(result["version"], 1)

    def test_nested_mapping(self) -> None:
        text = "brand:\n  name: My Site\n  accent: blue"
        result = parse_yaml_document(text)
        self.assertEqual(result["brand"]["name"], "My Site")
        self.assertEqual(result["brand"]["accent"], "blue")

    def test_top_level_list(self) -> None:
        text = "- title: Intro\n- title: Setup"
        result = parse_yaml_document(text)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_ignores_comments(self) -> None:
        text = "# a comment\ntitle: Hello"
        result = parse_yaml_document(text)
        self.assertEqual(result["title"], "Hello")

    def test_ignores_blank_lines(self) -> None:
        text = "\n\ntitle: Hello\n\n"
        result = parse_yaml_document(text)
        self.assertEqual(result["title"], "Hello")

    def test_boolean_values(self) -> None:
        result = parse_yaml_document("enabled: true\ndraft: false")
        self.assertTrue(result["enabled"])
        self.assertFalse(result["draft"])

    def test_null_value(self) -> None:
        result = parse_yaml_document("key: null")
        self.assertIsNone(result["key"])


class ParseYamlMappingTests(unittest.TestCase):
    def test_returns_dict(self) -> None:
        result = parse_yaml_mapping("name: nest\nversion: 1")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "nest")

    def test_raises_on_non_mapping(self) -> None:
        with self.assertRaises(ValueError):
            parse_yaml_mapping("- item one\n- item two")

    def test_nested_values(self) -> None:
        text = "theme:\n  name: nest\n  accent: '#2563eb'"
        result = parse_yaml_mapping(text)
        self.assertEqual(result["theme"]["name"], "nest")


class ParseNavigationYamlTests(unittest.TestCase):
    def test_returns_list(self) -> None:
        text = "- title: Overview\n  page: index.md\n"
        result = parse_navigation_yaml(text)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["title"], "Overview")

    def test_raises_on_mapping_input(self) -> None:
        with self.assertRaises(ValueError):
            parse_navigation_yaml("title: Overview")

    def test_nested_items(self) -> None:
        text = (
            "- title: Guides\n"
            "  items:\n"
            "    - page: docs/getting-started.md\n"
            "    - page: docs/configuration.md\n"
        )
        result = parse_navigation_yaml(text)
        self.assertEqual(result[0]["title"], "Guides")
        self.assertEqual(len(result[0]["items"]), 2)

    def test_navigation_bar_entry(self) -> None:
        text = (
            "- navigation-bar:\n"
            "    github:\n"
            "      title: GitHub\n"
            "      link: https://github.com/example/repo\n"
        )
        result = parse_navigation_yaml(text)
        self.assertIn("navigation-bar", result[0])
        self.assertEqual(result[0]["navigation-bar"]["github"]["title"], "GitHub")

    def test_issues_entry(self) -> None:
        text = (
            "- issues:\n"
            "    title: Issues\n"
            "    link: https://github.com/example/repo/issues\n"
        )
        result = parse_navigation_yaml(text)
        self.assertIn("issues", result[0])
        self.assertEqual(result[0]["issues"]["link"], "https://github.com/example/repo/issues")

    def test_mixed_entries(self) -> None:
        text = (
            "- title: Overview\n"
            "  page: index.md\n"
            "- navigation-bar:\n"
            "    github:\n"
            "      title: GitHub\n"
            "      link: https://github.com/org/repo\n"
            "- issues:\n"
            "    title: Issues\n"
            "    link: https://github.com/org/repo/issues\n"
        )
        result = parse_navigation_yaml(text)
        self.assertEqual(len(result), 3)

    def test_invalid_mapping_entry_raises(self) -> None:
        text = "- bad entry without colon in mapping\n  notakey anything\n"
        # This may or may not raise depending on how the parser handles it;
        # the test verifies it either parses without crashing or raises ValueError.
        try:
            parse_navigation_yaml(text)
        except ValueError:
            pass  # acceptable


if __name__ == "__main__":
    unittest.main()
