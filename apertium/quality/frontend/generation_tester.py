from apertium.quality.testing import GenerationTest
from apertium.quality.frontend import Frontend

class UI(Frontend, GenerationTest):
	def __init__(self):
		Frontend.__init__(self)
		self.description = "Test generation."
		self.add_argument("-d", "--dict", dest="directory", nargs='?',
			const=['.'], default=['.'],
			help="Directory of dictionary (Default: current directory)")
		self.add_argument("mode", nargs=1, help="Language mode (eg, br-fr)")
		self.add_argument("corpus", nargs=1, help="Corpus text file")
		self.args = self.parse_args()
		GenerationTest.__init__(self, self.args.directory[0], self.args.mode[0], self.args.corpus[0])
		
def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	main()