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

SED=`type -P gsed`
if [ $? -gt 0 ] ; then
	SED=sed
fi

OPTSIN="$*"
get_opt
eval "$GETOPTS"

if [ 'x'$PYTHON = 'x' ] ; then
	PYTHON=`type -P python`
else
	PYTHON=`type -P $PYTHON`
fi

# BEGIN CONFIG
if [ 'x'$VERBOSE = 'x' ] ; then
	_VERBOSE="2&>/dev/null"	
else
	unset _VERBOSE
fi

if [ 'x'$PREFIX = 'x' ] ; then
	_PREFIXED=0
fi

if [ 'x'$PYTHON = 'x' ] ; then
	echo "[!] Python not found. If not in \$PATH, use full path." >&2
	exit 1
fi

if [ 'x'$VERSION = 'x' ] ; then
	VERSION=`$PYTHON -c "import sys; print(sys.version[:3])"`
	if [ ! `echo $VERSION | cut -d '.' -f 1` = '3' ] ; then
		echo "[!] Only compatible with Python 3 (got $VERSION)."
		echo "[!] Try setting --python to your Python 3 binary."
		exit 1
	fi
fi

if [ 'x'$PREFIX = 'x' ] ; then
	_PKGDIR=`$PYTHON -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())"`
else
	_PKGDIR="${PREFIX}/lib/python${VERSION}/site-packages"
fi

echo "[*] Chosen package directory: ${_PKGDIR}"
echo "[*] Python binary: $PYTHON"
echo "[*] Python version: $VERSION"

if [ $_PREFIXED -gt 0 ] ; then
	echo "[*] Attempting a prefixed (rootless) installation"
else
	echo "[*] Attempting a normal installation (may require root)"
fi
echo -n "Ready to install [y/N]? "
read _READY

if [ ! 'x'$_READY = 'xy' ] ; then
	echo "Aborting."
	exit 255
fi

# BEGIN INSTALLATION
_install_nltk_prefixed() {
	eval "$PYTHON -c 'import nltk' ${_VERBOSE}" && return
	wget -qc https://github.com/downloads/bbqsrc/apertium-quality/nltk-3.0.1.tar.gz
	tar xf nltk-3.0.1.tar.gz
	pushd nltk-3.0.1
	eval "$PYTHON setup-distutils.py install --prefix=${PREFIX} ${_VERBOSE}"
	popd
	rm -r nltk-3.0.1.tar.gz
}

_install_nltk() {
	eval "$PYTHON -c 'import nltk' ${_VERBOSE}" && return
	wget -qc https://github.com/downloads/bbqsrc/apertium-quality/nltk-3.0.1.tar.gz
	tar xf nltk-3.0.1.tar.gz
	pushd nltk-3.0.1
	eval "$PYTHON setup-distutils.py install ${_VERBOSE}"
	popd
	rm -r nltk-3.0.1.tar.gz

}

_install_standalone() {
	echo "Stub"
}

_install_lxml() {
	eval "$PYTHON -c 'import lxml' ${_VERBOSE}" && return
	echo "[-] lxml not found. ElementTree will be used."
}

_install_prefixed() {
	export PYTHONPATH=$_PKGDIR
	mkdir -p $PYTHONPATH
	if [ $? -gt 0 ] ; then
		echo "[!] ${PREFIX} not writable. Aborting."
		exit 1
	fi
	echo "[*] Installing..."

	eval "$PYTHON setup.py install --prefix=${PREFIX} ${_VERBOSE}"
	_install_nltk_prefixed
	_install_lxml

	if [ -f $HOME/.bashrc ] ; then 
		rc=$HOME/.bashrc
	elif [ -f $HOME/.profile ] ; then
		rc=$HOME/.profile
	fi

	if [ x"$rc" != 'x' ] ; then
		grep ".apertium-quality" $rc 2&>/dev/null
		if [ $? = 1 ] ; then
			echo "source $HOME/.apertium-quality" >> $rc
		fi
		
		echo "export PATH="'$PATH'":${PREFIX}/bin" > $HOME/.apertium-quality
		echo 'export PYTHONPATH="$PYTHONPATH:'"${PYTHONPATH}\"" >> $HOME/.apertium-quality
		echo "[-] Restart your shell for the environment settings to take effect."
	else

		echo "[-] It is recommended that you add the following lines to your .bashrc:"
		echo 'export PATH=$PATH:'"${PREFIX}/bin"
		echo "export PYTHONPATH=${PYTHONPATH}"
	fi
}

_install() {
	echo "[*] Installing..."
	eval "$PYTHON setup.py install ${_VERBOSE}"
	_install_nltk
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
