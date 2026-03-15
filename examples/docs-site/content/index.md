---
title: Staticnest Documentation
nav_title: Overview
order: 0
summary: Learn how to scaffold, write, preview, customize, and deploy documentation sites with Staticnest.
---

# Staticnest Documentation

Staticnest is a Python static site generator for documentation. It gives you a polished docs layout, explicit navigation, local preview with live reload, and a built-in theme without forcing users into a frontend framework.

## What Staticnest gives you

- `staticnest init` to scaffold a new documentation project
- `site.toml` for site settings and theme selection
- `navigation.yml` for explicit sidebar and header navigation
- Markdown pages under `content/`
- Local preview with rebuilds and live reload
- A built-in `nest` docs theme
- GitHub Pages support through `gh-deploy`

## Typical workflow

1. Create a project with `staticnest init`.
2. Write docs in `content/`.
3. Organize pages in `navigation.yml`.
4. Preview locally with `staticnest preview`.
5. Build or deploy when you are ready.

## Start here next

- [Getting Started](docs/getting-started/) walks through the first project setup.
- [Configuration](docs/configuration/) explains `site.toml` and `navigation.yml`.
- [Authoring](docs/authoring/) covers Markdown, front matter, and code blocks.
- [Deployment](docs/deployment/) covers `build`, `publish`, and `gh-deploy`.
