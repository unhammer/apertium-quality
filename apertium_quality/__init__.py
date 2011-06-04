import xml.etree.cElementTree as etree
import os, os.path, re 
import matplotlib
matplotlib.use('Agg') # stops it from using X11 and breaking
import matplotlib.pyplot as plt

from cStringIO import StringIO
from collections import defaultdict
try:
	from collections import OrderedDict
except:
	from ordereddict import OrderedDict
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

def from_isoformat(t):
	return datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%f")

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
			<meta charset="UTF-8" />
			<meta name="title" content="{0}" />
			<title>{0}</title>
			<style type="text/css">
				{2}
			</style>
		</head>
		<body>
			<h1>{0} - {1}</h1>
			<div id="container"/>
		</body>
	</html>
	""")
	
	base_css = dedent("""
	* {
		margin: 0;
		padding: 0;
	}
	""")	

	def __init__(self, stats, fdir):
		#if not isinstance(stats, Statistics):
		#	raise TypeError("Input must be Statistics object.")
		self.stats = stats
		self.fdir = fdir

	def generate(self):
		tree = etree.ElementTree()
		title = "Apertium Statistics"
		date = datetime.strftime(datetime.utcnow(), "%Y-%m-%d %H:%M")
		xhtml = self.base_xhtml.format(title, date, self.base_css)
		root = tree.parse(StringIO(xhtml))
		div = root.find(self.ns + "body").find(self.ns + "div")
		div.append(self.generate_regressions())
		div.append(self.generate_coverages())
		tree.write(os.path.join(self.fdir, "index.html"), "utf-8")#, True)#, "html")

	def generate_regressions(self):
		ns = self.ns
		out = Element(ns + "div", id="regressions")
		root = self.stats.root.find('regressions')
		if not root:
			SubElement(out, ns + 'h2').text = "Not found."
			return out
		
		files = self.plot_regressions()
		st = SubElement(out, ns + 'div', {"class":"statistics"})
		for f in files:
			SubElement(st, ns + 'img', src=f)
			SubElement(st, ns + 'br')

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

	def plot_regressions(self):
		out = []
		space = re.compile('[ /]')
		regs = self.stats.get_regressions()
		for title, reg in regs.items():
			t = "%s - %s" % (title, "Passes")
			plt.title(t)
			plt.xlabel('Test ID')
			plt.ylabel('Passes (%)')
			
			x = range(len(reg))
			y = [[], [], [], []]
			
			for ts, vals in reg.items():
				y[0].append(vals['percent'])
				y[1].append(vals['total'])
				y[2].append(vals['passes'])
				y[3].append(vals['fails'])

			plt.plot(x, y[0])
			png = "%s.png" % space.sub('_', t)
			plt.savefig(os.path.join(self.fdir, png))
			out.append(png)
			plt.clf()

			t = "%s - %s" % (title, "Statistics")
			plt.title(t)
			plt.ylabel('Quantity')

			plt.plot(x, y[1], 'b', x, y[2], 'g', x, y[3], 'r')
			png = "%s.png" % space.sub('_', t)
			plt.savefig(os.path.join(self.fdir, png))
			out.append(png)
			plt.clf()
		return out


class Statistics(object):
	file_version = "1.0"
	file_type = "apertium"

	def __init__(self, f):
		self.f = f
		if os.path.exists(f):
			try:
				self.tree = etree.parse(open(f))
				if self.tree.getroot().tag == "statistics":
					#if self.tree.getroot().get('version') == "1.0":	
						#print "[STUB] Do version specific crap here for 1.0"
					#else:
						#pass
						#print "[DEBUG] Version incorrect."
					self.root = self.tree.getroot()
					#print "[DEBUG] Imported tree."
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
		self.tree.write(self.f, encoding="utf-8")#, xml_declaration=True)

	def add_regression(self, title, revision, passes, total, percent):
		root = self.root.find('regressions')
		if not root:
			root = SubElement(self.root, 'regressions')
		r = SubElement(root, 'regression', timestamp=datetime.utcnow().isoformat())
		s = SubElement(r, 'title')
		s.text = unicode(title.encode('utf-8'))
		s['revision'] = str(revision)
		
		SubElement(r, 'percent').text = str(percent) 
		SubElement(r, 'total').text = str(total)
		SubElement(r, 'passes').text = str(passes)
		SubElement(r, 'fails').text = str(total - passes)
	
	def get_regressions(self):
		r = self.root.find('regressions')
		if not r:
			return dict()
		regressions = defaultdict(dict)
		
		for i in r.getiterator("regression"):
			ts = from_isoformat(i.attrib['timestamp'])
			t = i.find("title")
			title = "%s - %s" % (t.text, t.attrib["revision"])
			regressions[title][ts] = {
				"percent": i.find("percent").text,
				"total": i.find("total").text,
				"passes": i.find("passes").text,
				"fails": i.find("fails").text
			}

		out = dict()
		for k, v in regressions.items():
			out[k] = OrderedDict(sorted(v.items()))

		return out

	
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
		SubElement(r, 'total').text = str(words)
		SubElement(r, 'known').text = str(kwords)
		SubElement(r, 'unknown').text = str(ukwords)
		
		s = SubElement(r, 'top')
		for mot, num in topuw:
			SubElement(s, 'word', count=str(num)).text = unicode(mot.encode('utf-8'))
		
