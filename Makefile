PRESENTATION ?=
PRESENTATION_DIRS := $(sort $(dir $(wildcard presentations/*/main.tex)))
PRESENTATION_NAMES := $(patsubst presentations/%/,%,$(PRESENTATION_DIRS))

.PHONY: all one html clean list

all: $(addprefix dist/,$(addsuffix .pdf,$(PRESENTATION_NAMES)))

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
