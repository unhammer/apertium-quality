from argparse import ArgumentParser

from apertium.quality.testing import Test
from apertium.quality import Statistics
#TODO add piping for great interfacing

class Frontend(Test, ArgumentParser):
    def __init__(self):
        ArgumentParser.__init__(self)
        Test.__init__(self)
        self.add_argument("-c", "--colour", dest="colour", action="store_true",
            help="Colours the output")
        self.add_argument("-X", "--statistics", dest="statfile", 
            nargs='?', const='quality-stats.xml', default=None,
            help="XML file that statistics are to be stored in")

    def start(self):
        ret = self.run()
        print(self.to_string())
        if self.args.statfile:
            stats = Statistics(self.args.statfile)
            stats.add(*self.to_xml())
            stats.write()
        self.exit(ret)
