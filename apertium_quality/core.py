import xml.etree.cElementTree as etree
import os, os.path
from hashlib import sha1
from datetime import datetime
#import logging

class ParseError(Exception):
	pass

def checksum(data):
	return str(sha1(data).hexdigest())

def whereis(program):
	for path in os.environ.get('PATH', '').split(':'):
		if os.path.exists(os.path.join(path, program)) and \
		   not os.path.isdir(os.path.join(path, program)):
			return os.path.join(path, program)
	return None

class Statistics(object):
	file_version = "1.0"

	def __init__(self, f):
		self.f = f
		if os.path.exists(f):
			try:
				self.tree = etree.parse(open(f))
				if self.tree.getroot().tag == "statistics":
					if self.tree.getroot().get('version') == "1.0":	
						print "[STUB] Do version specific crap here for 1.0"
					else:
						print "[DEBUG] Version incorrect."
					self.root = self.tree.getroot()
					print "[DEBUG] Imported tree."
				else:
					raise ParseError("File does not seem to be a statistics file.")
			except IOError:
				raise
			except ParseError:
				raise
			except:
				raise
		else:
			xml = '<statistics type="%s" version="%s" />' % ("apertium", Statistics.file_version)
			try:
				self.root = etree.fromstring(xml)
				self.tree = etree.ElementTree(self.root)
			except:
				raise
	
	def write(self):
		self.tree.write(self.f, encoding="utf-8", xml_declaration=True)

	def add_regression(self, name, cksum, passes, fails):
		root = self.root.find('regressions')
		r = etree.SubElement(root, 'regression', date=datetime.now().isoformat())
		etree.SubElement(r, 'name').text = str(name)
		etree.SubElement(r, 'checksum', type='sha1').text = str(cksum)
		etree.SubElement(r, 'passes').text = str(passes)
		etree.SubElement(r, 'fails').text = str(fails)
		

	
		
