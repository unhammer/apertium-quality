#!/bin/bash

get_opt() {
	local opts="['prefix=', 'python=', 'version=', 'verbose']"
	local pythonapp="
import getopt
out = ''
opts, args = getopt.getopt(\"$OPTSIN\".split(), \"v\", $opts)
for k, v in opts:
	if k in ('-v', '--verbose'):
		out += 'VERBOSE=1 '
	elif k.startswith('--'):
		out += '%s=%s ' % (k[2:].upper(), v)
	
out += ' '.join(args)
print(out)
"
	GETOPTS=`$PYTHON -c "$pythonapp"`
}

if [ `id -u` = 0 ] ; then
	_PREFIXED=0
else
	_PREFIXED=1
fi

_STANDALONE=0
standalone() {
	_STANDALONE=1
	echo "[!] Standalone is a stub for now!"
	exit 1
}

prefixed() {
	_PREFIXED=1	
}

clean() {
	echo "rm -rf *.pyc distribute-*{egg,tar.gz} *.egg-info build dist"
	rm -rf *.pyc distribute-*{egg,tar.gz} *.egg-info build dist
	exit 0
}

if [ 'x'$PYTHON = 'x' ] ; then
	PYTHON=`type -P python`
else
	PYTHON=`type -P $PYTHON`
fi

OPTSIN="$*"
get_opt
eval $GETOPTS

# BEGIN CONFIG
if [ 'x'$VERBOSE = 'x' ] ; then
	_VERBOSE=">/dev/null"	
else
	unset _VERBOSE
fi

if [ 'x'$PREFIX = 'x' ] ; then
	_PREFIXED=0
fi

if [ 'x'$PYTHON = 'x' ] ; then 
	echo "[!] Python not found. If not in \$PATH, set PYTHON variable." >&2
	exit 1
fi
echo "[*] Python binary: $PYTHON"

if [ 'x'$VERSION = 'x' ] ; then
	VERSION=`$PYTHON -c "import sys; print(sys.version[:3])"`
fi

echo "[*] Python version: $VERSION"

if [ 'x'$PREFIX = 'x' ] ; then
	_pkgdir=`$PYTHON -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())"`
else
	_pkgdir="${PREFIX}/lib/python${VERSION}/site-packages"
fi

echo "[*] Chosen package directory: ${_pkgdir}"

if [ $_PREFIXED -gt 0 ] ; then
	echo "[*] Attempting a prefixed (rootless) installation"
else
	echo "[*] Attempting a normal installation (may require root)"
fi
echo -n "Ready to install [y/N]? "
read _ready

if [ ! 'x'$_ready = 'xy' ] ; then
	echo "Aborting."
	exit 1
fi

# BEGIN INSTALLATION
_install_standalone() {
	echo "Stub"
}

_install_prefixed() {
	export PYTHONPATH=$_pkgdir
	mkdir -p $PYTHONPATH
	if [ $? -gt 0 ] ; then
		echo "[!] ${PREFIX} not writable. Aborting."
		exit 1
	fi
	echo "[*] Installing..."
	eval $PYTHON setup.py install --prefix=${PREFIX} ${_VERBOSE}
	echo "[-] It is recommended that you add the following lines to your .bashrc:"
	echo "export PATH=$PATH:${PREFIX}/bin"
	echo "export PYTHONPATH=${PYTHONPATH}"
}

_install() {
	echo "[*] Installing..."
	eval $PYTHON setup.py install ${_VERBOSE}
}

if [ $_PREFIXED -gt 0 ] ; then
	_install_prefixed
else
	_install
fi

if [ $? -gt 0 ] ; then 
	echo "[!] An error occurred."
else
	echo "[*] Installation complete."
fi
