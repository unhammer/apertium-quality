import os, os.path, re

from collections import defaultdict
from os.path import abspath, dirname, basename
from os import listdir

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

from hashlib import sha1
from datetime import datetime
#import logging


def whereis(programs):
	out = {}
	for p in programs:
		for path in os.environ.get('PATH', '').split(':'):
			if os.path.exists(os.path.join(path, p)) and \
			   not os.path.isdir(os.path.join(path, p)):
					out[p] = os.path.join(path, p)
		if not out.get(p):
			raise EnvironmentError("Cannot find `%s`. Check $PATH." % p)
	return out

def split_ext(fn):
	return tuple(fn.rsplit('.', 1))

def get_file_family(fn):
	f = split_ext(fn)[0]
	d = dirname(abspath(f))
	return [os.path.join(d, i) for i in listdir(d) if split_ext(i)[0] == basename(f)]

def get_files_by_ext(d, ext):
	return [ i for i in listdir(d) if split_ext(i)[1] == ext ]

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

def destxt(data):
	escape = re.compile(r"[\]\[\\/@<>^${}]")
	encap = re.compile(r"[\n\t\r]")
	output = escape.sub(lambda o: re.escape(o.group(0)), data)
	output = encap.sub(lambda o: " [%s]" % o.group(0), output)
	return output

def retxt(data):
	escape = re.compile(r"\\([\]\[\\/@<>^${}])")
	encap = re.compile(r" \[([\n\t\r])\]")
	output = escape.sub(lambda o: o.group(1), data)
	output = encap.sub(lambda o: o.group(1), output)
	return output


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
				self.rules.append(attrs.get("comment", None))

	def __init__(self, f):
		self.f = f
		self.dix = open(get_dix(f), 'rb')
		self.lemmas = None
		self.rules = None
		
	def get_entries(self):
		if not self.lemmas:
			parser = make_parser()
			handler = self.DIXHandler()
			parser.setContentHandler(handler)
			parser.parse(self.dix)
			self.lemmas = handler.lemmas
		return self.lemmas
	
	def get_unique_entries(self):	
		return set(self.get_entries())

	def get_rules(self):
		if not self.rules:
			self.rules = {}
			for i in get_file_family(self.f):
				ext = split_ext(i)[1]
				if is_tnx(ext):
					parser = make_parser()
					handler = self.TnXHandler()
					parser.setContentHandler(handler)
					parser.parse(i)
					self.rules[ext] = handler.rules
				elif is_rlx(ext):
					f = open(i, 'rb')
					self.rules[ext] = defaultdict(list)
					rules = ("SELECT", "REMOVE", "MAP", "SUBSTITUTE")
					for line in f.xreadlines():
						if line.startswith(rules):
							x = line.split(" ", 1)
							self.rules[ext][x[0]].append(x[1])
		return self.rules
	
	def get_rule_count(self):
		c = 0
		for i in self.get_rules().values():
			if isinstance(i, list):
				c += len(i)
			elif isinstance(i, dict):
				for j in i.values():
					c += len(j)
		return c

