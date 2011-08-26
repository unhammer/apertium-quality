from os.path import dirname, basename, abspath
from collections import defaultdict, Counter, OrderedDict
from multiprocessing import Process, Manager
from subprocess import Popen, PIPE
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from io import StringIO
from glob import glob
from datetime import datetime
from hashlib import sha1
from tempfile import NamedTemporaryFile
import os
import os.path
import re
import urllib.request
import shlex
import itertools
import traceback
import time

import yaml
try:
	from lxml import etree
	from lxml.etree import Element, SubElement
except:
	import xml.etree.ElementTree as etree
	from xml.etree.ElementTree import Element, SubElement

from apertium import whereis, destxt, retxt, DixFile, process
from apertium.quality import Statistics, schemas
from apertium.quality.html import Webpage

pjoin = os.path.join
ARROW = "\u2192"


class UncleanWorkingDirectoryException(Exception):
	pass

class Test(object):
	"""Abstract class for Test objects
	
	It is recommended that print not be used within a Test class.
	Use a StringIO instance and .getvalue() in to_string().
	"""
	
	"""Attributes"""
	timer = None
	
	def __str__(self):
		"""Will return to_string method's content if exists, 
		otherwise default to parent class
		"""
		try: return self.to_string()
		except: return object.__str__(self)
	
	def _checksum(self, data):
		"""Returns checksum hash for given data (currently SHA1) for the purpose
		of maintaining integrity of test data.
		"""
		if hasattr(data, 'encode'):
			data = data.encode('utf-8')
		return sha1(data).hexdigest()
	
	def _svn_revision(self, directory):
		"""Returns the SVN revision of the given dictionary directory"""
		whereis(['svnversion'])
		res = Popen('svnversion', stdout=PIPE, close_fds=True).communicate()[0].decode('utf-8').strip()
		try:
			int(res) # will raise error if it can't be int'd
			return str(res)
		except:
			raise UncleanWorkingDirectoryException("You must have a clean SVN directory. Commit or remove uncommitted files.")
	
	def run(self, *args, **kwargs):
		"""Runs the actual test
		
		Parameters: none
		Returns: integer >= 0 <= 255  (exit value)
		"""
		raise NotImplementedError("Required method `run` was not implemented.")
	
	def to_xml(self, *args, **kwargs):
		"""Output XML suitable for saving in Statistics format.
		It is recommended that you use etree for creating the tree.
		
		Parameters: none
		Returns: (string, string)
			first being parent node, second being xml
		"""
		raise NotImplementedError("Required method `to_xml` was not implemented.")
	
	def to_string(self, *args, **kwargs):
		"""Prints the output of StringIO instance and other printable output.
		
		Parameters: none
		Returns: string
		"""
		raise NotImplementedError("Required method `to_string` was not implemented.")

class AmbiguityTest(Test):
	delim = re.compile(":[<>]:")

	def __init__(self, f, **kwargs):
		self.f = kwargs.get('f', f)
		self.program = "lt-expand"
		whereis([self.program])
	
	def get_results(self):
		res, err = process([self.program, self.f])
		self.results = self.delim.sub(":", res).split('\n')

	def get_ambiguity(self):
		self.h = defaultdict(lambda: 0)
		self.surface_forms = 0
		self.total = 0

		for line in self.results:
			row = line.split(":")
			if not row[0] in self.h:
				self.surface_forms += 1
			self.h[row[0]] += 1
			self.total += 1
		
		self.average = float(self.total) / float(self.surface_forms)

	def run(self):
		timing_begin = time.time()
		self.get_results()
		self.get_ambiguity()
		self.timer = time.time() - timing_begin
		return 0
	
	def to_xml(self):
		q = Element('dictionary')
		q.attrib["value"] = self.f

		r = SubElement(q, "revision", value=str(self._svn_revision(dirname(self.f))))
		r.attrib['timestamp'] = datetime.utcnow().isoformat()
		r.attrib['checksum'] = self._checksum(open(self.f, 'rb').read())

		SubElement(r, 'surface-forms').text = str(self.surface_forms)
		SubElement(r, 'analyses').text = str(self.total)
		SubElement(r, 'average').text = str(self.average)
		
		return ("ambiguity", etree.tostring(q))

	def to_string(self):
		out = StringIO("Total surface forms: %d\n" % self.surface_forms)
		out.write("Total analyses: %d\n" % self.total)
		out.write("Average ambiguity: %.2f" % self.average)
		return out.getvalue().strip()


class AutoTest(Test):
	ns = "{%s}" % schemas['config']
	
	def __init__(self, stats=None, webdir=None, aqx=None, verbose=None, **kwargs):
		self.stats = kwargs.get('stats', stats)
		self.webdir = kwargs.get('webdir', webdir)
		self.aqx = kwargs.get('aqx', aqx)
		self.verbose = kwargs.get('verbose', verbose)
		
		if self.aqx is None:
			raise ValueError('A configuration file is required')
		
		self.langpair = abspath('.').split('apertium-')[-1]
		self.lang1, self.lang2 = self.langpair.split('-')
		
		if self.stats:
			self.stats = Statistics(self.stats)
		
		if self.aqx:
			self.root = etree.parse(self.aqx).getroot()
	
	def build(self):
		commands = self.root.find(self.ns + "commands")
		if commands is None:
			return
		
		for command in commands.getiterator(self.ns + "command"):
			p = Popen(command.text, shell=True, stdout=PIPE, stderr=PIPE, close_fds=True)
			out, err = p.communicate()
			out = out.decode('utf-8')
			err = err.decode('utf-8')
			
			if p.returncode != 0 or err.strip() != "":
				print("[!] Error:")
				print(err)
				return False
		return True
		
	def ambiguity(self):
		dixen = glob("apertium-%s.*.dix" % self.langpair)
		if dixen == []:
			print("[!] No .dix files")
			return
		
		print("[-] Ambiguity Tests")
		for d in dixen:
			print("[-] File: %s" % d)
			try:
				test = AmbiguityTest(d)
				test.run()
			except:
				print("[!] Error:")
				traceback.print_exc()
				continue
			
			if self.stats:
				self.stats.add(*test.to_xml())
	
	def coverage(self):
		corpora = self.root.find(self.ns + "coverage")
		if corpora is None:
			print("[!] No coverage tests")
			return 
		
		print("[-] Coverage Tests")
		for corpus in corpora.getiterator(self.ns + "corpus"):
			path = corpus.attrib.get("path", "")
			lang = corpus.attrib.get("language", "")
			gen = corpus.attrib.get("generator", "")
			
			if "" in (path, lang):
				print("[!] No path or language set.")
				continue
			
			print("[-] File: %s" % basename(path))
			
			if not os.path.isfile(path):
				if gen != "":
					p = Popen(gen, shell=True, stdout=PIPE, stderr=PIPE, close_fds=True)
					res, err = p.communicate()
					if p.returncode != 0:
						print("[!] Return code was %s." % p.returncode)
						continue
					elif os.path.isfile(path):
						print("[!] File at %s does not exist after generation." % path)
						continue
				else:
					print("[!] No generator and file does not exist at %s." % path)
					continue
			
			try:
				test = CoverageTest(path, "%s.automorf.bin" % lang)
				test.run()
			except:
				print("[!] Error:")
				traceback.print_exc()
				continue
			
			if self.stats:
				self.stats.add(*test.to_xml())
	
	def dictionary(self):
		print("[-] Dictionary Tests")
		try:
			test = DictionaryTest(self.langpair, '.')
			test.run()
		except:
			print("[!] Error:")
			traceback.print_exc()
		
		if self.stats:
			self.stats.add(*test.to_xml())
	
	def generation(self):
		corpora = self.root.find(self.ns + "generation")
		if corpora is None:
			print("[!] No generation corpora.")
			return
		
		print("[-] Generation Tests")
		for corpus in corpora.getiterator(self.ns + "corpus"):
			path = corpus.attrib.get("path", "")
			lang = corpus.attrib.get("language", "")
			gen = corpus.attrib.get("generator", "")
			
			if "" in (path, lang):
				print("[!] No path or language set.")
				continue
			
			print("[-] File: %s" % basename(path))
			
			if not os.path.isfile(path):
				if gen != "":
					p = Popen(gen, shell=True, stdout=PIPE, stderr=PIPE, close_fds=True)
					res, err = p.communicate()
					if p.returncode != 0:
						print("[!] Return code was %s." % p.returncode)
						continue
					elif os.path.isfile(path):
						print("[!] File at %s does not exist after generation." % path)
						continue
				else:
					print("[!] No generator and file does not exist at %s." % path)
					continue
			
			try:
				test = GenerationTest('.', lang, path)
				test.run()
			except:
				print("[!] Error:")
				traceback.print_exc()
				continue
			
			if self.stats:
				self.stats.add(*test.to_xml())
	
	def morph(self):
		tests = self.root.find(self.ns + "morph")
		if tests is None:
			print("[!] No morph tests")
			return 
		
		print("[-] Morph Tests")
		for test in tests.getiterator(self.ns + 'test'):
			path = test.attrib.get("path")
			if path is None:
				print("[!] No path value set." % path)
				continue
			
			print("[-] File: %s" % path)
			if not os.path.isfile(path):
				print("[!] File at %s does not exist." % path)
				continue
				
			try:
				test = MorphTest(path)
				test.run()
			except:
				print("[!] Error:")
				traceback.print_exc()
				continue
			
			if self.stats:
				self.stats.add(*test.to_xml())

	def regression(self):
		tests = self.root.find(self.ns + "regression")
		if tests is None:
			print("[!] No regression tests")
			return
		
		print("[-] Regression Tests")
		for test in tests.getiterator(self.ns + 'test'):
			path = test.attrib.get("path")
			language = test.attrib.get("language")
			
			if None in (path, language):
				print("[!] No path or language set.")
				continue
			
			if path.startswith("http"):
				print("[-] URL: %s" % path)
				
			else:
				print("[-] File: %s" % path)
				if not os.path.isfile(path):
					print("[!] No file exists at %s" % path)
					continue
				
			try:
				test = RegressionTest(path, language)
				test.run()
			except:
				print("[!] Error:")
				traceback.print_exc()
				continue
			
			if self.stats:
				self.stats.add(*test.to_xml())

	def vocabulary(self):
		print("[-] Vocabulary Tests")
		try:
			test = VocabularyTest("lr", self.lang1, self.lang2, "voctest.txt", '.')
			test.run()
		except:
			print("[!] Error:")
			traceback.print_exc()
		
		if self.stats:
			self.stats.add(*test.to_xml())
		
	def webpage(self):
		print("[-] Generating HTML content")
		self.web = Webpage(self.stats, self.webdir, self.langpair)
		self.web.generate()
	
	def run(self):
		res = self.build()
		if not res:
			print("[!] Bailing out.")
			return
		self.ambiguity()
		self.coverage()
		self.dictionary()
		self.generation()
		self.regression()
		self.morph()
		self.vocabulary()
		if self.stats:
			self.stats.write()
			if self.webdir:
				self.webpage()
		print("[-] Done!")


class CoverageTest(Test):
	app = "lt-proc"
	app_args = []
	
	def __init__(self, fn=None, dct=None, hfst=None, **kwargs):
		fn = kwargs.get('fn', fn)
		dct = kwargs.get('dct', dct)
		hfst = kwargs.get('hfst', hfst)
		if None in (fn, dct):
			raise TypeError("fn or dct parameter missing.")
		
		if hfst:
			self.app = "hfst-proc"
			self.app_args = ['-w']
			
		whereis([self.app])
		self.dct = dct
		self.result = None
		self.fn = fn
		
	def run(self):
		try:
			# Try parsing as XML
			root = etree.parse(self.fn)
			ns = "{%s}" % schemas['corpus']
			out = StringIO()
			for i in root.getiterator(ns + "entry"):
				out.write(i.text + "\n")
			self.corpus = out.getvalue()
			del out
		except:
			# Turns out it's not XML
			self.corpus = open(fn, 'r')
		
		try:
			open(self.dct) # test existence
		except:
			raise # TODO: wrap error for output
		
		if not self.result:
			delim = re.compile(r"\$[^^]*\^")
			f = open(self.fn, 'r')			
			data = f.read()
			f.close()

			output = destxt(data).encode('utf-8')
			timing_begin = time.time()
			proc = Popen([self.app] + self.app_args + [self.dct], stdin=PIPE, stdout=PIPE, close_fds=True)
			output = str(proc.communicate(output)[0].decode('utf-8'))
			self.timer = time.time() - timing_begin
			output = retxt(output) 
			
			output = delim.sub("$\n^", output)
			self.result = output.split('\n')
		return 0

	def get_words(self):
		if not self.result:
			self.run()
		return [ i.strip() for i in self.result ]

	def get_known_words(self):
		if not self.result:
			self.run()
		return [ i.strip() for i in self.result if not '*' in i ]

	def get_unknown_words(self):
		if not self.result:
			self.run()
		return [ i.strip() for i in self.result if '*' in i ]
	
	def get_top_unknown_words(self, c=20):
		return Counter(self.get_unknown_words()).most_common(c)

	def get_top_unknown_words_string(self, c=20):
		out = StringIO()
		for word, count in self.get_top_unknown_words(c):
			word = word.split('/')[0][1:]
			out.write("%d\t %s\n" % (count, word))
		return out.getvalue()
		
	def get_coverage(self):
		a = float(len(self.get_known_words()))
		b = float(len(self.get_words()))
		return a / b * 100
	
	def to_xml(self):
		q = Element('dictionary')
		q.attrib["value"] = basename(dirname(self.dct))
		
		r = SubElement(q, "revision", 
					value=str(self._svn_revision(dirname(self.dct))),
					timestamp=datetime.utcnow().isoformat(),
					checksum=self._checksum(open(self.dct, 'rb').read()))
		
		s = SubElement(r, 'corpus')
		s.attrib["value"] = basename(self.fn)
		s.attrib["checksum"] = self._checksum(open(self.fn, 'rb').read())
		
		SubElement(r, 'percent').text = "%.2f" % self.get_coverage()
		SubElement(r, 'total').text = str(len(self.get_words()))
		SubElement(r, 'known').text = str(len(self.get_known_words()))
		SubElement(r, 'unknown').text = str(len(self.get_unknown_words()))
		
		wrx = re.compile(r"\^(.*)/")
		s = SubElement(r, 'top')
		for word, count in self.get_top_unknown_words():
			SubElement(s, 'word', count=str(count)).text = wrx.search(word).group(1)
		
		s = SubElement(r, 'system')
		SubElement(s, 'time').text = "%.4f" % self.timer
		
		return ("coverage", etree.tostring(q))

	def to_string(self):
		out = StringIO()
		out.write("Number of tokenised words in the corpus: %s\n" % len(self.get_words()))
		out.write("Coverage: %.2f%%\n" % self.get_coverage())
		out.write("Top unknown words in the corpus:\n")
		out.write(self.get_top_unknown_words_string())
		out.write("Translation time: %s seconds\n" % self.timer)
		return out.getvalue().strip()

			
class DictionaryTest(Test):
	class TnXHandler(ContentHandler):
		def __init__(self):
			self.rules = []

		def startElement(self, tag, attrs):
			if tag == "rule":
				self.rules.append(attrs.get("comment", None))
	
	def __init__(self, langpair=None, directory=None, corpus=None, **kwargs):
		whereis(['apertium-transfer', 'apertium-pretransfer', 'lt-proc'])
		
		self.langpair = kwargs.get("langpair") or langpair
		self.directory = kwargs.get("directory") or directory or '.'
		self.corpus = kwargs.get("corpus") or corpus
		if None in (self.directory, self.langpair):
			raise ValueError("langpair or directory missing.")
		
		self.dixfiles = glob(pjoin(self.directory, '*.dix'))
		self.rlxfiles = glob(pjoin(self.directory, '*.rlx')) 
		self.tnxfiles = glob(pjoin(self.directory, '*.t[1-9]x'))
		
		self.trules = None
		self.rules = None
		self.entries = None
	
	def get_transfer_command(self, tnxcount, pair1, pair2):
		cmd = ["lt-proc {0}/{1}.automorf.bin | apertium-pretransfer".format(self.directory, self.langpair)]
		for i in range(1, tnxcount+1):
			if i == 1:
				cmd.append("""apertium-transfer {0}/apertium-{1}.{2}.t1x \
							{0}/{2}.t1x.bin \
							{0}/{2}.autobil.bin""".format(self.directory, pair1, pair2))
			elif i < tnxcount:
				cmd.append("""apertium-interchunk {0}/apertium-{1}.{2}.t{3}x \
							{0}/{2}.t{3}x.bin""".format(self.directory, pair1, pair2, i))
			elif i == tnxcount:
				cmd.append("""apertium-postchunk {0}/apertium-{1}.{2}.t{3}x \
							{0}/{2}.t{3}x.bin""".format(self.directory, pair1, pair2, i))
		return " | ".join(cmd)
	
	def get_transfer_rules(self):
		if not self.trules:
			tnxcount = len(glob(pjoin(self.directory, '*.{0}.t[1-9]x'.format(self.langpair))))
			if tnxcount == 0:
				raise ValueError("No tnx files found. Try compiling your dictionary or something.")
			self.trules = defaultdict(list)
			
			for i in range(tnxcount):
				cmd = self.get_transfer_command(i, self.langpair, self.langpair) # STUB must do btoh language pairs
				p = Popen(cmd, shell=True, close_fds=True, stdout=PIPE)
				res = p.communicate(destxt(open(self.corpus, 'r').read()))[0].decode('utf-8').split('\n')
				fn = "apertium-{0}.{1}.t{2}x".format(self.langpair, self.langpair, tnxcount+1)
				self.trules[fn] = [i for i in res if i in ": Rule"]
		return self.trules
	
	def get_transfer_rule_counter(self):
		c = Counter()
		for k, v in self.get_transfer_rules().items():
			c[k] = len(v)
		return c
	
	def get_transfer_rule_count(self):
		return sum(self.get_transfer_rule_counter().values())

	def get_unique_transfer_rule_count(self):
		c = Counter()
		for k, v in self.get_transfer_rules().items():
			c[k] = len(set(v))
		return sum(c.values())
	
	def get_rules(self):
		if not self.rules:
			self.rules = defaultdict(list)
			
			for i in self.tnxfiles:
				parser = make_parser()
				handler = self.TnXHandler()
				parser.setContentHandler(handler)
				parser.parse(i)
				self.rules[basename(i)] = handler.rules
			
			ruletypes = ("SELECT", "REMOVE", "MAP", "SUBSTITUTE")
			for i in self.rlxfiles:
				f = open(i, 'r')
				for line in f:
					if line.strip().startswith(ruletypes):
						self.rules[basename(i)].append(line)
						
		return self.rules
	
	def get_rule_counter(self):
		c = Counter()
		for k, v in self.get_rules().items():
			c[k] = len(v)
		return c
	
	def get_rule_count(self):
		return sum(self.get_rule_counter().values())
	
	def get_entries(self):
		if not self.entries:
			self.entries = defaultdict(list)
			
			for i in self.dixfiles:
				self.entries[basename(i)] += DixFile(i).get_entries()
		return self.entries
	
	def get_entry_counter(self):
		c = Counter()
		for k, v in self.get_entries().items():
			c[k] = len(v)
		return c
	
	def get_entry_count(self):
		return sum(self.get_entry_counter().values())
	
	def get_unique_entry_count(self):
		c = Counter()
		for k, v in self.get_entries().items():
			c[k] = len(set(v))
		return sum(c.values())
	
	def run(self):
		self.get_rules()
		self.get_entries()
		if self.corpus:
			self.get_transfer_rules()
	
	def to_xml(self):
		q = Element('dictionary')
		q.attrib["value"] = basename(abspath(self.directory))
		
		r = SubElement(q, 'revision')
		r.attrib["value"] = str(self._svn_revision(self.directory))
		r.attrib["timestamp"] = datetime.utcnow().isoformat()
		
		SubElement(r, 'entries').text = str(self.get_entry_count())
		SubElement(r, 'unique-entries').text = str(self.get_unique_entry_count())
		SubElement(r, 'rules').text = str(self.get_rule_count())
		
		return ("general", etree.tostring(q))
	
	def to_string(self):
		out = StringIO()
		
		out.write("Ordered rule count per file:\n")
		for file, count in self.get_rule_counter().most_common():
			out.write("%d\t %s\n" % (count, file))
		out.write("Total rules: %d\n\n" % self.get_rule_count())
		
		out.write("Ordered entry count per file:\n")
		for file, count in self.get_entry_counter().most_common():
			out.write("%d\t %s\n" % (count, file))
		out.write("Total entries: %d\n" % self.get_entry_count())
		out.write("Total unique entries: %d\n" % self.get_unique_entry_count())
		
		if self.trules:
			out.write("Ordered transfer rules count per file:\n")
			for file, count in self.get_transfer_rule_counter().most_common():
				out.write("%d\t %s\n" % (count, file))
			out.write("Total transfer rules: %d\n" % self.get_transfer_rule_count())
			out.write("Total unique transfer rules: %d\n" % self.get_unique_transfer_rule_count())
		
		return out.getvalue().strip()


class GenerationTest(Test):
	def __init__(self, direc=None, mode=None, corpus=None, **kwargs):
		self.directory = kwargs.get('direc', direc)
		self.mode = kwargs.get('mode', mode)
		self.corpus = kwargs.get('corpus', corpus)
		if None in (self.directory, self.mode, self.corpus):
			raise ValueError("direc, mode or corpus missing.")
		
		self.lang = '-'.join(self.mode.rsplit('-')[0:2])
		whereis(["apertium", "lt-proc"])
	
	def get_transfer(self, data):
		count = Counter()
		out = StringIO()
		buf = StringIO()
		in_word = False
		
		for i in data:
			if i == "^":
				in_word = True
			if i == "$":
				out.write("%s$\n" % buf.getvalue())
				count[buf.getvalue()] += 1
				buf = StringIO()
				in_word = False
			if in_word:
				buf.write(i)
		
		return out.getvalue().split('\n')
					
	def run(self):
		timing_begin = time.time()
		app = Popen(['apertium', '-d', self.directory, self.mode], stdin=open(self.corpus), stdout=PIPE, close_fds=True)
		raw = app.communicate()[0].decode('utf-8')
		transfer = self.get_transfer(raw)
		del raw
		
		stripped = StringIO()
		for word, count in Counter(transfer).most_common():
			stripped.write("{:>6} {:<}\n".format(count, word))
		stripped = stripped.getvalue()
		
		app = Popen(['lt-proc', '-d', "%s.autogen.bin" % pjoin(self.directory, self.lang)], stdin=PIPE, stdout=PIPE, close_fds=True)
		surface = app.communicate(stripped.encode('utf-8'))[0].decode('utf-8')
		nofreq = re.sub(r'[\s\t]*\d*\s*\^', '^', stripped)
		
		gen_errors = StringIO()
		for i in itertools.zip_longest(surface.split('\n'), nofreq.split('\n'), fillvalue=""):
			gen_errors.write("{:<16}{:<16}\n".format(*list(str(x) for x in i)))
		gen_errors = gen_errors.getvalue().split('\n')

		multiform = []
		multibidix = []
		tagmismatch = []
		
		for i in gen_errors:
			if "#" in i:
				if re.search(r'[0-9] #.*\/', i):
					multibidix.append(i)
				elif re.search(r'[0-9] #', i) and not '/' in i:
					tagmismatch.append(i)
			elif "/" in i:
				multiform.append(i)

		self.multiform = multiform
		self.multibidix = multibidix
		self.tagmismatch = tagmismatch
		self.timer = time.time() - timing_begin

	def to_xml(self):
		q = Element('dictionary')
		q.attrib["value"] = basename(abspath(self.directory))
		
		r = SubElement(q, "revision", 
					value=str(self._svn_revision(basename(abspath(self.directory)))),
					timestamp=datetime.utcnow().isoformat())
		
		s = SubElement(r, 'corpus')
		s.attrib["value"] = basename(self.corpus)
		s.attrib["checksum"] = self._checksum(open(self.corpus, 'rb').read())
		
		SubElement(r, "total").text = str(len(self.multiform) + len(self.multibidix) + len(self.tagmismatch))
		SubElement(r, "multiform").text = str(len(self.multiform))
		SubElement(r, "multibidix").text = str(len(self.multibidix))
		SubElement(r, "tagmismatch").text = str(len(self.tagmismatch))
		
		s = SubElement(r, "system")
		SubElement(s, "speed").text = "%.4f" % self.timer
		
		return ("generation", etree.tostring(q))
		
	
	def to_string(self):
		out = StringIO()
		border = "=" * 80
		
		out.write(border + "\n")
		out.write("Multiple surface forms for a single lexical form\n")
		out.write(border + "\n")
		out.write("\n".join(self.multiform)+'\n\n')
		
		out.write(border + "\n")
		out.write("Multiple bidix entries for a single source language lexical form\n")
		out.write(border + "\n")
		out.write("\n".join(self.multibidix)+"\n\n")
		
		out.write(border + "\n")
		out.write("Tag mismatch between transfer and generation\n")
		out.write(border + "\n")
		out.write("\n".join(self.tagmismatch)+"\n\n")
		
		out.write(border + "\n")
		out.write("Summary\n")
		out.write(border + "\n")
		
		out.write("%6d %s\n" % (len(self.multiform), "multiform"))
		out.write("%6d %s\n" % (len(self.multibidix), "multibidix"))
		out.write("%6d %s\n" % (len(self.tagmismatch), "tagmismatch"))
		out.write("Total: %d\n\n" % (len(self.multiform) + len(self.multibidix) + len(self.tagmismatch)))
		
		out.write("Time: %.4f seconds\n" % self.timer) 
		
		return out.getvalue()


class MorphTest(Test):
	class AllOutput(StringIO):
		def __str__(self):
			return self.to_string()
		
		def title(self, *args): pass
		def success(self, *args): pass
		def failure(self, *args): pass		
		def result(self, *args): pass
		
		def final_result(self, hfst):
			text = "Total passes: %d, Total fails: %d, Total: %d\n"
			self.write(colourise(text % (hfst.passes, hfst.fails, hfst.fails+hfst.passes), 2))
		
		def to_string(self):
			return self.getvalue().strip()	

	class NormalOutput(AllOutput):
		def title(self, text):
			self.write(colourise("-"*len(text)+'\n', 1))
			self.write(colourise(text+'\n', 1))
			self.write(colourise("-"*len(text)+'\n', 1))

		def success(self, l, r):
			self.write(colourise("[PASS] %s => %s\n" % (l, r)))

		def failure(self, form, err, errlist):
			self.write(colourise("[FAIL] %s => %s: %s\n" % (form, err, ", ".join(errlist))))

		def result(self, title, test, counts):
			p = counts["Pass"]
			f = counts["Fail"]
			text = "Test %d - Passes: %d, Fails: %d, Total: %d\n\n"
			self.write(colourise(text % (test, p, f, p+f), 2))

	class CompactOutput(AllOutput):
		def result(self, title, test, counts):
			p = counts["Pass"]
			f = counts["Fail"]
			out = "%s %d/%d/%d" % (title, p, f, p+f)
			if counts["Fail"] > 0:
				self.write(colourise("[FAIL] %s\n" % out))
			else:
				self.write(colourise("[PASS] %s\n" % out))
			
	def __init__(self, f=None, **kwargs):
		self.args = dict(kwargs)
		self.f = self.args.get('test_file', f)

		self.fails = 0
		self.passes = 0

		self.count = OrderedDict()
		self.load_config()

	def run(self):
		timing_begin = time.time()
		self.run_tests(self.args['test'])
		self.timer = time.time() - timing_begin
		return 0

	def load_config(self):
		global colourise
		f = yaml.load(open(self.f), _OrderedDictYAMLLoader)
		
		section = self.args['section']
		if not section in f["Config"]:
			raise AttributeError("'%s' not found in Config of test file." % section)
		
		self.program = shlex.split(self.args.get('app') or f["Config"][section].get("App", "hfst-lookup"))
		whereis([self.program[0]])

		self.gen = self.args.get('gen') or f["Config"][section].get("Gen", None)
		self.morph = self.args.get('morph') or f["Config"][section].get("Morph", None)
	
		if self.gen == self.morph == None:
			raise AttributeError("One of Gen or Morph must be configured.")

		for i in (self.gen, self.morph):
			if i and not os.path.isfile(i):
				raise IOError("File %s does not exist." % i)
		
		if self.args.get('compact'):
			self.out = MorphTest.CompactOutput()
		else:
			self.out = MorphTest.NormalOutput()
		
		if self.args.get('verbose'):
			self.out.write("`%s` will be used for parsing dictionaries.\n" % self.program)
		
		self.tests = f["Tests"]
		for test in self.tests:
			for key, val in self.tests[test].items():
				self.tests[test][key] = string_to_list(val)

		if not self.args.get('colour'):
			colourise = lambda x, y=None: x
		
	def run_tests(self, data=None):
		if self.args.get('surface') == self.args.get('lexical') == False:
			self.args['surface'] = self.args['lexical'] = True
		

		if(data != None):
			self.parse_fsts(self.tests[data[0]])
			if self.args.get('lexical'): self.run_test(data[0], True)
			if self.args.get('surface'): self.run_test(data[0], False)
		
		else:
			tests = {}
			for t in self.tests:
				tests.update(self.tests[t])
			self.parse_fsts(tests)
			for t in self.tests:
				if self.args.get('lexical'): self.run_test(t, True)
				if self.args.get('surface'): self.run_test(t, False)
		
		if self.args.get('verbose'):
			self.out.final_result(self)

	def parse_fsts(self, tests):
		invtests = invert_dict(tests)
		manager = Manager()
		self.results = manager.dict({"gen": {}, "morph": {}})

		def parser(self, d, f, tests):
			keys = tests.keys()
			app = Popen(self.program + [f], stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
			args = '\n'.join(keys) + '\n'
			
			res, err = app.communicate(args.encode('utf-8'))
			res = res.decode('utf-8').split('\n\n')
			err = err.decode('utf-8').strip()

			if app.returncode != 0:
				self.results['err'] = "\n".join(
					[i for i in [res[0], err, "(Error code: %s)" % app.returncode] if i != '']
				)
			else:
				self.results[d] = self.parse_fst_output(res)
		
		gen = Process(target=parser, args=(self, "gen", self.gen, tests))
		gen.daemon = True
		gen.start()
		if self.args.get('verbose'):
			self.out.write("Generating...\n")
		
		morph = Process(target=parser, args=(self, "morph", self.morph, invtests))
		morph.daemon = True
		morph.start()
		if self.args.get('verbose'):
			self.out.write("Morphing...\n")

		gen.join()
		morph.join()

		if self.args.get('verbose'):
			self.out.write("Done!\n")
		
	def run_test(self, data, is_lexical):
		if is_lexical:
			desc = "Lexical/Generation"
			f = "gen"
			tests = self.tests[data]

		else: #surface
			desc = "Surface/Analysis"
			f = "morph"
			tests = invert_dict(self.tests[data])
		
		if self.results.get('err'):
			raise LookupError('`%s` had an error:\n%s' % (self.program, self.results['err']))
		
		c = len(self.count)
		d = "%s (%s)" % (data, desc)
		title = "Test %d: %s" % (c, d)
		self.out.title(title)

		self.count[d] = {"Pass": 0, "Fail": 0}

		for test, forms in tests.items():
			expected_results = set(forms)
			actual_results = set(self.results[f][test])

			invalid = set()
			missing = set()
			success = set()
			passed = False

			for form in expected_results:
				if not form in actual_results:
					missing.add(form)

			for form in actual_results:
				if not form in expected_results:
					invalid.add(form)
		
			for form in actual_results:
				if not form in (invalid | missing):
					passed = True
					success.add(form)
					self.count[d]["Pass"] += 1
					if not self.args.get('hide_pass'):
						self.out.success(test, form)				
			
			if not self.args.get('hide_fail'):
				if len(invalid) > 0:
					self.out.failure(test, "unexpected results", invalid)
					self.count[d]["Fail"] += len(invalid)
				if len(missing) > 0 and \
						(not self.args.get('ignore_analyses') or not passed):
					self.out.failure(test, "missing results", missing)
					self.count[d]["Fail"] += len(missing)

		self.out.result(title, c, self.count[d])
		
		self.passes += self.count[d]["Pass"]
		self.fails += self.count[d]["Fail"]
	
	def parse_fst_output(self, fst):
		parsed = {}
		for item in fst:
			res = item.replace('\r\n','\n').replace('\r','\n').split('\n')
			for i in res:
				if i.strip() != '':
					results = i.split('\t')
					key = results[0].strip()
					if not key in parsed:
						parsed[key] = set()
					# This test is needed because xfst's lookup
					# sometimes output strings like
					# bearkoe\tbearkoe\t+N+Sg+Nom, instead of the expected
					# bearkoe\tbearkoe+N+Sg+Nom
					if len(results) > 2 and results[2][0] == '+':
						parsed[key].add(results[1].strip() + results[2].strip())
					else:
						parsed[key].add(results[1].strip())
		return parsed

	def to_xml(self):
		q = Element('config')
		q.attrib["value"] = self.f
		
		r = SubElement(q, "revision", value=str(self._svn_revision(dirname(self.f))),
					timestamp=datetime.utcnow().isoformat(),
					checksum=self._checksum(open(self.f, 'rb').read()))
		
		s = SubElement(r, 'gen')
		s.attrib["value"] = self.gen
		s.attrib["checksum"] = self._checksum(open(self.gen, 'rb').read())
		
		s = SubElement(r, 'morph')
		s.attrib["value"] = self.morph
		s.attrib["checksum"] = self._checksum(open(self.morph, 'rb').read())
		
		SubElement(r, 'total').text = str(self.passes + self.fails)
		SubElement(r, 'passes').text = str(self.passes)
		SubElement(r, 'fails').text = str(self.fails)
		
		s = SubElement(r, 'tests')
		for k, v in self.count.items():
			t = SubElement(s, 'test')
			t.text = str(k)
			t.attrib['fails'] = str(v["Fail"])
			t.attrib['passes'] = str(v["Pass"])
		
		s = SubElement(r, "system")
		SubElement(s, "speed").text = "%.4f" % self.timer
		
		return ("morph", etree.tostring(r))

	def to_string(self):
		return self.out.getvalue().strip()


class RegressionTest(Test):
	wrg = re.compile(r"{{test\|(.*)}}")
	ns = "{http://www.mediawiki.org/xml/export-0.3/}"
	program = "apertium"
	
	def __init__(self, url=None, mode=None, directory=".", **kwargs):
		url = kwargs.get('url', url)
		mode = kwargs.get('mode', mode)
		directory = kwargs.get('directory', directory)
		if None in (url, mode):
			raise ValueError("Url or mode parameter missing.")

		whereis([self.program])
		self.mode = mode
		
		self.directory = directory
		if url.startswith('http'):
			self.tree = etree.parse(urllib.request.urlopen(url))
		else:
			self.tree = etree.parse(open(url))
		
		self.passes = 0
		self.total = 0
		text = None
		for e in self.tree.getroot().getiterator():
			if e.tag == self.ns + "title":
				self.title = e.text
			if e.tag == self.ns + "revision":
				self.revision = e[0].text
			if e.tag == self.ns + "text":
				text = e.text
		if not text:
			raise AttributeError("No text element?")
		
		self.tests = defaultdict(OrderedDict)
		rtests = text.split('\n')
		rtests = [self.wrg.search(j) for j in rtests if self.wrg.search(j)]
		for i in rtests:
			test = i.group(1).split('|')
			if len(test) < 3:
				continue
			comment = None
			if len(test) >= 3:
				lang, left, right = test[0:3]
				if not left.endswith('.'):
					left += '[_].'
			if len(test) >= 4:
				comment = test[3].strip()
			self.tests[lang.strip()][left.strip()] = [right.strip(), comment]
		self.out = StringIO()
	
	def run(self):
		timing_begin = time.time()
		for side in self.tests:
			self.out.write("Now testing: %s\n" % side)
			
			args = '\n'.join(self.tests[side].keys())
			app = Popen([self.program, '-d', self.directory, self.mode], stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
			app.stdin.write(args.encode('utf-8'))
			res = app.communicate()[0]
			
			self.results = str(res.decode('utf-8')).split('\n')
			if app.returncode > 0:
				return app.returncode

			for n, test in enumerate(self.tests[side].items()):
				if n >= len(self.results):
					self.out.write("WARNING: more tests than results!\n")
					continue
				
				res = self.results[n].split("[_]")[0].strip()
				orig = test[0].split("[_]")[0].strip()
				targ = test[1][0].strip()
				
				self.out.write("%s\t  %s\n" % (self.mode, orig))
				if res == targ:
					self.out.write("WORKS\t  %s\n" % res)
					if not test[1][1] is None:
						self.out.write("//\t  %s\n" % test[1][1].strip())
					self.passes += 1
				else:
					self.out.write("\t- %s\n" % targ)
					self.out.write("\t+ %s\n" % res)
				
				self.total += 1
				self.out.write('\n')
			self.out.write("Passes: %d/%d, Success rate: %.2f%%\n" 
					% (self.passes, self.total, self.get_total_percent()))
		self.timer = time.time() - timing_begin
		return 0

	def get_passes(self):
		return self.passes

	def get_fails(self):
		return self.total - self.passes

	def get_total(self):
		return self.total
	
	def get_total_percent(self):
		if self.get_total() == 0:
			return 0
		return float(self.passes)/float(self.total)*100
	
	def to_xml(self):
		ns = self.ns
		page = self.tree.getroot().find(ns + "page")
		
		q = Element('title')
		q.attrib['value'] = page.find(ns + 'title').text
		q.attrib['revision'] = page.find(ns + 'revision').find(ns + 'id').text
		
		r = SubElement(q, 'revision', 
					value=str(self._svn_revision(self.directory)),
					timestamp=datetime.utcnow().isoformat())
		
		SubElement(r, 'percent').text = "%.2f" % self.get_total_percent()
		SubElement(r, 'total').text = str(self.get_total())
		SubElement(r, 'passes').text = str(self.get_passes())
		SubElement(r, 'fails').text = str(self.get_fails())
		
		s = SubElement(r, "system")
		SubElement(s, "speed").text = "%.4f" % self.timer
		
		return ("regression", etree.tostring(q))

	def to_string(self):
		return self.out.getvalue().strip()


class VocabularyTest(Test):
	def __init__(self, direction, lang1, lang2, output, 
				fdir=".", ana=None, gen=None):
		whereis(['apertium-transfer', 'apertium-pretransfer', 'lt-expand'])
		dictlang = langpair = "%s-%s" % (lang1, lang2)
		if direction.lower() == "rl":
			langpair = "%s-%s" % (lang2, lang1)
		
		tnxcount = len(glob(pjoin(fdir, '*.{0}-{1}.t[1-9]x'.format(lang1, lang2))))
		if tnxcount == 0:
			raise ValueError("No tnx files found. Try compiling your dictionary or something.")
		
		cmd = ["apertium-pretransfer"]
		for i in range(1, tnxcount+1):
			if i == 1:
				cmd.append("""apertium-transfer {0}/apertium-{1}.{2}.t1x \
							{0}/{2}.t1x.bin \
							{0}/{2}.autobil.bin""".format(fdir, dictlang, langpair))
			elif i < tnxcount:
				cmd.append("""apertium-interchunk {0}/apertium-{1}.{2}.t{3}x \
							{0}/{2}.t{3}x.bin""".format(fdir, dictlang, langpair, i))
			elif i == tnxcount:
				cmd.append("""apertium-postchunk {0}/apertium-{1}.{2}.t{3}x \
							{0}/{2}.t{3}x.bin""".format(fdir, dictlang, langpair, i))
		self.transfer_cmd = " | ".join(cmd)
		
		self.lang1 = lang1
		self.lang2 = lang2
		self.output = output
		self.out = open(output, 'w')
		
		self.tmp = []
		for i in range(3):
			self.tmp.append(NamedTemporaryFile(delete=False))
			self.tmp[i].close()
		
		self.fdir = fdir
		self.anadix = ana or pjoin(fdir, "apertium-{0}.{1}.dix".format(dictlang, langpair.split('-')[0]))
		self.genbin = gen or pjoin(fdir, "{0}.autogen.bin".format(langpair))
		
		self.alphabet = DixFile(self.anadix).get_alphabet()
		self.counter = None
		
	def run(self):
		#TODO: pythonise the awk command
		cmd = r"""lt-expand {dix} | awk -vPATTERN="[{alph}]:(>:)?[{alph}]" -F':|:>:' '$0 ~ PATTERN {{ gsub("/","\\/",$2); print "^" $2 "$ ^.<sent>$"; }}' | tee {f0} | {transfer} | tee {f1} | lt-proc -d {bin} > {f2}""".format(
			dix=self.anadix,
			bin=self.genbin,
			transfer=self.transfer_cmd,
			alph=self.alphabet,
			f0=self.tmp[0].name,
			f1=self.tmp[1].name,
			f2=self.tmp[2].name
		)

		for i in range(3):
			self.tmp[i] = open(self.tmp[i].name, 'r')
		
		timing_begin = time.time()
		p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, close_fds=True)
		res, err = p.communicate()
		self.timer = time.time() - timing_begin
		
		arrow_output = "{:<24} {A} {:<24} {A} {:<24}\n"
		regex = re.compile(r"(\^.<sent>\$|\\| \.$)")
		for a, b, c in zip(self.tmp[0], self.tmp[1], self.tmp[2]):
			a = regex.sub("", a).strip()
			b = regex.sub("", b).strip()
			c = regex.sub("", c).strip()
			self.out.write(arrow_output.format(a, b, c, A=ARROW))
		
		# TODO: allow saving this
		for i in self.tmp:
			i.close()
			os.unlink(i.name)
		
		self.out.close()
		self.get_symbol_count()
		
	def get_symbol_count(self):
		c = Counter()
		f = open(self.output, 'r')
		for line in f:
			c['lines'] += 1
			for char in line:
				if char in ("#", "@"):
					c[char] += 1
		self.counter = c

	def to_xml(self):
		q = Element('dictionary')
		q.attrib["value"] = basename(abspath(self.fdir))
		
		r = SubElement(q, "revision", 
					value=str(self._svn_revision(basename(abspath(self.fdir)))),
					timestamp=datetime.utcnow().isoformat())
		
		SubElement(r, "lines").text = str(self.counter['lines'])
		SubElement(r, "hashes").text = str(self.counter['#'])
		SubElement(r, "ats").text = str(self.counter['@'])
		
		s = SubElement(r, "system")
		SubElement(s, "speed").text = "%.4f" % self.timer
		
		return ("vocabulary", etree.tostring(q))

	def to_string(self):
		x = "Lines: %s\n" % self.counter['lines']
		x += "# count: %s\n" % self.counter['#']
		x += "@ count: %s\n\n" % self.counter['@']
		x += "Time: %.4f seconds\n" % self.timer
		return "%sData output to %s." % (x, self.output)


# SUPPORT FUNCTIONS

def string_to_list(data):
	if isinstance(data, bytes): return [data.decode('utf-8')]
	elif isinstance(data, str): return [data]
	else: return data
	
def invert_dict(data):
		tmp = OrderedDict()
		for key, val in data.items():
			for v in string_to_list(val):
				tmp.setdefault(v, set()).add(key)
		return tmp 

def colourise(string, opt=None):
	#TODO per class, make into a class too
	def red(s="", r="\033[m"):
		return "\033[1;31m%s%s" % (s, r) 
	def green(s="", r="\033[m"):
		return "\033[0;32m%s%s" % (s, r) 
	def orange(s="", r="\033[m"):
		return "\033[0;33m%s%s" % (s, r) 
	def yellow(s="", r="\033[m"):
		return "\033[1;33m%s%s" % (s, r) 
	def blue(s="", r="\033[m"):
		return "\033[0;34m%s%s" % (s, r) 
	def light_blue(s="", r="\033[m"):
		return "\033[0;36m%s%s" % (s, r) 
	def reset(s=""):
		return "\033[m%s" % s

	if not opt:
		x = string
		x = x.replace("=>", blue("=>"))
		x = x.replace("<=", blue("<="))
		x = x.replace(":", blue(":"))
		x = x.replace("[PASS]", green("[PASS]"))
		x = x.replace("[FAIL]", red("[FAIL]"))
		return x
	
	elif opt == 1:
		return light_blue(string)

	elif opt == 2:
		x = string.replace('asses: ', 'asses: %s' % green(r=""))
		x = x.replace('ails: ', 'ails: %s' % red(r=""))
		x = x.replace(', ', reset(', '))
		x = x.replace('otal: ', 'otal: %s' % light_blue(r=""))
		return "%s%s" % (x, reset())


# SUPPORT CLASSES

class LookupError(Exception):
	pass

# Courtesy of https://gist.github.com/844388. Thanks!
class _OrderedDictYAMLLoader(yaml.Loader):
	"""A YAML loader that loads mappings into ordered dictionaries."""

	def __init__(self, *args, **kwargs):
		yaml.Loader.__init__(self, *args, **kwargs)

		self.add_constructor('tag:yaml.org,2002:map', type(self).construct_yaml_map)
		self.add_constructor('tag:yaml.org,2002:omap', type(self).construct_yaml_map)

	def construct_yaml_map(self, node):
		data = OrderedDict()
		yield data
		value = self.construct_mapping(node)
		data.update(value)

	def construct_mapping(self, node, deep=False):
		if isinstance(node, yaml.MappingNode):
			self.flatten_mapping(node)
		else:
			raise yaml.constructor.ConstructorError(None, None,
				'expected a mapping node, but found %s' % node.id, node.start_mark)

		mapping = OrderedDict()
		for key_node, value_node in node.value:
			key = self.construct_object(key_node, deep=deep)
			try:
				hash(key)
			except TypeError as exc:
				raise yaml.constructor.ConstructorError('while constructing a mapping',
					node.start_mark, 'found unacceptable key (%s)' % exc, key_node.start_mark)
			value = self.construct_object(value_node, deep=deep)
			mapping[key] = value
		return mapping

