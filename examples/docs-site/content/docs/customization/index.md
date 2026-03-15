---
title: Customization
nav_title: Customization
order: 5
summary: Extend the built-in theme with optional local templates, CSS, and JavaScript.
---

# Customization

The default `nest` theme is built into Staticnest. Most users can stay on the bundled theme and only adjust content, navigation, and brand settings.

If you need deeper control, Staticnest supports local theme overrides.

## Included hooks

- Page-level front matter for order, summaries, and template selection
- Theme template overrides from `theme/templates/`
- Additional CSS and JavaScript from `theme/assets/`

## When to use overrides

Use local theme overrides when you want to:

- change the outer page shell
- add custom styling on top of the built-in theme
- inject custom page behavior with JavaScript

If you only need site name, accent, navigation, and content changes, stay in `site.toml`, `navigation.yml`, and `content/`.
