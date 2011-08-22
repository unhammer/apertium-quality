from apertium.quality.testing import AutoTest
from apertium.quality.frontend import Frontend


class UI(Frontend, AutoTest):
	def __init__(self):
		Frontend.__init__(self, stats=False, colour=True)
		self.description="Attempt all tests with default settings."
		self.add_argument("-v", "--verbose", dest="verbose",
					      action="store_true",
					      help="Verbose test output")
		self.add_argument("-X", "--statistics", dest="stats", 
                          nargs='?', const='quality-stats.xml', default=None,
                          help="XML file that statistics are to be stored in")
		self.add_argument("-o", "--html", dest="outdir", nargs='?',
						  const='htmlout', default=None, 
      					  help="Output directory for HTML content")
		self.add_argument("aqx", nargs=1, help="Apertium Quality XML configuration file")
		self.args = args = self.parse_args()
		AutoTest.__init__(self, self.args.stats, self.args.outdir, self.args.aqx[0], self.args.verbose)
		
	def start(self):
		try:
			self.run()
		except KeyboardInterrupt:
			self.exit()
		self.exit()

def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass


