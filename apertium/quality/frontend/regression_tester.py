from apertium.quality.frontend import Frontend
from apertium.quality.testing import RegressionTest


class UI(Frontend, RegressionTest):
	def __init__(self):
		Frontend.__init__(self)
		self.description="Test for regressions directly from Apertium wiki."
		self.add_argument("-d", "--dict", dest="dictdir", nargs='?',
			const=['.'], default=['.'],
			help="Directory of dictionary (Default: current directory)")
		self.add_argument("mode", nargs=1, help="Mode of operation (eg. br-fr)")
		self.add_argument("wikiurl", nargs=1, help="URL to regression tests")
		self.args = self.parse_args()
		RegressionTest.__init__(self, self.args.wikiurl[0], self.args.mode[0], self.args.dictdir[0])

def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	main()

