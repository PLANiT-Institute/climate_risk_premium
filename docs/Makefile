# Makefile for LaTeX document compilation

# Document name (without .tex extension)
DOC = mathematical_framework

# LaTeX compiler
LATEX = pdflatex

# BibTeX compiler
BIBTEX = bibtex

# Main target
all: $(DOC).pdf

# Compile PDF (run twice for references)
$(DOC).pdf: $(DOC).tex
	$(LATEX) $(DOC).tex
	$(BIBTEX) $(DOC) || true
	$(LATEX) $(DOC).tex
	$(LATEX) $(DOC).tex

# Clean auxiliary files
clean:
	rm -f *.aux *.log *.out *.toc *.bbl *.blg *.synctex.gz

# Clean everything including PDF
distclean: clean
	rm -f $(DOC).pdf

# Quick compile (single pass)
quick:
	$(LATEX) $(DOC).tex

# View PDF (macOS)
view: $(DOC).pdf
	open $(DOC).pdf

.PHONY: all clean distclean quick view
