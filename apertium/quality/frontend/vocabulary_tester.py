from apertium.quality.testing import VocabularyTest
from apertium.quality.frontend import Frontend

class UI(Frontend, VocabularyTest):
    def __init__(self):
        Frontend.__init__(self)
        self.description = "Test vocabulary for generation errors."
        self.add_argument("-d", "--dict", dest="dictdir", nargs='?',
            const=['.'], default=['.'],
            help="Directory of dictionary (Default: current directory)")
        self.add_argument("-D", "--direction", dest="direction", nargs='?',
            const=['lr'], default=['lr'],
            help="Dictionary direction (lr, rl)")
        self.add_argument("-o", "--output", dest="output", nargs='?',
            const=['voctest.txt'], default=['voctest.txt'],
            help="Output file for arrows output")
        self.add_argument("langpair", nargs=1, help="Language pair (eg, br-fr)")
        self.args = self.parse_args()
        lang1, lang2 = self.args.langpair[0].split('-')
        VocabularyTest.__init__(self, self.args.direction[0], lang1, lang2, self.args.output[0], self.args.dictdir[0])
        
def main():
    try:
        ui = UI()
        ui.start()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()