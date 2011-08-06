from apertium.quality.testing import DictionaryTest
from apertium.quality.frontend import Frontend

class UI(Frontend, DictionaryTest):
    def __init__(self):
        Frontend.__init__(self)
        self.description = "Get general dictionary statistics."
        self.add_argument("dictionary", nargs=1, help="Dictionary file (.dix)")
        self.args = self.parse_args()
        DictionaryTest.__init__(self, self.args.dictionary[0])

def main():
    try:
        ui = UI()
        ui.start()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()