import xml.etree.cElementTree as etree
import os, os.path

from cStringIO import StringIO
from collections import OrderedDict, defaultdict
from os.path import abspath, dirname, basename
from os import listdir
from xml.etree.cElementTree import Element, SubElement
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from hashlib import sha1
from datetime import datetime
from textwrap import dedent
#import logging

class ParseError(Exception):
	pass

def checksum(data):
	return str(sha1(data).hexdigest())

def whereis(program):
	for path in os.environ.get('PATH', '').split(':'):
		if os.path.exists(os.path.join(path, program)) and \
		   not os.path.isdir(os.path.join(path, program)):
			return os.path.join(path, program)
	return None

def split_ext(fn):
	return tuple(fn.rsplit('.', 1))

def get_file_family(fn):
	f = split_ext(fn)[0]
	d = dirname(abspath(f))
	return [os.path.join(d, i) for i in listdir(d) if split_ext(i)[0] == basename(f)]

def get_dix(fn):
	f = split_ext(fn)
	if f[-1].lower() == "dix":
		return fn
	if len(split_ext(fn)[0]) != len(fn):
		return "%s.dix" % f[0]
	return None

def is_tnx(ext):
	return True if (len(ext) == 3 and ext[1] in "123456789") else False

def is_rlx(ext):
	return True if (len(ext) == 3 and ext == "rlx") else False

#def is_transfer_rules(ext):
#	return (is_tnx(ext) or is_rlx(ext))

class Dictionary(object):
	class DIXHandler(ContentHandler):
		def __init__(self):
			self.lemmas = []

		def startElement(self, tag, attrs):
			if tag == "e":
				if "lm" in attrs:
					self.lemmas.append(attrs.get("lm"))
	
	class TnXHandler(ContentHandler):
		def __init__(self):
			self.rules = []

		def startElement(self, tag, attrs):
			if tag == "rule":
				if "comment" in attrs:
					self.rules.append(attrs.get("comment"))

	def __init__(self, f):
		self.fn = f
		self.f = open(get_dix(f))
		self.lemmas = None
		self.rules = None
		
	def get_entries(self):
		if not self.lemmas:
			parser = make_parser()
			handler = self.DIXHandler()
			parser.setContentHandler(handler)
			parser.parse(self.f)
			self.lemmas = handler.lemmas
		return self.lemmas
	
	def get_unique_entries(self):	
		return set(get_entries)

	def get_rules(self):
		if not self.rules:
			self.rules = {}
			for i in get_file_family(self.fn):
				ext = split_ext(i)[1]
				if is_tnx(ext):
					parser = make_parser()
					handler = self.TnXHandler()
					parser.setContentHandler(handler)
					parser.parse(i)
					self.rules[ext] = handler.rules
				elif is_rlx(ext):
					f = open(i, 'r')
					self.rules[ext] = defaultdict(list)
					rules = ("SELECT", "REMOVE", "MAP", "SUBSTITUTE")
					for line in f.xreadlines():
						if line.startswith(rules):
							x = line.split(" ", 1)
							self.rules[ext][x[0]].append(x[1])
		return self.rules
	
	def get_rule_count(self):
		if not self.rules:
			self.get_rules()
		c = 0
		for ik, iv in self.get_rules().items():
			if isinstance(iv, list):
				c += len(iv)
			elif isinstance(iv, dict):
				for jk, jv in iv.items():
					c += len(jv)
		return c

class Webpage(object):
	#ns = "{http://www.w3.org/1999/xhtml}"
	ns = ""
	base_xhtml = dedent("""
	<!DOCTYPE html>
	<html> <!--xmlns="http://www.w3.org/1999/xhtml" lang="en">-->
		<head>
			<meta name="title" content="%s" />
			<title>%s</title>
			<style type="text/css">
				* {
					margin: 0;
					padding: 0;
				}
			</style>
		</head>
		<body>
			<h1>Apertium Statistics - %s</h1>
			<div id="container"/>
		</body>
	</html>
	""")
	
	def __init__(self, stats, fn):
		#if not isinstance(stats, Statistics):
		#	raise TypeError("Input must be Statistics object.")
		self.stats = stats
		self.fn = fn

	def generate(self):
		tree = etree.ElementTree()
		title = "Apertium Statistics"
		date = datetime.strftime(datetime.now(), "%X %x")
		root = tree.parse(StringIO(self.base_xhtml % (title, title, date)))
		div = root.find(self.ns + "body").find(self.ns + "div")
		div.append(self.generate_regressions())
		div.append(self.generate_coverages())
		tree.write(self.fn, "utf-8", True)#, "html")

	def generate_regressions(self):
		ns = self.ns
		out = Element(ns + "div", id="regressions")
		root = self.stats.root.find('regressions')
		if not root:
			SubElement(out, ns + 'h2').text = "Not found."
			return out
		for i in root.getiterator("regression"):
			r = SubElement(out, ns + 'div', {"class":"regression"})
			title = SubElement(r, ns + 'h2')
			title.text = "%s - %s" % (i.find("title").text, i.attrib["timestamp"])
			SubElement(r, ns + 'h3').text = "Revision: %s" % i.find("title").attrib["revision"]
			SubElement(r, ns + 'p').text = "Total: %s" % i.find("total").text
			SubElement(r, ns + 'p').text = "Passes: %s" % i.find("passes").text
			SubElement(r, ns + 'p').text = "Fails: %s" % i.find("fails").text
		return out
			
	def generate_coverages(self):
		#stub
		return Element("div", id="coverages")


class Statistics(object):
	file_version = "1.0"
	file_type = "apertium"

	def __init__(self, f):
		self.f = f
		if os.path.exists(f):
			try:
				self.tree = etree.parse(open(f))
				if self.tree.getroot().tag == "statistics":
					if self.tree.getroot().get('version') == "1.0":	
						print "[STUB] Do version specific crap here for 1.0"
					else:
						print "[DEBUG] Version incorrect."
					self.root = self.tree.getroot()
					print "[DEBUG] Imported tree."
				else:
					raise ParseError("File does not seem to be a statistics file.")
			except IOError:
				raise
			except ParseError:
				raise
			except:
				raise
		else:
			xml = '<statistics type="%s" version="%s"/>' % \
				(Statistics.file_type, Statistics.file_version)
			try:
				self.root = etree.fromstring(xml)
				self.tree = etree.ElementTree(self.root)
			except:
				raise
	
	def write(self):
		self.tree.write(self.f, encoding="utf-8", xml_declaration=True)

	def add_regression(self, title, revision, passes, total):
		root = self.root.find('regressions')
		if not root:
			root = SubElement(self.root, 'regressions')
		r = SubElement(root, 'regression', timestamp=datetime.utcnow().isoformat())
		SubElement(r, 'title').text = unicode(title.encode('utf-8'))
		SubElement(r, 'revision').text = str(revision)
		SubElement(r, 'passes').text = str(passes)
		SubElement(r, 'fails').text = str(total - passes)
		SubElement(r, 'total').text = str(total)
	
	def add_coverage(self, f, df, fck, dck, cov, words, kwords, ukwords, topuw):
		root = self.root.find('coverages')
		if not root:
			root = SubElement(self.root, 'coverages')
		r = SubElement(root, 'coverage', timestamp=datetime.utcnow().isoformat())
		s = SubElement(r, 'corpus')
		s.text = unicode(f.encode('utf-8'))
		s.attrib["checksum"] = str(fck)
		s = SubElement(r, 'dictionary')
		s.text = unicode(df.encode('utf-8'))
		s.attrib["checksum"] = str(dck)
		SubElement(r, 'percent').text = str(cov)
		s = SubElement(r, 'words')
		SubElement(s, 'total').text = str(words)
		SubElement(s, 'known').text = str(kwords)
		SubElement(s, 'unknown').text = str(ukwords)
		s = SubElement(r, 'top')
		for mot, num in topuw:
			SubElement(s, 'word', count=str(num)).text = unicode(mot.encode('utf-8'))
		
