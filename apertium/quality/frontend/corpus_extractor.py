import argparse
from apertium.quality.corpora import CorpusExtractor

class UI(object):
    def __init__(self):
        ap = argparse.ArgumentParser(
            description="Extract a usable corpus from a Wikipedia dump.")
        ap.add_argument("-c", "--count",
            dest="count", nargs=1, required=False, default=[10000],
            help="""Maximum sentences to store in corpus output (default: 10000)""")
        ap.add_argument("wikidump", nargs=1, help="Wikipedia XML dump")
        ap.add_argument("outfile", nargs=1, help="Output filename")
        
        self.args = ap.parse_args()
        self.corpus = CorpusExtractor()
    
    def start(self):
        self.corpus.generate(self.args.wikidump[0], 
                self.args.outfile[0], int(self.args.count[0]))

def main():
    try:
        ui = UI()
        ui.start()
    except KeyboardInterrupt:
        pass

