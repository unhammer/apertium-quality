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


class ParseError(Exception):
	"""Exception for parsing errors."""
	pass

def from_isoformat(t):
	"""Converts time from ISO-8601 string to datetime object"""
	return datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%f")


class Webpage(object):
	"""Generate a webpage and supporting files from a given Statistics file"""
	space = re.compile('[ /:\n]')
	head = """<head>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
	<title>JS Stats</title>
{scripts}
	<link rel="stylesheet" type="text/css" href="style.css" />
	<link rel="stylesheet" type="text/css" href="menu.css" />
</head>"""
	menu_css = """ul { 
	list-style: none; 
}

.arrow:after {
	content: " \xbb ";
}
/* 
	LEVEL ONE
*/
ul.dropdown { 
	position: relative; 
}

ul.dropdown li { 
	font-weight: bold; 
	float: left; 
	zoom: 1; 
	background: #ccc; 
}

ul.dropdown a:hover { 
	color: #000; 
}

ul.dropdown a:active { 
	color: #ffa500; 
}

ul.dropdown li a { 
	display: block; 
	padding: 4px 8px; 
	border-right: 1px solid #333;
	color: #222; 
}

ul.dropdown li:last-child a { 
	border-right: none; 
} /* Doesn't work in IE */

ul.dropdown li.hover, ul.dropdown li:hover { 
	background: #F3D673; 
	color: black; 
	position: relative; 
}

ul.dropdown li.hover a { 
	color: black; 
}


/* 
	LEVEL TWO
*/
ul.dropdown ul 						{ width: 220px; visibility: hidden; position: absolute; top: 100%; left: 0; }
ul.dropdown ul li 					{ font-weight: normal; background: #f6f6f6; color: #000; 
									  border-bottom: 1px solid #ccc; float: none; }
									  
                                    /* IE 6 & 7 Needs Inline Block */
ul.dropdown ul li a					{ border-right: none; width: 100%; display: inline-block; } 

/* 
	LEVEL THREE
*/
ul.dropdown ul ul 					{ left: 100%; top: 0; }
ul.dropdown li:hover > ul 			{ visibility: visible; }"""

	css = """* {
	padding: 0;
	margin: 0;
}

"""
	body = """<body>
<div id="container" class="minimal">
	<div id="header">
		<h1 id="title">{title}</h1>
		<h2 id="subtitle"></h2>
		<h3 id="subsubtitle"></h3>
		<ul id="menu" class="dropdown"></ul>
		Save as: <a onclick="saveSvg()">SVG</a> <a onclick="savePng()">PNG(800)</a> <a onclick="savePng(1024, 768)">PNG(1024)</a>
	</div>
	<div id="chart"></div>
	<div id="footer">{footer}</div>
</div>
</body>"""

	base = """<!DOCTYPE html>
<html>
{head}
{body}
</html>
"""

	js = """var data = %s;
var w = 800 - 20;
var h = Math.round(window.innerHeight / 2);
var title = null;
var cur_data = null;
var div = "chart";
var chart = null;

function setData(title, subtitle, dat) {
	$("#title").empty().append(title);
	$("#subtitle").empty().append(subtitle);
	$("#subsubtitle").empty().append(dat);
	cur_data = data[title][subtitle][dat];
	$("#" + div).empty();
	makeChart();
}

function makeChart() {
	chart = Raphael(div, w, h);
	chart.lineChart({
		data: cur_data,
		width: w-10,
		height: Math.round(window.innerHeight / 2),
		show_area: true,
		x_labels_step: Math.round(cur_data.data.length / 5),
		y_labels_count: 4,
		mouse_coords: 'rect',
		gutter: {
			top: 12,
			bottom: 24,
			left: 0,
			right: 0
		},
		colors: {
			master: '#01A8F0'
		},
		hide_dots: 30
	});
}

function generateMenu() {
	var menu = $("<ul id='menu' class='dropdown'></ul>");
	
	var ul_i = $("<ul class='sub_menu'></ul>");
	for(var i in data) {
		var node_i = $("<li><a>"+i+"</a></li>");
		
		var ul_ii = $("<ul class='sub_menu'></ul>");
		for(var ii in data[i]) {
			var node_ii = $("<li><a>"+ii+"</a></li>");
			
			var ul_iii = $("<ul class='sub_menu'></ul>");
			for(var iii in data[i][ii]) {
				var link = $("<li><a>"+iii+"</a></li>");
				link.attr("onclick", "setData('"+i+"', '"+ii+"', '"+iii+"')");
				ul_iii.append(link);
			}
			
			node_ii.append(ul_iii);
			ul_ii.append(node_ii);
		}
		
		node_i.append(ul_ii);
		ul_i.append(node_i);
	} 
	
	var li = $("<li><a id='subtitle'>Menu</a></li>");
	li.append(ul_i);
	menu.append(li);
	$("#menu").replaceWith(menu);
	$("ul.dropdown li ul li:has(ul)").find("a:first").addClass("arrow");//.append(" &raquo; ");
}

function saveSvg() {
	$("#chart > svg > desc").remove(); // Raphael, escape your umlauted e's man.
	var svgElement = $("#chart > svg")[0];
	var svg = (new XMLSerializer()).serializeToString(svgElement);
	window.open("data:image/svg+xml;charset=utf-8;base64,"+btoa(svg));
	delete svg;
}

function savePng(pw, ph) {
	var canvas = $("<canvas />")[0];
	canvas.height = ph || 600;
	canvas.width = pw || 800;
	canvg(canvas, new XMLSerializer().serializeToString($("svg")[0]));
	window.open(canvas.toDataURL());
	delete canvas;
}

window.onload = function() {
	generateMenu();
	(function() {for (var i in data) { for (var ii in data[i]) { for (var iii in data[i][ii]) { 
		title = iii; setData(i, ii, iii); return;  }}}; })(); //data[i][ii][iii];
};

$(function(){

    $("ul.dropdown li").hover(function(){
    
        $(this).addClass("hover");
        $('ul:first',this).css('visibility', 'visible');
    
    }, function(){
    
        $(this).removeClass("hover");
        $('ul:first',this).css('visibility', 'hidden');
    
    });

});

/*
window.onresize = function() {
	w = window.innerWidth - 20;
	h = window.innerHeight - 20;
	
	makeChart();
}
*/
"""

	def __init__(self, stats, fdir, title):
		self.stats = stats
		try: os.makedirs(fdir)
		except: pass
		self.fdir = fdir
		self.title = title

	def generate(self):
		footer = "Generated: %s" % datetime.utcnow().strftime("%Y-%m-%d %H:%M (UTC)")
		
		chart_data = {}
		chart_data.update(self._coverage())
		chart_data.update(self._regression())
		chart_data.update(self._ambiguity())
		chart_data.update(self._general())
		
		scripts = OrderedDict((
				("jquery.js", "http://code.jquery.com/jquery-1.6.2.min.js"),
				("raphael.js", "https://github.com/DmitryBaranovskiy/raphael/raw/master/raphael-min.js"),
				("raphael_linechart.js", "https://github.com/bbqsrc/raphael-linechart/raw/master/js/raphael_linechart.js"),
				("rgbcolor.js", "http://canvg.googlecode.com/svn/trunk/rgbcolor.js"),
				("canvg.js", "http://canvg.googlecode.com/svn/trunk/canvg.js")
		))
		
		script_html = ''
		for script, url in scripts.items():
			script_html += '\t<script charset="utf-8" type="text/javascript" src="%s"></script>\n' % script
			if not os.path.exists(pjoin(self.fdir, script)):
				data = urllib.request.urlopen(url).read()
				f = open(pjoin(self.fdir, script), 'wb')
				f.write(data)
				f.close()
		script_html += '\t<script charset="utf-8" type="text/javascript" src="stats.js"></script>\n'
				
		writes = {
				"stats.js": self.js % json.dumps(chart_data),
				"index.html": self.base.format(head=self.head.format(scripts=script_html), body=self.body.format(title=self.title, footer=footer)),
				"style.css": css, #self.css,
				"menu.css": self.menu_css
		}
		
		for fn, data in writes.items():
			f = open(pjoin(self.fdir, fn), 'w')
			f.write(data)
			f.close()
		
	def _coverage(self):
		out = {'Coverage Testing':{}}
		out['Coverage Testing']['Coverage Over Time'] = self.stats.get_raphael("coverage", "Percent", "Known", "Total")
		return out
	
	def _regression(self):
		out = {'Regression Testing':{}}
		out['Regression Testing']['Regressions Over Time'] = self.stats.get_raphael("regression", "Percent", "Passes", "Total")
		return out
	
	def _ambiguity(self):
		out = {'Ambiguity Testing':{}}
		out['Ambiguity Testing']['Mean Ambiguity Over Time'] = self.stats.get_raphael("ambiguity", "Average", "Average", "Surface Forms")
		return out
	
	def _general(self):
		out = {'Dictionary Testing':{}}
		out['Dictionary Testing']['Dictionary Entries Over Time'] = self.stats.get_raphael("general", "Entries", "Entries", "Unique Entries")
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
		
		return self.elements[tag](root)

	def get_raphael(self, tag, data, lines1, lines2):
		"""Get output suitable for JSONing for Raphael charts"""
		out = {}
		dat = self.get(tag)
		
		for key, val in dat.items():
			out[key] = defaultdict(list)
			
			for k, v in val.items():
				if len(out[key]) == 0 or out[key].get('data')[-1] != v[data]:
					out[key]['labels'].append(k)
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
					"Entries": rev.find(self.ns + "entries"),
					"Unique Entries": rev.find(self.ns + "unique-entries"),
					"Rules": rev.find(self.ns + "rules")
				}
		
		out = dict()
		for k, v in dicts.items():
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

css = """* {
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
  /*div.minimal ul {
    margin: 1em 0 1em 1em; }*/
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