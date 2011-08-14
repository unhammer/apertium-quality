from apertium.quality.testing import DictionaryTest
from apertium.quality.frontend import Frontend

class UI(Frontend, DictionaryTest):
    def __init__(self):
        Frontend.__init__(self)
        self.description = "Get general dictionary statistics."
        self.add_argument("-d", "--dict", dest="dictdir", nargs='?',
            const=['.'], default=['.'],
            help="Directory of dictionary (Default: current directory)")
        # TODO add direction
        # TODO add trules option
        # should allow LR, RL and both at same time with multiple flags
        self.add_argument("langpair", nargs=1, help="Language pair (eg aa-ab)")
        self.args = self.parse_args()
        DictionaryTest.__init__(self, self.args.langpair[0], self.args.dictdir[0])

def main():
    try:
        ui = UI()
        ui.start()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()