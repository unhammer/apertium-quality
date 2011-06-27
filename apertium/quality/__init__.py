try:
	import matplotlib
	matplotlib.use('Agg') # stops it from using X11 and breaking
	import matplotlib.pyplot as plt
except:
	matplotlib = None

import xml.etree.cElementTree as etree
import re, os

from collections import defaultdict, OrderedDict
from io import StringIO
from textwrap import dedent
from xml.etree.cElementTree import Element, SubElement
from datetime import datetime

class ParseError(Exception):
	pass

def from_isoformat(t):
	return datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%f")


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
		if not matplotlib:
			raise ImportError("matplotlib not installed.")
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
				self.tree = etree.parse(open(f, 'rb'))
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
		s.text = str(title)
		s.attrib['revision'] = str(revision)
		
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
			title = "%s/%s" % (t.text, t.attrib["revision"])
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
		s.text = str(f)
		s.attrib["checksum"] = str(fck)
		
		s = SubElement(r, 'dictionary')
		s.text = str(df)
		s.attrib["checksum"] = str(dck)
		
		SubElement(r, 'percent').text = str(cov)
		SubElement(r, 'total').text = str(words)
		SubElement(r, 'known').text = str(kwords)
		SubElement(r, 'unknown').text = str(ukwords)
		
		s = SubElement(r, 'top')
		for mot, num in topuw:
			e = SubElement(s, 'word', count=str(num))
			e.text = str(mot)
	
	'''def get_coverages(self):
		r = self.root.find('coverages')
		if not r:
			return dict()
		coverages = defaultdict(dict)
		
		for i in r.getiterator("coverage"):
			ts = from_isoformat(i.attrib['timestamp'])
			c = i.find("corpus").text
			ck = i.find("corpus").attrib["checksum"]
			corpus = "%s/%s" % (c, ck)
			
			coverages[corpus][ts] = {
				
			}

		out = dict()
		for k, v in coverages.items():
			out[k] = OrderedDict(sorted(v.items()))

		return out'''
		
	def add_ambiguity(self, f, fck, sf, a, avg):
		root = self.root.find('ambiguities')
		if not root:
			root = SubElement(self.root, 'ambiguities')
		r = SubElement(root, 'ambiguity', timestamp=datetime.utcnow().isoformat())
		
		s = SubElement(r, 'dictionary')
		s.text = str(f)
		s.attrib["checksum"] = str(fck)

		SubElement(r, 'surface-forms').text = str(sf)
		SubElement(r, 'analyses').text = str(a)
		SubElement(r, 'average').text = str(avg)

	def add_hfst(self, config, ck, gen, gk, morph, mk, tests, passes, fails):
		root = self.root.find('hfsts')
		if not root:
			root = SubElement(self.root, 'hfsts')
		r = SubElement(root, 'hfst', timestamp=datetime.utcnow().isoformat())
		
		s = SubElement(r, 'config')
		s.text = str(config)
		s.attrib["checksum"] = str(ck)
		
		s = SubElement(r, 'gen')
		s.text = str(gen)
		s.attrib["checksum"] = str(gk)
		
		s = SubElement(r, 'morph')
		s.text = str(morph)
		s.attrib["checksum"] = str(mk)
		
		s = SubElement(r, 'tests')
		for k, v in tests.items():
			t = SubElement(s, 'test')
			t.text = str(k)
			t.attrib['passes'] = str(v["Pass"])
			t.attrib['fails'] = str(v["Fail"])
		
		SubElement(r, 'total').text = str(passes + fails)
		SubElement(r, 'passes').text = str(passes)
		SubElement(r, 'fails').text = str(fails)
		