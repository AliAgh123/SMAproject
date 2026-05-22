TEX = report.tex
PDF = report.pdf
CLEAN_TEX = report_clean.tex
CLEAN_JOB = sma_report_clean_latex
CLEAN_PDF = $(CLEAN_JOB).pdf

.PHONY: all clean clean-report

all:
	pdflatex -interaction=nonstopmode -file-line-error $(TEX)
	bibtex report
	pdflatex -interaction=nonstopmode -file-line-error $(TEX)
	pdflatex -interaction=nonstopmode -file-line-error $(TEX)

clean-report:
	TEXMFVAR=/private/tmp/texmf-var lualatex -jobname=$(CLEAN_JOB) -interaction=nonstopmode -file-line-error $(CLEAN_TEX)
	TEXMFVAR=/private/tmp/texmf-var lualatex -jobname=$(CLEAN_JOB) -interaction=nonstopmode -file-line-error $(CLEAN_TEX)

clean:
	rm -f report.aux report.bbl report.blg report.fdb_latexmk report.fls report.log report.out report.run.xml report.synctex.gz report.toc $(PDF) report_clean.aux report_clean.log report_clean.out report_clean.toc $(CLEAN_JOB).aux $(CLEAN_JOB).log $(CLEAN_JOB).out $(CLEAN_JOB).toc $(CLEAN_PDF)
