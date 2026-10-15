# Rapport final AuditHub

Le rapport est un projet LaTeX multi-fichier fond\'e sur l'impl\'ementation r\'eelle d'AuditHub.

## Compilation

Depuis `docs/rapport_final/` :

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Sans `latexmk`, ex\'ecuter `pdflatex`, `bibtex`, puis deux fois `pdflatex`.

## Captures

Les images de `figures/screenshots/` proviennent d'un parcours Playwright sur une base temporaire. Pour les reproduire depuis la racine du projet :

```powershell
node frontend/node_modules/@playwright/test/cli.js test --config docs/rapport_final/tools/playwright.config.mjs
```

Le sc\'enario ne touche pas \`a la base `audit.sqlite3`.
