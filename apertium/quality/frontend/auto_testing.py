from os.path import abspath, dirname, basename
import os
pjoin = os.path.join

try:
	import argparse	
except:
	raise ImportError("Please install argparse module.")

import apertium.quality.testing as testing
#from apertium import get_files_by_ext
from apertium.quality import Webpage, Statistics


#TODO add piping for great interfacing

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
		print(":: Ambiguity tests")
		files = [ i for i in self._listdir(self.args['dictdir'])
					if i in ('apertium-%s.%s.dix' % (self.args['langpair'], self.lang1), 
							'apertium-%s.%s.dix' % (self.args['langpair'], self.lang2)) ]
		
		for t in files:
			print("  :: %s" % t)
			test = testing.AmbiguityTest(t)
			test.run()
			test.save_statistics(self.args['statistics'])
	
	def coverage(self):
		print(":: Coverage tests")
		dirs = self._get_files('coverage')
		files = []
		for d in dirs:
			files.append(self._get_files(pjoin('coverage', d)))
		corpora = dict(zip(dirs, files))
		
		for k, v in corpora.items():
			if k in self._langpairs():
				print("  :: %s" % k)
				for i in v:
					print ("    :: %s" % i)
					test = testing.CoverageTest(self._abspath('coverage', k, i), "%s.automorf.bin" % k)
					test.run()
					test.save_statistics(self.args['statistics'])

	def regression(self):
		print(":: Regression tests")
		dirs = self._get_files('regression')
		files = []
		for d in dirs:
			files.append(self._get_files(pjoin('regression', d)))
		tests = dict(zip(dirs, files))
		
		for k, v in tests.items():
			if k in self._langpairs():
				print("  :: %s" % k)
				for i in v:
					print ("    :: %s" % i)
					test = testing.RegressionTest(self._abspath('regression', k, i), k, self.args['dictdir'])
					test.run()
					test.save_statistics(self.args['statistics'])
	
	def hfst(self):
		print(":: HFST tests")
		tests = self._get_files('hfst')
		
		for t in tests:
			print("  :: %s" % t)
			test = testing.HfstTest(self._abspath('hfst', t))
			test.run()
			test.save_statistics(self.args['statistics'])
	
	def webpage(self):
		print(":: Generating webpages...")
		self.stats = Statistics(self.args['statistics'])
		self.web = Webpage(self.stats, self.args.outdir)
		self.web.generate()
	
	def start(self):
		self.ambiguity()
		self.coverage()
		self.regression()
		self.hfst()
		self.webpage()
		print(":: Done.")


def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass


