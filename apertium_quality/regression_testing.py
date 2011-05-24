import xml.etree.cElementTree as etree
from cStringIO import StringIO
from apertium_quality.core import whereis
from collections import defaultdict
from subprocess import *
from tempfile import NamedTemporaryFile
import urllib

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
		self.tests = defaultdict(defaultdict)
		for i in self.text.split('\n'):
			if i[:4] == "* {{":
				x = i.strip("{}* ").split('|')
				self.tests[x[1]][x[2]] = x[3]
		self.out = StringIO()
	
	def run(self):
		for side in self.tests:
			self.out.write("Now testing: %s\n" % side)
			tmp = NamedTemporaryFile(delete=False)
			args = '<br>' + '<br>'.join(self.tests[side].keys()).encode('utf-8')
			tmp.write(args)
			app = Popen([self.program, '-t', 'html', '-d', self.directory, self.mode, tmp.name], stdin=PIPE, stdout=PIPE, stderr=PIPE)
			tmp.close()
			#tmp = open('derp.txt', 'w'); tmp.write(args); tmp.close()
			self.results = app.communicate()[0].decode('utf-8').split('<br>')
			
			print self.results
			print "Rst:",len(self.results),"Tst:",len(self.tests[side])
			for n, test in enumerate(self.tests[side].items()):
				self.out.write("%s\t  %s\n" % (self.mode, test[0].encode('utf-8')))
				if self.results[n].strip() == test[1].strip():
					self.out.write("WORKS\t  %s\n" % self.results[n].encode('utf-8'))
					self.passes += 1
				else:
					self.out.write("\t- %s\n" % test[1].encode('utf-8'))
					self.out.write("\t+ %s\n" % self.results[n].encode('utf-8'))
				self.total += 1

	def start(self):
		self.run()

	def get_output(self):
		print self.out.getvalue()
		print "%d/%d %d%" % (self.passes, self.total, self.passes / self.total * 100)
