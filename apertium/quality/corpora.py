from xml.sax import SAXException
from multiprocessing import Process, Pool, Queue, cpu_count
from io import StringIO
from queue import Empty
import sys
import re
import os
import string
import xml.sax.handler

try:
	from lxml import etree
	from lxml.etree import Element, SubElement
except:
	import xml.etree.ElementTree as etree
	from xml.etree.ElementTree import Element, SubElement

from apertium.quality import schemas
from mwtools import MediawikiHandler
import nltk.data

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
	
	def __init__(self, fin, fout, cores=0, tokenizer=None, q=None, xml=False):
		self.fin = fin
		self.fout = fout
		self.xml = xml
		self.cores = int(cores or 0)
		self.inq = Queue(q or 32)
		self.outq = Queue()
		try:
			if tokenizer:
				self.tokenizer = nltk.data.load("file:" + tokenizer)
			else:
				self.tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
		except:
			from nltk import download
			print("Downloading tokenisation library. This may take some time. (~6MB)")
			download('punkt')
			self.tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
	
	def generate(self, max_sentences=0):
		self._make_processes(max_sentences)
		self.parser.start()
		self._start_processes()

	def _make_processes(self, max_sentences):
		self.parser = Process(target=self._parser, args=(self.fin,))
		self.parser.daemon = True
		self.workers = [Process(target=self.worker) for i in range(self.cores or cpu_count())]
		for w in self.workers:
			w.daemon = True
		if self.xml:
			self.larry = Process(target=self.xml_output_worker, args=(self.fout, self.fin.name, max_sentences))
		else:
			self.larry = Process(target=self.output_worker, args=(self.fout, max_sentences))
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
		parser.parse(fin)
		del parser
	
	def heuristics(self, data, minwords=6, maxcomma=2, maxpunc=2, maxdigits=6):
		punc = "#$%&\'()*+-/:;<=>?@[\\]^_`{|}~"
		if '\n' in data:
			return False
		if "<" in data or ">" in data:
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
		if "Wikipedia" in data:
			return False
		if re.search(r'\$[0-9]', data):
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
			while 1:
				ch, title = self.inq.get(block=True)
				if ch.strip() == "":
					continue
				data = "[= %s =]\n\n%s" % (title, ch)
				article = MediawikiHandler(data).parse()
				del data
				parsed = self.tokenizer.tokenize(article)
				del article
				self.outq.put(parsed)
				del parsed
		except Empty:
			pass
	
	def output_worker(self, f, maxsentences=0):
		pid = os.getpid()
		try:
			count = 0
			if isinstance(f, str):
				f = open(f, 'w')
			if f.mode != 'w':
				f = open(f.name, 'w')

			while 1:
				if maxsentences > 0 and count >= maxsentences: 
					break
				sentencelist = self.outq.get(block=True, timeout=5)
				for s in sentencelist:
					if maxsentences > 0 and count >= maxsentences: 
						break
					if(self.heuristics(s.strip())):
						f.write("%s\n" % s.strip())
						count += 1
				f.flush()
				sys.stdout.write('\r%d' % count)
				sys.stdout.flush()
		except Empty:
			pass
		except KeyboardInterrupt:
			pass
		finally:
			sys.stdout.write("\r%d sentences written to %s.\n" % (count, f.name))
			sys.stdout.flush()
			f.close()
	
	def xml_output_worker(self, f, fname, maxsentences=0):
		pid = os.getpid()
		ns = "{%s}" % schemas['corpus']
		try:
			count = 0
			kwargs = {
				'name': "Generated Wikipedia Corpus from %s" % fname, 
				'tags': "generator:aq-wikicrp"
			}
			
			if etree.__name__ == "lxml.etree":
				kwargs['nsmap'] = {None: schemas['corpus']}
			else:
				kwargs["xmlns"] = schemas['corpus']
			
			root = Element(ns + "corpus", **kwargs)
			while 1:
				if maxsentences > 0 and count >= maxsentences: 
					break
				sentencelist = self.outq.get(block=True, timeout=5)
				el = Element(ns + "entry")
				el.text = ""
				for s in sentencelist:
					if maxsentences > 0 and count >= maxsentences: 
						break
					if(self.heuristics(s.strip())):
						el.text += s.strip() + '\n'
						count += 1
				if el.text != "":
					root.append(el)
				sys.stdout.write('\r%d' % count)
				sys.stdout.flush()
		except Empty:
			pass
		except KeyboardInterrupt:
			pass
		finally:
			etree.ElementTree(root).write(f.name, encoding="utf-8", xml_declaration=True)
			sys.stdout.write("\r%d sentences written to %s.\n" % (count, f.name))
			sys.stdout.flush()
		
