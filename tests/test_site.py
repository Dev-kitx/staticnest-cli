from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from staticnest.site import (
    BuildResult,
    HeaderAction,
    NavNode,
    NavPageLink,
    Page,
    SiteConfig,
    TopNavItem,
    build_inferred_nav_tree,
    build_search_text,
    build_site,
    build_url,
    default_title_from_path,
    find_nav_trail,
    flatten_nav_pages,
    load_config,
    output_path_for,
    render_breadcrumbs_html,
    render_header_action_html,
    render_nav_html,
    render_pager_html,
    render_toc_html,
    render_top_nav_html,
    sort_nav_tree,
    split_front_matter,
)
from staticnest.markdown import Heading


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_page(
    relative_path: str,
    title: str = "Page",
    url: str | None = None,
    order: int = 10_000,
    is_index: bool = False,
) -> Page:
    rel = Path(relative_path)
    return Page(
        source_path=Path(f"/fake/content/{relative_path}"),
        relative_path=rel,
        url=url or build_url(rel),
        title=title,
        nav_title=title,
        summary="",
        html="<p>content</p>",
        headings=[],
        search_text="",
        order=order,
        template=None,
        is_index=is_index,
        draft=False,
    )


def _make_node(key: str, title: str, url: str | None = None, order: int = 0, children: list[NavNode] | None = None) -> NavNode:
    node = NavNode(key=key, title=title, url=url, order=order)
    if children:
        node.children = children
    return node


# ---------------------------------------------------------------------------
# split_front_matter
# ---------------------------------------------------------------------------

class SplitFrontMatterTests(unittest.TestCase):
    def test_no_front_matter(self) -> None:
        meta, body = split_front_matter("# Hello\n\nText")
        self.assertEqual(meta, {})
        self.assertIn("Hello", body)

    def test_toml_front_matter(self) -> None:
        text = '+++\ntitle = "My Page"\n+++\n# Content'
        meta, body = split_front_matter(text)
        self.assertEqual(meta["title"], "My Page")
        self.assertIn("Content", body)

    def test_yaml_front_matter(self) -> None:
        text = "---\ntitle: My Page\n---\n# Content"
        meta, body = split_front_matter(text)
        self.assertEqual(meta["title"], "My Page")
        self.assertIn("Content", body)

    def test_incomplete_toml_delimiter_ignored(self) -> None:
        text = "+++\ntitle = 'oops'\n# no closing back-tick\n# Content"
        meta, body = split_front_matter(text)
        self.assertEqual(meta, {})

    def test_incomplete_yaml_delimiter_ignored(self) -> None:
        text = "---\ntitle: oops\n# no closing ---\n"
        meta, body = split_front_matter(text)
        self.assertEqual(meta, {})


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

class LoadConfigTests(unittest.TestCase):
    def _write_config(self, tmp: str, extra: str = "") -> Path:
        root = Path(tmp)
        config = root / "site.toml"
        config.write_text(
            'title = "Docs"\nbase_url = "/"\ncontent_dir = "content"\noutput_dir = "dist"\n'
            + extra +
            '[brand]\nname = "Docs"\n[links]\ngithub = "https://github.com/"\n'
            '[theme]\nname = "nest"\n'
        )
        return config

    def test_loads_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config(self._write_config(tmp))
            self.assertEqual(config.title, "Docs")

    def test_loads_content_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = load_config(self._write_config(tmp))
            self.assertTrue(str(cfg.content_dir).endswith("content"))

    def test_loads_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = load_config(self._write_config(tmp))
            self.assertTrue(str(cfg.output_dir).endswith("dist"))

    def test_nav_file_none_when_not_specified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = load_config(self._write_config(tmp))
            self.assertIsNone(cfg.nav_file)

    def test_nav_file_set_when_specified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = load_config(self._write_config(tmp, 'nav_file = "navigation.yml"\n'))
            self.assertIsNotNone(cfg.nav_file)
            self.assertTrue(str(cfg.nav_file).endswith("navigation.yml"))

    def test_brand_name_falls_back_to_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "site.toml").write_text(
                'title = "MyTitle"\nbase_url = "/"\ncontent_dir = "content"\noutput_dir = "dist"\n'
                '[links]\ngithub = "#"\n[theme]\nname = "nest"\n'
            )
            cfg = load_config(root / "site.toml")
            self.assertEqual(cfg.brand_name, "MyTitle")


# ---------------------------------------------------------------------------
# build_url
# ---------------------------------------------------------------------------

class BuildUrlTests(unittest.TestCase):
    def test_index_md_at_root(self) -> None:
        self.assertEqual(build_url(Path("index.md")), "/")

    def test_index_md_in_subdir(self) -> None:
        self.assertEqual(build_url(Path("docs/index.md")), "/docs/")

    def test_regular_page(self) -> None:
        self.assertEqual(build_url(Path("docs/getting-started.md")), "/docs/getting-started/")

    def test_nested_page(self) -> None:
        self.assertEqual(build_url(Path("guides/advanced/security.md")), "/guides/advanced/security/")


# ---------------------------------------------------------------------------
# default_title_from_path
# ---------------------------------------------------------------------------

class DefaultTitleFromPathTests(unittest.TestCase):
    def test_regular_file(self) -> None:
        self.assertEqual(default_title_from_path(Path("getting-started.md")), "Getting Started")

    def test_underscore_replaced(self) -> None:
        self.assertEqual(default_title_from_path(Path("quick_start.md")), "Quick Start")

    def test_index_uses_parent_dir(self) -> None:
        self.assertEqual(default_title_from_path(Path("guides/index.md")), "Guides")

    def test_root_index_yields_home(self) -> None:
        self.assertEqual(default_title_from_path(Path("index.md")), "Home")


# ---------------------------------------------------------------------------
# build_search_text
# ---------------------------------------------------------------------------

class BuildSearchTextTests(unittest.TestCase):
    def test_strips_code_fences(self) -> None:
        result = build_search_text("```python\nx = 1\n```\nText", [])
        self.assertNotIn("python", result)
        self.assertIn("Text", result)

    def test_strips_markdown_headings(self) -> None:
        result = build_search_text("## Section\n\nBody text", [])
        self.assertNotIn("##", result)
        self.assertIn("Body", result)

    def test_includes_heading_text_from_headings(self) -> None:
        headings = [Heading(level=2, text="Overview", slug="overview")]
        result = build_search_text("Body text", headings)
        self.assertIn("Overview", result)

    def test_strips_inline_code(self) -> None:
        result = build_search_text("Run `pip install` today", [])
        self.assertNotIn("`", result)
        self.assertIn("pip install", result)

    def test_strips_links(self) -> None:
        result = build_search_text("See [docs](https://example.com) here", [])
        self.assertIn("docs", result)
        self.assertNotIn("https://example.com", result)


# ---------------------------------------------------------------------------
# build_inferred_nav_tree
# ---------------------------------------------------------------------------

class BuildInferredNavTreeTests(unittest.TestCase):
    def test_root_page_becomes_child_of_root(self) -> None:
        pages = [_make_page("index.md", title="Home", is_index=True)]
        tree = build_inferred_nav_tree(pages)
        self.assertTrue(any(n.url == "/" for n in tree.children))

    def test_pages_sorted_by_order(self) -> None:
        pages = [
            _make_page("b.md", title="B", order=2),
            _make_page("a.md", title="A", order=1),
        ]
        tree = build_inferred_nav_tree(pages)
        titles = [n.title for n in tree.children]
        self.assertLess(titles.index("A"), titles.index("B"))

    def test_nested_page_creates_dir_node(self) -> None:
        pages = [_make_page("docs/getting-started.md", title="Getting Started")]
        tree = build_inferred_nav_tree(pages)
        dir_node = next((n for n in tree.children if "docs" in n.key.lower()), None)
        self.assertIsNotNone(dir_node)

    def test_index_md_sets_dir_node_url(self) -> None:
        pages = [_make_page("guides/index.md", title="Guides", is_index=True)]
        tree = build_inferred_nav_tree(pages)
        dir_node = next((n for n in tree.children if "guides" in n.key.lower()), None)
        self.assertIsNotNone(dir_node)
        self.assertEqual(dir_node.url, "/guides/")


# ---------------------------------------------------------------------------
# sort_nav_tree
# ---------------------------------------------------------------------------

class SortNavTreeTests(unittest.TestCase):
    def test_children_sorted_by_order(self) -> None:
        root = _make_node("root", "root", children=[
            _make_node("b", "B", order=2),
            _make_node("a", "A", order=1),
        ])
        sort_nav_tree(root)
        self.assertEqual(root.children[0].title, "A")

    def test_tie_broken_by_title(self) -> None:
        root = _make_node("root", "root", children=[
            _make_node("z", "Z", order=0),
            _make_node("a", "A", order=0),
        ])
        sort_nav_tree(root)
        self.assertEqual(root.children[0].title, "A")

    def test_nested_children_sorted(self) -> None:
        child = _make_node("parent", "Parent", children=[
            _make_node("y", "Y", order=2),
            _make_node("x", "X", order=1),
        ])
        root = _make_node("root", "root", children=[child])
        sort_nav_tree(root)
        self.assertEqual(root.children[0].children[0].title, "X")


# ---------------------------------------------------------------------------
# render_nav_html
# ---------------------------------------------------------------------------

class RenderNavHtmlTests(unittest.TestCase):
    def test_renders_link(self) -> None:
        node = _make_node("root", "root", children=[
            _make_node("home", "Home", url="/"),
        ])
        html = render_nav_html(node, "/")
        self.assertIn('href="/"', html)
        self.assertIn("Home", html)

    def test_active_class_on_current_page(self) -> None:
        node = _make_node("root", "root", children=[
            _make_node("home", "Home", url="/"),
        ])
        html = render_nav_html(node, "/")
        self.assertIn("active", html)

    def test_no_active_class_for_other_pages(self) -> None:
        node = _make_node("root", "root", children=[
            _make_node("home", "Home", url="/"),
        ])
        html = render_nav_html(node, "/other/")
        self.assertNotIn("active", html)

    def test_section_without_url_renders_label(self) -> None:
        node = _make_node("root", "root", children=[
            _make_node("sec", "Section"),
        ])
        html = render_nav_html(node, "/")
        self.assertIn("nav-group-label", html)
        self.assertIn("Section", html)

    def test_nested_children_rendered(self) -> None:
        child = _make_node("child", "Child", url="/child/")
        parent = _make_node("parent", "Parent", children=[child])
        root = _make_node("root", "root", children=[parent])
        html = render_nav_html(root, "/")
        self.assertIn("nav-children", html)
        self.assertIn("Child", html)

    def test_external_link_has_target_blank(self) -> None:
        node = NavNode(key="ext", title="Ext", url="https://example.com", external=True)
        root = _make_node("root", "root", children=[node])
        html = render_nav_html(root, "/")
        self.assertIn('target="_blank"', html)


# ---------------------------------------------------------------------------
# render_toc_html
# ---------------------------------------------------------------------------

class RenderTocHtmlTests(unittest.TestCase):
    def test_h2_included(self) -> None:
        headings = [Heading(level=2, text="Section", slug="section")]
        html = render_toc_html(headings)
        self.assertIn("toc-level-2", html)
        self.assertIn("#section", html)

    def test_h3_included(self) -> None:
        headings = [Heading(level=3, text="Sub", slug="sub")]
        html = render_toc_html(headings)
        self.assertIn("toc-level-3", html)

    def test_h1_excluded(self) -> None:
        headings = [Heading(level=1, text="Title", slug="title")]
        html = render_toc_html(headings)
        self.assertEqual(html, "")

    def test_h4_excluded(self) -> None:
        headings = [Heading(level=4, text="Deep", slug="deep")]
        html = render_toc_html(headings)
        self.assertEqual(html, "")

    def test_empty_headings_returns_empty(self) -> None:
        self.assertEqual(render_toc_html([]), "")


# ---------------------------------------------------------------------------
# find_nav_trail
# ---------------------------------------------------------------------------

class FindNavTrailTests(unittest.TestCase):
    def test_finds_direct_child(self) -> None:
        child = _make_node("home", "Home", url="/")
        root = _make_node("root", "root", url=None, children=[child])
        trail = find_nav_trail(root, "/")
        self.assertIsNotNone(trail)
        self.assertEqual(trail[-1].url, "/")

    def test_finds_nested_child(self) -> None:
        nested = _make_node("page", "Page", url="/docs/page/")
        parent = _make_node("docs", "Docs", children=[nested])
        root = _make_node("root", "root", children=[parent])
        trail = find_nav_trail(root, "/docs/page/")
        self.assertIsNotNone(trail)
        self.assertEqual(trail[-1].url, "/docs/page/")

    def test_returns_none_for_missing_url(self) -> None:
        root = _make_node("root", "root", children=[_make_node("home", "Home", url="/")])
        trail = find_nav_trail(root, "/nonexistent/")
        self.assertIsNone(trail)


# ---------------------------------------------------------------------------
# render_breadcrumbs_html
# ---------------------------------------------------------------------------

class RenderBreadcrumbsHtmlTests(unittest.TestCase):
    def test_contains_documentation_link(self) -> None:
        page = _make_page("index.md", title="Home", url="/", is_index=True)
        node = _make_node("home", "Home", url="/")
        root = _make_node("root", "root", children=[node])
        html = render_breadcrumbs_html(root, page)
        self.assertIn("Documentation", html)

    def test_contains_page_title(self) -> None:
        page = _make_page("docs/setup.md", title="Setup", url="/docs/setup/")
        leaf = _make_node("setup", "Setup", url="/docs/setup/")
        root = _make_node("root", "root", children=[leaf])
        html = render_breadcrumbs_html(root, page)
        self.assertIn("Setup", html)


# ---------------------------------------------------------------------------
# flatten_nav_pages
# ---------------------------------------------------------------------------

class FlattenNavPagesTests(unittest.TestCase):
    def test_flat_nodes(self) -> None:
        root = _make_node("root", "root", children=[
            _make_node("a", "A", url="/a/"),
            _make_node("b", "B", url="/b/"),
        ])
        pages = flatten_nav_pages(root)
        urls = [p.url for p in pages]
        self.assertIn("/a/", urls)
        self.assertIn("/b/", urls)

    def test_external_nodes_excluded(self) -> None:
        ext = NavNode(key="ext", title="Ext", url="https://external.com", external=True)
        root = _make_node("root", "root", children=[ext])
        pages = flatten_nav_pages(root)
        self.assertEqual(pages, [])

    def test_node_without_url_excluded(self) -> None:
        node = _make_node("sec", "Section")  # no url
        root = _make_node("root", "root", children=[node])
        pages = flatten_nav_pages(root)
        self.assertEqual(pages, [])

    def test_nested_pages_included(self) -> None:
        child = _make_node("child", "Child", url="/child/")
        parent = _make_node("parent", "Parent", children=[child])
        root = _make_node("root", "root", children=[parent])
        pages = flatten_nav_pages(root)
        urls = [p.url for p in pages]
        self.assertIn("/child/", urls)


# ---------------------------------------------------------------------------
# render_pager_html
# ---------------------------------------------------------------------------

class RenderPagerHtmlTests(unittest.TestCase):
    def _make_nav_with_pages(self, urls: list[str]) -> NavNode:
        nodes = [_make_node(f"p{i}", f"Page {i}", url=u) for i, u in enumerate(urls)]
        return _make_node("root", "root", children=nodes)

    def test_no_pager_for_single_page(self) -> None:
        nav = self._make_nav_with_pages(["/"])
        page = _make_page("index.md", title="Home", url="/", is_index=True)
        self.assertEqual(render_pager_html(nav, page), "")

    def test_first_page_has_no_prev(self) -> None:
        nav = self._make_nav_with_pages(["/", "/b/", "/c/"])
        page = _make_page("index.md", title="Home", url="/", is_index=True)
        html = render_pager_html(nav, page)
        self.assertIn("pager", html)
        self.assertNotIn("Previous", html)

    def test_last_page_has_no_next(self) -> None:
        nav = self._make_nav_with_pages(["/a/", "/b/", "/c/"])
        page = _make_page("c.md", title="C", url="/c/")
        html = render_pager_html(nav, page)
        self.assertNotIn("Next", html)

    def test_middle_page_has_both(self) -> None:
        nav = self._make_nav_with_pages(["/a/", "/b/", "/c/"])
        page = _make_page("b.md", title="B", url="/b/")
        html = render_pager_html(nav, page)
        self.assertIn("Previous", html)
        self.assertIn("Next", html)

    def test_page_not_in_nav_returns_empty(self) -> None:
        nav = self._make_nav_with_pages(["/a/", "/b/"])
        page = _make_page("z.md", title="Z", url="/z/")
        self.assertEqual(render_pager_html(nav, page), "")


# ---------------------------------------------------------------------------
# render_top_nav_html
# ---------------------------------------------------------------------------

class RenderTopNavHtmlTests(unittest.TestCase):
    def test_empty_list_returns_empty(self) -> None:
        self.assertEqual(render_top_nav_html([]), "")

    def test_simple_link(self) -> None:
        items = [TopNavItem(title="Blog", url="https://blog.example.com")]
        html = render_top_nav_html(items)
        self.assertIn("Blog", html)
        self.assertIn("blog.example.com", html)

    def test_group_with_children_uses_details(self) -> None:
        child = TopNavItem(title="Guide", url="/guide/")
        parent = TopNavItem(title="Resources", items=[child])
        html = render_top_nav_html([parent])
        self.assertIn("<details", html)
        self.assertIn("Guide", html)

    def test_active_class_for_root_url(self) -> None:
        items = [TopNavItem(title="Home", url="/")]
        html = render_top_nav_html(items)
        self.assertIn("active", html)


# ---------------------------------------------------------------------------
# render_header_action_html
# ---------------------------------------------------------------------------

class RenderHeaderActionHtmlTests(unittest.TestCase):
    def test_contains_href(self) -> None:
        action = HeaderAction(title="GitHub", url="https://github.com/org/repo")
        html = render_header_action_html(action)
        self.assertIn("https://github.com/org/repo", html)

    def test_contains_title_label(self) -> None:
        action = HeaderAction(title="GitHub", url="https://github.com/")
        html = render_header_action_html(action)
        self.assertIn("GitHub", html)

    def test_with_logo_renders_img(self) -> None:
        action = HeaderAction(
            title="GitHub",
            url="https://github.com/",
            logo="https://github.com/favicon.ico",
            alt="GitHub logo",
        )
        html = render_header_action_html(action)
        self.assertIn("<img", html)
        self.assertIn("GitHub logo", html)

    def test_without_logo_uses_first_letter(self) -> None:
        action = HeaderAction(title="GitHub", url="https://github.com/")
        html = render_header_action_html(action)
        self.assertNotIn("<img", html)
        self.assertIn("G", html)


# ---------------------------------------------------------------------------
# output_path_for
# ---------------------------------------------------------------------------

class OutputPathForTests(unittest.TestCase):
    def test_index_md_outputs_to_index_html(self) -> None:
        page = _make_page("index.md", is_index=True)
        result = output_path_for(page, Path("/out"))
        self.assertEqual(result, Path("/out/index.html"))

    def test_subdir_index_md(self) -> None:
        page = _make_page("docs/index.md", is_index=True)
        result = output_path_for(page, Path("/out"))
        self.assertEqual(result, Path("/out/docs/index.html"))

    def test_regular_page_becomes_slug_dir(self) -> None:
        page = _make_page("docs/getting-started.md")
        result = output_path_for(page, Path("/out"))
        self.assertEqual(result, Path("/out/docs/getting-started/index.html"))


# ---------------------------------------------------------------------------
# build_site (integration)
# ---------------------------------------------------------------------------

class BuildSiteIntegrationTests(unittest.TestCase):
    def _make_project(self, tmp: str) -> Path:
        root = Path(tmp)
        (root / "content").mkdir()
        (root / "content" / "index.md").write_text("# Home\n\nWelcome.\n")
        (root / "content" / "docs").mkdir()
        (root / "content" / "docs" / "getting-started.md").write_text(
            "# Getting Started\n\n## Quick Start\n\nRun `pip install staticnest`.\n"
        )
        (root / "site.toml").write_text(
            'title = "Docs"\ndescription = "A test"\nbase_url = "/"\n'
            'content_dir = "content"\noutput_dir = "dist"\n'
            '[brand]\nname = "Docs"\n[links]\ngithub = "https://github.com/"\n'
            '[theme]\nname = "nest"\n'
        )
        return root / "site.toml"

    def test_returns_build_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = build_site(self._make_project(tmp))
            self.assertIsInstance(result, BuildResult)

    def test_output_dir_created(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._make_project(tmp)
            result = build_site(config_path)
            self.assertTrue(result.config.output_dir.exists())

    def test_index_html_created(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._make_project(tmp)
            result = build_site(config_path)
            self.assertTrue((result.config.output_dir / "index.html").exists())

    def test_404_html_created(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._make_project(tmp)
            result = build_site(config_path)
            self.assertTrue((result.config.output_dir / "404.html").exists())

    def test_nojekyll_created(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._make_project(tmp)
            result = build_site(config_path)
            self.assertTrue((result.config.output_dir / ".nojekyll").exists())

    def test_assets_css_created(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._make_project(tmp)
            result = build_site(config_path)
            self.assertTrue((result.config.output_dir / "assets" / "site.css").exists())

    def test_pages_list_populated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._make_project(tmp)
            result = build_site(config_path)
            self.assertGreater(len(result.pages), 0)

    def test_draft_pages_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "content").mkdir()
            (root / "content" / "index.md").write_text("# Home\n")
            (root / "content" / "secret.md").write_text(
                "---\ndraft: true\n---\n# Secret\n\nHidden page.\n"
            )
            (root / "site.toml").write_text(
                'title = "Docs"\nbase_url = "/"\ncontent_dir = "content"\noutput_dir = "dist"\n'
                '[brand]\nname = "Docs"\n[links]\ngithub = "#"\n[theme]\nname = "nest"\n'
            )
            result = build_site(root / "site.toml")
            titles = [p.title for p in result.pages]
            self.assertNotIn("Secret", titles)

    def test_live_reload_script_injected_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._make_project(tmp)
            result = build_site(config_path, live_reload=True)
            content = (result.config.output_dir / "index.html").read_text()
            self.assertIn("__staticnest_version", content)

    def test_version_token_used_when_provided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._make_project(tmp)
            result = build_site(config_path, version_token="test-v42")
            self.assertEqual(result.version, "test-v42")

    def test_output_dir_cleared_on_rebuild(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._make_project(tmp)
            result = build_site(config_path)
            stale = result.config.output_dir / "stale-file.html"
            stale.write_text("<html>stale</html>")
            build_site(config_path)
            self.assertFalse(stale.exists())

    def test_site_json_contains_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = self._make_project(tmp)
            result = build_site(config_path, version_token="abc123")
            import json
            site_json = json.loads((result.config.output_dir / "assets" / "site.json").read_text())
            self.assertEqual(site_json["version"], "abc123")


if __name__ == "__main__":
    unittest.main()
