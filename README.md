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
Prerequisite: install a LaTeX distribution with Beamer/PGF support. On Ubuntu/Debian, the CI uses `latexmk texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-pictures`.

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

Build the HTML version of a presentation when it has a `web/` folder:

```sh
make PRESENTATION=search-migration html
```

The HTML export is written to `dist/search-migration-html/index.html`. GitHub Actions uploads it as a separate artifact when available.


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
