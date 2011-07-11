try:
	import matplotlib
	matplotlib.use('Agg') # stops it from using X11 and breaking
	import matplotlib.pyplot as plt
except:
	matplotlib = None

try:
	from mako.template import Template
	from mako.lookup import TemplateLookup
except:
	Template = None
	TemplateLookup = None

import xml.etree.ElementTree as etree
from xml.etree.ElementTree import Element, SubElement

from collections import defaultdict, OrderedDict
import re, os
pjoin = os.path.join
from io import StringIO
from textwrap import dedent

from datetime import datetime

class ParseError(Exception):
	pass

def from_isoformat(t):
	return datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%f")


class Webpage(object):
	#ns = "{http://www.w3.org/1999/xhtml}"
	space = re.compile('[ /:]')
	
	def __init__(self, stats, fdir):
		if not matplotlib:
			raise ImportError("matplotlib not installed.")
		if not Template or not TemplateLookup:
			raise ImportError("mako not installed.")
		
		self.base = Template(base)
		self.statblock = Template(statblock)
		self.statdiv = Template(statdiv)
		self.generaldiv = Template(generaldiv)
		self.chronodiv = Template(chronodiv)
		
		#if not isinstance(stats, Statistics):
		#	raise TypeError("Input must be Statistics object.")
		self.stats = stats
		try: os.makedirs(fdir)
		except: pass
		self.fdir = fdir

	def generate(self):
		footer = "<p>TIME GOES HERE</p>"
		divs = []
		divs.append(self.generate_regressions())
		# others
		out = self.base.render(dirname="DIRNAME", divs=divs, footer=footer)
		
		f = open(pjoin(self.fdir, "index.html"), 'w')
		f.write(out)
		f.close()
		
		f = open(pjoin(self.fdir, "style.css"), 'w')
		f.write(css)
		f.close()
		
	def generate_regressions(self):
		data = self.stats.get_regressions()
		images = self.plot_regressions()
		
		divs = []
		stat_type = "regressions"
		stat_type_title = "Regression Tests"
		
		for k, v in data.items():
			stat_title_human, stat_cksum = k.rsplit("__", 1)
			stat_title = self.space.sub('_', stat_title_human
			general = self.generaldiv.render(stat_title_human=stat_title_human, stat_title=stat_title, stat_type=stat_type, gen_stats={"Stub": "True!"})
			chrono = self.chronodiv.render(stat_title=stat_title, stat_type=stat_type, chrono_stats=v)
			stats = self.statdiv.render(stat_title=stat_title, stat_type=stat_type, stat_cksum=stat_cksum, 
									chrono=chrono, general=general, images=images)
			divs.append(stats)
		
		return self.statblock.render(stat_type=stat_type, stat_type_title=stat_type_title, divs=divs)
			
	def generate_coverages(self):
		data = self.stats.get_coverages()
	
	def generate_ambiguities(self):
		data = self.stats.get_ambiguities()
	
	def generate_hfsts(self):
		data = self.stats.get_hfsts()

	def plot_regressions(self):
		out = []
		regs = self.stats.get_regressions()
		for title, reg in regs.items():
			t = "%s - %s" % (title, "Passes")
			plt.title(t)
			plt.xlabel('Test ID')
			plt.ylabel('Passes (%)')
			
			x = range(len(reg))
			y = [[], [], [], []]
			
			for ts, vals in reg.items():
				y[0].append(vals['Percent'])
				y[1].append(vals['Total'])
				y[2].append(vals['Passes'])
				y[3].append(vals['Fails'])

			plt.plot(x, y[0])
			png = "%s.png" % self.space.sub('_', t)
			plt.savefig(pjoin(self.fdir, png))
			out.append(png)
			plt.clf()

			t = "%s - %s" % (title, "Statistics")
			plt.title(t)
			plt.ylabel('Quantity')

			plt.plot(x, y[1], 'b', x, y[2], 'g', x, y[3], 'r')
			png = "%s.png" % self.space.sub('_', t)
			plt.savefig(pjoin(self.fdir, png))
			out.append(png)
			plt.clf()
		return out


class Statistics(object):
	file_version = "1.0"
	file_type = "apertium"

	elements = {
		#element: parents,
		"ambiguity": "ambiguities",
		"hfst": "hfsts",
		"regression": "regressions",
		"coverage": "coverages"
	}
	
	def __init__(self, f=None):
		if f is None:
			return
		
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

	def add(self, xml):
		el = etree.XML(xml)
		parent = self.elements.get(el.tag, None)
		if parent is None:
			raise AttributeError("Element not supported.")
		
		root = self.root.find(parent)
		if root is None:
			root = SubElement(self.root, parent)		
		root.append(el)

	def get_regressions(self):
		root = self.root.find('regressions')
		if root is None:
			return dict()
		regressions = defaultdict(dict)
		
		for i in root.getiterator("regression"):
			ts = from_isoformat(i.attrib['timestamp'])
			t = i.find("title")
			title = "%s__%s" % (t.text, t.attrib["revision"])
			regressions[title][ts] = {
				"Percent": i.find("percent").text,
				"Total": i.find("total").text,
				"Passes": i.find("passes").text,
				"Fails": i.find("fails").text
			}

		out = dict()
		for k, v in regressions.items():
			out[k] = OrderedDict(sorted(v.items()))

		return out
	
	def get_coverages(self):
		root = self.root.find('coverages')
		if root is None:
			return dict()
		coverages = defaultdict(dict)
		
		for i in root.getiterator("coverage"):
			ts = from_isoformat(i.attrib['timestamp'])
			d = i.find("dictionary")
			dct = "%s__%s" % (d.text, d.attrib["checksum"])
			
			c = i.find("corpus")
			
			coverages[dct][ts] = {
				"Corpus": "%s__%s" % (c.text, c.attrib["checksum"]),
				"Percent": i.find("percent").text,
				"total": i.find("total").text,	
				"known": i.find("known").text,	
				"unknown": i.find("unknown").text,
				"top": OrderedDict()
			}

			for j in i.find("top").getiterator("word"):
				coverages[dct][ts]['top'][j.text] = j.attrib["count"]

		out = dict()
		for k, v in coverages.items():
			out[k] = OrderedDict(sorted(v.items()))

		return out

	def get_ambiguities(self):
		root = self.root.find('ambiguities')
		if root is None:
			return dict()
		ambiguities = defaultdict(dict)
		
		for i in root.getiterator("ambiguity"):
			ts = from_isoformat(i.attrib['timestamp'])
			d = i.find("dictionary")
			dct = "%s__%s" % (d.text, d.attrib["checksum"])
			
			ambiguities[dct][ts] = {
				"surface-forms": i.find("surface-forms").text,
				"analyses": i.find("analyses").text,
				"average": i.find("average").text
			}

		out = dict()
		for k, v in ambiguities.items():
			out[k] = OrderedDict(sorted(v.items()))

		return out	

	def get_hfsts(self):
		root = self.root.find('hfsts')
		if root is None:
			return dict()
		ambiguities = defaultdict(dict)
		
		for i in root.getiterator("hfst"):
			ts = from_isoformat(i.attrib['timestamp'])
			c = i.find("config")
			cfg = "%s__%s" % (c.text, c.attrib["checksum"])
			
			g = i.find("gen")
			m = i.find("morph")
			
			ambiguities[cfg][ts] = {
				"gen": "%s__%s" % (g.text, g.attrib["checksum"]),
				"morph": "%s__%s" % (m.text, m.attrib["checksum"]),
				
				"tests": OrderedDict(),
				"total": i.find("total").text,
				"passes": i.find("passes").text,
				"fails": i.find("fails").text
			}
			
			for j in i.find("tests").getiterator("test"):
				ambiguities[cfg][ts]['tests'][j.text] = {
					"passes": j.attrib['passes'], 
					"fails": j.attrib['fails']
				}

		out = dict()
		for k, v in ambiguities.items():
			out[k] = OrderedDict(sorted(v.items()))

		return out	

css = """
* {
  border: 0;
  padding: 0; }

body {
  background-color: #777777; }

div {
  border: 1px solid black;
  margin: 1em; }

h1 {
  margin: 0;
  padding: 0;
  margin-top: 0.5em;
  margin-left: 0.5em;
  font-variant: small-caps; }

table {
  border-collapse: collapse; }

/*table, th, td {
	border: 1px solid black;
}*/
div#container {
  padding: 0;
  margin: 0 auto;
  width: 100%; }

div#header, div#footer {
  margin-top: 1em;
  margin-bottom: 1em;
  margin-left: 0.5em;
  margin-right: 0.5em;
  /*border-radius: $radius;
  -moz-border-radius: $radius;
  -webkit-border-radius: $radius;*/
  background-color: white; }
  div#header h1, div#footer h1 {
    margin-top: 6px; }

div.s-container {
  background-color: white;
  border: 1px solid black;
  margin-top: 1em;
  margin-bottom: 1em;
  margin-left: 0.5em;
  margin-right: 0.5em;
  /*border-radius: $radius;
  -moz-border-radius: $radius;
  -webkit-border-radius: $radius;*/
  clear: both; }
  div.s-container div.s-stats {
    margin: 0;
    padding: 0; }
    div.s-container div.s-stats h1 {
      font-size: 16pt; }
    div.s-container div.s-stats hr {
      clear: both;
      border: 0;
      margin: 0;
      padding: 0; }
    div.s-container div.s-stats div.s-imgs img {
      width: 267px;
      height: 200px;
      border: 1px solid black;
      margin: 1em; }
    div.s-container div.s-stats div.s-data h1 {
      font-size: 14pt; }
    div.s-container div.s-stats div.s-data div.s-general {
      float: left;
      margin-right: 0;
      width: 47.75%; }
      div.s-container div.s-stats div.s-data div.s-general table {
        margin: 1em; }
        div.s-container div.s-stats div.s-data div.s-general table tr td {
          padding-left: 0.5em;
          padding-right: 0.5em;
          text-align: right; }
        div.s-container div.s-stats div.s-data div.s-general table tr td:nth-child(2) {
          text-align: left; }
    div.s-container div.s-stats div.s-data div.s-chrono {
      float: right;
      margin-left: 0;
      width: 47.75%; }
      div.s-container div.s-stats div.s-data div.s-chrono ul li {
        margin-left: 2em; }
        div.s-container div.s-stats div.s-data div.s-chrono ul li div {
          margin-left: -1em;
          padding: 6px; }
          div.s-container div.s-stats div.s-data div.s-chrono ul li div table {
            margin: 1em; }
            div.s-container div.s-stats div.s-data div.s-chrono ul li div table tr td {
              padding-left: 0.5em;
              padding-right: 0.5em;
              text-align: right; }
            div.s-container div.s-stats div.s-data div.s-chrono ul li div table tr td:nth-child(2) {
              text-align: left; }
"""

base = """
<html>
<head>
	<title>Statistics - ${dirname}</title>
	<!--<script type="application/javascript" src="js"></script>-->
  	<link rel="stylesheet" href="style.css" type="text/css" />
</head>

<body>

<div id="header">
	<h1>${dirname}</h1>
</div>

<!-- divs gonna div -->
% for div in divs:
${div}
% endfor

<div id="footer">
	${footer}
</div>

</body>
"""

statblock = """
<div id="${stat_type}" class="s-container">
	<h1>${stat_type_title}</h1>
	
	% for div in divs:
	${div}
	% endfor
</div>
"""

statdiv = """
	<div id="${stat_type}-${stat_title}" class="s-stats">
		<h1>${stat_title_human}</h1>
		<h2>${stat_cksum}</h2>
		<div id="${stat_type}-${stat_title}-imgs" class="s-imgs">
			% for src in images:
			<a href="${src}"><img src="${src}" /></a>
			% endfor
		</div>
	
		<div id="${stat_type}-${stat_title}-data" class="s-data">

			${general}
			
			${chrono}

			<hr />
		</div>
	</div>
"""

generaldiv = """
			<div id="${stat_type}-${stat_title}-general" class="s-general">
				<h1>General Statistics</h1>
				<table>
				% for left, right in gen_stats.items():
				<tr>
					<td>${left}:</td>
					<td>${right}</td>
				</tr>
				% endfor
				</table>
			</div>
"""

chronodiv = """
			<div id="${stat_type}-${stat_title}-chrono" class="s-chrono">
				<h1>Chronological Statistics</h1>
				<ul>
				% for date in reversed(chrono_stats):
					<li>
						<a href="#" id="${date}">${date}</a>
						<div id="${date}-div">
							<table>
							% for k, v in chrono_stats[date].items():
								<% 
								if "percent" in k.lower():
									v = "%s%%" % v
								%>
								<tr>
									<td>${k}</td>
									<td>${v}</td>
								</tr>
							% endfor
							</table>
						</div>
					</li>
				% endfor
				</ul>
			</div>
"""