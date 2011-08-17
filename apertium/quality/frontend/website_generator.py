import argparse
from os.path import basename, abspath

from apertium.quality import Statistics
from apertium.quality.html import Webpage

#TODO add piping for great interfacing

class UI(object):
	def __init__(self):
		ap = argparse.ArgumentParser(
			description="Generate webpage and related files.")
		ap.add_argument("-t", "--title", dest="title", nargs='?',
			const=basename(abspath('.')), default=basename(abspath('.')),
			help="Directory of dictionary (Default: current directory)")
		ap.add_argument("statistics", nargs=1, help="Statistics file")
		ap.add_argument("outdir", nargs=1, help="Output directory")
		self.args = args = ap.parse_args()
		self.stats = Statistics(args.statistics[0])
		self.web = Webpage(self.stats, args.outdir[0], args.title)
	
	def start(self):
		self.web.generate()

def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass

