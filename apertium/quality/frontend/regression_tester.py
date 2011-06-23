try:
	import argparse	
except:
	raise ImportError("Please install argparse module.")

from apertium.quality.testing import RegressionTest

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
		ap.add_argument("-X", "--statistics", dest="statfile",
			nargs='?', const='quality-stats.xml', default=None,
			help="XML file that statistics are to be stored in")
		ap.add_argument("mode", nargs=1, help="Mode of operation (eg. br-fr)")
		ap.add_argument("wikiurl", nargs=1, help="URL to regression tests")
		self.args = args = ap.parse_args()
		self.test = RegressionTest(args.wikiurl[0], args.mode[0], args.dictdir[0])
	
	def start(self):
		self.test.run()
		self.test.get_output()
		if self.args.statfile:
			self.test.save_statistics(self.args.statfile)

def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass

