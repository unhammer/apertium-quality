#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ(2.52)

AC_INIT([apertium-quality], [0.7.0], [brendan@bbqsrc.net])

AM_INIT_AUTOMAKE

# backport from automake.git so we can find python3.1:
m4_define_default([_AM_PYTHON_INTERPRETER_LIST],
[python python2 python3 python3.2 python3.1 python3.0 python2.7 dnl
 python2.6 python2.5 python2.4 python2.3 python2.2 python2.1 python2.0])

AM_PATH_PYTHON(3.0)

# There's probably some fancy autotools way of doing this:
echo -n "checking for lxml... "
if $PYTHON -c "import lxml" &>/dev/null; then
   echo "lxml found";
else
   echo "lxml not found, ElementTree workaround will be used";
   #echo "Error, lxml is required"; exit 1
fi

DOWNLOADER=`type -P wget`
if test 'x'$DOWNLOADER = 'x' ; then
	AC_SUBST(DOWNLOADER,"curl -O")
else
	AC_SUBST(DOWNLOADER,"wget -qc")
fi

AC_OUTPUT([Makefile])
