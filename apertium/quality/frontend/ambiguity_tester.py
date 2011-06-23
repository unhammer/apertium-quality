try:
	import argparse	
except:
	raise ImportError("Please install argparse module.")

from apertium.quality.testing import AmbiguityTest

#TODO add piping for great interfacing

class UI(object):
	def __init__(self):
		ap = argparse.ArgumentParser(
			description="Get average ambiguity.")
		ap.add_argument("-c", "--colour", dest="colour", action="store_true",
			help="Colours the output")
		ap.add_argument("-X", "--statistics", dest="statfile", 
			nargs='?', const='quality-stats.xml', default=None,
			help="XML file that statistics are to be stored in")
		ap.add_argument("dictionary", nargs=1, help="DIX file")
		self.args = args = ap.parse_args()
		self.test = AmbiguityTest(args.dictionary[0])
	
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

