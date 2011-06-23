#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')
import re, logging, string
import xml.sax
import xml.sax.handler
from xml.sax import SAXException
#import nltk.data

from multiprocessing import Process, Pool, Queue, cpu_count
import multiprocessing

from os import StringIO
from queue import Empty

from wpparser import *
from wputils import *

class CorpusGenerator(object):
	class Handler(xml.sax.handler.ContentHandler):
		def __init__(self, parent):
			self.inq = parent.inq
			
			self.inPage = False
			self.inTitle = False
			self.inText = False
			self.inRedirect = False
			self.inId = False
			self.firstId = False
			
			self.badText = False
			self.text = StringIO()
			self.curTitle = ""
		
		def startElement(self, name, attrs):
			if name == "mediawiki":
				self.inMediawiki = True	
			elif name == "page":	
				self.inPage = True
			elif name == "title":
				self.inTitle = True
			elif name == "id":
				self.inId = True
			elif name == "text":
				self.inText = True
			elif name == "redirect":
				self.inRedirect = True
			elif not self.inMediawiki:
				raise IOError("Not a valid wikipedia dump.")
	
		def characters(self, ch):
			if self.inId and not self.firstId:
				self.firstId = True
				# conservative 10 to stop first few crazy pages
				if int(ch.strip()) < 10:
					self.badText = True
			
			elif self.inTitle:
				if ":" in ch or "Wikipedia" in ch or "Page" in ch:
					self.badText = True
				else:
					self.curTitle = special_char(ch)
	
			elif self.inText:
				self.text.write(ch)
	
		def endElement(self, name):
			if name == "page":
				self.firstId = False
				self.inRedirect = False
				self.inPage = False
				self.badText = False
				self.text = StringIO()
			elif name == "id":
				self.inId = False
			elif name == "title":
				self.inTitle = False
			elif name == "text" and self.inRedirect == False and self.badText == False:
				if (len(self.text.getvalue()) > 8):
					self.inq.put((self.text.getvalue(), self.curTitle))
			elif name == "mediawiki":
				self.inMediawiki = False
	
	def __init__(self):
		self.inq = Queue()
		self.outq = Queue()
		#self.tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
	
	def generate(self, fin, fout, maxsentences=None):
		self._make_processes(fin, fout, maxsentences)
		self.parser.start()
		self._start_processes()

	def _make_processes(self, fin, fout, maxsentences=None):
		print("Cpus: ", cpu_count())
		self.parser = Process(target=self._parser, args=(fin,))
		self.parser.daemon = True
		self.workers = [Process(target=self.worker) for i in range(cpu_count())]
		for w in self.workers:
			w.daemon = True
		self.larry = Process(target=self.output_worker, args=(fout,maxsentences))
		self.larry.daemon = True
	
	def _start_processes(self):
		for w in self.workers:	
			w.start()
		self.larry.start()

		self.larry.join() #block some more.
		for w in self.workers:
			w.terminate() #block to end!
		self.parser.terminate() # no more waiting.

	def _parser(self, fin):
		pid = os.getpid()
		parser = xml.sax.make_parser()
		parser.setContentHandler(self.Handler(self))
		parser.parse(open(fin))
		print("%d parser done, exiting" % pid)

	
	def heuristics(self, input, minwords=6, maxcomma=2, maxpunc=2, maxdigits=6):
		punc = "#$%&\'()*+-/:;<=>?@[\\]^_`{|}~"
		if '\n' in input:
			return False
		if "</" in input or "/>" in input:
			return False
		if input[0] in punc:
			return False
		if minwords-1 > input.count(' '):
			return False
		if maxcomma < input.count(','):
			return False
		for p in punc:
			if maxpunc < input.count(p):
				return False
		count = 0
		for n in string.digits:
			count += input.count(n)
		if count > maxdigits:
			return False
		return True

	def worker(self):
		pid = os.getpid()
		try:		
			while True:
				ch, title = self.inq.get(block=True)
				if ch.strip() == "":
					continue
				#ch = preprocess(ch)
				article = Article(ch, title)
				#stripped = StringIO()
				#self.parseWiki(StringIO(ch), stripped)
				#stripped.seek(0)
				#parsed = self.tokenizer.tokenize(stripped.getvalue())
				self.outq.put(str(article))
		except Empty:
			print("%d done, exiting" % pid)
	
	def output_worker(self, fn, maxsentences=None):
		pid = os.getpid()
		try:
			f = open(fn, 'w')
			count = 0
			while True:
				sl = self.outq.get(block=True, timeout=5)
				f.write(sl)
				if maxsentences and count < maxsentences:
					count += 1
				if count == maxsentences: break
				'''
				sentencelist = self.outq.get(block=True, timeout=5)
				for s in sentencelist:
					if(self.heuristics(s.strip())):
						f.write("%s\n" % s.strip())
						if maxsentences and count < maxsentences:
							count += 1
					if count == maxsentences: break
				if count == maxsentences: break
				'''
			f.close()
		except Empty:
			print("%d output worker done, exiting" % pid)
	
if __name__ == '__main__':
	if len(sys.argv) == 3:
		CorpusGenerator().generate(sys.argv[1], sys.argv[2]) #maxpages
	elif len(sys.argv) == 4:
		CorpusGenerator().generate(sys.argv[1], sys.argv[2], int(sys.argv[3]))
	else: print("Fail. %s" % len(sys.argv))

