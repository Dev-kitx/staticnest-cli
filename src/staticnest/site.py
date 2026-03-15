from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import time
import tomllib
from typing import Any

from staticnest.markdown import Heading, render_markdown
from staticnest.simpleyaml import parse_navigation_yaml, parse_yaml_mapping
from staticnest.theme import get_theme_preset, render_css, render_not_found_page, render_page


@dataclass
class SiteConfig:
    title: str
    tagline: str
    description: str
    base_url: str
    content_dir: Path
    output_dir: Path
    nav_file: Path | None
    brand_name: str
    accent: str
    github_url: str
    theme_name: str
    theme_dir: Path | None = None


@dataclass
class Page:
    source_path: Path
    relative_path: Path
    url: str
    title: str
    nav_title: str
    summary: str
    html: str
    headings: list[Heading]
    search_text: str
    order: int
    template: str | None
    is_index: bool
    draft: bool


@dataclass
class NavNode:
    key: str
    title: str
    url: str | None = None
    order: int = 10_000
    external: bool = False
    children: list["NavNode"] = field(default_factory=list)


@dataclass
class BuildResult:
    config: SiteConfig
    pages: list[Page]
    version: str


@dataclass
class NavPageLink:
    title: str
    url: str


@dataclass
class TopNavItem:
    title: str
    url: str | None = None
    items: list["TopNavItem"] = field(default_factory=list)


@dataclass
class HeaderAction:
    title: str
    url: str
    logo: str | None = None
    alt: str | None = None


@dataclass
class DeployOptions:
    remote: str = "origin"
    branch: str = "gh-pages"
    message: str = "Deploy staticnest site"


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    if text.startswith("+++\n"):
        _, remainder = text.split("+++\n", 1)
        if "\n+++\n" in remainder:
            block, body = remainder.split("\n+++\n", 1)
            return tomllib.loads(block), body
    if text.startswith("---\n"):
        _, remainder = text.split("---\n", 1)
        if "\n---\n" in remainder:
            block, body = remainder.split("\n---\n", 1)
            return parse_yaml_mapping(block), body
    return {}, text


def load_config(config_path: Path) -> SiteConfig:
    data = tomllib.loads(config_path.read_text())
    brand = data.get("brand", {})
    links = data.get("links", {})
    theme = data.get("theme", {})
    root = config_path.parent
    theme_dir_value = theme.get("dir")
    nav_file_value = data.get("nav_file")
    return SiteConfig(
        title=data["title"],
        tagline=data.get("tagline", ""),
        description=data.get("description", ""),
        base_url=data.get("base_url", "/"),
        content_dir=root / data.get("content_dir", "content"),
        output_dir=root / data.get("output_dir", "dist"),
        nav_file=(root / nav_file_value) if nav_file_value else None,
        brand_name=brand.get("name", data["title"]),
        accent=brand.get("accent", "#0f766e"),
        github_url=links.get("github", "#"),
        theme_name=theme.get("name", "nest"),
        theme_dir=(root / theme_dir_value) if theme_dir_value else None,
    )


def iter_markdown_files(content_dir: Path) -> list[Path]:
    return sorted(content_dir.rglob("*.md"))


def build_url(relative_path: Path, base_url: str = "/") -> str:
    prefix = "/" + base_url.strip("/")
    prefix = prefix.rstrip("/")
    if relative_path.name == "index.md":
        if relative_path.parent == Path("."):
            return prefix + "/"
        return f"{prefix}/{relative_path.parent.as_posix()}/"
    stem = relative_path.with_suffix("")
    return f"{prefix}/{stem.as_posix()}/"


def default_title_from_path(relative_path: Path) -> str:
    part = relative_path.stem if relative_path.name != "index.md" else relative_path.parent.name or "Home"
    return part.replace("-", " ").replace("_", " ").title()


def build_search_text(markdown_body: str, headings: list[Heading]) -> str:
    text = markdown_body
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"[>*_#-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    heading_text = " ".join(heading.text for heading in headings)
    return f"{heading_text} {text}".strip()


def load_pages(config: SiteConfig) -> list[Page]:
    pages: list[Page] = []
    for source_path in iter_markdown_files(config.content_dir):
        relative_path = source_path.relative_to(config.content_dir)
        metadata, body = split_front_matter(source_path.read_text())
        rendered = render_markdown(body)
        title = str(metadata.get("title") or rendered.title or default_title_from_path(relative_path))
        draft = bool(metadata.get("draft", False))
        pages.append(
            Page(
                source_path=source_path,
                relative_path=relative_path,
                url=build_url(relative_path, config.base_url),
                title=title,
                nav_title=str(metadata.get("nav_title") or title),
                summary=str(metadata.get("summary") or rendered.summary or config.description),
                html=rendered.html,
                headings=rendered.headings,
                search_text=build_search_text(body, rendered.headings),
                order=int(metadata.get("order", 10_000)),
                template=metadata.get("template"),
                is_index=relative_path.name == "index.md",
                draft=draft,
            )
        )
    return [page for page in pages if not page.draft]


def build_inferred_nav_tree(pages: list[Page]) -> NavNode:
    root = NavNode(key="root", title="root")
    for page in pages:
        parts = list(page.relative_path.parent.parts)
        current = root
        for index, part in enumerate(parts):
            key = f"dir:{'/'.join(parts[: index + 1])}"
            existing = next((child for child in current.children if child.key == key), None)
            if existing is None:
                existing = NavNode(key=key, title=part.replace("-", " ").replace("_", " ").title())
                current.children.append(existing)
            current = existing

        if page.is_index:
            if parts:
                current.title = page.nav_title
                current.url = page.url
                current.order = page.order
            else:
                root.children.append(NavNode(key="page:/", title=page.nav_title, url=page.url, order=page.order))
            continue

        current.children.append(
            NavNode(
                key=f"page:{page.relative_path.as_posix()}",
                title=page.nav_title,
                url=page.url,
                order=page.order,
            )
        )

    sort_nav_tree(root)
    return root


def load_navigation_entries(config: SiteConfig) -> list[dict[str, Any]]:
    if config.nav_file is None or not config.nav_file.exists():
        return []
    return parse_navigation_yaml(config.nav_file.read_text())


def split_navigation_entries(entries: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    docs_entries: list[dict[str, Any]] = []
    top_nav_config: dict[str, Any] = {}
    issues_config: dict[str, Any] = {}
    for entry in entries:
        if "navigation-bar" in entry:
            top_nav_config = entry["navigation-bar"] or {}
            continue
        if "issues" in entry:
            issues_config = entry["issues"] or {}
            continue
        docs_entries.append(entry)
    return docs_entries, top_nav_config, issues_config


def nav_page_key(page_ref: str) -> str:
    normalized = page_ref.strip("/")
    if normalized.endswith(".md"):
        return normalized
    return f"{normalized}/index.md" if normalized else "index.md"


def build_nav_from_config(config: SiteConfig, pages: list[Page]) -> NavNode:
    if config.nav_file is None or not config.nav_file.exists():
        return build_inferred_nav_tree(pages)

    pages_by_ref = {page.relative_path.as_posix(): page for page in pages}
    entries, _, _ = split_navigation_entries(load_navigation_entries(config))

    def to_node(entry: dict[str, Any], order: int) -> NavNode:
        page_ref = entry.get("page")
        external_url = entry.get("url")
        children_data = entry.get("items", [])
        page = None
        if page_ref:
            lookup = nav_page_key(str(page_ref))
            page = pages_by_ref.get(lookup)
            if page is None:
                raise ValueError(f"Navigation page '{page_ref}' was not found in content/")
        title = str(entry.get("title") or (page.nav_title if page else "Section"))
        url = str(external_url) if external_url else (page.url if page else None)
        node = NavNode(
            key=f"nav:{title}:{order}",
            title=title,
            url=url,
            order=int(entry.get("order", order)),
            external=bool(external_url),
        )
        node.children = [to_node(child, index) for index, child in enumerate(children_data)]
        return node

    root = NavNode(key="root", title="root")
    root.children = [to_node(entry, index) for index, entry in enumerate(entries)]
    sort_nav_tree(root)
    return root


def build_top_nav_items(config: SiteConfig) -> list[TopNavItem]:
    entries = load_navigation_entries(config)
    _, top_nav_config, _ = split_navigation_entries(entries)
    if not top_nav_config:
        return []

    items: list[TopNavItem] = []
    for key, value in top_nav_config.items():
        if key in {"github", "issues"}:
            continue
        if not isinstance(value, dict):
            continue
        title = str(value.get("title") or key.replace("-", " ").replace("_", " ").title())
        link = value.get("link")
        nested = value.get("items", [])
        child_items = []
        if isinstance(nested, list):
            for child in nested:
                if not isinstance(child, dict):
                    continue
                child_items.append(
                    TopNavItem(
                        title=str(child.get("name") or child.get("title") or "Link"),
                        url=str(child.get("link") or "#"),
                    )
                )
        items.append(TopNavItem(title=title, url=str(link) if link else None, items=child_items))
    return items


def build_header_action(config: SiteConfig) -> HeaderAction:
    entries = load_navigation_entries(config)
    _, top_nav_config, _ = split_navigation_entries(entries)
    github_entry = top_nav_config.get("github", {}) if isinstance(top_nav_config, dict) else {}
    if not isinstance(github_entry, dict):
        github_entry = {}

    title = str(github_entry.get("title") or "GitHub")
    url = str(github_entry.get("link") or config.github_url or "#")
    logo = github_entry.get("logo")
    alt = github_entry.get("alt")
    return HeaderAction(
        title=title,
        url=url,
        logo=str(logo) if logo else None,
        alt=str(alt) if alt else None,
    )


def render_header_action_html(action: HeaderAction) -> str:
    label = escape(action.title[:1].upper() if action.title else "G")
    logo_html = label
    if action.logo:
        alt = escape(action.alt or action.title)
        src = escape(action.logo, quote=True)
        logo_html = f'<img class="icon-link-image" src="{src}" alt="{alt}" />'
    href = escape(action.url, quote=True)
    title = escape(action.title, quote=True)
    return f'<a class="icon-link" href="{href}" aria-label="{title}" title="{title}">{logo_html}</a>'


def build_feedback_url(config: SiteConfig) -> str:
    entries = load_navigation_entries(config)
    _, _, issues_config = split_navigation_entries(entries)
    issues_entry = issues_config if isinstance(issues_config, dict) else {}
    if not isinstance(issues_entry, dict):
        issues_entry = {}
    return str(issues_entry.get("link") or "#")


def sort_nav_tree(node: NavNode) -> None:
    for child in node.children:
        sort_nav_tree(child)
    node.children.sort(key=lambda item: (item.order, item.title.lower()))


def render_nav_html(node: NavNode, current_url: str, depth: int = 0) -> str:
    chunks: list[str] = []
    for child in node.children:
        active = " active" if child.url == current_url else ""
        target = ' target="_blank" rel="noreferrer"' if child.external else ""
        if child.url:
            chunks.append(
                f'<a class="nav-link{active} nav-depth-{depth}" href="{child.url}"{target}>{child.title}</a>'
            )
        else:
            chunks.append(f'<div class="nav-group-label nav-depth-{depth}">{child.title}</div>')
        if child.children:
            chunks.append(f'<div class="nav-children nav-depth-{depth + 1}">{render_nav_html(child, current_url, depth + 1)}</div>')
    return "".join(chunks)


def render_toc_html(headings: list[Heading]) -> str:
    items = [
        f'<a class="toc-link toc-level-{heading.level}" href="#{heading.slug}">{heading.text}</a>'
        for heading in headings
        if heading.level in (2, 3)
    ]
    return "".join(items)


def find_nav_trail(node: NavNode, target_url: str, trail: list[NavNode] | None = None) -> list[NavNode] | None:
    active_trail = (trail or []) + [node]
    if node.url == target_url and not node.external:
        return active_trail
    for child in node.children:
        result = find_nav_trail(child, target_url, active_trail)
        if result:
            return result
    return None


def render_breadcrumbs_html(nav_tree: NavNode, page: Page) -> str:
    trail = find_nav_trail(nav_tree, page.url) or []
    crumbs = ['<a href="/">Documentation</a>']
    visible_nodes = [node for node in trail[1:] if node.title != page.title]
    for node in visible_nodes:
        crumbs.append('<span class="breadcrumb-sep">›</span>')
        crumbs.append(f"<span>{node.title}</span>")
    crumbs.append('<span class="breadcrumb-sep">›</span>')
    crumbs.append(f"<strong>{page.title}</strong>")
    return "".join(crumbs)


def flatten_nav_pages(node: NavNode) -> list[NavPageLink]:
    items: list[NavPageLink] = []
    if node.url and not node.external:
        items.append(NavPageLink(title=node.title, url=node.url))
    for child in node.children:
        items.extend(flatten_nav_pages(child))
    return items


def render_pager_html(nav_tree: NavNode, page: Page) -> str:
    ordered_pages: list[NavPageLink] = []
    seen_urls: set[str] = set()
    for item in flatten_nav_pages(nav_tree):
        if item.url in seen_urls:
            continue
        seen_urls.add(item.url)
        ordered_pages.append(item)

    current_index = next((index for index, item in enumerate(ordered_pages) if item.url == page.url), None)
    if current_index is None:
        return ""

    previous_item = ordered_pages[current_index - 1] if current_index > 0 else None
    next_item = ordered_pages[current_index + 1] if current_index < len(ordered_pages) - 1 else None
    if previous_item is None and next_item is None:
        return ""

    previous_html = (
        f'<a class="pager-link prev" href="{previous_item.url}"><span class="pager-label">Previous</span><strong>{previous_item.title}</strong></a>'
        if previous_item
        else '<span></span>'
    )
    next_html = (
        f'<a class="pager-link next" href="{next_item.url}"><span class="pager-label">Next</span><strong>{next_item.title}</strong></a>'
        if next_item
        else '<span></span>'
    )
    return f'<nav class="pager">{previous_html}{next_html}</nav>'


def render_top_nav_html(items: list[TopNavItem]) -> str:
    chunks: list[str] = []
    for item in items:
        if item.items:
            links = "".join(
                f'<a class="top-nav-menu-link" href="{child.url or "#"}">{child.title}</a>'
                for child in item.items
            )
            chunks.append(
                f'<details class="top-nav-group">'
                f'<summary class="top-nav-link">{item.title}</summary>'
                f'<div class="top-nav-menu">{links}</div>'
                f"</details>"
            )
        else:
            href = item.url or "#"
            active = " active" if href == "/" else ""
            chunks.append(f'<a class="top-nav-link{active}" href="{href}">{item.title}</a>')
    return "".join(chunks)


def output_path_for(page: Page, output_dir: Path) -> Path:
    if page.relative_path.name == "index.md":
        return output_dir / page.relative_path.parent / "index.html"
    return output_dir / page.relative_path.with_suffix("") / "index.html"


def load_user_template(config: SiteConfig, template_name: str | None) -> str | None:
    if config.theme_dir is None:
        return None
    template_dir = config.theme_dir / "templates"
    candidate_names = [template_name] if template_name else []
    candidate_names.append("page.html")
    for name in candidate_names:
        if not name:
            continue
        path = template_dir / name
        if path.exists():
            return path.read_text()
    return None


def write_theme_assets(config: SiteConfig) -> tuple[bool, bool]:
    (config.output_dir / "assets").mkdir(parents=True, exist_ok=True)
    preset = get_theme_preset(config.theme_name, accent=config.accent)
    (config.output_dir / "assets" / "site.css").write_text(render_css(preset))
    has_custom_css = False
    has_custom_js = False
    if config.theme_dir is None:
        return has_custom_css, has_custom_js

    asset_dir = config.theme_dir / "assets"
    if not asset_dir.exists():
        return has_custom_css, has_custom_js

    for path in asset_dir.rglob("*"):
        if path.is_dir():
            continue
        destination = config.output_dir / "assets" / path.relative_to(asset_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        if destination.name == "custom.css":
            has_custom_css = True
        if destination.name == "custom.js":
            has_custom_js = True
    return has_custom_css, has_custom_js


def build_site(config_path: Path, *, live_reload: bool = False, version_token: str | None = None) -> BuildResult:
    config = load_config(config_path)
    pages = load_pages(config)
    nav_tree = build_nav_from_config(config, pages)
    top_nav_items = build_top_nav_items(config)
    header_action = build_header_action(config)
    feedback_url = build_feedback_url(config)
    base_url = config.base_url.rstrip("/") + "/"

    if config.output_dir.exists():
        shutil.rmtree(config.output_dir)

    has_custom_css, has_custom_js = write_theme_assets(config)
    version = version_token or str(int(time.time() * 1000))
    (config.output_dir / "assets" / "site.json").write_text(json.dumps({"version": version}, indent=2))

    search_index = [
        {
            "title": page.title,
            "url": page.url,
            "summary": page.summary,
            "headings": [heading.text for heading in page.headings],
            "content": page.search_text,
        }
        for page in pages
    ]

    for page in pages:
        output_path = output_path_for(page, config.output_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        html = render_page(
            site_title=config.title,
            brand_name=config.brand_name,
            description=config.description,
            tagline=config.tagline,
            github_url=header_action.url,
            feedback_url=feedback_url,
            header_action_html=render_header_action_html(header_action),
            page_title=page.title,
            page_summary=page.summary,
            nav_html=render_nav_html(nav_tree, page.url),
            top_nav_html=render_top_nav_html(top_nav_items),
            toc_html=render_toc_html(page.headings),
            article_html=page.html,
            current_url=base_url,
            search_index=search_index,
            template_override=load_user_template(config, page.template),
            has_custom_css=has_custom_css,
            has_custom_js=has_custom_js,
            live_reload=live_reload,
            live_reload_path="/__staticnest_version",
            breadcrumbs_html=render_breadcrumbs_html(nav_tree, page),
            pager_html=render_pager_html(nav_tree, page),
        )
        output_path.write_text(html)

    write_pages_artifacts(
        config.output_dir,
        render_not_found_page(
            site_title=config.title,
            brand_name=config.brand_name,
            description=config.description,
            github_url=header_action.url,
            feedback_url=feedback_url,
            header_action_html=render_header_action_html(header_action),
            top_nav_html=render_top_nav_html(top_nav_items),
            nav_html=render_nav_html(nav_tree, ""),
            current_url=base_url,
            search_index=search_index,
            has_custom_css=has_custom_css,
            has_custom_js=has_custom_js,
            live_reload=live_reload,
            live_reload_path="/__staticnest_version",
        ),
    )
    return BuildResult(config=config, pages=pages, version=version)


def write_pages_artifacts(output_dir: Path, not_found_html: str) -> None:
    (output_dir / "404.html").write_text(not_found_html)
    (output_dir / ".nojekyll").write_text("")


def publish_site(config_path: Path, destination: Path | None = None) -> Path:
    result = build_site(config_path, live_reload=False)
    target = destination or result.config.output_dir
    if target.resolve() == result.config.output_dir.resolve():
        return result.config.output_dir
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(result.config.output_dir, target)
    return target


def run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def gh_deploy_site(config_path: Path, options: DeployOptions) -> str:
    result = build_site(config_path, live_reload=False)
    repo_root = Path(run_git(["rev-parse", "--show-toplevel"], config_path.parent))
    remote_url = run_git(["remote", "get-url", options.remote], repo_root)

    with tempfile.TemporaryDirectory(prefix="staticnest-gh-pages-") as tmp_dir:
        publish_root = Path(tmp_dir)
        shutil.copytree(result.config.output_dir, publish_root / "site")
        site_root = publish_root / "site"
        run_git(["init", "-b", options.branch], site_root)
        run_git(["remote", "add", options.remote, remote_url], site_root)
        run_git(["add", "."], site_root)
        subprocess.run(
            ["git", "commit", "-m", options.message],
            cwd=site_root,
            check=True,
            capture_output=True,
            text=True,
        )
        run_git(["push", "--force", options.remote, f"{options.branch}:{options.branch}"], site_root)

    return f"{options.remote}/{options.branch}"


def snapshot_inputs(config_path: Path) -> dict[str, float]:
    config = load_config(config_path)
    watched_paths = [config_path, *iter_markdown_files(config.content_dir)]
    if config.nav_file and config.nav_file.exists():
        watched_paths.append(config.nav_file)
    if config.theme_dir and config.theme_dir.exists():
        watched_paths.extend(path for path in config.theme_dir.rglob("*") if path.is_file())
    return {str(path): path.stat().st_mtime for path in watched_paths if path.exists()}


class BuildWatcher:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.version = str(int(time.time() * 1000))
        self._snapshot = snapshot_inputs(config_path)
        self._lock = threading.Lock()

    def current_version(self) -> str:
        with self._lock:
            return self.version

    def rebuild(self) -> BuildResult:
        result = build_site(self.config_path, live_reload=True, version_token=str(int(time.time() * 1000)))
        with self._lock:
            self.version = result.version
            self._snapshot = snapshot_inputs(self.config_path)
        return result

    def poll(self) -> bool:
        latest = snapshot_inputs(self.config_path)
        changed = latest != self._snapshot
        if changed:
            self.rebuild()
        return changed
