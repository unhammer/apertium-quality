from apertium.quality.testing import AutoTest
from apertium.quality.frontend import Frontend


class UI(Frontend, AutoTest):
	def __init__(self):
		Frontend.__init__(self, stats=False, colour=True)
		self.description="Attempt all tests with default settings."
		self.add_argument("-X", "--statistics", dest="stats", 
                          nargs='?', const=['quality-stats.xml'], default=[None],
                          help="XML file that statistics are to be stored in")
		self.add_argument("-H", "--html", dest="outdir", nargs='?',
						  const=[None], default=['htmlout'], 
      					  help="Output directory for HTML content")
		self.add_argument("aqx", nargs=1, help="Apertium Quality XML configuration file")
		self.args = args = self.parse_args()
		AutoTest.__init__(self, self.args.stats[0], self.args.outdir[0], self.args.aqx[0])
		

def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass


