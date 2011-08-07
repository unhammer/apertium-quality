from collections import defaultdict, Counter
from os.path import abspath, dirname, basename
from os import listdir
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from hashlib import sha1
from datetime import datetime
import os
import os.path
import re

pjoin = os.path.join


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

def is_tnx(ext):
	return re.match(r't[1-9]x', ext) != None

def is_rlx(ext):
	return ext == "rlx"

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


class DixFile(object):
	class DIXHandler(ContentHandler):
		def __init__(self):
			self.lemmas = []

		def startElement(self, tag, attrs):
			if tag == "e":
				self.lemmas.append(attrs.get("lm", None))

	def __init__(self, f):
		self.f = f
		self.dix = open(f, 'r')
		self.lemmas = None
		self.alphabet = None
	
	def get_alphabet(self):
		if not self.alphabet:
			for line in self.dix:
				if "<alphabet>" in line:
					self.alphabet = line.split("<alphabet>")[-1].split("</alphabet>")[0]
					break
			self.dix.seek(0)
		return self.alphabet
	
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

