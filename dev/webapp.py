import xml.etree.ElementTree as etree
import os.path
pjoin = os.path.join
import tarfile
from hashlib import sha1
from time import time
from os import makedirs

import bottle
from bottle import abort, get, post, redirect, request, route, static_file
from bottle import HTTPResponse, urljoin
from apertium.quality import Statistics, Webpage

# Config
STATIC_FILES = "/Users/brendan/Temporal/aq-webapp/static"
WORKING_DIR = "/Users/brendan/Temporal/aq-webapp/working"
# END

html = """
<html>
	<head>
		<title>Apertium Quality Statistics Webpage Generator</title>
	</head>
	<body>
		%s
	</body>
</html>
"""

# TODO: add captcha
@route('/')
def frontpage():
	form = """
	<h3>Select statistics .xml</h3>
	<form action="/upload" method="post" enctype="multipart/form-data">
	  <input type="file" name="data" />
	  <input type="submit" value="Submit" />
	</form>
	"""
	return html % form

# TODO: add captcha check
@post('/upload')
def upload():
	data = request.files.get('data')
	raw = data.file.getvalue().decode('utf-8')
	cksum = sha1(raw.encode('utf-8')).hexdigest()

	stats = Statistics()
	stats.root = etree.fromstring(raw)
	stats.tree = etree.ElementTree(stats.root)

	wdir = pjoin(WORKING_DIR, cksum)
	try: makedirs(wdir)
	except: pass
	web = Webpage(stats, wdir)

	tf = tarfile.open(pjoin(STATIC_FILES, "%s.tgz" % cksum), "w:gz")
	tf.add(wdir)
	tf.close()

	out = """
	<h3>Website bundled successfully.</h3>
	<a href="/download/%s.tgz">Download</a>
	""" % cksum

	return html % out
	
@route('/download/:filename')
def download(filename):
	return static_file(filename, root=STATIC_FILES, download=True)

def main():
	bottle.debug(True)
	application = bottle.app()
	bottle.run(host='0.0.0.0', port=8080, app=application)

if __name__ == "__main__":
	main()
