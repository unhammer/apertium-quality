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
		data = self.stats.get_regressions()
		images = self.plot_regressions()
		
		divs = []
		stat_type = "regression"
		stat_type_title = "Regression Tests"
		
		for cfg, ts in data.items():
			tsk = list(ts.keys())
			first = tsk[0].strftime("%Y-%m-%d %H:%M")
			last = tsk[-1].strftime("%Y-%m-%d %H:%M")
			
			avg = 0.0
			for i in ts.values():
				avg += float(i['Percent'])
			avg /= float(len(ts))
			
			gen_stats = {
				"First test": first,
				"Last test": last,
				"Average percent": "%s%%" % avg
			}
			
			stat_title_human, stat_cksum = cfg.rsplit("__", 1)
			stat_cksum = "Revision: %s" % stat_cksum
			stat_title = self.space.sub('_', stat_title_human.lower())
			general = self.generaldiv.render(stat_title=stat_title, stat_type=stat_type, gen_stats=gen_stats)
			chrono = self.chronodiv.render(stat_title=stat_title, stat_type=stat_type, chrono_stats=ts)
			stats = self.statdiv.render(stat_title_human=stat_title_human, stat_title=stat_title, stat_type=stat_type, 
									stat_cksum=stat_cksum, chrono=chrono, general=general, images=images)
			divs.append(stats)
		
		return self.statblock.render(stat_type=stat_type, stat_type_title=stat_type_title, divs=divs)
			
	def generate_coverages(self):
		data = self.stats.get_coverages()
		images = []#self.plot_regressions()
		
		divs = []
		stat_type = "coverage"
		stat_type_title = "Coverage Tests"
		
		for cfg, ts in data.items():
			tsk = list(ts.keys())
			first = tsk[0].strftime("%Y-%m-%d %H:%M")
			last = tsk[-1].strftime("%Y-%m-%d %H:%M")
			
			avg = 0.0
			for i in ts.values():
				avg += float(i['Percent'])
			avg /= float(len(ts))
			
			gen_stats = {
				"First test": first,
				"Last test": last,
				"Average percent": "%s%%" % avg
			}
			
			stat_title_human, stat_cksum = cfg.rsplit("__", 1)
			stat_cksum = stat_cksum.upper()
			stat_title = self.space.sub('_', stat_title_human.lower())
			general = self.generaldiv.render(stat_title=stat_title, stat_type=stat_type, gen_stats=gen_stats)
			chrono = self.chronodiv.render(stat_title=stat_title, stat_type=stat_type, chrono_stats=ts)
			stats = self.statdiv.render(stat_title_human=stat_title_human, stat_title=stat_title, stat_type=stat_type, 
									stat_cksum=stat_cksum, chrono=chrono, general=general, images=images)
			divs.append(stats)
		
		return self.statblock.render(stat_type=stat_type, stat_type_title=stat_type_title, divs=divs)
	
	def generate_ambiguities(self):
		data = self.stats.get_ambiguities()
		images = []#self.plot_regressions()
		
		divs = []
		stat_type = "ambiguity"
		stat_type_title = "Ambiguity Tests"
		
		for cfg, ts in data.items():
			tsk = list(ts.keys())
			first = tsk[0].strftime("%Y-%m-%d %H:%M")
			last = tsk[-1].strftime("%Y-%m-%d %H:%M")
			
			avg = 0.0
			for i in ts.values():
				avg += float(i['Average'])
			avg /= float(len(ts))
			
			gen_stats = {
				"First test": first,
				"Last test": last,
				"Overall average": avg
			}
			
			stat_title_human, stat_cksum = cfg.rsplit("__", 1)
			stat_cksum = stat_cksum.upper()
			stat_title = self.space.sub('_', stat_title_human.lower())
			general = self.generaldiv.render(stat_title=stat_title, stat_type=stat_type, gen_stats=gen_stats)
			chrono = self.chronodiv.render(stat_title=stat_title, stat_type=stat_type, chrono_stats=ts)
			stats = self.statdiv.render(stat_title_human=stat_title_human, stat_title=stat_title, stat_type=stat_type, 
									stat_cksum=stat_cksum, chrono=chrono, general=general, images=images)
			divs.append(stats)
		
		return self.statblock.render(stat_type=stat_type, stat_type_title=stat_type_title, divs=divs)
	
	def generate_hfsts(self):
		data = self.stats.get_hfsts()
		images = []#self.plot_regressions()
		
		divs = []
		stat_type = "morph"
		stat_type_title = "Morph (HFST) Tests"
		
		for cfg, ts in data.items():
			tsk = list(ts.keys())
			first = tsk[0].strftime("%Y-%m-%d %H:%M")
			last = tsk[-1].strftime("%Y-%m-%d %H:%M")
			
			#avg = 0.0
			#for i in ts.values():
			#	avg += float(i['Percent'])
			#avg /= float(len(ts))
			
			gen_stats = {
				"First test": first,
				"Last test": last#,
				#"Average percent": avg
			}
			
			stat_title_human, stat_cksum = cfg.rsplit("__", 1)
			stat_cksum = stat_cksum.upper()
			stat_title = self.space.sub('_', stat_title_human.lower())
			general = self.generaldiv.render(stat_title=stat_title, stat_type=stat_type, gen_stats=gen_stats)
			chrono = self.chronodiv.render(stat_title=stat_title, stat_type=stat_type, chrono_stats=ts)
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
			
			
	
	def plot_regressions(self):
		#def 
		
		out = []
		regs = self.stats.get_regressions()
		
		for title, reg in regs.items():
			t = "%s\n%s" % (title, "Passes over time")
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

			t = "%s\n%s" % (title, "Statistics")
			plt.title(t)
			plt.ylabel('Quantity')

			plt.plot(x, y[1], 'b', x, y[2], 'g', x, y[3], 'r')
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

	elements = [
		"general", "regression", "coverage",
		"ambiguity", "morph"
	]
	
	@staticmethod
	def node_equal(a, b):
		for i in (a, b):
			if not (hasattr(i, "tag") and hasattr(i, "attrib")):
				raise
				return False
		print("%s:%s %s:%s" % a.tag, b.tag, a.attrib, b.attrib)
		return a.tag == b.tag and a.attrib == b.attrib
	
	def __init__(self, f=None):
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
		try: 
			self.tree.write(self.f, encoding="utf-8", xml_declaration=True, pretty_print=True)
		except:
			raise
			self.tree.write(self.f, encoding="utf-8", xml_declaration=True)

	def add(self, parent, xml):
		ns = self.ns
		if parent not in self.elements:
			raise AttributeError("Element not supported.")
		
		old_node = None
		new_node = etree.fromstring(xml)
		if not new_node.tag.startswith(ns):
			new_node.tag = ns + new_node.tag
		
		parent_node = self.root.find(ns + parent) or SubElement(self.root, ns + parent)
		
		for i in parent_node.getiterator(new_node.tag):
			print("NODE_EQUAL")
			if self.node_equal(new_node, i):
				old_node = i
				break
		
		print(old_node or "None")
		print(etree.__name__)
		if old_node is None:
			parent_node.append(new_node)
		else:
			old_node.append(new_node.find(ns + "timestamp"))

	def get_regressions(self):
		root = self.root.find('regression')
		if root is None:
			return dict()
		regressions = defaultdict(dict)
		
		for d in root.getiterator("title"):
			title = "%s__%s" % (d.attrib['value'], d.attrib["revision"])
			for ts in d.getiterator('timestamp'):
				tsv = from_isoformat(ts.attrib['value'])
				
				regressions[title][tsv] = {
					"Percent": ts.find("percent").text,
					"Total": ts.find("total").text,
					"Passes": ts.find("passes").text,
					"Fails": ts.find("fails").text
				}

		out = dict()
		for k, v in regressions.items():
			out[k] = OrderedDict(sorted(v.items()))

		return out
	
	def get_coverages(self):
		root = self.root.find('coverage')
		if root is None:
			return dict()
		coverages = defaultdict(dict)
		
		for d in root.getiterator("dictionary"):
			dct = "%s__%s" % (d.attrib["value"], d.attrib["checksum"])
			for ts in d.getiterator("timestamp"):
				tsv = from_isoformat(ts.attrib['value'])
				c = ts.find("corpus")
			
				coverages[dct][tsv] = OrderedDict({
					"Corpus": "%s__%s" % (c.attrib["value"], c.attrib["checksum"]),
					"Percent": ts.find("percent").text,
					"Total": ts.find("total").text,	
					"Known": ts.find("known").text,	
					"Unknown": ts.find("unknown").text,
					#'':'',
					#"Top words:": ''#OrderedDict()
				})
			#for j in i.find("top").getiterator("word"):
			#	coverages[dct][ts][j.text] = j.attrib["count"]
			##for j in i.find("top").getiterator("word"):
			##	coverages[dct][ts]['top'][j.text] = j.attrib["count"]

		out = dict()
		for k, v in coverages.items():
			out[k] = OrderedDict(sorted(v.items()))

		return out

	def get_ambiguities(self):
		root = self.root.find('ambiguity')
		if root is None:
			return dict()
		ambiguities = defaultdict(dict)
		
		for d in root.getiterator("dictionary"):
			dct = "%s__%s" % (d.attrib["value"], d.attrib["checksum"])
			for ts in d.getiterator("timestamp"):
				tsv = from_isoformat(ts.attrib['value'])

				ambiguities[dct][tsv] = {
					"Surface forms": ts.find("surface-forms").text,
					"Analyses": ts.find("analyses").text,
					"Average": ts.find("average").text
				}

		out = dict()
		for k, v in ambiguities.items():
			out[k] = OrderedDict(sorted(v.items()))

		return out	

	def get_hfsts(self):
		root = self.root.find('morph')
		if root is None:
			return dict()
		hfsts = defaultdict(dict)
		
		for d in root.getiterator("config"):
			cfg = "%s__%s" % (d.attrib["value"], d.attrib["checksum"])
			for ts in d.getiterator("timestamp"):
				tsv = from_isoformat(ts.attrib['value'])
				g = ts.find("gen")
				m = ts.find("morph")
			
				hfsts[cfg][tsv] = {
					"Gen": "%s__%s" % (g.attrib['value'], g.attrib["checksum"]),
					"Morph": "%s__%s" % (m.attrib['value'], m.attrib["checksum"]),
					'':'',
					#"Tests": OrderedDict(),
					"Total": ts.find("total").text,
					"Passes": ts.find("passes").text,
					"Fails": ts.find("fails").text
				}
			
			#for j in i.find("tests").getiterator("test"):
			#	hfsts[cfg][ts]['tests'][j.text] = {
			#		"passes": j.attrib['passes'], 
			#		"fails": j.attrib['fails']
			#	}

		out = dict()
		for k, v in hfsts.items():
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
  margin: 12px; }

h1, h2 {
  margin: 0;
  padding: 0;
  padding-left: 12px;
  font-variant: small-caps; }

h1 {
  padding-top: 8px; }

table {
  border-collapse: collapse; }

/*table, th, td {
	border: 1px solid black;
}*/
div#container {
  padding: 0;
  margin: 0 auto;
  width: 100%; }

div#header {
  margin-top: 12px;
  margin-bottom: 12px;
  margin-left: 6px;
  margin-right: 6px;
  border-radius: 7px;
  -moz-border-radius: 7px;
  -webkit-border-radius: 7px;
  background-color: white; }
  div#header h1 {
    margin-top: 6px; }

div#footer {
  border: 0;
  padding: 0;
  margin: 0;
  color: black;
  text-align: center;
  font-size: 9pt; }

div.s-container {
  background-color: white;
  border: 1px solid black;
  margin-top: 12px;
  margin-bottom: 12px;
  margin-left: 6px;
  margin-right: 6px;
  border-radius: 7px;
  -moz-border-radius: 7px;
  -webkit-border-radius: 7px;
  clear: both; }
  div.s-container div.s-stats {
    margin: 0;
    padding: 0;
    border: 0; }
    div.s-container div.s-stats h1 {
      border-top: 1px dotted black;
      font-size: 16pt;
      padding-left: 16px;
      text-decoration: none; }
    div.s-container div.s-stats h2 {
      font-size: 8pt;
      padding-left: 16px; }
    div.s-container div.s-stats hr {
      clear: both;
      border: 0;
      margin: 0;
      padding: 0; }
    div.s-container div.s-stats div.s-imgs {
      margin-top: 12px;
      margin-bottom: 12px;
      margin-left: 6px;
      margin-right: 6px;
      border-radius: 7px;
      -moz-border-radius: 7px;
      -webkit-border-radius: 7px; }
      div.s-container div.s-stats div.s-imgs img {
        width: 267px;
        height: 200px;
        border: 1px solid black;
        margin: 12px; }
    div.s-container div.s-stats div.s-data {
      margin-top: 12px;
      margin-bottom: 12px;
      margin-left: 6px;
      margin-right: 6px;
      border-radius: 7px;
      -moz-border-radius: 7px;
      -webkit-border-radius: 7px; }
      div.s-container div.s-stats div.s-data h1 {
        font-size: 14pt;
        border: 0; }
      div.s-container div.s-stats div.s-data div.s-general {
        /*float: left;
        margin-right: 0;
        width: 47.75%;*/ }
        div.s-container div.s-stats div.s-data div.s-general table {
          margin: 12px; }
          div.s-container div.s-stats div.s-data div.s-general table tr td {
            padding-left: 6px;
            padding-right: 6px;
            text-align: right; }
          div.s-container div.s-stats div.s-data div.s-general table tr td:nth-child(2) {
            text-align: left; }
      div.s-container div.s-stats div.s-data div.s-chrono {
        /*float: right;
        margin-left: 0;
        width: 47.75%;*/ }
        div.s-container div.s-stats div.s-data div.s-chrono ul li {
          margin-left: 24px; }
          div.s-container div.s-stats div.s-data div.s-chrono ul li div {
            margin-left: -12px;
            padding: 6px; }
            div.s-container div.s-stats div.s-data div.s-chrono ul li div table {
              margin: 12px; }
              div.s-container div.s-stats div.s-data div.s-chrono ul li div table tr td {
                padding-left: 6px;
                padding-right: 6px;
                text-align: right; }
              div.s-container div.s-stats div.s-data div.s-chrono ul li div table tr td:nth-child(2) {
                text-align: left; }
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
				% for c, date in enumerate(reversed(chrono_stats)):
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