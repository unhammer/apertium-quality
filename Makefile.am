_VERBOSE=`test -z "$(VERBOSE)" || echo "-v";`
_PKGDIR="$(prefix)/lib/python$(PYTHON_VERSION)/site-packages"

all:
	@$(PYTHON) setup.py build

install:
	@if test -z "$(prefix)"; then \
		$(PYTHON) setup.py $(_VERBOSE) install; \
	else \
		export PYTHONPATH=$(_PKGDIR); \
		mkdir -p $(_PKGDIR); \
		$(PYTHON) setup.py $(_VERBOSE) install --prefix $(prefix); \
		echo '' ;\
		echo 'IMPORTANT: Remember to add $(_PKGDIR) to your $$PYTHONPATH!'; \
	fi 


install-nltk:
	@$(DOWNLOADER) http://cloud.github.com/downloads/bbqsrc/apertium-quality/nltk-3.0.1.tar.gz
	@tar xf nltk-3.0.1.tar.gz
	@if test -z "$(prefix)"; then \
		cd nltk-3.0.1 && \
		$(PYTHON) setup-distutils.py $(_VERBOSE) install; \
	else \
		cd nltk-3.0.1 && \
		export PYTHONPATH=$(_PKGDIR); \
		mkdir -p $(_PKGDIR); \
		$(PYTHON) setup-distutils.py $(_VERBOSE) install --prefix $(prefix); \
		echo '' ;\
		echo 'IMPORTANT: Remember to add $(_PKGDIR) to your $$PYTHONPATH!'; \
	fi 

clean:
	@rm -rf *.pyc distribute-*{egg,tar.gz} *.egg-info build dist
