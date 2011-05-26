from cStringIO import StringIO
from apertium_quality import whereis
from collections import Counter
from subprocess import *
import re

class CoverageTest(object):
	def __init__(self, f, dct):
		for app in (("lt-proc",)):#, "apertium-destxt", "apertium-retxt"):
			if not whereis(app):
				raise IOError("Cannot find `%s`. Check $PATH." % app)
		self.fn = f #TODO: make sure file exists
		self.f = open(f, 'r')
		self.dct = dct
		self.result = None
		
	def run(self):
		if not self.result:
			delim = re.compile(r"\$[^^]*\^")
			destxt_escape = re.compile(r"[\]\[\\/@<>^${}]")
			destxt_space = re.compile(r"[ \n\t\r]")
			retxt_escape = re.compile(r"\\.")
			retxt_space = re.compile(r"[\]\[]")
			
			f = self.f.read()
			output = destxt_escape.sub(lambda o: "\\"+o.group(0), f)
			output = destxt_space.sub(lambda o: " ", output)
			
			proc = Popen(['lt-proc', self.dct], stdin=PIPE, stdout=PIPE)
			output = proc.communicate(output)[0]
			
			output = retxt_escape.sub(lambda o: o.group(0)[-1], output)
			output = retxt_space.sub('', output)
			
			output = delim.sub("$\n^", output)
			self.result = output.split('\n')

	def get_words(self):
		if not self.result:
			self.run()
		return [ i.strip() for i in self.result ]

	def get_known_words(self):
		if not self.result:
			self.run()
		return [ i.strip() for i in self.result if not '*' in i ]

	def get_unknown_words(self):
		if not self.result:
			self.run()
		return [ i.strip() for i in self.result if '*' in i ]
	
	def get_top_unknown_words(self, c=20):
		return Counter(self.get_unknown_words()).most_common(c)

	def get_top_unknown_words_string(self, c=20):
		out = StringIO()
		for word, count in self.get_top_unknown_words(c):
			out.write("%d\t %s\n" % (count, word))
		return out.getvalue()
		
	def get_coverage(self):
		a = float(len(self.get_known_words()))
		b = float(len(self.get_words()))
		return a / b * 100

	def get_output(self):
		print "Number of tokenised words in the corpus:",len(self.get_words())
		print "Number of known words in the corpus:",len(self.get_known_words())
		print "Coverage: %.2f%%" % self.get_coverage()
		print "Top unknown words in the corpus:"
		print self.get_top_unknown_words_string()
