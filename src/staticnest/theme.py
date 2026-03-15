from __future__ import annotations

import json
from html import escape


THEME_PRESETS = {
    "nest": {
        "accent": "#2563eb",
        "bg": "#ffffff",
        "surface": "#ffffff",
        "surface_alt": "#fafafa",
        "border": "#e5e7eb",
        "text": "#111827",
        "muted": "#6b7280",
        "muted_soft": "#9ca3af",
        "active_bg": "#eff6ff",
        "active_text": "#2563eb",
        "code_bg": "#f8fafc",
        "quote_bg": "#ecfdf5",
        "quote_border": "#22c55e",
    },
}


BASE_CSS = r"""
:root {
  --accent: {{ accent }};
  --bg: {{ bg }};
  --surface: {{ surface }};
  --surface-alt: {{ surface_alt }};
  --border: {{ border }};
  --text: {{ text }};
  --muted: {{ muted }};
  --muted-soft: {{ muted_soft }};
  --active-bg: {{ active_bg }};
  --active-text: {{ active_text }};
  --code-bg: {{ code_bg }};
  --quote-bg: {{ quote_bg }};
  --quote-border: {{ quote_border }};
  --topbar-height: 60px;
  --sidebar-width: 300px;
  --toc-width: 280px;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: "Inter", "Segoe UI", sans-serif;
  background: var(--bg);
  color: var(--text);
}

a {
  color: inherit;
  text-decoration: none;
}

code, pre {
  font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 1.15rem;
  height: var(--topbar-height);
  padding: 0 1.25rem;
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(8px);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  font-size: 0.86rem;
  font-weight: 700;
}

.brand-label {
  display: inline-block;
  font-size: 1rem;
  background: linear-gradient(120deg, #ff7e5f 0%, #feb47b 50%, #ff7e5f 100%);
  background-size: 200% auto;
  background-position: right center;
  color: transparent;
  -webkit-background-clip: text;
  background-clip: text;
  transition: background-position 0.5s ease-in-out;
}

.brand:hover .brand-label {
  background-position: left center;
}

.brand-mark {
  width: 1.1rem;
  height: 1.1rem;
  border-radius: 0.3rem;
  border: 2px solid var(--text);
  transform: rotate(45deg);
}

.top-nav {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 1.1rem;
  min-width: 0;
}

.top-nav-link {
  color: var(--muted);
  font-size: 0.88rem;
  font-weight: 500;
}

.top-nav-link.active {
  color: var(--text);
  font-weight: 600;
}

.top-nav-group {
  position: relative;
}

.top-nav-group summary {
  list-style: none;
  cursor: pointer;
}

.top-nav-group summary::-webkit-details-marker {
  display: none;
}

.top-nav-menu {
  position: absolute;
  top: calc(100% + 0.55rem);
  left: 0;
  min-width: 12rem;
  padding: 0.4rem;
  border: 1px solid var(--border);
  border-radius: 0.8rem;
  background: var(--surface);
  box-shadow: 0 10px 32px rgba(17, 24, 39, 0.08);
}

.top-nav-menu-link {
  display: block;
  padding: 0.55rem 0.7rem;
  border-radius: 0.55rem;
  color: var(--muted);
  font-size: 0.86rem;
}

.top-nav-menu-link:hover {
  background: var(--surface-alt);
  color: var(--text);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  justify-content: flex-end;
  min-width: 0;
}

.search-shell {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  min-width: 280px;
  padding: 0.42rem 0.68rem;
  border: 1px solid var(--border);
  border-radius: 0.65rem;
  background: var(--surface-alt);
}

.search-shell input {
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  font: inherit;
  color: var(--text);
  font-size: 0.9rem;
}

.search-kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.7rem;
  height: 1.35rem;
  padding: 0 0.3rem;
  border: 1px solid var(--border);
  border-radius: 0.45rem;
  color: var(--muted);
  font-size: 0.72rem;
}

.icon-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border: 1px solid var(--border);
  border-radius: 999px;
  font-weight: 700;
  font-size: 0.86rem;
  overflow: hidden;
}

.icon-link-image {
  width: 1.05rem;
  height: 1.05rem;
  object-fit: contain;
}

.layout {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr) var(--toc-width);
  min-height: calc(100vh - var(--topbar-height));
}

.sidebar {
  position: sticky;
  top: var(--topbar-height);
  height: calc(100vh - var(--topbar-height));
  overflow: auto;
  padding: 1rem 0.9rem 1.75rem 1.35rem;
  border-right: 1px solid var(--border);
  background: var(--surface);
}

.sidebar-title {
  margin: 0 0 0.8rem;
  color: var(--muted-soft);
  font-size: 0.76rem;
  font-weight: 600;
}

.nav-tree,
.toc-list {
  display: grid;
  gap: 0.15rem;
}

.nav-group-label {
  margin-top: 0.9rem;
  margin-bottom: 0.35rem;
  color: #374151;
  font-size: 0.9rem;
  font-weight: 600;
}

.nav-children {
  display: grid;
  gap: 0.15rem;
}

.nav-depth-1 { margin-left: 0.4rem; }
.nav-depth-2 { margin-left: 1rem; }

.nav-link {
  display: block;
  padding: 0.52rem 0.72rem;
  border-radius: 0.55rem;
  color: #4b5563;
  font-size: 0.9rem;
}

.nav-link:hover {
  background: #f9fafb;
}

.nav-link.active {
  background: var(--active-bg);
  color: var(--active-text);
  font-weight: 600;
}

.content-shell {
  padding: 1.4rem 2.35rem 3.5rem;
}

.breadcrumbs {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  margin-bottom: 0.85rem;
  color: var(--muted);
  font-size: 0.84rem;
}

.breadcrumb-sep {
  color: var(--muted-soft);
}

.article-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0.75rem;
}

.copy-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem 0.8rem;
  border: 1px solid var(--border);
  border-radius: 0.75rem;
  background: var(--surface);
  color: #374151;
  font: inherit;
  cursor: pointer;
  font-size: 0.88rem;
}

.article-shell h1 {
  margin: 0 0 1.25rem;
  font-size: clamp(1.75rem, 3.15vw, 2.55rem);
  line-height: 1.05;
  letter-spacing: -0.05em;
}

.article-shell h2 {
  margin-top: 2.5rem;
  margin-bottom: 0.85rem;
  padding-bottom: 0.6rem;
  border-bottom: 1px solid var(--border);
  font-size: 1.18rem;
  letter-spacing: -0.03em;
}

.article-shell h3 {
  margin-top: 1.7rem;
  margin-bottom: 0.65rem;
  font-size: 0.98rem;
}

.article-shell p,
.article-shell li,
.article-shell blockquote {
  color: #374151;
  font-size: 0.96rem;
  line-height: 1.8;
}

.article-shell ul,
.article-shell ol {
  padding-left: 1.5rem;
}

.article-shell pre {
  overflow: auto;
  margin: 0;
  padding: 1rem 1.1rem;
  border-top: 1px solid var(--border);
  background: var(--code-bg);
}

.article-shell code {
  padding: 0.16rem 0.35rem;
  border-radius: 0.35rem;
  background: #f3f4f6;
  font-size: 0.92em;
}

.article-shell pre code {
  padding: 0;
  background: transparent;
  color: #1f2937;
}

.code-block {
  margin: 1.25rem 0;
  border: 1px solid var(--border);
  border-radius: 0.85rem;
  overflow: hidden;
  background: var(--code-bg);
}

.code-block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.7rem 0.95rem;
  background: var(--surface);
}

.code-block-language {
  color: var(--muted);
  font-size: 0.82rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.code-copy-button {
  border: 1px solid var(--border);
  border-radius: 0.55rem;
  background: var(--surface);
  color: #374151;
  padding: 0.4rem 0.65rem;
  font: inherit;
  font-size: 0.85rem;
  cursor: pointer;
}

.tok-comment { color: #9ca3af; }
.tok-keyword { color: #7c3aed; font-weight: 600; }
.tok-string { color: #047857; }
.tok-number { color: #b45309; }
.tok-key { color: #1d4ed8; }
.tok-operator { color: #6d28d9; }
.tok-punct { color: #6b7280; }
.tok-variable { color: #db2777; }
.tok-flag { color: #0f766e; }
.tok-command { color: #b91c1c; font-weight: 600; }

.article-shell blockquote {
  margin: 1.5rem 0;
  padding: 1rem 1.2rem;
  border: 1px solid var(--quote-border);
  border-radius: 0.9rem;
  background: var(--quote-bg);
}

.pager {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  margin-top: 2.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
}

.pager-link {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 1rem 1.1rem;
  border: 1px solid var(--border);
  border-radius: 0.85rem;
  background: var(--surface);
}

.pager-link.next {
  text-align: right;
}

.pager-label {
  color: var(--muted);
  font-size: 0.82rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.toc {
  position: sticky;
  top: var(--topbar-height);
  height: calc(100vh - var(--topbar-height));
  overflow: auto;
  padding: 1.7rem 1.35rem 1.8rem 1.1rem;
  border-left: 1px solid var(--border);
  background: var(--surface);
}

.toc-title {
  margin: 0 0 1rem;
  font-size: 0.84rem;
  font-weight: 700;
}

.toc-link {
  display: block;
  padding: 0.26rem 0;
  color: var(--muted);
  font-size: 0.88rem;
}

.toc-link.active {
  color: var(--text);
  font-weight: 600;
}

.toc-level-3 {
  margin-left: 0.85rem;
}

.toc-meta {
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

.toc-meta a {
  display: block;
  margin-top: 0.6rem;
  color: var(--muted);
  font-size: 0.86rem;
}

.search-results {
  display: none;
  margin: 1rem 0 1.5rem;
  border: 1px solid var(--border);
  border-radius: 0.75rem;
  background: var(--surface);
}

.search-results.visible {
  display: block;
}

.search-result {
  display: block;
  padding: 0.85rem 0.95rem;
}

.search-result + .search-result {
  border-top: 1px solid var(--border);
}

.search-result-title {
  display: block;
  font-weight: 600;
}

.search-result-copy {
  display: block;
  margin-top: 0.22rem;
  color: var(--muted);
  font-size: 0.92rem;
  line-height: 1.55;
}

.menu-toggle {
  display: none;
}

.not-found-shell {
  display: grid;
  gap: 0.9rem;
  max-width: 34rem;
  padding: 4rem 0 2rem;
}

.not-found-eyebrow {
  margin: 0;
  color: var(--accent);
  font-size: 0.86rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.not-found-shell h1 {
  margin: 0;
  font-size: clamp(2rem, 3vw, 2.75rem);
}

.not-found-shell p:last-of-type {
  margin: 0;
  color: var(--muted);
  font-size: 1rem;
}

.not-found-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 0.4rem;
}

.not-found-link {
  display: inline-flex;
  align-items: center;
  padding: 0.7rem 0.95rem;
  border: 1px solid var(--border);
  border-radius: 0.75rem;
  color: var(--text);
  font-size: 0.92rem;
  font-weight: 600;
}

.not-found-link.primary {
  border-color: var(--accent);
  background: var(--accent);
  color: #ffffff;
}

@media (max-width: 1200px) {
  .layout {
    grid-template-columns: 280px minmax(0, 1fr);
  }

  .toc {
    display: none;
  }
}

@media (max-width: 920px) {
  .topbar {
    grid-template-columns: auto 1fr;
    gap: 0.8rem;
    padding: 0 1rem;
  }

  .search-shell {
    min-width: 0;
  }

  .layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .sidebar {
    position: fixed;
    left: 0;
    top: var(--topbar-height);
    z-index: 30;
    width: min(320px, 90vw);
    transform: translateX(-101%);
    transition: transform 180ms ease;
  }

  .sidebar.open {
    transform: translateX(0);
  }

  .content-shell {
    padding: 1.25rem 1rem 3rem;
  }

  .menu-toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.2rem;
    height: 2.2rem;
    border: 1px solid var(--border);
    border-radius: 0.65rem;
    background: var(--surface);
  }
}
"""


BASE_JS = r"""
const searchInput = document.querySelector('[data-search-input]');
const searchResults = document.querySelector('[data-search-results]');
const sidebar = document.querySelector('[data-sidebar]');
const menuToggle = document.querySelector('[data-menu-toggle]');
const copyButton = document.querySelector('[data-copy-link]');
const tocLinks = [...document.querySelectorAll('.toc-link')];
const sections = tocLinks
  .map((link) => document.querySelector(link.getAttribute('href')))
  .filter(Boolean);

if (menuToggle && sidebar) {
  menuToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });
}

if (copyButton) {
  copyButton.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      copyButton.querySelector('span').textContent = 'Copied';
      window.setTimeout(() => {
        copyButton.querySelector('span').textContent = 'Copy page';
      }, 1200);
    } catch (_error) {
      copyButton.querySelector('span').textContent = 'Copy failed';
    }
  });
}

document.querySelectorAll('[data-code-copy]').forEach((button) => {
  button.addEventListener('click', async () => {
    const block = button.closest('.code-block');
    const code = block ? block.querySelector('code') : null;
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code.textContent || '');
      button.textContent = 'Copied';
      window.setTimeout(() => {
        button.textContent = 'Copy';
      }, 1200);
    } catch (_error) {
      button.textContent = 'Failed';
    }
  });
});

if (searchInput && searchResults) {
  const pages = JSON.parse(document.querySelector('#search-index').textContent);
  const renderMatches = (matches) => {
    searchResults.innerHTML = matches.map((page) => `
      <a class="search-result" href="${page.url}">
        <span class="search-result-title">${page.title}</span>
        <span class="search-result-copy">${page.summary}</span>
      </a>
    `).join('');
    searchResults.classList.toggle('visible', matches.length > 0);
  };

  const focusSearch = () => {
    searchInput.focus();
    searchInput.select();
  };

  searchInput.addEventListener('input', () => {
    const query = searchInput.value.trim().toLowerCase();
    if (!query) {
      searchResults.classList.remove('visible');
      searchResults.innerHTML = '';
      return;
    }

    const matches = pages
      .map((page) => {
        const title = (page.title || '').toLowerCase();
        const summary = (page.summary || '').toLowerCase();
        const headings = (page.headings || []).join(' ').toLowerCase();
        const content = (page.content || '').toLowerCase();
        let score = 0;
        if (title.includes(query)) score += 10;
        if (summary.includes(query)) score += 6;
        if (headings.includes(query)) score += 4;
        if (content.includes(query)) score += 2;
        return { ...page, score };
      })
      .filter((page) => page.score > 0)
      .sort((a, b) => b.score - a.score || a.title.localeCompare(b.title))
      .slice(0, 8);

    renderMatches(matches);
  });

  document.addEventListener('keydown', (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      focusSearch();
    }
  });

  document.addEventListener('click', (event) => {
    if (!searchResults.contains(event.target) && event.target !== searchInput) {
      searchResults.classList.remove('visible');
    }
  });
}

if (sections.length) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const id = entry.target.getAttribute('id');
      tocLinks.forEach((link) => {
        link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
      });
    });
  }, { rootMargin: '-20% 0px -65% 0px', threshold: 1.0 });

  sections.forEach((section) => observer.observe(section));
}
"""


LIVE_RELOAD_JS = r"""
(function() {
  const endpoint = "{{ live_reload_path }}";
  let version = null;
  async function check() {
    try {
      const response = await fetch(endpoint, { cache: 'no-store' });
      const payload = await response.json();
      if (version && version !== payload.version) {
        window.location.reload();
        return;
      }
      version = payload.version;
    } catch (_error) {}
  }
  setInterval(check, 1000);
  check();
})();
"""


DEFAULT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{{ title }}</title>
    <meta name="description" content="{{ description_text }}" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="{{ current_url }}assets/site.css" />
    {{ custom_css_tag }}
  </head>
  <body>
    <header class="topbar">
      <div class="topbar-left">
        <button class="menu-toggle" type="button" data-menu-toggle>≡</button>
        <a class="brand" href="{{ current_url }}">
          <span class="brand-mark"></span>
          <span class="brand-label">{{ brand_name }}</span>
        </a>
      </div>
      <div class="topbar-actions">
        <nav class="top-nav">{{ top_nav_html }}</nav>
        <label class="search-shell">
          <input type="search" placeholder="Search documentation..." data-search-input />
          <span class="search-kbd">K</span>
        </label>
        {{ header_action_html }}
      </div>
    </header>
    <main class="layout">
      <aside class="sidebar" data-sidebar>
        <p class="sidebar-title">Documentation</p>
        <nav class="nav-tree">{{ nav_html }}</nav>
      </aside>
      <section class="content-shell">
        <div class="breadcrumbs">{{ breadcrumbs_html }}</div>
        <div class="article-toolbar">
          <button class="copy-link" type="button" data-copy-link><span>Copy page</span></button>
        </div>
        <div class="search-results" data-search-results></div>
        <article class="article-shell">
          {{ page_heading_html }}
          {{ article_html }}
          {{ pager_html }}
        </article>
      </section>
      <aside class="toc">
        <p class="toc-title">On This Page</p>
        <nav class="toc-list">{{ toc_html }}</nav>
        <div class="toc-meta">
          <a href="{{ feedback_url }}">Question? Give us feedback</a>
          <a href="{{ github_url }}">Edit this page on GitHub</a>
        </div>
      </aside>
    </main>
    <script id="search-index" type="application/json">{{ search_json }}</script>
    <script>{{ base_js }}</script>
    {{ custom_js_tag }}
    {{ live_reload_tag }}
  </body>
</html>
"""


NOT_FOUND_ARTICLE_HTML = """
<div class="not-found-shell">
  <p class="not-found-eyebrow">404</p>
  <h1>Page not found</h1>
  <p>The page you requested does not exist or may have moved.</p>
  <div class="not-found-actions">
    <a class="not-found-link primary" href="{{ current_url }}">Go home</a>
    <a class="not-found-link" href="{{ current_url }}docs/getting-started/">Open getting started</a>
  </div>
</div>
"""


def get_theme_preset(name: str | None, accent: str | None = None) -> dict[str, str] | dict[str, dict[str, str]]:
    if name is None:
        return THEME_PRESETS
    if name not in THEME_PRESETS:
        raise ValueError("Unknown theme. Soft launch supports only 'nest'.")
    preset = dict(THEME_PRESETS[name])
    if accent:
        preset["accent"] = accent
        preset["active_text"] = accent
    return preset


def render_css(theme_tokens: dict[str, str]) -> str:
    rendered = BASE_CSS
    for key, value in theme_tokens.items():
        rendered = rendered.replace(f"{{{{ {key} }}}}", value)
    return rendered


def replace_tokens(template: str, context: dict[str, str]) -> str:
    rendered = template
    for key in [
        "title",
        "description_text",
        "current_url",
        "brand_name",
        "github_url",
        "feedback_url",
        "header_action_html",
        "breadcrumbs_html",
        "page_title",
        "page_heading_html",
        "custom_css_tag",
        "custom_js_tag",
        "live_reload_tag",
        "top_nav_html",
        "nav_html",
        "pager_html",
        "toc_html",
        "search_json",
        "base_js",
        "article_html",
    ]:
        rendered = rendered.replace(f"{{{{ {key} }}}}", context[key])
    return rendered


def render_page(
    *,
    site_title: str,
    brand_name: str,
    description: str,
    tagline: str,
    github_url: str,
    feedback_url: str,
    header_action_html: str,
    page_title: str,
    page_summary: str,
    nav_html: str,
    top_nav_html: str,
    toc_html: str,
    article_html: str,
    current_url: str,
    search_index: list[dict[str, str]],
    template_override: str | None,
    has_custom_css: bool,
    has_custom_js: bool,
    live_reload: bool,
    live_reload_path: str,
    breadcrumbs_html: str,
    pager_html: str,
) -> str:
    template = template_override or DEFAULT_TEMPLATE
    title = escape(f"{page_title} | {site_title}")
    description_text = escape(page_summary or description)
    page_heading_html = f"<h1>{escape(page_title)}</h1>" if page_title else ""
    search_json = escape(json.dumps(search_index))
    custom_css_tag = f'<link rel="stylesheet" href="{current_url}assets/custom.css" />' if has_custom_css else ""
    custom_js_tag = f'<script src="{current_url}assets/custom.js"></script>' if has_custom_js else ""
    live_reload_tag = ""
    if live_reload:
        live_reload_tag = f"<script>{LIVE_RELOAD_JS.replace('{{ live_reload_path }}', live_reload_path)}</script>"
    toc_markup = toc_html or '<p class="toc-link">No headings on this page.</p>'
    return replace_tokens(
        template,
        {
            "title": title,
            "description_text": description_text,
            "current_url": escape(current_url, quote=True),
            "brand_name": escape(brand_name),
            "github_url": escape(github_url, quote=True),
            "feedback_url": escape(feedback_url, quote=True),
            "header_action_html": header_action_html,
            "top_nav_html": top_nav_html,
            "nav_html": nav_html,
            "breadcrumbs_html": breadcrumbs_html,
            "page_title": escape(page_title),
            "page_heading_html": page_heading_html,
            "article_html": article_html,
            "pager_html": pager_html,
            "toc_html": toc_markup,
            "search_json": search_json,
            "base_js": BASE_JS,
            "custom_css_tag": custom_css_tag,
            "custom_js_tag": custom_js_tag,
            "live_reload_tag": live_reload_tag,
        },
    )


def render_not_found_page(
    *,
    site_title: str,
    brand_name: str,
    description: str,
    github_url: str,
    feedback_url: str,
    header_action_html: str,
    top_nav_html: str,
    nav_html: str,
    current_url: str,
    search_index: list[dict[str, str]],
    has_custom_css: bool,
    has_custom_js: bool,
    live_reload: bool,
    live_reload_path: str,
) -> str:
    article_html = NOT_FOUND_ARTICLE_HTML.replace("{{ current_url }}", escape(current_url, quote=True))
    return render_page(
        site_title=site_title,
        brand_name=brand_name,
        description=description,
        tagline="",
        github_url=github_url,
        feedback_url=feedback_url,
        header_action_html=header_action_html,
        page_title="",
        page_summary="The requested page could not be found.",
        nav_html=nav_html,
        top_nav_html=top_nav_html,
        toc_html="",
        article_html=article_html,
        current_url=current_url,
        search_index=search_index,
        template_override=None,
        has_custom_css=has_custom_css,
        has_custom_js=has_custom_js,
        live_reload=live_reload,
        live_reload_path=live_reload_path,
        breadcrumbs_html='<a href="/">Documentation</a><span class="breadcrumb-sep">›</span><strong>404</strong>',
        pager_html="",
    )
