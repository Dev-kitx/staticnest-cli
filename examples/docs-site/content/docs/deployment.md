---
title: Deployment
nav_title: Deployment
order: 4
summary: Build production output, publish to a destination, and deploy to GitHub Pages.
---

# Deployment

Staticnest supports both local build output and GitHub Pages deployment.

## Build output

Generate the static site into `output_dir`:

```bash
staticnest build
```

By default that writes to the directory configured in `site.toml`:

```toml
output_dir = "dist"
```

## Preview before publishing

Use the preview server during development:

```bash
staticnest preview --host 127.0.0.1 --port 8000
```

This serves the generated site and reloads when content or config changes.

## Publish

`publish` uses the configured `output_dir` unless you provide a one-off destination:

```bash
staticnest publish
```

```bash
staticnest publish --destination ./release
```

## GitHub Pages

Use `gh-deploy` to publish the built site to a `gh-pages` branch.

```bash
staticnest gh-deploy
```

Optional flags:

- `--remote origin`
- `--branch gh-pages`
- `--message "Deploy staticnest site"`

The generated output includes:

- `.nojekyll`
- `404.html`

These files help GitHub Pages serve the site correctly.

## What `gh-deploy` expects

- a Git repository
- a configured remote
- permission to push to the target branch
