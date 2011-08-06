from os.path import abspath, basename
import argparse
import os

import apertium.quality.testing as testing
from apertium.quality import Webpage, Statistics

pjoin = os.path.join


class AutoTest(object):
	def __init__(self, args):
		self.args = args
		self.tdir = "tests"
		self.args['langpair'] = basename(abspath(self.args['dictdir'])).split('apertium-')[-1]
		self.stats = Statistics(self.args['statistics'])
		self.lang1, self.lang2 = self.args['langpair'].split('-')
		
	def _tab(self, data, n=0):
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
			try:
				test = testing.AmbiguityTest(t)
				test.run()
			except:
				print(self._tab("An error occurred.", 2))
				continue
			self.stats.add(*test.to_xml())
	
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
					print (self._tab(i, 2))
					try:
						test = testing.CoverageTest(self._abspath('coverage', k, i), "%s.automorf.bin" % k)
						test.run()
					except:
						print(self._tab("An error occurred.", 3))
						continue
					self.stats.add(*test.to_xml())

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
					try:
						test = testing.RegressionTest(self._abspath('regression', k, i), k, self.args['dictdir'])
						test.run()
					except:
						print(self._tab("An error occurred.", 3))
						continue
					self.stats.add(*test.to_xml())
	
	def morph(self):
		print(self._tab("Morph tests"))
		tests = self._get_files('morph')
		
		for t in tests:
			print(self._tab(t, 1))
			try:
				test = testing.MorphTest(self._abspath('morph', t))
				test.run()
			except: 
				print(self._tab("An error occurred.", 2))
				continue
			self.stats.add(*test.to_xml())
	
	def webpage(self):
		print(self._tab("Generating webpages..."))
		self.web = Webpage(self.stats, self.args['outdir'])
		self.web.generate()
	
	def run(self):
		self.ambiguity()
		self.coverage()
		self.regression()
		self.morph()
		self.stats.write()
		if self.args.get('outdir'):
			self.webpage()
		print(self._tab("Done."))


class UI(object):
	def __init__(self):
		ap = argparse.ArgumentParser(
			description="Attempt all tests with default settings.")
		ap.add_argument("dictdir", nargs=1, help="Dictionary directory")
		ap.add_argument("statistics", nargs=1, help="Statistics file")
		ap.add_argument("-w", "--webpages", dest="outdir", nargs=1, 
      		help="Output directory for webpages")
		self.args = dict(ap.parse_args()._get_kwargs())
		
		for k, v in self.args.copy().items():
			if isinstance(v, list) and len(v) == 1:
				self.args[k] = v[0]
		
	def start(self):
		self.test = AutoTest(self.args)
		self.run()

def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass


