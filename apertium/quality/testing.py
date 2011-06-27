# -*- coding: utf-8 -*-

import os.path, re, yaml
pjoin = os.path.join
from collections import defaultdict, Counter, OrderedDict

import xml.etree.cElementTree as etree
import urllib.request

from multiprocessing import Process, Manager
from subprocess import Popen, PIPE
from io import StringIO

from apertium import whereis, destxt, retxt, checksum
from apertium.quality import Statistics

ARROW = "\u2192"


class RegressionTest(object):
	wrg = re.compile(r"{{test\|(.*)\|(.*)\|(.*)}}")
	ns = "{http://www.mediawiki.org/xml/export-0.3/}"
	program = "apertium"
	
	def __init__(self, url=None, mode=None, directory=".", **kwargs):
		url = kwargs.get('url', url)
		mode = kwargs.get('mode', mode)
		directory = kwargs.get('directory', directory)
		if None in (url, mode):
			raise TypeError("Url or mode parameter missing.")

		whereis([self.program])
		if not "Special:Export" in url:
			print("Warning: URL did not contain Special:Export.")
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
				self.revision = e[0].text # should be <id>
			if e.tag == self.ns + "text":
				text = e.text
		if not text:
			raise AttributeError("No text element?")
		
		self.tests = defaultdict(OrderedDict)
		rtests = text.split('\n')
		rtests = [self.wrg.search(j) for j in rtests if self.wrg.search(j)]
		for i in rtests:
			lang, left, right = i.group(1), i.group(2), i.group(3)
			if not left.endswith('.'):
				left += '[_].'
			self.tests[lang.strip()][left.strip()] = right.strip()
		self.out = StringIO()
	
	def run(self):
		for side in self.tests:
			self.out.write("Now testing: %s\n" % side)
			args = '\n'.join(self.tests[side].keys())
			app = Popen([self.program, '-d', self.directory, self.mode], stdin=PIPE, stdout=PIPE, stderr=PIPE)
			app.stdin.write(args.encode('utf-8'))
			res = app.communicate()[0]
			self.results = str(res.decode('utf-8')).split('\n')
			if app.returncode > 0:
				return app.returncode

			for n, test in enumerate(self.tests[side].items()):
				if n >= len(self.results):
					#raise AttributeError("More tests than results.")
					continue
				res = self.results[n].split("[_]")[0].strip()
				orig = test[0].split("[_]")[0].strip()
				targ = test[1].strip()
				self.out.write("%s\t  %s\n" % (self.mode, orig))
				if res == targ:
					self.out.write("WORKS\t  %s\n" % res)
					self.passes += 1
				else:
					self.out.write("\t- %s\n" % targ)
					self.out.write("\t+ %s\n" % res)
				self.total += 1
				self.out.write('\n')
		return 0

	def get_passes(self):
		return self.passes

	def get_fails(self):
		return self.total - self.passes

	def get_total(self):
		return self.total
	
	def get_total_percent(self):
		return "%.2f" % (float(self.passes)/float(self.total)*100)
	
	def save_statistics(self, f):		
		stats = Statistics(f)
		ns = "{http://www.mediawiki.org/xml/export-0.3/}"
		page = self.tree.getroot().find(ns + 'page')
		rev = page.find(ns + 'revision').find(ns + 'id').text
		title = page.find(ns + 'title').text
		stats.add_regression(title, rev, self.passes, self.total, self.get_total_percent())
		stats.write()

	def get_output(self):
		print(self.out.getvalue())
		percent = 0
		if self.total > 0:
			percent = float(self.passes) / float(self.total) * 100
		print("Passes: %d/%d, Success rate: %.2f%%" % (self.passes, self.total, percent))


class CoverageTest(object):
	def __init__(self, f=None, dct=None, **kwargs):
		f = kwargs.get('f', f)
		dct = kwargs.get('dct', dct)
		if None in (f, dct):
			raise TypeError("f or dct parameter missing.")
			
		whereis(["lt-proc"])#, "apertium-destxt", "apertium-retxt"):
		self.fn = f #TODO: make sure file exists
		self.f = open(f, 'r')
		self.dct = dct
		self.result = None
		
	def run(self):
		if not self.result:
			delim = re.compile(r"\$[^^]*\^")			
			f = self.f.read()
			self.f.seek(0)

			output = destxt(f).encode('utf-8')
			proc = Popen(['lt-proc', self.dct], stdin=PIPE, stdout=PIPE)
			output = str(proc.communicate(output)[0].decode('utf-8'))
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
			out.write("%d\t %s\n" % (count, word))
		return out.getvalue()
		
	def get_coverage(self):
		a = float(len(self.get_known_words()))
		b = float(len(self.get_words()))
		return a / b * 100
	
	def save_statistics(self, f):
		stats = Statistics(f)
		
		wrx = re.compile(r"\^(.*)/")

		cfn = os.path.basename(self.fn)
		dfn = os.path.basename(self.dct)
		cck = checksum(self.f.read())
		dck = checksum(open(self.dct).read())
		cov = "%.2f" % self.get_coverage()
		words = len(self.get_words())
		kwords = len(self.get_known_words())
		ukwords = len(self.get_unknown_words())
		topukwtmp = self.get_top_unknown_words()
		topukw = []
		for word, count in topukwtmp:
			topukw.append((wrx.search(word).group(1), count))
		
		stats.add_coverage(cfn, dfn, cck, dck, cov, words, kwords, ukwords, topukw)
		stats.write()

	def get_output(self):
		print("Number of tokenised words in the corpus:",len(self.get_words()))
		print("Number of known words in the corpus:",len(self.get_known_words()))
		print("Coverage: %.2f%%" % self.get_coverage())
		print("Top unknown words in the corpus:")
		print(self.get_top_unknown_words_string())


'''class VocabularyTest(object):
	class DIXHandler(ContentHandler):
		def __init__(self):
			self.alph = None
		
		def startElement(self, tag, attrs):
			if tag == "alphabet":
				self.tag == "alphabet"

		def characters(self, ch):
			if self.tag == "alphabet":
				self.alph = ch.strip()

	def get_alphabet(self, f):
		parser = make_parser()
		handler = self.DIXHandler()
		parser.setContentHandler(handler)
		parser.parse(f)
		self.alph = hander.alph
	
	def __init__(self, lang1, lang2, transfer, fdir="."):
		self.out = StringIO()
		self.fdir = fdir
		self.lang1 = lang1
		self.lang2 = lang2
		self.transfer = transfer
		self.prefix = prefix = "%s-%s" % (lang1, lang2)
		self.basename = basename = "apertium-%s" % self.prefix

		self.anadix = pjoin(fdir, "%s.%s.dix" % (basename, lang1))
		self.genbin = pjoin(fdir, "%s.autogen.bin" % prefix)

		self.get_alphabet(anadix)
		self.delim = re.compile("[%s]:(>:)?[%s]" % (self.alph, self.alph))

		#TODO whereis binaries
		
	def run(self):
		p = Popen(['lt-expand', self.anadix], stdout=PIPE)
		dixout = p.communicate()[0]
	
	def save_statistics(self, f):
		return NotImplemented

	def get_output(self):
		return NotImplemented
'''


class AmbiguityTest(object):
	delim = re.compile(":[<>]:")

	def __init__(self, f, **kwargs):
		self.f = kwargs.get('f', f)
		self.program = "lt-expand"
		whereis([self.program])
	
	def get_results(self):
		app = Popen([self.program, self.f], stdin=PIPE, stdout=PIPE)
		res = str(app.communicate()[0].decode('utf-8'))
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
		self.get_results()
		self.get_ambiguity()
		return 0

	def save_statistics(self, f):
		stats = Statistics(f)
		fck = checksum(open(self.f, 'rb').read())
		stats.add_ambiguity(self.f, fck, self.surface_forms, self.total, self.average)
		stats.write()

	def get_output(self):
		print("Total surface forms: %d" % self.surface_forms)
		print("Total analyses: %d" % self.total)
		print("Average ambiguity: %.2f" % self.average)


class HfstTest(object):
	class AllOutput(StringIO):
		def get_output(self):
			return self.getvalue()

		def final_result(self, hfst):
			text = "Total passes: %d, Total fails: %d, Total: %d\n"
			self.write(colourise(text % (hfst.passes, hfst.fails, hfst.fails+hfst.passes), 2))

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
		def title(self, *args):
			pass

		def success(self, *args):
			pass

		def failure(self, *args):
			pass

		def result(self, title, test, counts):
			p = counts["Pass"]
			f = counts["Fail"]
			out = "%s %d/%d/%d" % (title, p, f, p+f)
			if counts["Fail"] > 0:
				self.write(colourise("[FAIL] %s\n" % out))
			else:
				self.write(colourise("[PASS] %s\n" % out))
			
	def __init__(self, **kwargs):
		self.args = dict(kwargs)

		self.fails = 0
		self.passes = 0

		self.count = OrderedDict()
		self.load_config()

	def run(self):
		self.run_tests(self.args['test'])
		return 0

	def load_config(self):
		global colourise
		f = yaml.load(open(self.args['test_file'][0]), _OrderedDictYAMLLoader)
		
		section = self.args['section'][0]
		if not section in f["Config"]:
			raise AttributeError("'%s' not found in Config of test file." % section)
		
		self.program = f["Config"][section].get("App", "hfst-lookup")
		whereis([self.program])

		self.gen = f["Config"][section].get("Gen", None)
		self.morph = f["Config"][section].get("Morph", None)
	
		if self.gen == self.morph == None:
			raise AttributeError("One of Gen or Morph must be configured.")

		for i in (self.gen, self.morph):
			if i and not os.path.isfile(i):
				raise IOError("File %s does not exist." % i)
		
		if self.args.get('compact'):
			self.out = HfstTest.CompactOutput()
		else:
			self.out = HfstTest.NormalOutput()
		
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
			app = Popen([self.program, f], stdin=PIPE, stdout=PIPE, stderr=PIPE)
			args = '\n'.join(keys) + '\n'
			res = str(app.communicate(args.encode('utf-8'))[0].decode('utf-8')).split('\n\n')
			if app.returncode > 0:
				self.results[d] = res[0]
			elif res[0] == '':
				self.results[d] = "Possible segfault"
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
		
		if isinstance(self.results[f], str):
			raise LookupError('%s had an error:\n%s' % (self.program, self.results[f]))
		
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

	def save_statistics(self, f):
		stats = Statistics(f)
		stats.add_hfst(self.args['test_file'][0], checksum(open(self.args['test_file'][0]).read()), 
					self.gen, checksum(open(self.gen, 'rb').read()), 
					self.morph, checksum(open(self.morph, 'rb').read()),
					self.count, self.passes, self.fails)
		stats.write()

	def get_output(self):
		print(self.out.get_output())



# SUPPORT FUNCTIONS

def string_to_list(data):
	if isinstance(data, bytes): raise TypeError("Function does not accept bytes as input.")
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

