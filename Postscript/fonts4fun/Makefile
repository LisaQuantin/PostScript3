all:	x.ps cmbxti10rand.1

%.dvi:	%.tex
	tex $<

%.ps:	%.dvi myfonts.map
	dvips $<

%.png:	%.ps Makefile
	gs -sDEVICE=pngmono -r72 -sPaperSize=a3 -sOutputFile=$@ -dNOPAUSE -q -- $<
	convert -trim $@ $@

%orig.src:	%.pfb
	t1disasm $< > $@

%rand.src:	%orig.src randit.awk
	awk -f randit.awk $< > $@

%rand.pfb:	%rand.src
	t1asm $< > $@

cmbxti10rand.mp:	cmbxti10rand.src t1tomp.awk
	awk -f t1tomp.awk $< > $@

cmbxti10rand.1:	cmbxti10rand.mp
	mpost $<

cmbxti10.pfb:
	@echo "----> Put a copy of font file $@ into this directory."
	@false

myfonts.map:	cmbxti10rand.pfb
	echo "cmbxti10 CMBXTI10 <cmbxti10rand.pfb" >> $@

tar:
	tar cvfz fonts4fun.tgz \
	Makefile randit.awk t1tomp.awk x.tex
	
clean:
	- rm -f cmbxti10rand*
	- rm -f *.ps
	- rm -f *.src
	- rm -f *rand.pfb
	- rm -f myfonts.map
	- rm -f *.log
	- rm -f *.dvi
	- rm -f *.pdf
	- rm -f *.mp
	- rm -f *.png
	- rm -f *.tgz
