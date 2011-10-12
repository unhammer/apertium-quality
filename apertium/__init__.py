from collections import defaultdict, Counter
from os.path import abspath, dirname, basename
from os import listdir
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from hashlib import sha1
from datetime import datetime
from subprocess import Popen, PIPE
import traceback
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

def process(command, data="", shell=False, stdin=PIPE, stdout=PIPE, 
		stderr=PIPE, close_fds=True):
	p = Popen(command, shell=shell, stdin=stdin, stdout=stdout, 
			stderr=stderr, close_fds=close_fds)
	
	out, err = p.communicate(data)
	out = out.decode('utf-8')
	err = err.decode('utf-8')

	if p.returncode != 0:
		raise Exception("Return code: %s\nstderr: %s" % (p.returncode, err))
	
	return out, err


class DixFile(object):
	class DIXHandler(ContentHandler):
		def __init__(self):
			self.lemmas = []
			self.in_section = False

		def startElement(self, tag, attrs):
			if tag == "section":
				self.in_section = True
			
			if tag == "e" and self.in_section:
				self.lemmas.append(attrs.get("lm", None))
		
		def endElement(self, tag):
			if tag == "section":
				self.in_section = False

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
			try:
				parser.parse(self.f)
				self.lemmas = handler.lemmas
			except Exception as e:
				print("File %s caused an exception:" % self.f)
				print(traceback.format_exception_only(type(e), e)[0])
		return self.lemmas
	
	def get_unique_entries(self):	
		return set(self.get_entries())

