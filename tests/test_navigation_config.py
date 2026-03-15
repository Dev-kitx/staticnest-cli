from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from staticnest.site import (
    SiteConfig,
    build_feedback_url,
    build_header_action,
    build_site,
    build_top_nav_items,
    split_navigation_entries,
)


class NavigationConfigTests(unittest.TestCase):
    def make_config(self, root: Path) -> SiteConfig:
        return SiteConfig(
            title="Test Docs",
            tagline="",
            description="Test site",
            base_url="/",
            content_dir=root / "content",
            output_dir=root / "dist",
            nav_file=root / "navigation.yml",
            brand_name="Test Docs",
            accent="#2563eb",
            github_url="https://example.com/fallback-github",
            theme_name="nest",
            theme_dir=None,
        )

    def write_navigation(self, root: Path, text: str) -> None:
        (root / "navigation.yml").write_text(text)

    def test_split_navigation_entries_keeps_special_sections_out_of_docs_tree(self) -> None:
        entries = [
            {"title": "Overview", "page": "index.md"},
            {"navigation-bar": {"github": {"title": "GitHub", "link": "https://github.com/example/repo"}}},
            {"issues": {"title": "Issues", "link": "https://github.com/example/repo/issues"}},
        ]

        docs_entries, top_nav_config, issues_config = split_navigation_entries(entries)

        self.assertEqual(docs_entries, [{"title": "Overview", "page": "index.md"}])
        self.assertIn("github", top_nav_config)
        self.assertEqual(issues_config["link"], "https://github.com/example/repo/issues")

    def test_build_top_nav_items_excludes_github_and_issues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            self.write_navigation(
                root,
                """- navigation-bar:
    github:
      title: GitHub
      link: https://github.com/example/repo
      logo: https://example.com/logo.svg
    resources:
      title: Resources
      items:
        - name: Getting Started
          link: /docs/getting-started/
- issues:
    title: Issues
    link: https://github.com/example/repo/issues
""",
            )
            config = self.make_config(root)

            items = build_top_nav_items(config)

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].title, "Resources")
            self.assertEqual(items[0].items[0].title, "Getting Started")

    def test_build_header_action_prefers_navigation_bar_github(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            self.write_navigation(
                root,
                """- navigation-bar:
    github:
      title: Source
      link: https://github.com/example/repo
      logo: https://example.com/logo.svg
      alt: Example logo
""",
            )
            config = self.make_config(root)

            action = build_header_action(config)

            self.assertEqual(action.title, "Source")
            self.assertEqual(action.url, "https://github.com/example/repo")
            self.assertEqual(action.logo, "https://example.com/logo.svg")
            self.assertEqual(action.alt, "Example logo")

    def test_build_feedback_url_uses_top_level_issues_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            self.write_navigation(
                root,
                """- issues:
    title: Issues
    link: https://github.com/example/repo/issues
""",
            )
            config = self.make_config(root)

            self.assertEqual(build_feedback_url(config), "https://github.com/example/repo/issues")

    def test_build_site_wires_feedback_and_header_links_from_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "content").mkdir()
            (root / "content" / "index.md").write_text("# Home\n\nWelcome.\n")
            (root / "site.toml").write_text(
                """title = "Test Docs"
description = "Test site"
base_url = "/"
content_dir = "content"
output_dir = "dist"
nav_file = "navigation.yml"

[brand]
name = "Test Docs"
accent = "#2563eb"

[links]
github = "https://example.com/fallback-github"

[theme]
name = "nest"
"""
            )
            self.write_navigation(
                root,
                """- title: Overview
  page: index.md
- navigation-bar:
    github:
      title: GitHub
      link: https://github.com/example/repo
      logo: https://example.com/logo.svg
    resources:
      title: Resources
      items:
        - name: Getting Started
          link: /docs/getting-started/
- issues:
    title: Issues
    link: https://github.com/example/repo/issues
""",
            )

            build_site(root / "site.toml")
            html = (root / "dist" / "index.html").read_text()

            self.assertIn('href="https://github.com/example/repo/issues">Question? Give us feedback</a>', html)
            self.assertIn('href="https://github.com/example/repo" aria-label="GitHub"', html)
            self.assertIn('src="https://example.com/logo.svg"', html)
            self.assertIn(">Resources</summary>", html)
            self.assertNotIn(">Issues</a>", html)


if __name__ == "__main__":
    unittest.main()
