PRESENTATION ?=
PRESENTATION_DIRS := $(sort $(dir $(wildcard presentations/*/main.tex)))
PRESENTATION_NAMES := $(patsubst presentations/%/,%,$(PRESENTATION_DIRS))

.PHONY: all one clean list

all: $(addprefix dist/,$(addsuffix .pdf,$(PRESENTATION_NAMES)))

list:
	@printf '%s\n' $(PRESENTATION_NAMES)

one:
	@if [ -z "$(PRESENTATION)" ]; then \
		echo "Set PRESENTATION=<name>, for example: make PRESENTATION=example one"; \
		exit 1; \
	fi
	$(MAKE) dist/$(PRESENTATION).pdf

dist/%.pdf: presentations/%/main.tex common/preamble.tex
	@mkdir -p build/$* dist
	@if command -v latexmk >/dev/null 2>&1; then \
		cd presentations/$* && latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=../../build/$* main.tex; \
	else \
		cd presentations/$* && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=../../build/$* main.tex && \
			pdflatex -interaction=nonstopmode -halt-on-error -output-directory=../../build/$* main.tex; \
	fi
	@cp build/$*/main.pdf $@

clean:
	@rm -rf build dist
