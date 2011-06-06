import os, os.path, re
pjoin = os.path.join
import urllib

from tempfile import NamedTemporaryFile
from cStringIO import StringIO

import xml.etree.cElementTree as etree
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

from collections import defaultdict, Counter
try:
	from collections import OrderedDict
except:
	from ordereddict import OrderedDict

from multiprocessing import Process
from subprocess import *

from apertium_quality import whereis

ARROW = u"\u2192"


class RegressionTest(object):
	ns = "{http://www.mediawiki.org/xml/export-0.3/}"
	program = "apertium"
	
	def __init__(self, url, mode, directory="."):
		if not whereis(self.program):
			raise IOError("Cannot find `%s`. Check $PATH." % self.program)	
		if not "Special:Export" in url:
			raise AttributeError("URL did not contain Special:Export.")
		self.mode = mode
		self.directory = directory
		self.tree = etree.parse(urllib.urlopen(url))
		self.passes = 0
		self.total = 0
		for e in self.tree.getroot().getiterator():
			if e.tag == self.ns + "title":
				self.title = e.text
			if e.tag == self.ns + "revision":
				self.revision = e[0].text # should be <id>
			if e.tag == self.ns + "text":
				self.text = e.text
		if not self.text:
			raise AttributeError("No text element?")
		
		self.tests = defaultdict(OrderedDict)
		for i in self.text.split('\n'):
			if i[:4] == "* {{": # TODO: make {{test regex here
				x = i.strip("{}* ").split('|')
				y = x[2].strip()
				self.tests[x[1]][y if y[-1] == '.' else y+'[_].'] = x[3].strip()
		self.out = StringIO()
	
	def run(self):
		for side in self.tests:
			self.out.write("Now testing: %s\n" % side)
			args = '\n'.join(self.tests[side].keys()).encode('utf-8')
			app = Popen([self.program, '-d', self.directory, self.mode], stdin=PIPE, stdout=PIPE, stderr=PIPE)
			app.stdin.write(args)
			self.results = app.communicate()[0].decode('utf-8').split('\n')

			for n, test in enumerate(self.tests[side].items()):
				if n >= len(self.results):
					raise AttributeError("More tests than results.")
					#continue
				res = self.results[n].split("[_]")[0].strip().encode('utf-8')
				orig = test[0].split("[_]")[0].strip().encode('utf-8')
				targ = test[1].strip().encode('utf-8')
				self.out.write("%s\t  %s\n" % (self.mode, orig))
				if res == targ:
					self.out.write("WORKS\t  %s\n" % res)
					self.passes += 1
				else:
					self.out.write("\t- %s\n" % targ)
					self.out.write("\t+ %s\n" % res)
				self.total += 1
				self.out.write('\n')

	def get_passes(self):
		return self.passes

	def get_fails(self):
		return self.total - self.passes

	def get_total(self):
		return self.total
	
	def get_total_percent(self):
		return "%.2f" % (float(self.passes)/float(self.total)*100)

	def get_output(self):
		print self.out.getvalue()
		percent = 0
		if self.total > 0:
			percent = float(self.passes) / float(self.total) * 100
		print "Passes: %d/%d, Success rate: %.2f%%" % (self.passes, self.total, percent)


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
			self.f.seek(0)

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



class VocabularyTest(object):
	class DIXHandler(ContentHandler):
		def __init__(self):
			self.alph = None
		def startElement(self, tag, attrs):
			if tag == "alphabet":
				self.tag == "alphabet"

		def characters(self, ch):
			if self.tag == "alphabet":
				self.alph = ch.strip()

	def get_alphabet(self, f):
		parser = make_parser()
		handler = self.DIXHandler()
		parser.setContentHandler(handler)
		parser.parse(f)
		self.alph = hander.alph
	
	def __init__(self, lang1, lang2, transfer, fdir="."):
		self.out = StringIO()
		self.fdir = fdir
		self.lang1 = lang1
		self.lang2 = lang2
		self.transfer = transfer
		self.prefix = prefix = "%s-%s" % (lang1, lang2)
		self.basename = basename = "apertium-%s" % self.prefix

		self.anadix = pjoin(fdir, "%s.%s.dix" % (basename, lang1))
		self.genbin = pjoin(fdir, "%s.autogen.bin" % prefix)

		self.get_alphabet(anadix)
		self.delim = re.compile("[%s]:(>:)?[%s]" % (self.alph, self.alph))

		#TODO whereis binaries
		
	def run(self):
		p = Popen(['lt-expand', self.anadix], stdout=PIPE)
		dixout = p.communicate()[0]


		
