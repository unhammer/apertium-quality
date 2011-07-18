from apertium.quality.frontend import Frontend
from apertium.quality.testing import MorphTest
from apertium.quality import Statistics

class UI(Frontend, MorphTest):
	def __init__(self):
		Frontend.__init__(self)
		self.description="""Test morphological transducers for consistency. 
			`hfst-lookup` (or Xerox' `lookup` with argument -x) must be
			available on the PATH."""
		self.epilog="Will run all tests in the test_file by default."
		
		self.add_argument("-C", "--compact",
			dest="compact", action="store_true",
			help="Makes output more compact")
		self.add_argument("-i", "--ignore-extra-analyses",
			dest="ignore_analyses", action="store_true",
			help="""Ignore extra analyses when there are more than expected,
			will PASS if the expected one is found.""")
		self.add_argument("-s", "--surface",
			dest="surface", action="store_true",
			help="Surface input/analysis tests only")
		self.add_argument("-l", "--lexical",
			dest="lexical", action="store_true",
			help="Lexical input/generation tests only")
		self.add_argument("-f", "--hide-fails",
			dest="hide_fail", action="store_true",
			help="Suppresses passes to make finding failures easier")
		self.add_argument("-p", "--hide-passes",
			dest="hide_pass", action="store_true",
			help="Suppresses failures to make finding passes easier")
		self.add_argument("-S", "--section", default=["hfst"],
			dest="section", nargs=1, required=False, 
			help="The section to be used for testing (default is `hfst`)")
		self.add_argument("-t", "--test",
			dest="test", nargs=1, required=False,
			help="""Which test to run (Default: all). TEST = test ID, e.g.
			'Noun - g\u00E5etie' (remember quotes if the ID contains spaces)""")
		self.add_argument("-v", "--verbose",
			dest="verbose", action="store_true",
			help="More verbose output.")
		
		self.add_argument("--app", dest="app", nargs=1, required=False, 
			help="Override application used for test")
		self.add_argument("--gen", dest="gen", nargs=1, required=False, 
			help="Override generation transducer used for test")
		self.add_argument("--morph", dest="morph", nargs=1, required=False, 
			help="Override morph transducer used for test")
		
		self.add_argument("test_file", nargs=1,
			help="YAML file with test rules")
		
		self.args = dict(self.parse_args()._get_kwargs())
		for k, v in self.args.copy().items():
			if isinstance(v, list) and len(v) == 1:
				self.args[k] = v[0]

		MorphTest.__init__(self, **self.args)
	
	def start(self):
		ret = self.run()
		print(self.to_string())
		if self.args.get('statfile'):
			stats = Statistics(self.args['statfile'])
			stats.add(*self.to_xml())
			stats.write()
		self.exit(ret)
		
def main():
	try:
		ui = UI()
		ui.start()
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	main()