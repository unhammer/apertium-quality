from collections import OrderedDict
from datetime import datetime
import urllib.request
import os.path
import json
import re

pjoin = os.path.join

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

    body = """<body>
<div id="container" class="minimal">
    <div id="navigation">
        <ul id="menu" class="dropdown"></ul>
    </div>
    <div id="header">
        <!--<h1 id="title">{title}</h1>-->
        <h1 id="subtitle"></h1>
        <h3 id="subsubtitle"></h3>
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
                "stats.js": js % json.dumps(chart_data),
                "index.html": self.base.format(head=self.head.format(scripts=script_html), body=self.body.format(title=self.title, footer=footer)),
                "style.css": core_css, #self.css,
                "menu.css": menu_css
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
        out['Ambiguity Testing']['Mean Ambiguity Over Time'] = self.stats.get_raphael("ambiguity", "Average", "Average", "Surface forms")
        return out
    
    def _general(self):
        out = {'Dictionary Testing':{}}
        out['Dictionary Testing']['Dictionary Entries Over Time'] = self.stats.get_raphael("general", "Entries", "Entries", "Unique entries")
        return out


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
    color: #01A8F0; 
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
    background: #41F8FF; 
    color: black; 
    position: relative; 
}

ul.dropdown li.hover a { 
    color: black; 
}


/* 
    LEVEL TWO
*/
ul.dropdown ul                         { width: 220px; visibility: hidden; position: absolute; top: 100%; left: 0; }
ul.dropdown ul li                     { font-weight: normal; background: #f6f6f6; color: #000; 
                                      border-bottom: 1px solid #ccc; float: none; }
                                      
                                    /* IE 6 & 7 Needs Inline Block */
ul.dropdown ul li a                    { border-right: none; width: 100%; display: inline-block; } 

/* 
    LEVEL THREE
*/
ul.dropdown ul ul                     { left: 100%; top: 0; }
ul.dropdown li:hover > ul             { visibility: visible; }"""

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
        //ul_i.append(node_i);
        menu.append(node_i);
    } 
    
    //var li = $("<li><a id='subtitle'>Menu</a></li>");
    //li.append(ul_i);
    //menu.append(li);
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

core_css = """* {
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

#navigation {
  position: fixed;
  top: 0px;
}

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
    padding-top: 0.5em; 
    margin-top: 6px;}
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