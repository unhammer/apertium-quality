#!/usr/bin/env python

import sys
try:
	import argparse	
except:
	raise ImportError("Please install argparse module.")

from apertium_quality.regression_testing import RegressionTest

class UI(object):
	def __init__(self):
		ap = argparse.ArgumentParser(
			description="Test for regressions directly from Apertium wiki.")
		ap.add_argument("-c", "--colour", dest="colour", action="store_true",
			help="Colours the output")
		ap.add_argument("-d", "--dict", default=["."], dest="dictdir", nargs=1,
			help="Directory of dictionary (Default: current directory)")
		ap.add_argument("mode", nargs=1, help="Mode of operation (eg. br-fr)")
		ap.add_argument("wikiurl", nargs=1, help="URL to regression tests")
		args = ap.parse_args()
		self.test = RegressionTest(args.wikiurl[0], args.mode[0], args.dictdir[0])
	
	def start(self):
		self.test.run()
		self.test.get_output()

if __name__ == "__main__":
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass
