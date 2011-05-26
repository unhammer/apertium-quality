import sys, re, os.path
try:
	import argparse	
except:
	raise ImportError("Please install argparse module.")

from apertium_quality.coverage_testing import CoverageTest
from apertium_quality import Statistics, checksum

#TODO add piping for great interfacing

class UI(object):
	def __init__(self):
		ap = argparse.ArgumentParser(
			description="Test coverage.")
		ap.add_argument("-c", "--colour", dest="colour", action="store_true",
			help="Colours the output")
		ap.add_argument("-s", "--statistics", dest="statfile", 
			nargs='?', const=['quality-stats.xml'], default=[],
			help="XML file that statistics are to be stored in")
		ap.add_argument("corpus", nargs=1, help="Corpus text file")
		ap.add_argument("dictionary", nargs=1, help="Binary dictionary")
		self.args = args = ap.parse_args()
		self.test = CoverageTest(args.corpus[0], args.dictionary[0])
	
	def start(self):
		self.test.run()
		self.test.get_output()
		if self.args.statfile != []:
			stats = Statistics(self.args.statfile[0])
			
			wrx = re.compile(r"\^(.*)/")

			cfn = os.path.basename(self.test.fn)
			dfn = os.path.basename(self.test.dct)
			cck = checksum(self.test.f.read())
			dck = checksum(open(self.test.dct).read())
			cov = "%.2f" % self.test.get_coverage()
			words = len(self.test.get_words())
			kwords = len(self.test.get_known_words())
			ukwords = len(self.test.get_unknown_words())
			topukwtmp = self.test.get_top_unknown_words()
			topukw = []
			for word, count in topukwtmp:
				topukw.append((wrx.search(word).group(1), count))
			
			stats.add_coverage(cfn, dfn, cck, dck, cov, words, kwords, ukwords, topukw)
			stats.write()

def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	main()

