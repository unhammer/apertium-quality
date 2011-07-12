from os.path import abspath, basename
import os
pjoin = os.path.join
import argparse

import apertium.quality.testing as testing
from apertium.quality import Webpage, Statistics



class UI(object):
	def __init__(self):
		self.tdir = "tests"
		
		ap = argparse.ArgumentParser(
			description="Attempt all tests with default settings.")
		ap.add_argument("dictdir", nargs=1, help="Dictionary directory")
		ap.add_argument("outdir", nargs=1, help="Output directory")
		ap.add_argument("statistics", nargs=1, help="Statistics file")
		self.args = dict(ap.parse_args()._get_kwargs())
		
		for k, v in self.args.copy().items():
			if isinstance(v, list) and len(v) == 1:
				self.args[k] = v[0]
		
		self.args['langpair'] = basename(abspath(self.args['dictdir'])).split('apertium-')[-1]
		self.lang1, self.lang2 = self.args['langpair'].split('-')
	
	def _tab(data, n=0):
		return "%s:: %s" % ("  "*n, data) 
	
	def _langpairs(self):
		return ['%s-%s' % (self.lang1, self.lang2), 
			'%s-%s' % (self.lang2, self.lang1)]
	
	def _listdir(self, dir):
		x = []
		try:
			x = os.listdir(dir)
		except:
			pass
		return x 
	
	def _abspath(self, *args):
		return abspath(pjoin(self.args['dictdir'], self.tdir, *args))

	def _get_files(self, d):
		return self._listdir(self._abspath(d))
	
	def ambiguity(self):
		print(self._tab("Ambiguity tests"))
		files = [ i for i in self._listdir(self.args['dictdir'])
					if i in ('apertium-%s.%s.dix' % (self.args['langpair'], self.lang1), 
							'apertium-%s.%s.dix' % (self.args['langpair'], self.lang2)) ]
		
		for t in files:
			print(self._tab(t, 1))
			test = testing.AmbiguityTest(t)
			test.run()
			test.save_statistics(self.args['statistics'])
	
	def coverage(self):
		print(self._tab("Coverage tests"))
		dirs = self._get_files('coverage')
		files = []
		for d in dirs:
			files.append(self._get_files(pjoin('coverage', d)))
		corpora = dict(zip(dirs, files))
		
		for k, v in corpora.items():
			if k in self._langpairs():
				print(self._tab(k, 1))
				for i in v:
					print ("    :: %s" % i)
					test = testing.CoverageTest(self._abspath('coverage', k, i), "%s.automorf.bin" % k)
					test.run()
					test.save_statistics(self.args['statistics'])

	def regression(self):
		print(self._tab("Regression tests"))
		dirs = self._get_files('regression')
		files = []
		for d in dirs:
			files.append(self._get_files(pjoin('regression', d)))
		tests = dict(zip(dirs, files))
		
		for k, v in tests.items():
			if k in self._langpairs():
				print(self._tab(k, 1))
				for i in v:
					print (self._tab(i, 2))
					test = testing.RegressionTest(self._abspath('regression', k, i), k, self.args['dictdir'])
					test.run()
					test.save_statistics(self.args['statistics'])
	
	def hfst(self):
		print(self._tab("Morph tests"))
		tests = self._get_files('morph')
		
		for t in tests:
			print(self._tab(t, 1))
			test = testing.MorphTest(self._abspath('morph', t))
			test.run()
			test.save_statistics(self.args['statistics'])
	
	def webpage(self):
		print(self._tab("Generating webpages..."))
		self.stats = Statistics(self.args['statistics'])
		self.web = Webpage(self.stats, self.args['outdir'])
		self.web.generate()
	
	def start(self):
		self.ambiguity()
		self.coverage()
		self.regression()
		self.hfst()
		self.webpage()
		print(self._tab("Done."))


def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass

