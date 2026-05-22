TEX = report.tex
PDF = report.pdf

.PHONY: all clean

all:
	pdflatex -interaction=nonstopmode -file-line-error $(TEX)
	bibtex report
	pdflatex -interaction=nonstopmode -file-line-error $(TEX)
	pdflatex -interaction=nonstopmode -file-line-error $(TEX)

clean:
	rm -f report.aux report.bbl report.blg report.fdb_latexmk report.fls report.log report.out report.run.xml report.synctex.gz report.toc $(PDF)
