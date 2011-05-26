import sys
try:
	import argparse	
except:
	raise ImportError("Please install argparse module.")

from apertium_quality.regression_testing import RegressionTest
from apertium_quality import Statistics

#TODO add piping for great interfacing

class UI(object):
	def __init__(self):
		ap = argparse.ArgumentParser(
			description="Test for regressions directly from Apertium wiki.")
		ap.add_argument("-c", "--colour", dest="colour", action="store_true",
			help="Colours the output")
		ap.add_argument("-d", "--dict", dest="dictdir", nargs='?',
			const=['.'], default=['.'],
			help="Directory of dictionary (Default: current directory)")
		ap.add_argument("-s", "--statistics", dest="statfile",
			nargs='?', const=['quality-stats.xml'], default=[],
			help="XML file that statistics are to be stored in")
		ap.add_argument("mode", nargs=1, help="Mode of operation (eg. br-fr)")
		ap.add_argument("wikiurl", nargs=1, help="URL to regression tests")
		self.args = args = ap.parse_args()
		self.test = RegressionTest(args.wikiurl[0], args.mode[0], args.dictdir[0])
	
	def start(self):
		self.test.run()
		self.test.get_output()
		if self.args.statfile != []:
			stats = Statistics(self.args.statfile[0])
			ns = "{http://www.mediawiki.org/xml/export-0.3/}"
			page = self.test.tree.getroot().find(ns + 'page')
			rev = page.find(ns + 'revision').find(ns + 'id').text
			title = page.find(ns + 'title').text
			stats.add_regression(title, rev, self.test.passes, self.test.total)
			stats.write()

def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	main()
