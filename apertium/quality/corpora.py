#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys, os
import re, logging, string
import xml.sax
import xml.sax.handler
from xml.sax import SAXException
from multiprocessing import Process, Pool, Queue, cpu_count
import multiprocessing
from io import StringIO
from queue import Empty

import nltk.data
from mwtools import MediawikiHandler

class CorpusExtractor(object):
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
				if ch in (":", "Wikipedia", "Page"):
					self.badText = True
				else:
					self.curTitle = ch
	
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
		try:
			self.tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
		except:
			from nltk import download
			download('punkt')
			self.tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
	
	def generate(self, fin, fout, max_sentences=10000):
		self._make_processes(fin, fout, max_sentences)
		self.parser.start()
		self._start_processes()

	def _make_processes(self, fin, fout, max_sentences):
		#print("Threads: ", cpu_count())
		self.parser = Process(target=self._parser, args=(fin,))
		self.parser.daemon = True
		self.workers = [Process(target=self.worker) for i in range(cpu_count())]
		for w in self.workers:
			w.daemon = True
		self.larry = Process(target=self.output_worker, args=(fout, max_sentences))
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
		print("XML parser done, exiting [PID %d]" % pid)
	
	def heuristics(self, data, minwords=6, maxcomma=2, maxpunc=2, maxdigits=6):
		punc = "#$%&\'()*+-/:;<=>?@[\\]^_`{|}~"
		if '\n' in data:
			return False
		if "</" in data or "/>" in data:
			return False
		if data[0] in punc:
			return False
		if minwords-1 > data.count(' '):
			return False
		if maxcomma < data.count(','):
			return False
		for p in punc:
			if maxpunc < data.count(p):
				return False
		count = 0
		for n in string.digits:
			count += data.count(n)
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
				data = "= %s =\n\n%s" % (title, ch)
				article = MediawikiHandler(data).parse()
				parsed = self.tokenizer.tokenize(article)
				self.outq.put(parsed)
		except Empty:
			print("Mediawiki parser done, exiting [PID %d]" % pid)
	
	def output_worker(self, fn, maxsentences=None):
		pid = os.getpid()
		try:
			f = open(fn, 'w')
			count = 0
			while True:
				sentencelist = self.outq.get(block=True, timeout=5)
				for s in sentencelist:
					if(self.heuristics(s.strip())):
						f.write("%s\n" % s.strip())
						count += 1
						sys.stdout.write('\r%d' % count)
						sys.stdout.flush()
					if count >= maxsentences: break
				if count >= maxsentences: break
			f.close()
			sys.stdout.write("\r%d sentences written to %s.\n" % (count, fn))
			sys.stdout.flush()
		except Empty:
			print("Output worker done, exiting [PID %d]" % pid)

