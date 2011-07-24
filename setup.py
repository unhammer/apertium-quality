import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages
from os import listdir

install_requires = ['lxml', 'pyyaml', 'mwtools']
#, 'argparse'], 'numpy', 'matplotlib']

try:
	import argparse
except:
	install_requires.append('argparse')

try:
	from collections import OrderedDict
except:
	install_requires.append('ordereddict')

setup(
	name = "apertium-quality",
	version = "0.2",
	packages = find_packages(),
	install_requires = install_requires,

	author = "Brendan Molloy",
	author_email = "brendan@bbqsrc.net",
	description = "Apertium Quality Control Framework",
	license = "CC0",
	keywords = "apertium nlp quality control framework",
	entry_points = """
	[console_scripts]
	aq-morftest = apertium.quality.frontend.morph_tester:main
	aq-covtest = apertium.quality.frontend.coverage_tester:main
	aq-regtest = apertium.quality.frontend.regression_tester:main
	aq-gentest = apertium.quality.frontend.generation_tester:main
	aq-ambtest = apertium.quality.frontend.ambiguity_tester:main
	aq-htmlgen = apertium.quality.frontend.website_generator:main
	aq-autotest = apertium.quality.frontend.auto_tester:main
	aq-wikicrp = apertium.quality.frontend.corpus_extractor:main
	"""
)
