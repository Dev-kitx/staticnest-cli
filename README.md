# Staticnest

`staticnest` is a custom Python static site generator built for documentation sites with a polished docs-first visual style: strong typography, left navigation, right table of contents, responsive docs shell, and client-side search.

## Features

- Pure Python generator with no runtime framework dependency
- TOML-based site configuration
- YAML navigation file for explicit sidebar order and sections
- Front matter for page metadata, summaries, template choice, draft state, and nav ordering
- Markdown support for headings, paragraphs, lists, blockquotes, fenced code blocks, and links
- Heading-based table of contents
- Responsive theme with mobile navigation and in-page search
- Local dev server with rebuild-on-change and live reload
- CLI preview and publish commands
- One built-in `nest` theme
- User template and asset overrides from `theme/`

## Repository layout

This repository now contains two separate things:

- the `staticnest` package itself
- an example site in [examples/docs-site](/examples/docs-site)

## Project layout

```text
.
└── src/staticnest/
```

Example site layout:

```text
examples/docs-site/
├── content/
├── navigation.yml
└── site.toml
```

## Run locally

Create a new docs project:

```bash
python3 build.py init my-docs
```

That scaffolds:

- `site.toml`
- `navigation.yml`
- `content/`

Then build it:

```bash
python3 build.py build --config my-docs/site.toml
```

Or preview it locally:

```bash
python3 build.py preview --config my-docs/site.toml --host 127.0.0.1 --port 8000
```

You can also initialize the current directory with:

```bash
python3 build.py init
```

For the bundled example site in this repository:

```bash
python3 build.py build --config examples/docs-site/site.toml
```

For local development:

```bash
python3 build.py preview --config examples/docs-site/site.toml --host 127.0.0.1 --port 8000
```

To publish the final output:

```bash
python3 build.py publish --config examples/docs-site/site.toml
```

To deploy to GitHub Pages:

```bash
python3 build.py gh-deploy --config examples/docs-site/site.toml
```

If you prefer the console script after installation:

```bash
pip install -e .
staticnest build --config examples/docs-site/site.toml
```

The example site's generated output is written to [examples/docs-site/dist](/examples/docs-site/dist).

## Author content

Create `.md` files inside `content/`. The first `# Heading` becomes the page title unless front matter overrides it.

## Navigation

Sidebar navigation comes from [navigation.yml](/examples/docs-site/navigation.yml), not from the file tree.

```yaml
- title: Overview
  page: index.md
- title: Guides
  items:
    - page: docs/getting-started.md
    - page: docs/configuration.md
```

Each navigation item can use:

- `title`
- `page`
- `url`
- `items`
- `order`

You can also configure the top header navigation in the same file:

```yaml
- navigation-bar:
    github:
      title: GitHub
      link: https://github.com/your-org/your-repo
      logo: https://github.githubassets.com/favicons/favicon.svg
    resources:
      title: Resources
      items:
        - name: Release notes
          link: https://example.com/releases
        - name: Roadmap
          link: https://example.com/roadmap
- issues:
    title: Issues
    link: https://github.com/your-org/your-repo/issues
```

The built-in theme treats `navigation-bar.github` as a dedicated top-right logo link, not a center navigation item. Other `navigation-bar` entries render just to the left of search. Add:

- `title` for the accessible label and text fallback
- `link` for the GitHub destination
- `logo` for the image shown in the header
- `alt` for custom image alt text if needed

If you add a top-level `issues.link`, the built-in theme uses it for the `Question? Give us feedback` link in the right-side table of contents.

## Front matter

Use either YAML-style `---` blocks or TOML-style `+++` blocks at the top of a page.

```md
---
title: Architecture
nav_title: System Design
order: 4
summary: Explain the pipeline and page rendering model.
template: page.html
draft: false
---
```

Supported fields:

- `title`
- `nav_title`
- `order`
- `summary`
- `template`
- `draft`

## Theme overrides

The soft launch ships with one built-in theme:

```toml
[theme]
name = "nest"
```

Optional advanced overrides can still be added with `[theme].dir`:

```toml
[theme]
name = "nest"
dir = "theme"
```

If `[theme].dir` is set, the generator will:

- copy `theme/assets/*` into `dist/assets/`
- auto-load `theme/assets/custom.css`
- auto-load `theme/assets/custom.js`
- use `theme/templates/page.html` as the outer shell override
- use `template: <name>.html` in front matter to select other templates

The CLI does not scaffold `theme/` by default because the built-in `nest` theme is bundled with the package. A local `theme/` directory is only needed for advanced overrides.

## Publish workflow

`publish` uses the configured `output_dir` by default. If you want a different destination for a specific run, pass `--destination`.

`gh-deploy` builds the site, ensures GitHub Pages artifacts like `.nojekyll` and `404.html` exist, and force-pushes the output to a `gh-pages` branch. It expects to run inside a Git repository with a configured remote.
