import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages
from os import listdir

install_requires = ['PyYAML', 'mwtools']

# Workaround for Python 3.1's failure to include argparse
try: import argparse
except: install_requires.append('argparse')

setup(
	name = "apertium-quality",
	version = "0.3",
	packages = find_packages(),
	install_requires = install_requires,
	url = "https://github.com/bbqsrc/apertium-quality",
	download_url="https://github.com/bbqsrc/apertium-quality/archives/master",
	author = "Brendan Molloy",
	author_email = "brendan@bbqsrc.net",
	description = "Apertium Quality Control Framework",
	license = "CC0",
	keywords = ["apertium", "nlp", "quality control", "framework"],
	classifiers = [
		"Development Status :: 4 - Beta",
		"Operating System :: OS Independent",
		"License :: Public Domain",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3.1",
		"Programming Language :: Python :: 3.2",
		"Intended Audience :: Developers",
		"Topic :: Software Development :: Libraries :: Python Modules",
		"Topic :: Text Processing :: Linguistic",
    ],
	entry_points = """
	[console_scripts]
	aq-morftest = apertium.quality.frontend.morph_tester:main
	aq-covtest = apertium.quality.frontend.coverage_tester:main
	aq-regtest = apertium.quality.frontend.regression_tester:main
	aq-dixtest = apertium.quality.frontend.dictionary_tester:main
	aq-voctest = apertium.quality.frontend.vocabulary_tester:main
	aq-gentest = apertium.quality.frontend.generation_tester:main
	aq-ambtest = apertium.quality.frontend.ambiguity_tester:main
	aq-htmlgen = apertium.quality.frontend.website_generator:main
	aq-autotest = apertium.quality.frontend.auto_tester:main
	aq-wikicrp = apertium.quality.frontend.corpus_extractor:main
	"""
)
