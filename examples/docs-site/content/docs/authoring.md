---
title: Authoring
nav_title: Authoring
order: 3
summary: Write pages with Markdown, front matter, headings, and fenced code blocks.
---

# Authoring

Staticnest reads Markdown files from your configured `content/` directory and turns them into documentation pages.

## Content structure

A typical project looks like this:

```text
content/
├── index.md
└── docs/
    ├── getting-started.md
    └── configuration.md
```

- `index.md` becomes `/`
- `docs/getting-started.md` becomes `/docs/getting-started/`
- `docs/configuration.md` becomes `/docs/configuration/`

## Page titles

The first `# Heading` in a file becomes the page title unless front matter overrides it.

```md
# Architecture

Explain how the system fits together.
```

## Front matter

Staticnest supports both YAML-style and TOML-style front matter.

```md
---
title: Architecture
nav_title: System Design
summary: Explain how requests move through the system.
order: 4
draft: false
---
```

Supported fields:

- `title`
- `nav_title`
- `summary`
- `order`
- `template`
- `draft`

## Headings and table of contents

Second-level and third-level headings are collected into the right-side table of contents automatically.

```md
## API flow
### Authentication
### Response format
```

## Code blocks

Use fenced code blocks for commands and examples.

```bash
staticnest preview --host 127.0.0.1 --port 8000
```

```toml
[theme]
name = "nest"
```

The built-in theme adds a language label, copy button, and lightweight syntax highlighting.

## Links

Use normal Markdown links for internal or external references.

```md
[Configuration](configuration/)
[GitHub](https://github.com/)
```
