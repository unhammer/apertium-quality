from os.path import abspath, dirname, basename
from os import listdir
pjoin = os.path.join

try:
	import argparse	
except:
	raise ImportError("Please install argparse module.")

import apertium.quality.testing as testing
from apertium import get_files_by_ext
from apertium.quality import Webpage, Statistics


#TODO add piping for great interfacing

class UI(object):
	def __init__(self):
		self.tdir = "aqtests"
		ap = argparse.ArgumentParser(
			description="Attempt all tests with default settings.")
		ap.add_argument("dictdir", nargs=1, help="Dictionary directory")
		ap.add_argument("outdir", nargs=1, help="Output directory")
		ap.add_argument("statistics", nargs=1, help="Statistics file")
		self.args = args = ap.parse_args()
	
	def _test(self, tst, files):
		for f in files:
			print("  :: %s" % basename(f))
			test = tst(f)
			test.run()
			test.save_statistics(self.statistics[0])

	def _get_files(self, d, title, things): 
		print(":: %s" % title)
		tdir = abspath(pjoin(self.args.dictdir[0], pjoin(self.tdir, d)))
		try:
			return listdir(tdir)
		except:
			print("  :: No %s found in %s" % (things, tdir))
			return []

	def ambiguity(self):
		print(":: Ambiguity tests")
		files = get_files_by_ext(self.args.outdir[0], "dix")
		if files == []:
			print("  :: No .dix files found in %s" % abspath(self.args.dictdir[0]))
			return
		self._test(files, testing.AmbiguityTest)
	
	def coverage(self):
		self._test(
			testing.CoverageTest, 
			self._get_files(
				"coverage", "Coverage tests", "corpora"
			)
		)

	def regression(self):
		self._test(
			testing.RegressionTest, 
			self._get_files(
				"regression", "Regression tests", "regression tests"
			)
		)
	
	def hfst(self):
		self._test(
			testing.HfstTest, 
			self._get_files(
				"hfst", "HFST tests", "HFST tests"
			)
		)
	
	def start(self):
		self.stats = Statistics(args.statistics[0])
		
		self.ambiguity()
		self.coverage()
		self.regression()
		self.hfst()
		
		self.web = Webpage(self.stats, args.outdir[0])
		self.web.generate()

def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass


