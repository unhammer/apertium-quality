#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ(2.52)

AC_INIT([apertium-quality], [0.7.0], [brendan@bbqsrc.net])

AM_INIT_AUTOMAKE

AM_PATH_PYTHON(3.0)

# There's probably some fancy autotools way of doing this:
echo -n "checking for lxml... "
if $PYTHON -c "import lxml" &>/dev/null; then
   echo "lxml found, won't have to use ElementTree which is a hack anyway";
else
   echo "lxml not found, ElementTree hack will be used";
   #echo "Error, lxml is required"; exit 1
fi

DOWNLOADER=`type -P wget`
if test 'x'$DOWNLOADER = 'x' ; then
	AC_SUBST(DOWNLOADER,"curl -O")
else
	AC_SUBST(DOWNLOADER,"wget -qc")
fi

AC_OUTPUT([Makefile])
