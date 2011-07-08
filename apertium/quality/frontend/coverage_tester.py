from apertium.quality.testing import CoverageTest
from apertium.quality.frontend import Frontend

#TODO add piping for great interfacing

class UI(Frontend, CoverageTest):
	def __init__(self):
		print("HELLO")
		Frontend.__init__(self)
		self.description = "Test coverage."
		self.add_argument("corpus", nargs=1, help="Corpus text file")
		self.add_argument("dictionary", nargs=1, help="Binary dictionary (.bin)")
		self.args = self.parse_args()
		print(self.args.corpus[0], self.args.dictionary[0])
		CoverageTest.__init__(self, self.args.corpus[0], self.args.dictionary[0])

def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	main()