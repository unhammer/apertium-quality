import argparse
from apertium.quality.corpora import CorpusExtractor

class UI(object):
    def __init__(self):
        ap = argparse.ArgumentParser(
            description="Extract a usable corpus from a Wikipedia dump.")
        ap.add_argument("-c", "--count",
            dest="count", nargs=1, required=False, default=[-1],
            help="""Maximum sentences to store in corpus output (default: unlimited)""")
        ap.add_argument("-C", "--cores", dest="cores", nargs=1, required=False,
            default=[None], help="""Limit how many cores to use for generation""")
        ap.add_argument("-t", "--tokeniser", dest="tokeniser", nargs=1, required=False,
            default=[None], help="""Tokeniser to use""")
        ap.add_argument("-q", "--queue", dest="queue", nargs=1, required=False,
            default=[None], help="""Set queue size (for advanced users)""")
        ap.add_argument("-x", "--xml", dest="xml", action="store_true",
            help="Output corpora in XML format")
        ap.add_argument("wikidump", nargs=1, help="Wikipedia XML dump")
        ap.add_argument("outfile", nargs=1, help="Output filename")
        
        self.args = ap.parse_args()
        self.corpus = CorpusExtractor(self.args.wikidump[0], 
                self.args.outfile[0], self.args.cores[0], self.args.tokeniser[0],
                xml=self.args.xml)
    
    def start(self):
        self.corpus.generate(int(self.args.count[0]))

def main():
    try:
        ui = UI()
        ui.start()
    except KeyboardInterrupt:
        pass

