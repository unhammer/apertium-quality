import xml.etree.cElementTree as etree
import os, os.path

from collections import OrderedDict
from os.path import abspath, dirname, basename
from os import listdir
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

class Dictionary(object):
	class DIXHandler(ContentHandler):
		def __init__(self):
			self.lemmas = []
			#self.in_e = False

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

	def get_rules(self):
		if not self.rules:
			self.rules = {}
			for i in get_file_family(self.fn):
				tnx = split_ext(i)[1]
				if is_tnx(tnx):
					parser = make_parser()
					handler = self.TnXHandler()
					parser.setContentHandler(handler)
					parser.parse(i)
					self.rules[tnx] = handler.rules
		return self.rules
					
			

class Statistics(object):
	file_version = "1.0"

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
			xml = dedent("""
			<statistics type="%s" version="%s">
			<regressions/>
			</statistics>
			""" % ("apertium", Statistics.file_version))
			try:
				self.root = etree.fromstring(xml)
				self.tree = etree.ElementTree(self.root)
			except:
				raise
	
	def write(self):
		self.tree.write(self.f, encoding="utf-8", xml_declaration=True)

	def add_regression(self, title, revision, passes, total):
		root = self.root.find('regressions')
		r = etree.SubElement(root, 'regression', timestamp=datetime.now().isoformat())
		etree.SubElement(r, 'title').text = unicode(title.encode('utf-8'))
		etree.SubElement(r, 'revision').text = str(revision)
		etree.SubElement(r, 'passes').text = str(passes)
		etree.SubElement(r, 'fails').text = str(total - passes)
		etree.SubElement(r, 'total').text = str(total)	
