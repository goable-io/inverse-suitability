# Inverse Suitability preprint -- tectonic-driven build.
#
# Deliberately NOT latexmk/pdflatex: tectonic is a single self-contained binary
# that fetches TeX packages on demand and handles bibliography in one pass.
#
#   make        build main.pdf
#   make repro  regenerate data-derived artifacts (results.tex + figure) then build
#   make clean  remove build artifacts

MAIN     := main
TECTONIC := tectonic
REPRO    := reproducibility/run.sh

.PHONY: all repro clean

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex sections/*.tex appendix.tex refs.bib figures/difficulty-atlas.pdf
	$(TECTONIC) -X compile $(MAIN).tex

repro:
	bash $(REPRO)
	$(TECTONIC) -X compile $(MAIN).tex

clean:
	rm -f $(MAIN).pdf $(MAIN).aux $(MAIN).log $(MAIN).out \
	      $(MAIN).bbl $(MAIN).blg $(MAIN).bcf $(MAIN).run.xml \
	      $(MAIN).toc $(MAIN).fls $(MAIN).fdb_latexmk
