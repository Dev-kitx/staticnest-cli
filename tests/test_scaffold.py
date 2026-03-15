from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from staticnest.scaffold import (
    DEFAULT_CONFIGURATION_MD,
    DEFAULT_GETTING_STARTED_MD,
    DEFAULT_INDEX_MD,
    DEFAULT_NAVIGATION_YML,
    DEFAULT_SITE_TOML,
    init_project,
)


class InitProjectTests(unittest.TestCase):
    def test_creates_all_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "my-site"
            init_project(target)

            self.assertTrue((target / "site.toml").exists())
            self.assertTrue((target / "navigation.yml").exists())
            self.assertTrue((target / "content" / "index.md").exists())
            self.assertTrue((target / "content" / "docs" / "getting-started.md").exists())
            self.assertTrue((target / "content" / "docs" / "configuration.md").exists())

    def test_returns_resolved_target_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "new-project"
            result = init_project(target)
            self.assertEqual(result, target.resolve())

    def test_creates_target_directory_if_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "deeply" / "nested" / "project"
            self.assertFalse(target.exists())
            init_project(target)
            self.assertTrue(target.exists())

    def test_site_toml_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "site"
            init_project(target)
            content = (target / "site.toml").read_text()
            self.assertIn("title", content)
            self.assertIn("content_dir", content)
            self.assertIn("output_dir", content)

    def test_navigation_yml_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "site"
            init_project(target)
            content = (target / "navigation.yml").read_text()
            self.assertIn("navigation-bar", content)
            self.assertIn("issues", content)

    def test_index_md_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "site"
            init_project(target)
            content = (target / "content" / "index.md").read_text()
            self.assertTrue(content.startswith("#"))

    def test_refuses_to_overwrite_existing_site_toml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "site"
            init_project(target)
            with self.assertRaises(ValueError) as ctx:
                init_project(target)
            self.assertIn("site.toml", str(ctx.exception))
            self.assertIn("Refusing", str(ctx.exception))

    def test_refuses_to_overwrite_existing_navigation_yml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "site"
            target.mkdir(parents=True)
            (target / "navigation.yml").write_text("- title: Existing\n")
            with self.assertRaises(ValueError) as ctx:
                init_project(target)
            self.assertIn("navigation.yml", str(ctx.exception))

    def test_refuses_to_overwrite_lists_all_conflicting_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "site"
            init_project(target)
            with self.assertRaises(ValueError) as ctx:
                init_project(target)
            error_message = str(ctx.exception)
            self.assertIn("site.toml", error_message)
            self.assertIn("navigation.yml", error_message)

    def test_default_site_toml_is_valid_toml(self) -> None:
        import tomllib
        parsed = tomllib.loads(DEFAULT_SITE_TOML)
        self.assertIn("title", parsed)

    def test_default_navigation_yml_starts_with_list(self) -> None:
        self.assertTrue(DEFAULT_NAVIGATION_YML.lstrip().startswith("-"))

    def test_default_index_md_has_heading(self) -> None:
        self.assertIn("# ", DEFAULT_INDEX_MD)

    def test_default_getting_started_md_has_heading(self) -> None:
        self.assertIn("# ", DEFAULT_GETTING_STARTED_MD)

    def test_default_configuration_md_has_heading(self) -> None:
        self.assertIn("# ", DEFAULT_CONFIGURATION_MD)


if __name__ == "__main__":
    unittest.main()
