import sys
try:
	import argparse	
except:
	raise ImportError("Please install argparse module.")

from apertium_quality.testing import HfstTest
from apertium_quality import Statistics, checksum

#TODO add piping for great interfacing

class UI(object):
	def __init__(self):
		self.args = args = self.parse_args()
		self.test = HfstTest(args)
	
	def parse_args(self):
		ap = argparse.ArgumentParser(
			description="""Test morphological transducers for consistency. 
			`hfst-lookup` (or Xerox' `lookup` with argument -x) must be
			available on the PATH.""",
			epilog="Will run all tests in the test_file by default.")
		ap.add_argument("-c", "--colour",
			dest="colour", action="store_true",
			help="Colours the output")
		ap.add_argument("-C", "--compact",
			dest="compact", action="store_true",
			help="Makes output more compact")
		ap.add_argument("-i", "--ignore-extra-analyses",
			dest="ignore_analyses", action="store_true",
			help="""Ignore extra analyses when there are more than expected,
			will PASS if the expected one is found.""")
		ap.add_argument("-s", "--surface",
			dest="surface", action="store_true",
			help="Surface input/analysis tests only")
		ap.add_argument("-l", "--lexical",
			dest="lexical", action="store_true",
			help="Lexical input/generation tests only")
		ap.add_argument("-f", "--hide-fails",
			dest="hide_fail", action="store_true",
			help="Suppresses passes to make finding failures easier")
		ap.add_argument("-p", "--hide-passes",
			dest="hide_pass", action="store_true",
			help="Suppresses failures to make finding passes easier")
		ap.add_argument("-S", "--section", default=["hfst"],
			dest="section", nargs=1, required=False, 
			help="The section to be used for testing (default is `hfst`)")
		ap.add_argument("-t", "--test",
			dest="test", nargs=1, required=False,
			help="""Which test to run (Default: all). TEST = test ID, e.g.
			'Noun - gåetie' (remember quotes if the ID contains spaces)""")
		ap.add_argument("-v", "--verbose",
			dest="verbose", action="store_true",
			help="More verbose output.")
		ap.add_argument("-X", "--statistics", dest="statfile", 
			nargs='?', const='quality-stats.xml', default=None,
			help="XML file that statistics are to be stored in")
		ap.add_argument("test_file", nargs=1,
			help="YAML file with test rules")
		return ap.parse_args()
	
	def start(self):
		self.test.run()
		self.test.get_output()
		if self.args.statfile:
			stats = Statistics(self.args.statfile)
			print("[STUB] Not done yet. Relax, have a coffee :)")	

def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	main()

