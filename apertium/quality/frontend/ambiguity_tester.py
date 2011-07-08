from apertium.quality.testing import AmbiguityTest
from apertium.quality.frontend import Frontend

class UI(Frontend, AmbiguityTest):
	def __init__(self):
		Frontend.__init__(self)
		self.description="Get average ambiguity."
		self.add_argument("dictionary", nargs=1, help="DIX file")
		self.args = self.parse_args()
		AmbiguityTest.__init__(self, self.args.dictionary[0])

def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	main()