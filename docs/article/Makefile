DOC  := article.tex
INTERMEDIARY_OUT := *.aux *.bbl *.blg *.idx *.ilg *.ind *.loa *.lof *.lot *.synctex.gz *.log *.out *.toc *.fls *.fdb_latexmk

RERUN := "(undefined references|Rerun to get (cross-references|the bars|point totals) right|Table widths have changed. Rerun LaTeX.|Linenumber reference failed)"
RERUNBIB := "No file.*\.bbl|Citation.*undefined"

all: doc

doc: $(DOC:.tex=.pdf)

%.pdf: %.tex
	-latexmk -pv -pdf $<

format:
	tex-fmt $(DOC) references.bib

check:
	@chktex -q $(DOC); rc=$$?; \
	if [ $$rc -eq 1 ] || [ $$rc -eq 3 ]; then \
		echo "chktex reported errors (exit $$rc)"; exit 1; \
	else \
		echo "chktex: no errors (exit $$rc)"; \
	fi

purge:
	for name in $(INTERMEDIARY_OUT); do \
		find . -name "$$name" -type f | xargs rm -fv ;\
	done

clean: purge
	-rm -f $(DOC:.tex=.pdf)


rebuild: purge build

build: doc
	zip -r -9 $(DATE)-$(DOC:.tex=).zip $(DOC:.tex=.pdf) $(DOC) references.bib images/

.PHONY: all purge clean
