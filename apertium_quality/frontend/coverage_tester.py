import sys
try:
	import argparse	
except:
	raise ImportError("Please install argparse module.")

from apertium_quality.coverage_testing import CoverageTest
from apertium_quality import Statistics

class UI(object):
	def __init__(self):
		ap = argparse.ArgumentParser(
			description="Test coverage.")
		ap.add_argument("-c", "--colour", dest="colour", action="store_true",
			help="Colours the output")
		ap.add_argument("-s", "--statistics", default=['quality-stats.xml'], 
			dest="statfile", nargs=1, 
			help="XML file that statistics are to be stored in")
		ap.add_argument("corpus", nargs=1, help="Corpus text file")
		ap.add_argument("dictionary", nargs=1, help="Binary dictionary")
		self.args = args = ap.parse_args()
		self.test = CoverageTest(args.corpus[0], args.dictionary[0])

	def start(self):
		self.test.run()
		self.test.get_output()

def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	main()

