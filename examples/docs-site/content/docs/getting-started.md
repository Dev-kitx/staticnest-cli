---
title: Getting Started
nav_title: Getting Started
order: 1
summary: Create a project, understand the generated files, and start the local preview loop.
---

# Getting Started

Create a new docs project with the CLI:

```bash
staticnest init my-docs
cd my-docs
```

This scaffolds:

- `site.toml`
- `navigation.yml`
- `content/`

## Install or run locally

If `staticnest` is installed as a package, use the console command directly:

```bash
staticnest preview
```

If you are developing from this repository, you can run the module form:

```bash
PYTHONPATH=src python3 -m staticnest preview --config examples/docs-site/site.toml
```

## Understand the scaffold

`site.toml` controls site settings and selects the built-in `nest` theme.

```toml
[theme]
name = "nest"
```

`navigation.yml` controls the left sidebar, the top navigation, and the top-right GitHub logo link.

`content/` contains your Markdown pages.

## Preview the site

Start the local preview server:

```bash
staticnest preview --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000`.

## Build the static output

When you want the generated files:

```bash
staticnest build
```

That writes the site into the configured `output_dir`.

## Add your first page

Create a new file such as `content/docs/architecture.md`.

```md
# Architecture

Document the system clearly.
```

Then add it to `navigation.yml`:

```yaml
- title: Guides
  items:
    - page: docs/getting-started.md
    - page: docs/architecture.md
```

## Next steps

- [Configuration](configuration/) for `site.toml` and `navigation.yml`
- [Authoring](authoring/) for Markdown and front matter
- [Deployment](deployment/) for publish and GitHub Pages
