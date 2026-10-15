# Presentations

LaTeX Beamer presentations with one independently buildable PDF per folder.

## Layout

```text
presentations/
  example/
    main.tex
common/
  preamble.tex
dist/
  example.pdf
```

Each presentation lives in `presentations/<name>/main.tex`. Shared packages and
theme settings belong in `common/preamble.tex`.

## Local Builds
On Ubuntu/Debian, install all PDF and HTML build dependencies:

```sh
make install-deps
```

This installs Python 3, Pandoc, Poppler, XeLaTeX, latexmk, and the required TeX
packages/fonts using apt. It may prompt for your sudo password. When already
running as root, use `make install-deps SUDO=`. GitHub Actions uses the same target.
Older distribution repositories may need a separate Pandoc 3+ installation.

Build every presentation:

```sh
make
```

Build one presentation:

```sh
make PRESENTATION=example one
```

Clean generated files:

```sh
make clean
```

PDFs are written to `dist/`.

## HTML Builds

For the search migration talk, the [presenter notes](presentations/search-migration/speaker-notes.md)
include talking points and facts still needing confirmation. The
[concise feedback reply](presentations/search-migration/feedback-response.md),
[example mapping](presentations/search-migration/example-index.json), and
[example queries](presentations/search-migration/example-queries.http) accompany the slides.

Build real HTML slides directly from the same LaTeX source (requires Pandoc 3+, Python 3, XeLaTeX, and Poppler’s `pdftocairo`):

```sh
make PRESENTATION=search-migration html
```

Or build HTML for every presentation:

```sh
make html-all
```

The result is a self-contained `dist/search-migration-html/index.html` that works
offline. Open it in a browser and use the arrow keys, navigation buttons, or agenda
links. Text, tables, code, and equations are HTML/MathML; TikZ and PDF diagrams are
converted to embedded SVG images. There is no PDF viewer or separately maintained
HTML deck. Slide order and content come from `main.tex`; the shared browser theme
and controls live in `common/slides.html`. Browser layout is not pixel-identical
to the PDF. The converter handles the Beamer structures used in this repository;
check the HTML when introducing new custom LaTeX commands or environments.

GitHub Actions generates and uploads HTML for every presentation. A nonstandard
Pandoc installation can be selected with `PANDOC` and `PANDOC_DATA_DIR` environment
variables. After building the search deck, run `python3 -m unittest discover -s tests -v`
to verify slide order, code examples, links, and embedded assets.


## GitHub Export

The workflow in `.github/workflows/build-presentations.yml` discovers every
`presentations/*/main.tex` file, builds each presentation separately, and uploads
each PDF as its own GitHub Actions artifact.

After pushing to GitHub, open the repository's **Actions** tab, select a build,
and download the artifact for the presentation you need.

## Adding A Presentation

```sh
mkdir -p presentations/my-talk
cp presentations/example/main.tex presentations/my-talk/main.tex
```

Then edit `presentations/my-talk/main.tex`. The next local or GitHub build will
produce `dist/my-talk.pdf`.
