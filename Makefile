PRESENTATION ?=
SUDO ?= sudo
BUILD_PACKAGES := python3 pandoc poppler-utils latexmk texlive-latex-recommended \
	texlive-latex-extra texlive-fonts-recommended texlive-pictures texlive-xetex
PRESENTATION_DIRS := $(sort $(dir $(wildcard presentations/*/main.tex)))
PRESENTATION_NAMES := $(patsubst presentations/%/,%,$(PRESENTATION_DIRS))

.PHONY: all one html html-all install-deps clean list

all: $(addprefix dist/,$(addsuffix .pdf,$(PRESENTATION_NAMES)))

# Ubuntu/Debian. Set SUDO= when already running as root.
install-deps:
	@command -v apt-get >/dev/null 2>&1 || { echo "install-deps requires Ubuntu/Debian (apt-get)."; exit 1; }
	$(SUDO) apt-get update
	$(SUDO) apt-get install -y $(BUILD_PACKAGES)

list:
	@printf '%s\n' $(PRESENTATION_NAMES)

one:
	@if [ -z "$(PRESENTATION)" ]; then \
		echo "Set PRESENTATION=<name>, for example: make PRESENTATION=example one"; \
		exit 1; \
	fi
	$(MAKE) dist/$(PRESENTATION).pdf

html:
	@if [ -z "$(PRESENTATION)" ]; then \
		echo "Set PRESENTATION=<name>, for example: make PRESENTATION=search-migration html"; \
		exit 1; \
	fi
	python3 scripts/build-html.py "$(PRESENTATION)"

html-all:
	@set -e; for presentation in $(PRESENTATION_NAMES); do \
		$(MAKE) PRESENTATION="$$presentation" html; \
	done

dist/%.pdf: presentations/%/main.tex common/preamble.tex
	@mkdir -p build/$* dist
	@if command -v latexmk >/dev/null 2>&1; then \
		cd presentations/$* && latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=../../build/$* main.tex; \
	else \
		cd presentations/$* && xelatex -interaction=nonstopmode -halt-on-error -output-directory=../../build/$* main.tex && \
			xelatex -interaction=nonstopmode -halt-on-error -output-directory=../../build/$* main.tex; \
	fi
	@cp build/$*/main.pdf $@

clean:
	@rm -rf build dist
