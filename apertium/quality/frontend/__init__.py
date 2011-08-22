from argparse import ArgumentParser

from apertium.quality.testing import Test
from apertium.quality import Statistics, ParseError
#TODO add piping for great interfacing

class Frontend(Test, ArgumentParser):
	def __init__(self, stats=True, colour=False):
		ArgumentParser.__init__(self)
		Test.__init__(self)
		if colour:
			self.add_argument("-c", "--colour", dest="colour", action="store_true",
							  help="Colours the output") 
		if stats:
			self.add_argument("-X", "--statistics", dest="statfile", 
							  nargs='?', const='quality-stats.xml', default=None,
							  help="XML file that statistics are to be stored in")

	def start(self):
		ret = self.run()
		print(self.to_string())
		if self.args.statfile:
			try:
				stats = Statistics(self.args.statfile)
				stats.add(*self.to_xml())
				stats.write()
			except ParseError:
				print("ERROR: your statistics file is either an unsupported version or not an XML file.")
		self.exit(ret)
