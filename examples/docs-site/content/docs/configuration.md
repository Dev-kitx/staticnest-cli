---
title: Configuration
nav_title: Configuration
order: 2
summary: Configure the site title, brand, content paths, theme, and navigation behavior.
---

# Configuration

Site settings live in `site.toml`.

## Example configuration

```toml
title = "Staticnest"
tagline = "Python static docs with a polished nest theme"
description = "A custom Python static website generator focused on stylish documentation sites."
base_url = "/"
content_dir = "content"
output_dir = "dist"
nav_file = "navigation.yml"

[brand]
name = "Staticnest"
accent = "#0f766e"

[links]
github = "https://github.com/"

[theme]
name = "nest"
```

## Core fields

- `title`: Browser title and top navigation label
- `tagline`: Introductory text shown in the shell
- `description`: Metadata description
- `base_url`: Root path for the site
- `content_dir`: Source markdown directory
- `output_dir`: Generated site directory
- `nav_file`: YAML file that controls sidebar structure and order

## Navigation file

The `nav_file` points to a YAML file that defines both:

- the left documentation sidebar
- the top header navigation bar

Example:

```yaml
- title: Overview
  page: index.md
- title: Guides
  items:
    - page: docs/getting-started.md
    - page: docs/configuration.md
- navigation-bar:
    github:
      title: GitHub
      link: https://github.com/your-org/your-repo
      logo: https://github.githubassets.com/favicons/favicon.svg
    resources:
      title: Resources
      items:
        - name: Getting Started
          link: /docs/getting-started/
        - name: Configuration
          link: /docs/configuration/
- issues:
    title: Issues
    link: https://github.com/your-org/your-repo/issues
```

In that example, `github` is a special top-right header logo link. `resources` is a regular header navigation item, so with `items` it renders as a dropdown just to the left of search.

The built-in theme treats `navigation-bar.github` as the dedicated top-right logo action, not a regular header nav item. Other `navigation-bar` entries render just to the left of search. Set:

- `title` for the link label and text fallback
- `link` for the repository or organization URL
- `logo` for the image shown in the top-right corner
- `alt` if you want custom image alt text

If you set a top-level `issues.link`, the built-in theme uses it for the `Question? Give us feedback` link in the table of contents panel.

## Brand section

The `[brand]` table controls presentation.

```toml
[brand]
name = "Staticnest"
accent = "#0f766e"
```

## Links section

Use `[links]` for external destinations like GitHub. `links.github` remains the fallback if `navigation-bar.github.link` is not set.

## Theme section

Use `[theme]` to select the built-in `nest` theme.

```toml
[theme]
name = "nest"
```

The theme is bundled with the package, so users do not need a local `theme/` directory just to use it.

For advanced overrides:

```toml
[theme]
name = "nest"
dir = "theme"
```

## Output and publish behavior

The `publish` command uses `output_dir` by default. Pass `--destination` if you want a one-off publish location.

For GitHub Pages, use `gh-deploy`. The build output now includes:

- `.nojekyll`
- `404.html`
