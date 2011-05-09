#!/usr/bin/env python

import urllib, os, os.path
import xml.etree.cElementTree as etree
from collections import defaultdict
from subprocess import *

def whereis(program):
	for path in os.environ.get('PATH', '').split(':'):
		if os.path.exists(os.path.join(path, program)) and \
		   not os.path.isdir(os.path.join(path, program)):
			return os.path.join(path, program)
	return None

class ApertiumRegressionTest(object):
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
	def run(self):
		for side in self.tests:
			print "Now testing: %s" % side
			
			app = Popen([self.program, '-d', self.directory, self.mode],
				stdin=PIPE, stdout=PIPE, stderr=PIPE)
			args = '\n'.join(self.tests[side].keys()) + '\n'
			app.stdin.write(args.encode('utf-8'))
			self.results = app.communicate()[0].decode('utf-8').split('\n')
			
			for n, test in enumerate(self.tests[side].items()):
				print "%s\t  %s" % (self.mode, test[0])
				if self.results[n].strip() == test[1].strip():
					print "WORKS\t  %s" % self.results[n]
					self.passes += 1
				else:
					print "\t- %s" % test[1]
					print "\t+ %s" % self.results[n]
				self.total += 1

			print "%d/%d %d%" % (self.passes, self.total, self.passes / self.total * 100)
if __name__ == "__main__":
	import sys, os.path
	if len(sys.argv) < 4:
		name = os.path.basename(sys.argv[0])
		print "Usage:   %s <dictdir> <mode> <url>" % name
		print "Example: %s . br-fr http://wiki.apertium.org/wiki/Special:Export/Breton_and_French/Regression_tests" % name
	else:
		regtest = ApertiumRegressionTest(sys.argv[3], sys.argv[2], sys.argv[1])
		regtest.run()	
