from __future__ import annotations

import unittest

from staticnest.theme import (
    THEME_PRESETS,
    get_theme_preset,
    render_css,
    render_not_found_page,
    render_page,
    replace_tokens,
)


class GetThemePresetTests(unittest.TestCase):
    def test_returns_nest_preset(self) -> None:
        preset = get_theme_preset("nest")
        self.assertIsInstance(preset, dict)
        self.assertIn("accent", preset)

    def test_none_returns_all_presets(self) -> None:
        result = get_theme_preset(None)
        self.assertIn("nest", result)

    def test_unknown_theme_raises(self) -> None:
        with self.assertRaises(ValueError):
            get_theme_preset("nonexistent-theme")

    def test_accent_override_applied(self) -> None:
        preset = get_theme_preset("nest", accent="#ff0000")
        self.assertEqual(preset["accent"], "#ff0000")
        self.assertEqual(preset["active_text"], "#ff0000")

    def test_no_accent_override_uses_default(self) -> None:
        preset = get_theme_preset("nest")
        self.assertEqual(preset["accent"], THEME_PRESETS["nest"]["accent"])

    def test_original_preset_not_mutated(self) -> None:
        original_accent = THEME_PRESETS["nest"]["accent"]
        get_theme_preset("nest", accent="#123456")
        self.assertEqual(THEME_PRESETS["nest"]["accent"], original_accent)


class RenderCssTests(unittest.TestCase):
    def test_replaces_all_tokens(self) -> None:
        preset = get_theme_preset("nest")
        css = render_css(preset)
        self.assertNotIn("{{", css)
        self.assertNotIn("}}", css)

    def test_contains_accent_color(self) -> None:
        preset = get_theme_preset("nest", accent="#abcdef")
        css = render_css(preset)
        self.assertIn("#abcdef", css)

    def test_returns_string(self) -> None:
        preset = get_theme_preset("nest")
        self.assertIsInstance(render_css(preset), str)

    def test_contains_css_variable_declarations(self) -> None:
        preset = get_theme_preset("nest")
        css = render_css(preset)
        self.assertIn("--accent:", css)
        self.assertIn("--bg:", css)


class ReplaceTokensTests(unittest.TestCase):
    def _make_context(self, **overrides: str) -> dict[str, str]:
        defaults = {
            "title": "Test Title",
            "description_text": "A description",
            "current_url": "/",
            "brand_name": "MyBrand",
            "github_url": "https://github.com/",
            "feedback_url": "#",
            "header_action_html": "",
            "breadcrumbs_html": "",
            "page_title": "Page",
            "page_heading_html": "<h1>Page</h1>",
            "custom_css_tag": "",
            "custom_js_tag": "",
            "live_reload_tag": "",
            "top_nav_html": "",
            "nav_html": "",
            "pager_html": "",
            "toc_html": "",
            "search_json": "[]",
            "base_js": "",
            "article_html": "<p>content</p>",
        }
        defaults.update(overrides)
        return defaults

    def test_replaces_title_token(self) -> None:
        template = "{{ title }}"
        ctx = self._make_context(title="Hello")
        result = replace_tokens(template, ctx)
        self.assertEqual(result, "Hello")

    def test_replaces_multiple_tokens(self) -> None:
        template = "{{ brand_name }} | {{ title }}"
        ctx = self._make_context(brand_name="Brand", title="Docs")
        result = replace_tokens(template, ctx)
        self.assertEqual(result, "Brand | Docs")

    def test_unknown_tokens_left_untouched(self) -> None:
        template = "{{ unknown_token }}"
        ctx = self._make_context()
        result = replace_tokens(template, ctx)
        self.assertEqual(result, "{{ unknown_token }}")


class RenderPageTests(unittest.TestCase):
    def _call_render_page(self, **overrides):
        defaults = dict(
            site_title="My Site",
            brand_name="My Site",
            description="A test site",
            tagline="Test docs",
            github_url="https://github.com/",
            feedback_url="#",
            header_action_html="",
            page_title="Home",
            page_summary="Home page",
            nav_html="",
            top_nav_html="",
            toc_html="",
            article_html="<p>Hello</p>",
            current_url="/",
            search_index=[],
            template_override=None,
            has_custom_css=False,
            has_custom_js=False,
            live_reload=False,
            live_reload_path="/__staticnest_version",
            breadcrumbs_html="",
            pager_html="",
        )
        defaults.update(overrides)
        return render_page(**defaults)

    def test_returns_html_string(self) -> None:
        result = self._call_render_page()
        self.assertIsInstance(result, str)
        self.assertIn("<!doctype html>", result.lower())

    def test_contains_page_title(self) -> None:
        result = self._call_render_page(page_title="Getting Started")
        self.assertIn("Getting Started", result)

    def test_contains_article_html(self) -> None:
        result = self._call_render_page(article_html="<p>My content</p>")
        self.assertIn("My content", result)

    def test_contains_brand_name(self) -> None:
        result = self._call_render_page(brand_name="SuperDocs")
        self.assertIn("SuperDocs", result)

    def test_no_custom_css_tag_when_disabled(self) -> None:
        result = self._call_render_page(has_custom_css=False)
        self.assertNotIn("custom.css", result)

    def test_custom_css_tag_when_enabled(self) -> None:
        result = self._call_render_page(has_custom_css=True)
        self.assertIn("custom.css", result)

    def test_no_custom_js_tag_when_disabled(self) -> None:
        result = self._call_render_page(has_custom_js=False)
        self.assertNotIn("custom.js", result)

    def test_custom_js_tag_when_enabled(self) -> None:
        result = self._call_render_page(has_custom_js=True)
        self.assertIn("custom.js", result)

    def test_live_reload_tag_when_enabled(self) -> None:
        result = self._call_render_page(live_reload=True, live_reload_path="/__staticnest_version")
        self.assertIn("__staticnest_version", result)

    def test_no_live_reload_tag_when_disabled(self) -> None:
        result = self._call_render_page(live_reload=False)
        self.assertNotIn("__staticnest_version", result)

    def test_template_override_used(self) -> None:
        template = "CUSTOM {{ article_html }}"
        result = self._call_render_page(template_override=template, article_html="<p>hi</p>")
        self.assertEqual(result, "CUSTOM <p>hi</p>")

    def test_empty_toc_shows_fallback_message(self) -> None:
        result = self._call_render_page(toc_html="")
        self.assertIn("No headings", result)

    def test_github_url_escaped(self) -> None:
        result = self._call_render_page(github_url='https://example.com?a=1&b=2')
        self.assertNotIn("&b=2", result)

    def test_search_index_serialised(self) -> None:
        index = [{"title": "Home", "url": "/", "summary": "", "headings": [], "content": ""}]
        result = self._call_render_page(search_index=index)
        self.assertIn("Home", result)


class RenderNotFoundPageTests(unittest.TestCase):
    def _call(self, **overrides):
        defaults = dict(
            site_title="My Site",
            brand_name="My Site",
            description="A test site",
            github_url="https://github.com/",
            feedback_url="#",
            header_action_html="",
            top_nav_html="",
            nav_html="",
            current_url="/",
            search_index=[],
            has_custom_css=False,
            has_custom_js=False,
            live_reload=False,
            live_reload_path="/__staticnest_version",
        )
        defaults.update(overrides)
        return render_not_found_page(**defaults)

    def test_returns_html_string(self) -> None:
        result = self._call()
        self.assertIsInstance(result, str)

    def test_contains_404_content(self) -> None:
        result = self._call()
        self.assertIn("404", result)

    def test_contains_site_title(self) -> None:
        result = self._call(site_title="MySite404")
        self.assertIn("MySite404", result)


if __name__ == "__main__":
    unittest.main()
