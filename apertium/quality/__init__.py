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

try:
	from lxml import etree
	from lxml.etree import Element, SubElement
except:
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
	space = re.compile('[ /:\n]')
	
	def __init__(self, stats, fdir, title):
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
		self.title = title

	def generate(self):
		footer = "Generated: %s" % datetime.utcnow().strftime("%Y-%m-%d %H:%M (UTC)")
		divs = []
		divs.append(self.generate_regressions())
		divs.append(self.generate_coverages())
		divs.append(self.generate_ambiguities())
		divs.append(self.generate_hfsts())
		# others
		out = self.base.render(dirname=self.title, divs=divs, footer=footer)
		
		f = open(pjoin(self.fdir, "index.html"), 'w')
		f.write(out)
		f.close()
		
		f = open(pjoin(self.fdir, "style.css"), 'w')
		f.write(css)
		f.close()
		
		f = open(pjoin(self.fdir, "stats.js"), 'w')
		f.write(js)
		f.close()
		
	def generate_regressions(self):
		images = self.plot_regressions()
		
		divs = []
		stat_type = "regression"
		data = self.stats.get(stat_type)
		stat_type_title = "Regression Tests"
		
		for cfg, rev in data.items():
			tsk = list(rev.keys())
			first = tsk[0]
			last = tsk[-1]
			
			avg = 0.0
			for i in rev.values():
				avg += float(i['Percent'])
			avg /= float(len(rev))
			
			gen_stats = {
				"First test": first,
				"Last test": last,
				"Average": avg
			}
			
			stat_title_human, stat_cksum = cfg, last
			stat_title = self.space.sub('_', stat_title_human.lower())
			general = self.generaldiv.render(stat_title=stat_title, stat_type=stat_type, gen_stats=gen_stats)
			chrono = self.chronodiv.render(stat_title=stat_title, stat_type=stat_type, chrono_stats=rev)
			stats = self.statdiv.render(stat_title_human=stat_title_human, stat_title=stat_title, stat_type=stat_type, 
									stat_cksum=stat_cksum, chrono=chrono, general=general, images=images)
			divs.append(stats)
		
		return self.statblock.render(stat_type=stat_type, stat_type_title=stat_type_title, divs=divs)
			
	def generate_coverages(self):
		images = self.plot_coverage()
		
		divs = []
		stat_type = "coverage"
		data = self.stats.get(stat_type)
		stat_type_title = "Coverage Tests"
		
		for cfg, rev in data.items():
			tsk = list(rev.keys())
			first = tsk[0]
			last = tsk[-1]
			
			avg = 0.0
			for i in rev.values():
				avg += float(i['Percent'])
			avg /= float(len(rev))
			
			gen_stats = {
				"First test": first,
				"Last test": last,
				"Average": avg
			}
			
			stat_title_human, stat_cksum = cfg, last
			stat_cksum = stat_cksum.upper()
			stat_title = self.space.sub('_', stat_title_human.lower())
			general = self.generaldiv.render(stat_title=stat_title, stat_type=stat_type, gen_stats=gen_stats)
			chrono = self.chronodiv.render(stat_title=stat_title, stat_type=stat_type, chrono_stats=rev)
			stats = self.statdiv.render(stat_title_human=stat_title_human, stat_title=stat_title, stat_type=stat_type, 
									stat_cksum=stat_cksum, chrono=chrono, general=general, images=images)
			divs.append(stats)
		
		return self.statblock.render(stat_type=stat_type, stat_type_title=stat_type_title, divs=divs)
	
	def generate_ambiguities(self):
		images = []#self.plot_regressions()
		
		divs = []
		stat_type = "ambiguity"
		data = self.stats.get(stat_type)
		stat_type_title = "Ambiguity Tests"
		
		for cfg, rev in data.items():
			tsk = list(rev.keys())
			first = tsk[0]
			last = tsk[-1]
			
			avg = 0.0
			for i in rev.values():
				avg += float(i['Average'])
			avg /= float(len(rev))
			
			gen_stats = {
				"First test": first,
				"Last test": last,
				"Overall average": avg
			}
			
			stat_title_human, stat_cksum = cfg, last
			stat_cksum = stat_cksum.upper()
			stat_title = self.space.sub('_', stat_title_human.lower())
			general = self.generaldiv.render(stat_title=stat_title, stat_type=stat_type, gen_stats=gen_stats)
			chrono = self.chronodiv.render(stat_title=stat_title, stat_type=stat_type, chrono_stats=rev)
			stats = self.statdiv.render(stat_title_human=stat_title_human, stat_title=stat_title, stat_type=stat_type, 
									stat_cksum=stat_cksum, chrono=chrono, general=general, images=images)
			divs.append(stats)
		
		return self.statblock.render(stat_type=stat_type, stat_type_title=stat_type_title, divs=divs)
	
	def generate_hfsts(self):
		images = []#self.plot_regressions()
		
		divs = []
		stat_type = "morph"
		data = self.stats.get(stat_type)
		stat_type_title = "Morph (HFST) Tests"
		
		for cfg, rev in data.items():
			tsk = list(rev.keys())
			first = tsk[0]
			last = tsk[-1]
			
			gen_stats = {
				"First test": first,
				"Last test": last
			}
			
			stat_title_human, stat_cksum = cfg, last
			stat_cksum = stat_cksum.upper()
			stat_title = self.space.sub('_', stat_title_human.lower())
			general = self.generaldiv.render(stat_title=stat_title, stat_type=stat_type, gen_stats=gen_stats)
			chrono = self.chronodiv.render(stat_title=stat_title, stat_type=stat_type, chrono_stats=rev)
			stats = self.statdiv.render(stat_title_human=stat_title_human, stat_title=stat_title, stat_type=stat_type, 
									stat_cksum=stat_cksum, chrono=chrono, general=general, images=images)
			divs.append(stats)
		
		return self.statblock.render(stat_type=stat_type, stat_type_title=stat_type_title, divs=divs)
	
	# coverage over time
	# number of rules over time
	# mean ambiguity over time
	# number of dict entries over time
	# translation speed over time
	# WER/PER/BLEU over time
	# percentage of regression tests passed over time 
	
	'''def plot_coverages(self):
		data = self.stats.get_coverages()
		out = []
		
		def coverage_over_time(title, data):
			plt.title(title)
			plt.xlabel("Time")
			plt.ylabel("Coverage (%)")
	'''		
			
			
	def plot_coverage(self):
		coverage = self.stats.get('coverage')
		out = []
		
		for dictionary, revisions in coverage.items():
			title = "%s\n%s" % (dictionary, "Coverage Percentage Over Time")
			
			plt.title(title)
			plt.xlabel("Revision")
			plt.ylabel("Coverage (%)")
			
			x = list(revisions.keys())
			y = [ i['Percent'] for i in revisions.values() ]
			
			x.insert(0, 0)
			y.insert(0, 0)
			
			plt.plot(x, y)
			plt.ylim(ymin=0, ymax=100)
			plt.xlim(xmin=int(x[1]), xmax=int(x[-1]))
			
			png = "%s.png" % self.space.sub('_', title)
			plt.savefig(pjoin(self.fdir, png))
			out.append(png)
			plt.clf()
		return out
		
	def plot_regressions(self):
		#def 
		
		out = []
		regs = self.stats.get('regression')
		
		for title, reg in regs.items():
			t = "%s\n%s" % (title, "Passes Over Time")
			plt.title(t)
			plt.xlabel('Revision')
			plt.ylabel('Passes (%)')
			
			x = list(reg.keys())
			x.insert(0, 0)
			
			y = [[0], [0], [0], [0]]
			
			for rev, vals in reg.items():
				y[0].append(vals['Percent'])
				y[1].append(vals['Total'])
				y[2].append(vals['Passes'])
				y[3].append(vals['Fails'])

			plt.plot(x, y[0])
			plt.ylim(ymin=0, ymax=100)
			plt.xlim(xmin=int(x[1]), xmax=int(x[-1]))
			png = "%s.png" % self.space.sub('_', t)
			plt.savefig(pjoin(self.fdir, png))
			out.append(png)
			plt.clf()

			t = "%s\n%s" % (title, "Statistics")
			plt.title(t)
			plt.ylabel('Passes (Green) - Fails (Red)')

			plt.plot(x, y[1], 'b', x, y[2], 'g', x, y[3], 'r')
			plt.xlim(xmin=int(x[1]), xmax=int(x[-1]))
			png = "%s.png" % self.space.sub('_', t)
			plt.savefig(pjoin(self.fdir, png))
			out.append(png)
			plt.clf()
		return out
	
	

class Statistics(object):
	version = "0.1"
	type = "apertium"
	xmlns = "http://apertium.org/xml/statistics/0.1"
	ns = "{%s}" % xmlns
	
	@staticmethod
	def node_equal(a, b):
		return a.tag == b.tag and a.attrib == b.attrib
	
	def __init__(self, f=None):
		self.elements = {
			"general": self.get_general,
			"regression": self.get_regression,
			"coverage": self.get_coverage,
			"ambiguity": self.get_ambiguity,
			"morph": self.get_morph
		}
		
		if f is None:
			return
		self.f = f
		
		if os.path.exists(f):
			try:
				self.tree = etree.parse(open(f, 'rb'))
				if self.tree.getroot().tag == Statistics.ns + "statistics":
					#if self.tree.getroot().get('version') == "1.0":	
						#print "[STUB] Do version specific crap here for 1.0"
					#else:
						#pass
						#print "[DEBUG] Version incorrect."
					self.root = self.tree.getroot()
					#print "[DEBUG] Imported tree."
				else:
					raise ParseError("File does not seem to be a statistics file.")
			except:
				raise
		else:
			kwargs = {
				"type": Statistics.type,
				"version": Statistics.version
			}
			if etree.__name__ == "lxml.etree":
				kwargs['nsmap'] = {None: Statistics.xmlns}
			else:
				kwargs["xmlns"] = Statistics.xmlns
			
			self.root = Element(Statistics.ns + "statistics", **kwargs)
			self.tree = etree.ElementTree(self.root)
	
	def write(self):
		self.tree.write(self.f, encoding="utf-8", xml_declaration=True)

	def add(self, parent, xml):
		ns = self.ns
		if parent not in self.elements:
			raise AttributeError("Element not supported.")
		
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
		
		out = defaultdict(dict)
		return self.elements[tag](root)

	def get_general(self, root):
		return dict() # stub
	
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

css = """
* {
  margin: 0;
  padding: 0; }

html {
  overflow-y: scroll; }

body {
  background-color: #585858; }

a {
  color: #4183c4;
  text-decoration: none; }

a:hover {
  text-decoration: underline; }

a:active {
  outline: none; }

#container {
  width: 800px;
  text-align: center;
  margin: 0 auto; }

div.minimal {
  font-family: sans-serif;
  text-align: justify;
  font-size: 10pt;
  background-color: #f8f8f8;
  border: 1px solid #e9e9e9;
  padding: 1.2em; }
  div.minimal p.info {
    margin: 0 0 15px 0;
    padding: 10px;
    padding-left: 40px;
    font-size: 12px;
    color: #333;
    background: #fbfff4;
    background-image: url("info.png");
    background-position: 8px 45%;
    background-repeat: no-repeat;
    border: 1px solid #dddddd; }
  div.minimal p.warning {
    margin: 0 0 15px 0;
    padding: 10px;
    padding-left: 40px;
    font-size: 12px;
    color: #333;
    background: #fff4fb;
    background-image: url("warning.png");
    background-position: 8px 45%;
    background-repeat: no-repeat;
    border: 1px solid #dddddd;
    font-weight: bold; }
  div.minimal h1 {
    font-size: 170%;
    border-top: 4px solid #999999;
    padding-top: 0.5em; }
  div.minimal h2 {
    font-size: 150%;
    margin-top: 1.5em;
    margin-bottom: 15px;
    border-top: 4px solid #dddddd;
    padding-top: 0.5em; }
  div.minimal h3 {
    margin-top: 1em;
    margin-bottom: 0.5em;
    border-bottom: 1px solid #dddddd; }
  div.minimal h4, div.minimal h5, div.minimal h6 {
    margin-top: 0.4em; }
  div.minimal p {
    margin: 1em 0;
    line-height: 1.5em; }
  div.minimal ul {
    margin: 1em 0 1em 1em; }
  div.minimal ol {
    margin: 1em 0 1em 1.5em; }
  div.minimal blockquote {
    margin: 1em 0;
    border-left: 5px solid #dddddd;
    padding-left: 0.6em;
    color: #555; }
  div.minimal table {
    margin: 1em 0; }
    div.minimal table th {
      border-bottom: 1px solid #999999;
      padding: 0.2em 1em; }
    div.minimal table td {
      border-bottom: 1px solid #dddddd;
      padding: 0.2em 1em; }
  div.minimal pre {
    font-family: "Bitstream Vera Sans Mono", "DejaVu Sans Mono", "Menlo", monospace;
    font-size: 90%;
    background-color: #f8f8ff;
    color: #444;
    padding: 0 0.5em;
    border: 1px solid #dedede;
    overflow-x: scroll;
    margin: 1em 0;
    line-height: 1.5em; }
  div.minimal code {
    font-family: "Bitstream Vera Sans Mono", "DejaVu Sans Mono", "Menlo", monospace;
    font-size: 90%;
    background-color: #f8f8ff;
    color: #444;
    padding: 0 0.2em;
    border: 1px solid #dedede; }
  div.minimal pre.console {
    margin: 1em 0;
    font-size: 90%;
    background-color: #333333;
    padding: 0.5em;
    line-height: 1.5em;
    color: #999999; }
    div.minimal pre.console span.command {
      color: #dddddd; }
"""

js = """function toggle(id)
{
	var div = document.getElementById(id);
	
	if (div.style.display == 'block') {
		div.style.display = 'none';
	}
	else {
		div.style.display = 'block';
	}
}

function init() 
{
	var cdivs = document.getElementsByClassName("cdiv");
	for (var i = 0; i < cdivs.length; ++i) {
		cdivs[i].style.display = "none";
	}
}

window.addEventListener("load", init, false);
"""

base = """<!DOCTYPE html>
<html>
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
	<title>Statistics - ${dirname}</title>
	<script type="application/javascript" src="stats.js"></script>
  	<link rel="stylesheet" href="style.css" type="text/css" />
</head>

<body>
<div id="container" class="minimal">

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

</div>
</body>
</html>
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
				% for c, date in enumerate(reversed(list(chrono_stats.keys()))):
					<li>
						<a href="javascript:toggle('${stat_type}-${stat_title}-chrono-${c}-div')">${date}</a>
						<div class="cdiv" id="${stat_type}-${stat_title}-chrono-${c}-div">
							<table>
							% for k, v in chrono_stats[date].items():
								<% 
								if "percent" in k.lower():
									v = "%s%%" % v
								elif "__" in v:
									tmp = v.rsplit('__', 1)
									v = "%s (%s)" % (tmp[0], tmp[1].upper())
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