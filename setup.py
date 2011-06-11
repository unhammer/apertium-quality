import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages
from os import listdir

install_requires = ['pyyaml']#, 'argparse'], 'numpy', 'matplotlib']

try:
	import argparse
except:
	install_requires.append('argparse')

try:
	from collections import OrderedDict
except:
	install_requires.append('ordereddict')

scripts = [ "bin/" + i for i in listdir("bin") if i[0] != '.' ]

setup(
	name = "apertium-quality",
	version = "0.0",
	packages = find_packages(),
	scripts = scripts,
	install_requires = install_requires,

	author = "Brendan Molloy",
	author_email = "brendan@bbqsrc.net",
	description = "Apertium Quality Control Framework",
	license = "CC0",
	keywords = "apertium nlp quality control framework"
)
