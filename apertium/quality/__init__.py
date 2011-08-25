from collections import defaultdict, OrderedDict
from datetime import datetime
from textwrap import dedent
from io import StringIO
import re
import os 
import json
import urllib.request

try:
	from lxml import etree
	from lxml.etree import Element, SubElement
except:
	import xml.etree.ElementTree as etree
	from xml.etree.ElementTree import Element, SubElement

pjoin = os.path.join


schemas = {
	'config': "http://apertium.org/xml/quality/config/0.1",
	'corpus': "http://apertium.org/xml/corpus/0.1",
	'statistics': "http://apertium.org/xml/quality/statistics/0.9"
}

class ParseError(Exception):
	"""Exception for parsing errors."""
	pass

def from_isoformat(t):
	"""Converts time from ISO-8601 string to datetime object"""
	return datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%f")


class Statistics(object):
	ns = "{%s}" % schemas['statistics']
	
	@staticmethod
	def node_equal(a, b):
		return a.tag == b.tag and a.attrib == b.attrib
	
	def __init__(self, f=None):
		self.elements = {
			"general": self.get_general,
			"generation": self.get_generation,
			"regression": self.get_regression,
			"coverage": self.get_coverage,
			"ambiguity": self.get_ambiguity,
			"morph": self.get_morph,
			"vocabulary": lambda x, y: None
		}
		
		if f is None:
			return
		self.f = f
		
		if os.path.exists(f):
			self.tree = etree.parse(open(f, 'rb'))
			if self.tree.getroot().tag == Statistics.ns + "statistics":
				self.root = self.tree.getroot()
			else:
				raise ParseError("File does not seem to be a statistics file.")
		else:
			kwargs = {}
			if etree.__name__ == "lxml.etree":
				kwargs['nsmap'] = {None: schemas['statistics']}
			else:
				kwargs["xmlns"] = schemas['statistics']
			
			self.root = Element(Statistics.ns + "statistics", **kwargs)
			self.tree = etree.ElementTree(self.root)
	
	def write(self):
		try: 
			self.tree.write(self.f, encoding="utf-8", xml_declaration=True)
		except:
			f = open(self.f, 'w')
			f.write("<?xml version='1.0' encoding='utf-8'?>\n")
			f.write(etree.tostring(self.tree.getroot()))
			f.close()
		
	def add(self, parent, xml):
		ns = self.ns
		if parent not in self.elements:
			raise AttributeError("Element '%s' not supported." % parent)
		
		# Get new node, fix namespace prefix
		old_node = None
		new_node = etree.fromstring(xml)
		if not new_node.tag.startswith(ns):
			new_node.tag = ns + new_node.tag
		
		# If parent node doesn't exist, create it
		parent_node = self.root.find(ns + parent)
		if parent_node is None: 
			parent_node = SubElement(self.root, ns + parent)
		
		# Try to find an equal node for second level node
		for i in parent_node.getiterator(new_node.tag):
			if self.node_equal(new_node, i):
				old_node = i
				break
	
		if old_node is None:
			parent_node.append(new_node)
			return
		
		# Try to find an equal node for third level node
		rev_node = new_node.find("revision")	
		for i in old_node.getiterator(rev_node.tag):
			a = i.attrib.get("value")
			b = rev_node.attrib.get("value")
			if not None in (a, b) and a == b:
				i = rev_node # Overwrite old data
				return
		
		# Else append as no override required
		old_node.append(new_node.find("revision"))

	def get(self, tag):
		if not tag in self.elements:
			raise AttributeError("Element not supported.")
		
		root = self.root.find(self.ns + tag)
		if root is None:
			return dict()
		
		return self.elements[tag](root)

	def get_raphael(self, tag, data, lines1, lines2, x=None):
		"""Get output suitable for JSONing for Raphael charts"""
		out = {}
		dat = self.get(tag)
		
		for key, val in dat.items():
			out[key] = defaultdict(list)
			
			for k, v in val.items():
				if len(out[key]) == 0 or out[key].get('data')[-1] != v[data]:
					j = None
					if x: j = v.get(x)
					
					out[key]['labels'].append(j or k)
					out[key]['data'].append(v[data])
					out[key]['lines1'].append("%s: %s" % (lines1, v[lines1]))
					out[key]['lines2'].append("%s: %s" % (lines2, v[lines2]))
		
		return out			

	def get_general(self, root):
		dicts = defaultdict(dict)
		
		for d in root.getiterator(self.ns + "dictionary"):
			dct = d.attrib['value']
			for rev in d.getiterator(self.ns + 'revision'):
				r = rev.attrib['value']
				
				dicts[dct][r] = {
					"Timestamp": rev.attrib['timestamp'],
					"Entries": rev.find(self.ns + "entries").text,
					"Unique entries": rev.find(self.ns + "unique-entries").text,
					"Rules": rev.find(self.ns + "rules").text
				}
		
		out = dict()
		for k, v in dicts.items():
			out[k] = OrderedDict(sorted(v.items()))

		return out
	
	def get_generation(self, root):
		generations = defaultdict(dict)
		
		for d in root.getiterator(self.ns + "dictionary"):
			dct = d.attrib["value"]
			for rev in d.getiterator(self.ns + "revision"):
				r = rev.attrib["value"]
				c = rev.find("corpus")
				
				generations[dct][r] = {
					"Timestamp": rev.attrib["timestamp"],
					"Corpus": "%s__%s" % (c.attrib["value"], c.attrib["checksum"]),
					"Total": rev.find(self.ns + "total").text,
					"Multiform": rev.find(self.ns + "multiform").text,
					"Multibidix": rev.find(self.ns + "multibidix").text,
					"Tag mismatch": rev.find(self.ns + "tagmismatch").text
				}
		
		out = dict()
		for k, v in generations.items():
			out[k] = OrderedDict(sorted(v.items()))

		return out

	def get_regression(self, root):
		regressions = defaultdict(dict)
		
		for d in root.getiterator(self.ns + "title"):
			title = d.attrib['value']
			for rev in d.getiterator(self.ns + 'revision'):
				r = rev.attrib['value']
				
				regressions[title][r] = {
					"Timestamp": rev.attrib['timestamp'],
					"Percent": rev.find(self.ns + "percent").text,
					"Total": rev.find(self.ns + "total").text,
					"Passes": rev.find(self.ns + "passes").text,
					"Fails": rev.find(self.ns + "fails").text
				}

		out = dict()
		for k, v in regressions.items():
			out[k] = OrderedDict(sorted(v.items()))

		return out
	
	def get_coverage(self, root):	
		coverages = defaultdict(dict)	
		for d in root.getiterator(self.ns + "dictionary"):
			dct = d.attrib["value"]
			for rev in d.getiterator(self.ns + "revision"):
				
				r = rev.attrib['value']
				c = rev.find(self.ns + "corpus")
			
				coverages[dct][r] = OrderedDict({
					"Checksum": rev.attrib["checksum"],
					"Timestamp": rev.attrib['timestamp'],
					"Corpus": "%s__%s" % (c.attrib["value"], c.attrib["checksum"]),
					"Percent": rev.find(self.ns + "percent").text,
					"Total": rev.find(self.ns + "total").text,	
					"Known": rev.find(self.ns + "known").text,	
					"Unknown": rev.find(self.ns + "unknown").text,
					#'':'',
					#"Top words:": ''#OrderedDict()
				})
			#for j in i.find("top").getiterator("word"):
			#	coverages[dct][rev][j.text] = j.attrib["count"]
			##for j in i.find("top").getiterator("word"):
			##	coverages[dct][rev]['top'][j.text] = j.attrib["count"]

		out = dict()
		for k, v in coverages.items():
			out[k] = OrderedDict(sorted(v.items()))

		return out

	def get_ambiguity(self, root):
		ambiguities = defaultdict(dict)
		
		for d in root.getiterator(self.ns + "dictionary"):
			dct = d.attrib["value"]
			for rev in d.getiterator(self.ns + "revision"):
				
				r = rev.attrib['value']

				ambiguities[dct][r] = {
					"Checksum": rev.attrib["checksum"],
					"Timestamp": rev.attrib['timestamp'],
					"Surface forms": rev.find(self.ns + "surface-forms").text,
					"Analyses": rev.find(self.ns + "analyses").text,
					"Average": rev.find(self.ns + "average").text
				}

		out = dict()
		for k, v in ambiguities.items():
			out[k] = OrderedDict(sorted(v.items()))

		return out	

	def get_morph(self, root):
		morphs = defaultdict(dict)
		
		for d in root.getiterator(self.ns + "config"):
			cfg = d.attrib["value"]
			for rev in d.getiterator(self.ns + "revision"):
				
				r = rev.attrib['value']
				g = rev.find(self.ns + "gen")
				m = rev.find(self.ns + "morph")
			
				morphs[cfg][r] = {
					"Checksum": rev.attrib["checksum"],
					"Timestamp": rev.attrib['timestamp'],
					"Gen": "%s__%s" % (g.attrib['value'], g.attrib["checksum"]),
					"Morph": "%s__%s" % (m.attrib['value'], m.attrib["checksum"]),
					'':'',
					#"Tests": OrderedDict(),
					"Total": rev.find(self.ns + "total").text,
					"Passes": rev.find(self.ns + "passes").text,
					"Fails": rev.find(self.ns + "fails").text
				}
			
			#for j in i.find("tests").getiterator("test"):
			#	hfsts[cfg][rev]['tests'][j.text] = {
			#		"passes": j.attrib['passes'], 
			#		"fails": j.attrib['fails']
			#	}

		out = dict()
		for k, v in morphs.items():
			out[k] = OrderedDict(sorted(v.items()))

		return out
