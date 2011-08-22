_VERBOSE=`test -z "$(VERBOSE)" || echo "-v";`
_PKGDIR="$(prefix)/lib/python$(PYTHON_VERSION)/site-packages"

all:
	@$(PYTHON) setup.py build

install:
	@if test -z "$(prefix)"; then \
		$(PYTHON) setup.py $(_VERBOSE) install; \
	else \
		PYTHONPATH=$(_PKGDIR)':$$PYTHONPATH' $(PYTHON) setup.py $(_VERBOSE) install --prefix=$(prefix); \
		echo '' ;\
		echo 'IMPORTANT: Remember to add $(_PKGDIR) to your $$PYTHONPATH!'; \
	fi 

clean:
	@rm -rf *.pyc distribute-*{egg,tar.gz} *.egg-info build dist
