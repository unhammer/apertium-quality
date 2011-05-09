================================================================================
|                  ApertiumQA - Quality Assurance Framework                    |
================================================================================

DESCRIPTION GOES HERE.

== Setup ==
To install traditionally to the Python library directory on your system:

# python setup.py install

To install in a rootless environment, you can create your own personal "system root". A sysroot at a minimum contains a bin/ and lib/ directory, so you may use your $HOME directory for this (and it will be used in this example.) To setup a root in your home:

$ mkdir $HOME/lib/python2.x/site-packages # where 2.x == your python version
$ export PYTHONPATH=$PYTHONPATH:$HOME/lib/python2.x/site-packages
$ export PATH=$PATH:$HOME/bin
$ python setup.py install --prefix=$HOME

You may also add the export lines to your ~/.bashrc so that it is automatically set when you enter your shell.

You may also create a Python egg. If you don't know what this is, you don't need to know.

$ python setup.py bdist_egg
