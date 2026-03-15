---
title: Theme Overrides
nav_title: Theme Overrides
order: 1
summary: Replace the page shell and layer custom CSS or JavaScript on top of the built-in nest theme.
---

# Theme Overrides

Theme overrides are optional. Staticnest looks for user-owned presentation files in the `theme/` directory configured by `site.toml`.

Enable them like this:

```toml
[theme]
name = "nest"
dir = "theme"
```

## Template files

- `theme/templates/page.html` replaces the outer page shell
- `theme/templates/<name>.html` can be selected per page using front matter

## Recommended project structure

```text
theme/
├── assets/
│   ├── custom.css
│   └── custom.js
└── templates/
    └── page.html
```

## What the page template receives

- site title and page title
- brand and GitHub link values
- top navigation and sidebar navigation markup
- breadcrumbs and pager markup
- rendered article HTML
- table of contents HTML
- search index data and base JavaScript
- optional custom CSS, custom JavaScript, and live reload script tags

If you want to replace the outer shell, start from the built-in structure and make one change at a time instead of rewriting the whole template at once.

## Asset overrides

Files in `theme/assets/` are copied into `dist/assets/`.

- `custom.css` is linked automatically
- `custom.js` is loaded automatically

## Start with CSS first

Most customization work should begin in `theme/assets/custom.css`.

```css
.brand {
  letter-spacing: -0.02em;
}

.article-shell h1 {
  color: #0f172a;
}

.nav-link.active {
  border-left: 2px solid #2563eb;
}
```

## Per-page template selection

If you create additional templates under `theme/templates/`, you can select them from front matter.

```yaml
---
title: Release Notes
template: landing.html
---
```

## Recommended approach

Start small:

1. add `theme/assets/custom.css`
2. add `theme/assets/custom.js` only if needed
3. override `theme/templates/page.html` only when the shell itself needs to change

If you are only changing colors, spacing, or component styling, prefer `custom.css` over replacing the whole page shell.
