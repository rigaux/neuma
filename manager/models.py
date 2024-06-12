
from datetime import datetime, date
from urllib.request import urlopen
import io
import json
import jsonref
import jsonschema

import zipfile
import os
import shortuuid

from django.db import models
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.core.files.base import ContentFile, File

from .utils import OverwriteStorage

from django.contrib.auth.models import User
from django.db.models import Count
from django.urls import reverse
#from django.urls import reverse_lazy
from django.conf import settings


from lib.music.Score import *
from lib.music.jsonld import JsonLD

# Score model
import lib.music.annotation as annot_mod
import lib.music.source as source_mod
import lib.music.opusmeta as opusmeta_mod
import lib.music.iiifutils as iiif_mod

# DMOS parser
from lib.collabscore.parser import CollabScoreParser, OmrScore
from lib.collabscore.editions import Edition


# For tree models
from mptt.models import MPTTModel, TreeForeignKey

import inspect
from pprint import pprint
import music21 as m21

import verovio

from xml.dom import minidom
import itertools
import uuid
from hashlib import md5

# Note : we no longer need sklearn nor scipy
#from lib.neumautils.stats import symetrical_chi_square
#from lib.neumautils.matrix_transform import matrix_transform
#from lib.neumautils.kmedoids import cluster


# Get an instance of a logger
# See https://realpython.com/python-logging/

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# For the console
c_handler = logging.StreamHandler()
c_handler.setLevel(logging.INFO)
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
logger.addHandler(c_handler)

def set_logging_level(level):
	logger.setLevel(level)

class Person (models.Model):
	'''Persons (authors, composers, etc)'''
	first_name = models.CharField(max_length=100)
	last_name = models.CharField(max_length=100)
	year_birth = models.IntegerField()
	year_death = models.IntegerField()
	dbpedia_uri = models.CharField(max_length=255,null=True)

	class Meta:
		db_table = "Person"	

	def __str__(self):  # __unicode__ on Python 2
		return self.first_name  + "  " + self.last_name
	
	def to_json (self):
		return {"first_name": self.first_name,
			"last_name": self.last_name,
			"year_birth": self.year_birth,
			"year_death": self.year_death,
			"dbpedia_uri": self.dbpedia_uri			
			}
	
class Licence (models.Model):
	'''Description of a licence'''
	code = models.CharField(max_length=25,primary_key=True)
	name = models.CharField(max_length=100)
	url = models.CharField(max_length=255,null=True,blank=True)
	notice =   models.TextField()
	full_text =   models.TextField(null=True,blank=True)

	class Meta:
		db_table = "Licence"	

	def __str__(self):  # __unicode__ on Python 2
		return "(" + self.code + ") " + self.name

class Corpus(models.Model):
	title = models.CharField(max_length=255)
	short_title = models.CharField(max_length=255)
	description = models.TextField()
	short_description = models.TextField()
	is_public = models.BooleanField(default=True)
	parent = models.ForeignKey('self', null=True,on_delete=models.CASCADE)
	composer = models.ForeignKey(Person, null=True,blank=True,on_delete=models.PROTECT)
	creation_timestamp = models.DateTimeField('Created',auto_now_add=True)
	update_timestamp = models.DateTimeField('Updated',auto_now=True)
	ref = models.CharField(max_length=255,unique=True)
	licence = models.ForeignKey(Licence, null=True,blank=True,on_delete=models.PROTECT)
	copyright = models.CharField(max_length=255,null=True,blank=True)
	supervisors = models.CharField(max_length=255,null=True,blank=True)

	def upload_path(self, filename):
		'''Set the path where corpus-related files must be stored'''
		return 'corpora/%s/%s' % (self.ref.replace(settings.NEUMA_ID_SEPARATOR, "/"), filename)
	cover = models.FileField(upload_to=upload_path,null=True,storage=OverwriteStorage())


	def __init__(self, *args, **kwargs):
		super(Corpus, self).__init__(*args, **kwargs)

		# Non persistent fields
		self.children = []
		self.matrix = {}

	class Meta:
		db_table = "Corpus"

#		permissions = (
#			('view_corpus', 'View corpus')
#			('import_corpus', 'Import corpus'),
#		)

	def __str__(self):			  # __unicode__ on Python 2
		return "(" + self.ref + ") " + self.title

	@staticmethod
	def local_ref(ref):
		"""
			Get the local ref from the full corpus ref
		"""
		if settings.NEUMA_ID_SEPARATOR in ref:
			# Find the last occurrence of the separator
			last_pos = ref.rfind(settings.NEUMA_ID_SEPARATOR)
			return ref[last_pos+1:]
		else:
			# Top-level corpus
			return ref

	@staticmethod
	def parent_ref(ref):
		"""
			Get the parent ref from the full corpus ref
		"""
		if settings.NEUMA_ID_SEPARATOR in ref:
			# Find the last occurrence of the separator
			last_pos = ref.rfind(settings.NEUMA_ID_SEPARATOR)
			return ref[:last_pos]
		else:
			# Top-level corpus
			return ""
		
	@staticmethod
	def make_ref_from_local_and_parent(local_ref, parent_ref):
		"""
			Create the corpus reference from the local reference and parent reference
		"""
		return parent_ref + settings.NEUMA_ID_SEPARATOR + local_ref

	def get_cover(self):
		"""
			Return the corpus cover if exists, else take the parent cover (recursively)
		"""
		if self.cover != "":
			return self.cover;
		elif self.parent is not None:
			return self.parent.get_cover()
		else:
			# Should not happen: a top level corpus without image
			return ""

	def get_url(self):
		"""
			Get the URL to the Web corpus page, taken from urls.py
		"""
		return reverse('home:corpus', args=[self.ref])

	def load_from_dict(self, dict_corpus):

		"""Load content from a dictionary."""
		self.title = dict_corpus["title"]
		self.short_title = dict_corpus["short_title"]
		self.description = dict_corpus["description"]
		self.short_description = dict_corpus["short_description"]
		self.is_public = dict_corpus["is_public"]
		if "licence_code" in dict_corpus:
			try:
				self.licence = Licence.objects.get(code=dict_corpus["licence_code"])
			except Licence.DoesNotExist:
				print ("Unknown licence. Ignored. Did you run setup_neuma?")
		if "composer" in dict_corpus:
			try:
				self.composer = Person.objects.get(dbpedia_uri=dict_corpus["composer"])
			except Person.DoesNotExist:
				print (f"Unknown composer {dict_corpus['composer']}. Ignored. Did you run setup_neuma?")
		if "copyright" in dict_corpus:
			self.copyright = dict_corpus["copyright"]
		if "supervisors" in dict_corpus:
			self.supervisors = dict_corpus["supervisors"]
		return
	   
	def to_json(self):
		"""
		  Create a dictionary that can be used for JSON exports
		"""
		if self.licence is not None:
			licence_code = self.licence.code
		else:
			licence_code = None

		core = {"ref": Corpus.local_ref(self.ref), 
				 "title": self.title, 
				 "short_title": self.short_title, 
				 "description": self.description, 
				 "is_public": self.is_public,
				 "short_description": self.short_description,
				 "licence_code":  licence_code,
				 "copyright": self.copyright,
				 "supervisors": self.supervisors
		}
		
		if self.composer is not None:
			core["composer"] = self.composer.to_json()
		return core

		if self.composer is not None:
			core["composer"] = self.composer.dbpedia_uri
		return core

	def get_children(self, recursive=True):
		self.children = Corpus.objects.filter(parent=self).order_by("ref")
		for child in self.children:
			child.get_children(recursive)
		return self.children
	
	def parse_dmos(self):
		for opus in Opus.objects.filter(corpus=self).order_by("ref"):
			print (f"\n\nProcessing opus {opus.ref}")
			try:
				opus.parse_dmos()
			except Exception as e:
				print ("Error when trying to convert DMOS file for opus {opus.ref}:{e}")

	def get_direct_children(self):
		return self.get_children(False)

	def get_nb_children(self):
		return Corpus.objects.filter(parent=self).count()

	def get_nb_grammars(self):
		return transcription.models.Grammar.objects.filter(corpus=self).count()
	
	def get_grammars(self):
		return transcription.models.Grammar.objects.filter(corpus=self).order_by('name')

	def get_nb_opera(self):
		return Opus.objects.filter(corpus=self).count()

	def get_nb_opera_and_descendants(self):
		return Opus.objects.filter(ref__startswith=self.ref).count()

	def get_opera(self):
		return Opus.objects.filter(corpus=self).order_by('ref')

	def generate_sim_matrix(self):
		''' Compute distance matrix and store them in database in form
			of triplets (opus,opus,distance) '''

		all_pairs = itertools.combinations(self.get_opera(),2)
		i,l = 0, len(list(all_pairs))

		missing_score = {}
		error_status = {}

		for pair in itertools.combinations(self.get_opera(),2):
			#print(str(i)+'/'+str(l),end="	")
			if pair[0].ref != pair[1].ref:
				for crit in SimMeasure.objects.order_by('code'):#does this work without @/map ?
					self.matrix[crit] = {} # temp local storage

#					print ("Process opus " + matrix.opus1.ref + " and opus " + matrix.opus2.ref)
					try:
						hist1 = pair[0].get_histograms(crit)#.values() 
					except LookupError:
						missing_score[pair[0].ref] = True
						continue				
					except Exception as e:
						error_status[pair[0].ref] = True
						continue										

					try:
						hist2 = pair[1].get_histograms(crit)#.values()
					except LookupError:
						missing_score[pair[1].ref] = True
						continue				
					except Exception as e:
						error_status[pair[1].ref] = True
						continue						  

					# Make the two histogram have the same keys
					# This solves rhythms "problem"
					for a in set(hist1.keys()).union(set(hist2.keys())):
						if a not in hist1:
							hist1[a] = 0
						if a not in hist2:
							hist2[a] = 0
			  

					value = symetrical_chi_square(list(hist1.values()),list(hist2.values()))

					# Note : we update or create value to avoid duplication of matrix in DB
					if value != 'nan':
						SimMatrix.objects.update_or_create(
							sim_measure = crit,
							opus1 = pair[0],
							opus2 = pair[1],
							value = value
						)
						SimMatrix.objects.update_or_create(
							sim_measure = crit,
							opus1 = pair[1],
							opus2 = pair[0],
							value = value
						)
			i+=1
			#print("\r",end="")
		print(str(l-len(error_status)-len(missing_score))+"/"+str(l)+" combination computed")
		print("Missing score for "+str(len(missing_score))+" opera : ")
		print(",".join(missing_score.keys()))
		print("Error processing "+str(len(error_status))+" opera : ")
		print(",".join(error_status.keys()))

	def get_matrix_data(self, measure):
		# measure = SimMeasure.objects.get(code=measure)
		data = SimMatrix.objects.filter(sim_measure=measure,
										opus1__corpus=self,
										opus2__corpus=self)
		return data

	def has_matrix(self,measure):
		return len(self.get_matrix_data(measure))>0

	def generate_kmeans(self,measure_name,nb_class):

		# Prevents crash if distances haven't been computed for this corpus
		if not self.has_matrix(measure_name):
			return []


		try:
			measure = SimMeasure.objects.get(code=measure_name)
		except:
			print('Invalid measure given "'+measure_name+'"')
			return
		
		q1 = SimMatrix.objects.filter(sim_measure=measure,
				opus1__corpus=self).values_list('opus1','opus2','value')
		q2 = SimMatrix.objects.filter(sim_measure=measure,
				opus2__corpus=self).values_list('opus1','opus2','value')

		# x + (y-x)   :: note : this is missing on neighbor query !!!
		all_distances = list(q1) + list(set(q1) - set(q2))

		# Mapping distances to matrix
		#distances , map_ids = matrix_transform(all_distances)

		# Computing clusters / medoids
		#clusters , medoids = cluster(distances,int(nb_class))


		
	#	pprint(clusters)
	#	pprint(medoids)
#		pprint(list(map(lambda x:map_ids[x],clusters)))
	#	pprint(list(map(lambda x:map_ids[x],medoids)))


 #		SimMatrix.objects.update_or_create(
 #		   sim_measure = crit,
 #		   corpus = self,
 #		   value = value
 #	   )
 
		# ok FIXME : how should we store kmedoids / clusters in DB ?
		# --> how to display them on corpus page ?


		# Return n medoids
		return list(map(lambda x:map_ids[x],medoids))

	def get_medoids(self,measure,k):
		x = list(map(lambda x:Opus.objects.filter(id=x)[0],self.generate_kmeans(measure,k)))
		pprint(x)
		return x

	def export_as_zip(self, request, mode="json"):
		''' Export a corpus, its children and all opuses in
			a recursive zip file.
			By default, standard JSON files are used to encode corpus and opus
			If mode == jsonld, we export as linked data
		'''
		
		# Write the ZIP file in memory
		s = io.BytesIO()

		# The zip compressor
		zf = zipfile.ZipFile(s, "w")
	
		# Add a JSON file with meta data
		if mode == "jsonld":
			zf.writestr("corpus.json", json.dumps(self.to_jsonld()))
		else:
			zf.writestr("corpus.json", json.dumps(self.to_json()))
			# Write the cover file
			if self.cover is not None:
				try:
					with open (self.cover.path, "r") as coverfile:
						zf.writestr("cover.jpg", self.cover.read())
				except Exception as ex:
					print ("Cannot read the cover file ?" + str(ex))
			
		# Add the zip files of the children
		for child in self.get_direct_children():
			# Composer at the corpus level ? Then each child inherits the composer
			if self.composer is not None:
				child.composer = self.composer
				child.save()

			zf.writestr(Corpus.local_ref(child.ref) + ".zip", 
					child.export_as_zip(request,mode).getvalue())
			
		for opus in self.get_opera():
			# Only add files where we are not in momde JSON-LD
			if not mode == "jsonld":
				# Add MusicXML file
				if opus.musicxml:
					if os.path.exists(opus.musicxml.path):
						zf.write(opus.musicxml.path, opus.local_ref() + ".xml")
				if opus.mei:
					if os.path.exists(opus.mei.path):
						zf.write(opus.mei.path, opus.local_ref() + ".mei")
			# Add a sub dir for sources files
			source_bytes = io.BytesIO()
			# The zip compressor
			source_compressor = zipfile.ZipFile(source_bytes, "w")
			nb_source_files = 0
			for source in opus.opussource_set.all():
				if source.source_file:
					nb_source_files += 1
					source_compressor.write(source.source_file.path, 
							source.ref + "." + source.source_file.path.split(".")[-1])
				if source.manifest:
					nb_source_files += 1
					source_compressor.write(source.manifest.path, 
							source.ref + "_mnf." + source.manifest.path.split(".")[-1])
			source_compressor.close()
			if nb_source_files > 0:
				source_file = opus.local_ref() +  '.szip'
				#source_file = opus.local_ref() +  '.source_files.zip'
				zf.writestr( source_file, source_bytes.getvalue())

			# Composer at the corpus level ? Then each opus inherits the composer
			if self.composer is not None:
				opus.add_meta(OpusMeta.MK_COMPOSER, self.composer.dbpedia_uri)
				opus.save()
			# Add a JSON file with meta data
			if mode == "jsonld":
				opus_json = json.dumps(opus.to_jsonld())
			else:
				opus_json = json.dumps(opus.to_json(request))
			zf.writestr(opus.local_ref() + ".json", opus_json)
		zf.close()
		
		return s

	def to_jsonld (self):
		ontos = {"scorelib": settings.SCORELIB_ONTOLOGY_URI}
		jsonld = JsonLD (ontos)
		
		jsonld.add_type("scorelib", "Collection")
		jsonld.add_type("scorelib", "Opus")
		jsonld.add_type("scorelib", "Score")
		
		dict_corpus = {"@id": self.ref, 
			    "@type": "Collection",
				"hasCollectionTitle": self.title,
				"hasCollectionCopyright": self.copyright
				}
		if self.licence is not None:
			dict_corpus["hasLicence"] = self.licence.code
		if self.parent is not None:
			dict_corpus["isInCollection"] = self.parent.ref
			
		tab_opus = []
		for opus in self.get_opera():
			tab_opus.append(opus.to_jsonld())

		has_opus = {"hasOpus": tab_opus}
		return jsonld.get_context() | dict_corpus #| has_opus 
	
	@staticmethod
	def import_from_zip(zfile, parent_corpus, zip_name):
		''' Import a corpus from a Neuma zip export. If necessary, the
			 corpus is created, and its descriptions loaded from the json file
		'''
		opus_files = {}
		children = {}
		found_corpus_data = False
		found_cover = False
		corpus_dict = {}
		cover_data = ""
		# Scan the content of the ZIP file to find the list of opus
		for fname in zfile.namelist():
			# Skip files with weird names
			base, extension = decompose_zip_name (fname)
			if base == "" or base.startswith('_') or  base.startswith('.'):
				continue
			# Look for the corpus data file
			if base == "corpus" and extension == ".json":
				found_corpus_data = True 
				corpus_dict = json.loads(zfile.open(fname).read().decode('utf-8'))
			elif base == "cover" and extension == ".jpg":
				found_cover = True 
				cover_data = zfile.open(fname).read()
			elif extension == ".zip":
				# If not a zip of source files: A zip file with a sub corpus
				if not base.__contains__ ("source_files"):
					children[base] = zipfile.ZipFile(io.BytesIO(zfile.open(fname).read()))
			# OK, there is an Opus there
			elif (extension ==".json" or extension == ".mei" or extension == ".xml"
				or extension == '.mxl' or extension=='.krn' or extension=='.mid'):
				opus_files[base] = {"mei": "", 
						"musicxml": "",
						"compressed_xml": "",
						"json": "",
						"kern": "",
						"source_files": ""}
			else:
				print ("Ignoring file %s%s" % (base, extension))

		# Sanity
		if not found_corpus_data:
			logger.warning ("Missing corpus JSON file. Producing a skeleton with ref %s" % zip_name)
			corpus_dict = {"ref": zip_name, 
				 "title": zip_name, 
				 "short_title": zip_name, 
				 "description": zip_name, 
				 "is_public": True,
				 "short_description": zip_name,
				 "copyright": "",
				 "supervisors": ""
				}
		if not found_cover:
			logger.warning ("Missing cover for corpus " + corpus_dict['ref'])
			
		# Get the corpus, or create it
		logger.info ("Importing corpus %s in %s" % (corpus_dict['ref'], parent_corpus.ref) )
		print ("Importing corpus %s in %s" % (corpus_dict['ref'], parent_corpus.ref) )
		full_corpus_ref = Corpus.make_ref_from_local_and_parent(corpus_dict['ref'], parent_corpus.ref)
		try:
			corpus = Corpus.objects.get(ref=full_corpus_ref)
		except Corpus.DoesNotExist as e:
			# Create this corpus
			corpus = Corpus (parent=parent_corpus, ref=full_corpus_ref)
		# Load / replace content from the dictionary
		corpus.load_from_dict(corpus_dict)
		corpus.save()
		# Take the cover image
		if found_cover :
			corpus.cover.save("cover.jpg", ContentFile(cover_data))
		else:
			# Good to know: sets the file field to blank string
			corpus.cover = None
		
		# Recursive import of the children
		for base in children.keys():
			print ("*** Importing sub corpus " + base)
			corpus.import_from_zip(children[base], corpus, base)

		# Second scan: we note the files present for each opus
		for fname in zfile.namelist():
			(opus_ref, extension) = decompose_zip_name (fname)
			if opus_ref in opus_files:
				if extension == '.mxl':
					 opus_files[opus_ref]["compressed_xml"] = fname
				elif (extension == '.xml' or extension == '.musicxml'):
					opus_files[opus_ref]["musicxml"] = fname
				elif extension == '.mei':
					opus_files[opus_ref]["mei"] = fname
				elif extension == '.json':
					opus_files[opus_ref]["json"] = fname
				elif extension == '.mid':
					opus_files[opus_ref]["midi"] = fname
				elif extension == '.krn':
					opus_files[opus_ref]["kern"] = fname
				elif extension == ".szip":
					# If a zip of source files
					opus_files[opus_ref]["source_files"] = fname

		# OK, now in opus_files, we know whether we have the MusicXML, MEI or any other
		list_imported = []
		for opus_ref, opus_files_desc in opus_files.items():			
				full_opus_ref = corpus.ref + settings.NEUMA_ID_SEPARATOR + opus_ref
				print ("Import opus with ref " + opus_ref + " in corpus " +  corpus_dict['ref'])
				try:
					opus = Opus.objects.get(ref=full_opus_ref)
					
				except Opus.DoesNotExist as e:
					# Create the Opus
					opus = Opus(corpus=corpus, ref=full_opus_ref, title=opus_ref)
				list_imported.append(opus)
				opus.mei = None

				# If a json exists, then it should contain the relevant metadata
				if opus_files_desc["json"] != "":
					logger.info ("Found JSON metadata file %s" % opus_files_desc["json"])
					json_file = zfile.open(opus_files_desc["json"])
					json_doc = json_file.read()
					opus.load_from_dict (corpus, json.loads(json_doc.decode('utf-8')))
					
					# Check whether a source file exists for each source
					for source in opus.opussource_set.all():
						if opus_files_desc["source_files"] != "":
							# Yep we found one
							source_zip_content = io.BytesIO(zfile.read(opus_files_desc["source_files"]))
							source_zip = zipfile.ZipFile(source_zip_content)
							# Check in the zip file for the file that corresponds to the source
							for fname in source_zip.namelist():
								base, extension = decompose_zip_name (fname)
								if base == source.ref:
									# The file contains the source itself
									sfile_content = source_zip.read(fname)
									print (f"Saving source file {fname}")
									source.source_file.save(fname, ContentFile(sfile_content))
									# In that case the URL is irrelevant
									source.url=""
									source.save()
								if base == source.ref + "_mnf":
									# The file contains the source manifest
									print ("Import manifest")
									manifest_content = source_zip.read(fname)
									source.manifest.save(fname, ContentFile(manifest_content))
									source.save()

				# OK, we loaded metada : save
				opus.mei = None
				opus.save()
			
				if opus_files_desc["compressed_xml"] != "":
					logger.info ("Found compressed MusicXML content")
					# Compressed XML
					container = io.BytesIO(zfile.read(opus_files_desc["compressed_xml"]))
					xmlzip = zipfile.ZipFile(container)
					# Keep the file in the container with the same basename
					for name2 in xmlzip.namelist():
						basename2 = os.path.basename(name2)
						ref2 = os.path.splitext(basename2)[0]
						if opus_files_desc["opus_ref"]  == ref2:
							xml_content = xmlzip.read(name2)
					opus.musicxml.save("score.xml", ContentFile(xml_content))
				if opus_files_desc["musicxml"] != "":
					logger.info ("Found MusicXML content")
					xml_content = zfile.read(opus_files_desc["musicxml"])
					opus.musicxml.save("score.xml", ContentFile(xml_content))
				if opus_files_desc["kern"] != "":
					logger.info ("Found KERN content")
					kern_content = zfile.read(opus_files_desc["kern"])
					# We need to write in a tmp file, probably 
					tmp_file = "/tmp/tmp_kern.txt"
					f = open(tmp_file, "w")
					lines = kern_content.splitlines()
					for line in lines:
						if not (line.startswith(b"!!!ARE: ") 
							or line.startswith(b"!!!AGN: ")
							or line.startswith(b"!!!OTL: ")
							or line.startswith(b"!!!YOR: ")
							or line.startswith(b"!!!SCA: ")
							or line.startswith(b"!!!OCY: ")
							or line.startswith(b"!! ")
							):
							f.write (line.decode()  + os.linesep)
					f.close()
					try:
						tk = verovio.toolkit()
						tk.loadFile(tmp_file)
						mei_content = tk.getMEI()
						opus.mei.save("mei.xml", ContentFile(mei_content))
						doc = minidom.parseString(mei_content)
						titles = doc.getElementsByTagName("title")
						for title in titles:
							for txtnode in title.childNodes:
								opus.title = str(txtnode.data)
								break
							break
					except Exception as e:
						print ("Exception pendant le traitement d'un fichier Kern: " + str(e))
						return

				if bool(opus.mei) == False:
					if opus_files_desc["mei"] != "":
						logger.info ("Load MEI content")
						# Add the MEI file
						try:
							mei_file = zfile.open(opus_files_desc["mei"])
							mei_raw  = mei_file.read()
							encoding = "utf-8"
							try:
								logger.info("Attempt to read in UTF 8")
								mei_raw.decode(encoding)
							except Exception as ex:
								logger.info("Read in UTF 16")
								encoding = "utf-16"
								mei_raw.decode(encoding)
							logger.info("Correct encoding: " + encoding)
							mei_content = mei_raw.decode(encoding)
							logger.info ("Save the MEI file.")
							opus.mei.save("mei.xml", ContentFile(mei_content))
						except Exception as ex:
							logger.error ("Error processing MEI  " + str(ex))
					else:
						# Produce the MEI from the MusicXML
						if opus_files_desc["musicxml"] != "":
							logger.info ("Produce the MEI from MusicXML")
							try:
								print ("Produce the MEI from MusicXML")
								tk = verovio.toolkit()
								tk.loadFile(opus.musicxml.path)
								mei_content = tk.getMEI()
								opus.mei.save("mei.xml", ContentFile(mei_content))
							except Exception as e:
								print ("Exception : " + str(e))
								# Workflow.produce_opus_mei(opus)	 
						else:
							logger.warning ("No MEI, no MusicXML: opus %s is incomplete" % opus.ref)

				# Now try to obtain metadata
				if opus_files_desc["compressed_xml"]!="" or opus_files_desc["musicxml"]!="":
					# Get MusicXML metadata
					doc = minidom.parseString(xml_content)
					titles = doc.getElementsByTagName("movement-title")
					for title in titles:
						for txtnode in title.childNodes:
							opus.title = str(txtnode.data)
							break
						break
				elif opus_files_desc["compressed_xml"]!="" or opus_files_desc["musicxml"]!="":
					# Get MusicXML metadata
					doc = minidom.parseString(xml_content)
					titles = doc.getElementsByTagName("movement-title")
					for title in titles:
						for txtnode in title.childNodes:
							opus.title = str(txtnode.data)
							break
						break
					
				try:
					if opus.title == opus_ref:
						#print ("Title = " + opus.title + " Try to obtain metadata")
						logger.info ("Try to find metadata in the XML file with music21")
						score = opus.get_score()
						if score.get_title() != None and len(score.get_title()) > 0:
							opus.title = score.get_title()
						if score.get_composer() != None and len(score.get_composer()) > 0:
							opus.composer = score.get_composer()
							
					opus.save()
				except Exception as ex:
					print ("Error importing opus  " + str(ex))
					logger.error ("Error importing opus " + str(ex))
					
				print ("Opus ref " + opus_ref + " imported in corpus " + corpus.ref+ "\n")
		return list_imported
	
####################################################

class Opus(models.Model):
	corpus = models.ForeignKey(Corpus,on_delete=models.CASCADE)
	title = models.CharField(max_length=255)
	lyricist = models.CharField(max_length=255,null=True, blank=True)
	composer = models.CharField(max_length=255,null=True, blank=True)
	
	# Linked data to the composer entity
	composer_ld = models.ForeignKey(Person, null=True,blank=True,on_delete=models.PROTECT)

	ref = models.CharField(max_length=255,unique=True)
	external_link  = models.CharField(max_length=255,null=True, blank=True)
	
	# .Files names
	FILE_NAMES = {"score.xml": "musicxml", 
				   "mei.xml": "mei",
				   "summary.json": "summary"}

	def statsDic(opus):
		""" produces a dic with features"""
		stats = StatsDesc(opus)
		dico = stats.computeStats()
		return dico

	def upload_path(self, filename):
		'''Set the path where opus-related files must be stored'''
		return 'corpora/%s/%s' % (self.ref.replace(settings.NEUMA_ID_SEPARATOR, "/"), filename)

	def __init__(self, *args, **kwargs):
		super(Opus, self).__init__(*args, **kwargs)
		# Non persistent fields
		# self.stats = self.statsDic()
		self.histogram_cache={}

	# List of files associated to an Opus
	musicxml = models.FileField(upload_to=upload_path,null=True,blank=True,storage=OverwriteStorage())
	mei = models.FileField(upload_to=upload_path,null=True,blank=True,storage=OverwriteStorage(), max_length=255)
	summary = models.FileField(upload_to=upload_path,null=True,blank=True,storage=OverwriteStorage())

	class Meta:
		db_table = "Opus"

	def get_url(self):
		"""
		  Get the URL to the Web opus page, taken from urls.py
		"""
		return reverse('home:opus', args=[self.ref])

	def local_ref(self):
		"""
		The ref of the Opus inside its Corpus
		"""
		last_pos = self.ref.rfind(settings.NEUMA_ID_SEPARATOR)
		return self.ref[last_pos+1:]

	def add_meta (self, mkey, mvalue):
		"""Add a (key, value) pair as an ad-hoc attribute"""
		
		# The key must belongs to the list of pre-deefined accepted values
		if mkey not in OpusMeta.META_KEYS:
			raise Exception(f"Sorry, the key {mkey} does not belong to the accepted meta keys")
		
		# Search if exists
		try:
			meta_pair = OpusMeta.objects.get(opus=self,meta_key=mkey)
		except OpusMeta.DoesNotExist as e:

			meta_pair = OpusMeta(opus=self, meta_key=mkey, meta_value=mvalue)
			meta_pair.save()

	def get_metas (self):
		"""Return the list of key-value pairs"""
		metas = []
		for m in OpusMeta.objects.filter(opus=self):
			m.displayed_label = OpusMeta.META_KEYS[m.meta_key]["displayed_label"]
			metas.append (m)
		return metas

	def add_source (self,source_dict):
		"""Add a source to the opus"""
		
		# Search if exists
		try:
			source = OpusSource.objects.get(opus=self,ref=source_dict["ref"])
			source.description = source_dict["description"]
			source.url=source_dict["url"]
		except OpusSource.DoesNotExist as e:
			stype = SourceType.objects.get(code=source_dict["source_type"])
			source = OpusSource(opus=self,
							ref=source_dict["ref"],
							description=source_dict["description"],
							source_type=stype,
							url=source_dict["url"])
		source.save()
		return source

	def copy_mei_as_source(self):
		# Save the MEI file as a reference source 
		if self.mei:
			source_dict = {"ref": "ref_mei", 
						"source_type": SourceType.STYPE_MEI,
						"description": "Référence MEI",
						"url": ""}
			source = self.add_source (source_dict)
			source.source_file.save("ref_mei.xml", File(self.mei))

	def load_from_dict(self, corpus, dict_opus, files={}, opus_url=""):
		"""Load content from a dictionary.

		The dictionary is commonly a decrypted JSON object, coming
		either from the Neuma REST API or from ElasticSearch

		"""
		# The id can be named id or _id
		if ("ref" in dict_opus.keys()):
			self.ref = Corpus.make_ref_from_local_and_parent(dict_opus["ref"].strip(), corpus.ref)
		elif ("_ref" in dict_opus.keys()):
			self.ref = Corpus.make_ref_from_local_and_parent(dict_opus["_ref"].strip(), corpus.ref)
		else:
			raise  KeyError('Missing ref field in an Opus dictionary')

		self.corpus = corpus
		self.title = dict_opus["title"]

		if ("lyricist" in dict_opus.keys()):
			if (dict_opus["lyricist"] != None):
				self.lyricist = dict_opus["lyricist"]
		if ("composer" in dict_opus.keys()):
			if (dict_opus["composer"] != None):
				self.composer = dict_opus["composer"]
				
		# Saving before adding related objects
		self.save()

		if ("features" in dict_opus.keys()):
			if (dict_opus["features"] != None):
				for m in dict_opus["features"]:
					self.add_meta (m["feature_key"], m["feature_value"])
		if ("sources" in dict_opus.keys() 
		         and type(dict_opus["sources"]) in {list} ):
			if (dict_opus["sources"] != None):
				for source in dict_opus["sources"]:
					self.add_source (source)

		# Cas ou la source contient une réf Gallica
		if ("sources" in dict_opus.keys() 
		         and isinstance(dict_opus["sources"], str)):
			source_dict = {"ref": "iiif", 
						"source_type": "JPEG",
						"description": "Lien Gallica",
						"url": dict_opus["sources"]}
			self.add_source (source_dict)
			print ("Source Gallica: " + dict_opus["sources"] )

		# Get the Opus files
		for fname, desc  in files.items():
			if (fname in Opus.FILE_NAMES):
				print ("Found " + fname + " at URL " + opus_url + fname)
				# Take the score
				file_temp = NamedTemporaryFile()
				f = urlopen(opus_url + fname)
				content = f.read()
				file_temp.write(content)
				file_temp.flush()
				getattr(self, Opus.FILE_NAMES[fname]).save(fname, File(file_temp))

		# Get the sequence file if any
		if opus_url != "":
			print ("Try to import sequence file")
			try:
				f = urlopen(opus_url + "sequence.json")
				content = f.read().decode("utf-8")
				# test that we got it
				jseq = json.loads(content)
				if "status" in jseq.keys():
					print ("Something wrong. Received message: " + jseq["message"])
				else:
					self.music_summary = content
			except:
				print("Something wrong when getting "  + opus_url + "sequence.json")

		return

	def get_score(self):
		"""Get a score object from an XML document"""
		score = Score()
		# Try to obtain the MEI document, which contains IDs

		if self.mei:
			print ("Load from MEI")
			score.load_from_xml(self.mei.path, "mei")
			return score
		elif self.musicxml:
			print ("Load from MusicXML")
			score.load_from_xml(self.musicxml.path, "musicxml")
			return score
		else:
			raise LookupError ("Opus " + self.ref + " doesn't have any XML file attached")

	def freeze(self,filepath="./"):
		# http://web.mit.edu/music21/doc/moduleReference/moduleConverter.html#music21.converter.freeze
		try:
			score = self.get_score().m21_score
			path = filepath
			m21.converter.freeze(score, fp=path)
			# print("Opus "+self.ref+" was serialized at "+path)
		except:
			print("something went wrong in serializing with m21")
		return filepath

	def unfreeze(self,filepath="./"):
		score = m21.converter.thaw(filepath)
		return score


	@staticmethod
	def createFromMusicXML(corpus, reference, mxml_content):
		"""Create a new Opus by getting metadata as much as possible from the XML file"""
		opus_ref = corpus.ref + settings.NEUMA_ID_SEPARATOR + reference
		try:
			opus = Opus.objects.get(ref=opus_ref)
		except Opus.DoesNotExist as e:
			opus = Opus()
		
		opus.corpus = corpus
		opus.ref = opus_ref
		opus.title = reference # Temporary
		opus.musicxml.save("score.xml", ContentFile(mxml_content))
		
		doc = minidom.parseString(mxml_content)
		titles = doc.getElementsByTagName("movement-title")
		for title in titles:
			for txtnode in title.childNodes:
				opus.title = str(txtnode.data)
				print ("Found title metadata : " + opus.title)
				break
			break
		
		if opus.title == reference:
			# Try to find metadata in the XML file with music21
			score = opus.get_score()
		
			if score.get_title() != None and len(score.get_title()) > 0:
				opus.title = score.get_title()
			if score.get_composer() != None and len(score.get_composer()) > 0:
				opus.composer = score.get_composer()

		return opus
	
	def __str__(self):			  # __unicode__ on Python 2
		return self.title

	def get_histograms(self,measure):
		"""Compute the histogram feature from some measure
		   and put it in the cache. Further requests of the same
		   feature will find it in the cache"""
		measure=str(measure)

		if measure in self.histogram_cache and self.histogram_cache[measure]:
			# The histogram already exists
			return self.histogram_cache[measure]
		else:
			# We need to compute it
			score = self.get_score()
			voices = score.get_all_voices()
			if not len(voices):
				raise LookupError

			voice = voices[0] # FIXME
			if measure == 'pitches':
				self.histogram_cache[measure] = voice.get_pitches_norm()
			elif measure == 'degrees':
				self.histogram_cache[measure] = voice.get_degrees_norm()
			elif measure == 'intervals':
				self.histogram_cache[measure] = voice.get_intervals_norm()
			elif measure == 'rhythms':
				self.histogram_cache[measure] = voice.get_rhythmicfigures_norm()
			else:
				print("WARNING : unknown measure " + str(measure))#raise UnknownSimMeasure(measure)

			return self.histogram_cache[measure]

	def delete_index(self):
		#
		#   Delete opus in ElasticSearch
		#   Called by signal delete_index_opus
		#
		opus = OpusIndex.get(id=self.id, index=settings.ELASTIC_SEARCH["index"])
		result = opus.delete()
		return result

	def to_serializable(self, absolute_url):
		" Produce a serialisable object from the Opus data"
				
		if self.composer_ld is not None:
			opusmeta = opusmeta_mod.OpusMeta(self.corpus.ref, self.local_ref(), 
											self.title, 
											self.composer_ld.dbpedia_uri)
		else:
			opusmeta = opusmeta_mod.OpusMeta(self.corpus.ref, self.local_ref(), self.title, 
											self.composer, self.id)
			
		# Adding sources
		for source in self.opussource_set.all ():
			opusmeta.add_source(source.to_serializable(absolute_url))

		# Adding meta fields (features)
		for meta in self.get_metas():
			feature = opusmeta_mod.OpusFeature (meta.meta_key, meta.meta_value)
			opusmeta.add_feature(feature)

		# Adding files
		for fname, fattr in Opus.FILE_NAMES.items():
			the_file = getattr(self, fattr)
			if the_file:
				opus_file = opusmeta_mod.OpusFile (fname, absolute_url + the_file.url)
				opusmeta.add_file(opus_file)
		return opusmeta

	def to_json(self, request):
		"""
		  Produces a JSON representation (useful for REST services)
		"""
		# We need the absolute URL 
		abs_url = request.build_absolute_uri("/")[:-1]
		opusmeta = self.to_serializable(abs_url)
		return opusmeta.to_json()
	

	def to_jsonld (self):
		
		my_url = "http://neuma.huma-num.fr/"
		
		opusmeta = self.to_serializable(my_url)
		return opusmeta.to_jsonld()
	
	def create_source_with_file(self, source_ref, source_type_code,
							url, file_path=None, 
							file_name=None, file_mode="r"):
		
		try:
			source = OpusSource.objects.get(opus=self,ref=source_ref)
			description = f"{source_type_code} file updated on {date.today()}", 
		except OpusSource.DoesNotExist:
			description = f"{source_type_code} file created on {date.today()}", 
			source = OpusSource (opus=self,ref=source_ref,
								url = url)
		source.url = url 
		source.description = description
		source.source_type = SourceType.objects.get(code=source_type_code)
		source.save()
		
		if file_path is not None:
			with open(file_path,file_mode) as f:
				print (f"Replace  file for source {source_ref}")
				source.source_file.save(file_name, File(f))
				source.save()
				
		return source
		
	def parse_dmos(self):
		dmos_dir = os.path.join("file://" + settings.BASE_DIR, 'static/json/', 'dmos')
		
		# In case we just want to test annotations
		just_annotations = False 

		# Where is the schema?
		schema_dir = os.path.join(dmos_dir, 'schema/')
		# The main schema file
		schema_file = os.path.join(schema_dir, 'dmos_schema.json')
		# Parse the schema
		try:
			parser = CollabScoreParser(schema_file, schema_dir)
		except jsonschema.SchemaError as ex:
			return "Schema parsing error: " + ex.message
		except Exception as ex:
			return  "Unexpected error during parser initialization: " + str (ex)

		dmos_data = None
		dmos_source =None
		editions = []
		for source in self.opussource_set.all ():
			if source.ref == source_mod.OpusSource.IIIF_REF:
				dmos_source = source
				if dmos_source.source_file:
					dmos_data = json.loads(dmos_source.source_file.read())
				for json_edition in dmos_source.operations:
					editions.append (Edition.from_json(json_edition))

			#if source.ref == source_mod.OpusSource.DMOS_REF:
				# Clean this old source
			#	source.delete()

		if dmos_data == None:
			return "Unable to find the DMOS file ??"
		try:
			parser.validate_data (dmos_data)
		except Exception as ex:
			return "DMOS file validation error : " + str(ex)
		
		# Parse DMOS data
		omr_score = OmrScore (self.get_url(), dmos_data, {}, editions)
		score = omr_score.get_score()
	
		# Store the MusicXML file in the opus
		if not just_annotations:
			print ("Replace XML file")
			mxml_file = "/tmp/" + shortuuid.uuid() + ".xml"
			omr_score.write_as_musicxml (mxml_file)

			with open(mxml_file) as f:
				self.musicxml = File(f,name="score.xml")
				self.save()
			self.create_source_with_file(source_mod.OpusSource.MUSICXML_REF, 
									SourceType.STYPE_MXML,
							"", mxml_file, "score.xml")
		
			# Generate and store the MEI file as a source and main file
			# Create the file
			mei_file = "/tmp/" + shortuuid.uuid() + "_mei.xml"
			omr_score.write_as_mei (mxml_file, mei_file)
			with open(mei_file) as f:
				print ("Replace MEI file")
				self.mei = File(f,name="mei.xml")
				self.save()	
			mei_source = self.create_source_with_file("mei", SourceType.STYPE_MEI,
							"", mei_file, "score.mei")
		
			# Generate the MIDI file
			print ("Produce MIDI file")
			midi_file = "/tmp/score.midi"
			score.write_as_midi (midi_file)
			self.create_source_with_file(source_mod.OpusSource.MIDI_REF, 
									SourceType.STYPE_MIDI,
							"", midi_file, "score.midi", "rb")
		
			# Get the IIIF manifest for image infos
			iiif_proxy = iiif_mod.Proxy(iiif_mod.GALLICA_BASEURL)
			docid = iiif_mod.Proxy.decompose_gallica_ref(dmos_source.url)
			try:
				iiif_doc = iiif_proxy.get_document(docid)
				print (f"Got the IIIF manifest. Nb canvases {iiif_doc.nb_canvases}")
				images = iiif_doc.get_images()
				for img in images:
					print (f"Image {img.url}. Width {img.width}")
				omr_score.manifest.add_image_info (images) 
			except Exception as ex:
				logger.error(str(ex))

			# Store the manifest 
			for source in self.opussource_set.all ():
				if source.ref == source_mod.OpusSource.IIIF_REF:
					print ("Save the manifest")
					source.manifest = ContentFile(json.dumps(omr_score.manifest.to_json()), name="manifest.json")
					source.save()
		
			# Now we know the full url of the MEI document
			score.uri = mei_source.source_file.url
		else:
			score.uri = "Undetermined: change the 'just_annotations' setting"

		# <clean existing annotations
		for dba in Annotation.objects.filter(opus=self):
			if dba.target is not None:
				dba.target.delete()
			if dba.body is not None:
				dba.body.delete()
			dba.delete()

		print (f'Inserting annotations')
		user_annot = User.objects.get(username=settings.COMPUTER_USER_NAME)
		for annotation in score.annotations:
			annotation.target.resource.source = score.uri

			db_annot = Annotation.create_from_web_annotation(user_annot, 
															self, annotation)
			db_annot.target.save()
			if db_annot.body is not None:
				db_annot.body.save()
			db_annot.save()

		return score


class OpusDiff(models.Model):
	
	def upload_path(self, filename):
		'''Set the path where opus-related files must be stored'''
		return 'corpora/%s/%s' % (self.opus.ref.replace(settings.NEUMA_ID_SEPARATOR, "/"), filename)

	# Record the differences between two MEI versions of an Opus
	opus = models.ForeignKey(Opus,on_delete=models.CASCADE)
	mei_omr = models.FileField(upload_to=upload_path,null=True,blank=True,storage=OverwriteStorage())
	mei_ref = models.FileField(upload_to=upload_path,null=True,blank=True,storage=OverwriteStorage(), max_length=255)


class OpusMeta(models.Model):
	opus = models.ForeignKey(Opus,on_delete=models.CASCADE)
	meta_key = models.CharField(max_length=255)
	meta_value = models.TextField()
	
	# 
	# List of allowed meta keys, 
	MK_COLLECTION = "collection"
	MK_OFFICE = "office"
	MK_FETE = "fete"
	MK_MODE = "mode"
	MK_GENRE = "genre"
	MK_YEAR = "year"
	MK_SOLENNITE = "solennite"
	MK_TEXTE = "texte"
	MK_COMPOSER = "composer"
	MK_LYRICIST = "lyricist"
	MK_KEY_TONIC = "key_tonic_name"
	MK_KEY_MODE = "key_mode"
	MK_METER = "meter"	
	MK_NUM_OF_PARTS = "num_of_parts"
	MK_NUM_OF_MEASURES = "num_of_measures"
	MK_NUM_OF_NOTES = "num_of_notes"
	ML_INSTRUMENTS = "instruments"
	MK_LOWEST_PITCH_EACH_PART = "lowest_pitch_each_part"
	MK_HIGHEST_PITCH_EACH_PART = "highest_pitch_each_part"
	MK_MOST_COMMON_PITCHES = "most_common_pitches"
	MK_AVE_MELODIC_INTERVAL = "average_melodic_interval"
	MK_DIRECTION_OF_MOTION = "direction_of_motion"
	MK_MOST_COMMON_NOTE_QUARTER_LENGTH = "most_common_note_quarter_length"
	MK_RANGE_NOTE_QUARTER_LENGTH = "range_note_quarter_length"
	MK_INIT_TIME_SIG = "initial_time_signature"
	
	# Descriptive infos for meta pairs
	META_KEYS = {
		MK_COLLECTION: {"displayed_label": "Collection"},
		MK_OFFICE: {"displayed_label": "Office"},
		MK_FETE: {"displayed_label": "Fête"},
		MK_MODE: {"displayed_label": "Mode"},
		MK_GENRE: {"displayed_label": "Genre"},
		MK_SOLENNITE: {"displayed_label": "Degré de solennité"},
		MK_TEXTE: {"displayed_label": "Texte"},
		MK_COMPOSER: {"displayed_label": "Composer"},
		MK_LYRICIST: {"displayed_label": "Composer"},
		MK_KEY_TONIC: {"displayed_label": "Key Tonic Name"},
		MK_KEY_MODE: {"displayed_label":"Key Mode"},
		MK_METER: {"displayed_label":"Meter"},
		MK_YEAR: {"displayed_label":"Year"},
		MK_NUM_OF_PARTS: {"displayed_label": "Number of parts"},
		MK_NUM_OF_MEASURES: {"displayed_label": "Number of measures"},
		MK_NUM_OF_NOTES: {"displayed_label": "Number of notes"},
		ML_INSTRUMENTS: {"displayed_label": "Instruments"},
		MK_LOWEST_PITCH_EACH_PART: {"displayed_label": "Lowest fpitch each part"},
		MK_HIGHEST_PITCH_EACH_PART: {"displayed_label": "Highest pitch each part"},
		MK_MOST_COMMON_PITCHES: {"displayed_label": "Most common pitches"},
		MK_AVE_MELODIC_INTERVAL: {"displayed_label": "Average melodic interval"},
		MK_DIRECTION_OF_MOTION: {"displayed_label": "Direction of motion"},
		MK_MOST_COMMON_NOTE_QUARTER_LENGTH: {"displayed_label": "Most common note quarter length"},
		MK_RANGE_NOTE_QUARTER_LENGTH: {"displayed_label": "Range of note quarter length"},
		MK_INIT_TIME_SIG:{"displayed_label": "Initial time signature"}
	}

	def __init__(self, *args, **kwargs):
		super(OpusMeta, self).__init__(*args, **kwargs)

	class Meta:
		db_table = "OpusMeta"

class Patterns(models.Model):

	'''
	#TODO TIANGE: IS it necessary to store in postgres?

	Patterns class is used for storing the statistical information of patterns appeared in the dataset.
	
	pattern_dict stores the occurrence number of every pattern within the dataset/corpus/opus,
	so that the most frequent patterns existing in the dataset/corpus/opus could be found.
	'''

	opus = models.ForeignKey(Opus,on_delete=models.CASCADE)
	part = models.CharField(max_length=30)
	voice = models.CharField(max_length=30)

	#content_type: melodic, diatonic or rhythmic
	content_type = models.CharField(max_length=30)
	value = models.TextField()

	#A dictionary of melodic patterns
	mel_pattern_dict = dict()
	#A dictionary of diatonic patterns
	dia_pattern_dict = dict()
	#A dictionary of rhythmic patterns
	rhy_pattern_dict = dict()

	class Meta:
		db_table = "Patterns"

	def __str__(self):
		return self.content_type + " " + str(self.opus.ref) + " " + str(self.opus.corpus)
		#Apart from corpus, we can also get title, composer using opus information

class Descriptor(models.Model):
	'''A descriptor is a textual representation for some musical feature, used for full text indexing'''
	opus = models.ForeignKey(Opus,on_delete=models.CASCADE)
	part = models.CharField(max_length=30)
	voice = models.CharField(max_length=30)
	type = models.CharField(max_length=30)
	value = models.TextField()

	class Meta:
		db_table = "Descriptor"

	def to_dict(self):
		return dict(part=self.part, voice=self.voice, value=self.value)

	def __str__(self):
		return self.type + " " + str(self.opus.ref) + " " + str(self.opus.corpus)
	
class SourceType (models.Model):
	'''Description of the accepted types of sources'''
	code = models.CharField(max_length=25,primary_key=True)
	description = models.TextField()
	mime_type = models.CharField(max_length=255)

	# List of accepted codes
	STYPE_MEI = "MEI"
	STYPE_DMOS = "DMOS"
	STYPE_MIDI = "MIDI"
	STYPE_MXML = "MusicXML"
	STYPE_JPEG = "JPEG"
	STYPE_PDF = "PDF"
	STYPE_MPEG = "M"
		
	class Meta:
		db_table = "SourceType"	

	def __str__(self):  # __unicode__ on Python 2
		return self.description + " (" + self.code + ")"

class OpusSource (models.Model):
	'''A link to a source that contains the representation of an Opus'''
	opus = models.ForeignKey(Opus,on_delete=models.CASCADE)
	ref =   models.CharField(max_length=25)
	description =   models.TextField()
	source_type = models.ForeignKey(SourceType,on_delete=models.PROTECT)
	url = models.CharField(max_length=255,blank=True,null=True)
	# A set of operations applied to the source file. Example: post-OMR processing
	operations = models.JSONField(blank=True,default=[])
	creation_timestamp = models.DateTimeField('Created', auto_now_add=True)
	update_timestamp = models.DateTimeField('Updated', auto_now=True)

	def upload_path(self, filename):
		'''Set the path where source files must be stored'''
		source_ref = self.opus.ref.replace(settings.NEUMA_ID_SEPARATOR, "-")
		return 'sources/' + source_ref + '/' + filename
	source_file = models.FileField(upload_to=upload_path,blank=True,null=True,storage=OverwriteStorage())
	manifest = models.FileField(upload_to=upload_path,blank=True,null=True,storage=OverwriteStorage())

	class Meta:
		db_table = "OpusSource"	

	def __str__(self):  # __unicode__ on Python 2
		return "(" + self.opus.ref + ") " + self.ref

	def to_serializable(self, abs_url):
		"""
		  Create an object that can be serialized for JSON exports
		"""
		source_dict = source_mod.OpusSource(
			self.ref, self.source_type.code, self.source_type.mime_type, 
			self.url)
		source_dict.description = self.description
		if self.source_file:
			source_dict.file_path =  self.source_file.url
		if self.manifest:
			source_dict.has_manifest =  True			
		return source_dict

	def to_json(self, request):
		"""
		  Produces a JSON representation (useful for REST services)
		"""
		# We need the absolute URL 
		abs_url = request.build_absolute_uri("/")[:-1]
		src_dict = self.to_serializable(abs_url)
		output = src_dict.to_json()
		
				
		return output

class Bookmark(models.Model):
	'''Record accesses from user to opera'''
	opus = models.ForeignKey(Opus,on_delete=models.CASCADE)
	user = models.ForeignKey(User,on_delete=models.CASCADE)
	timestamp = models.DateTimeField('Created', auto_now_add=True)

	class Meta:
		db_table = "Bookmark"

		
class Upload (models.Model):
	'''Storage and desription of ZIP file containing
	a list of XML pieces to be imported in a corpus'''
	corpus = models.ForeignKey(Corpus,on_delete=models.CASCADE)
	description =   models.TextField()
	creation_timestamp = models.DateTimeField('Created', auto_now_add=True)
	update_timestamp = models.DateTimeField('Updated', auto_now=True)

	def upload_path(self, filename):
		'''Set the path where upload files must be stored'''
		corpus_ref = self.corpus.ref.replace(settings.NEUMA_ID_SEPARATOR, "-")
		timestamp = datetime.utcnow().strftime("%Y_%m_%d_%H_%M_%S_%f")
		return 'uploads/' + corpus_ref + '-' + timestamp  + '.zip'
	zip_file = models.FileField(upload_to=upload_path,null=True,storage=OverwriteStorage())

	class Meta:
		db_table = "Upload"	

	def __str__(self):  # __unicode__ on Python 2
		return "(" + self.corpus.ref + ") " + self.zip_file.name

class Audio (models.Model):
	'''Storage of audio files associated to an opus'''
	opus = models.ForeignKey(Opus,on_delete=models.PROTECT)
	filename = models.TextField()
	description =   models.TextField()
	creation_timestamp = models.DateTimeField('Created', auto_now_add=True)
	update_timestamp = models.DateTimeField('Updated', auto_now=True)

	def upload_path(self, filename):
		'''Set the path where audio files must be stored'''
		audio_ref = self.opus.ref.replace(settings.NEUMA_ID_SEPARATOR, "-")
		return 'audio_files/' + audio_ref + '/' + self.filename
	audio_file = models.FileField(upload_to=upload_path,null=True,storage=OverwriteStorage())

	class Meta:
		db_table = "Audio"	

	def __str__(self):  # __unicode__ on Python 2
		return "(" + self.opus.ref + ") " + self.filename


class SimMeasure(models.Model):
	code = models.CharField(max_length=255,unique=True)

	def __init__(self, *args, **kwargs):
		super(SimMeasure, self).__init__(*args, **kwargs)

	class Meta:
		db_table = "SimMeasure"
		
	def __str__(self):
		return  self.code 


class SimMatrix(models.Model):
	sim_measure = models.ForeignKey(SimMeasure,on_delete=models.CASCADE)
	opus1 = models.ForeignKey(Opus, related_name="%(app_label)s_%(class)s_opus1",on_delete=models.CASCADE)
	opus2 = models.ForeignKey(Opus, related_name="%(app_label)s_%(class)s_opus2",on_delete=models.CASCADE)
	value = models.FloatField()

	def __init__(self, *args, **kwargs):
		super(SimMatrix, self).__init__(*args, **kwargs)

	class Meta:
		db_table = "SimMatrix"


class Kmeans(models.Model):
	tag = models.CharField(max_length=255,unique=True)
	corpus = models.ForeignKey(Corpus,on_delete=models.PROTECT)
	group = models.IntegerField()
	measure = models.ForeignKey(SimMeasure,on_delete=models.PROTECT)

	class Meta:
		db_table = "Kmeans"


class Histogram(object):
	''' Represents an histogram, ready to be displayed on stat page '''
	def __init__(self,data,labels,title,labelling_closure=None):
		self.data = data
		self.labels = labels
		self.title = title
		if labelling_closure:
			self.labelling_closure = labelling_closure
		else:
			self.labelling_closure = lambda x:str(x)

		# Color is completely pseudo-randomly generated.
		# Hopefully the result is not that bad.
		# We can still add salt to change them.
		self.color = md5(str(self.title).encode('utf-8')).hexdigest()[0:6]

	def generate_uid(self):
		return self.title+str(uuid.uuid4())


class UnknownSimMeasure(Exception):
	pass


class AnalyticModel(models.Model):
	"""Analytic model = a set of concepts used to interpret a music language"""
	code = models.CharField(max_length=30,unique=True)
	name = models.CharField(max_length=50, unique=True)
	description = models.TextField()

	class Meta:
		db_table = "AnalyticModel"
		
	def __str__(self):			  # __unicode__ on Python 2
		return self.name


class AnalyticConcept(MPTTModel):
	model = models.ForeignKey(AnalyticModel,on_delete=models.CASCADE)
	code = models.CharField(max_length=30,unique=True)
	name = models.CharField(max_length=50, unique=True)
	parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True,on_delete=models.PROTECT)
	description = models.TextField()
	display_options = models.CharField(max_length=255,  default='#ff0000')
	icon = models.TextField(default='')

	class Meta:
		db_table = "AnalyticConcept"

	def __str__(self):			  # __unicode__ on Python 2
		return self.name

	class MPTTMeta:
		order_insertion_by = ['name']


class Resource(models.Model):
	# Used for a resource without selector
	NO_SELECTOR = "None"

	''' A (web) resource, possibly with a selector 
	     to address one of its segments. Used as body and target in annotations '''
	source = models.TextField()
	# A selector. Inspired by the W3C annotation model
	selector_type = models.CharField(max_length=100, default=NO_SELECTOR)
	selector_conforms_to = models.CharField(max_length=100,
								choices=annot_mod.FRAGMENT_CONFORMITY,
								default=annot_mod.FragmentSelector.XML_SELECTOR)
	selector_value = models.CharField(max_length=100)

	# Creation / update dates
	created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
	updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

	class Meta:
		db_table = "Resource"
		
	def __str__(self):
		return self.source + f'(conforms to {self.selector_conforms_to}), value {self.selector_value}'

class Annotation(models.Model):
	'''An annotation qualifies a fragment of a score with an analytic concept'''
	opus = models.ForeignKey(Opus,on_delete=models.CASCADE)
	# Analytic concept: for the moment, a simple code. See how we can do better
	analytic_concept = models.ForeignKey(AnalyticConcept,on_delete=models.CASCADE,null=True)

	# reference to the element being annotated, in principle an xml:id
	ref = models.TextField(default="")
	# Whether the annotation is manual or not 
	is_manual = models.BooleanField(default=False)
	# The user that creates the annotation
	user = models.ForeignKey(User, null=True,on_delete=models.PROTECT)


	##### New version, with target and body
	target  = models.ForeignKey(Resource,null=True,on_delete=models.CASCADE, related_name="annot_target")
	body =  models.ForeignKey(Resource,null=True,on_delete=models.CASCADE, related_name="annot_body")
	motivation = models.CharField(max_length=30,
								choices=annot_mod.MOTIVATION_OPTIONS,
								default=annot_mod.Annotation.MOTIVATION_LINKING)
	textual_body = models.TextField(null=True)
	
	# We "cache" the web annotation as a JSON object for web exchanges
	web_annotation = models.JSONField(blank=True,default=dict)
	
	# Creation / update dates
	created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
	updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

	class Meta:
		db_table = "Annotation"
		
	def create_from_web_input (self, form_data):
		print ("Annotation from JSON")
		print (str(form_data))
		
	def produce_web_annotation(self):
		'''
			Create an annotation of our score model from the DB data
		'''
		
		if len(self.web_annotation) == 0:
			# Let's create the annotation
			target_selector = annot_mod.FragmentSelector(
					annot_mod.FragmentSelector.XML_SELECTOR, self.target.selector_value)
			target_resource = annot_mod.SpecificResource(self.target.source, target_selector)
			target = annot_mod.Target(target_resource)
		
			if self.body is not None:
				body_selector = annot_mod.FragmentSelector(self.body.selector_conforms_to, 
												self.body.selector_value)
				body_resource = annot_mod.SpecificResource(self.body.source, body_selector)
				body = annot_mod.ResourceBody(body_resource)
			if self.textual_body is not None:
				body = annot_mod.TextualBody(self.textual_body)
			if self.user is not None:
				creator = annot_mod.Creator(self.user.id, annot_mod.Creator.PERSON_TYPE, 
									self.user.username)
			else:
				creator = annot_mod.Creator('xxx', annot_mod.Creator.SOFTWARE_TYPE, 
									settings.COMPUTER_USER_NAME)

			annotation = annot_mod.Annotation(self.id, creator, target, body, 
							self.analytic_concept.model.code, self.analytic_concept.code, 
							self.motivation,
							self.created_at, self.updated_at)
			annotation.set_style (annot_mod.Style (self.analytic_concept.icon,
											 self.analytic_concept.display_options))
			
			# Store it for the next time !
			self.web_annotation = annotation.get_json_obj(False)
			self.save()
			return annotation
		else:
			return self.web_annotation
		
	@staticmethod 
	def create_from_web_annotation(user, opus, webannot):
		'''
			Create a DB annotation from an annotation of our score model
		'''
		try:
			annot_concept = AnalyticConcept.objects.get(code=webannot.annotation_concept)
		except AnalyticConcept.DoesNotExist:
			logger.error (f'Unknown annotation concept {webannot.annotation_concept}')
		
		# Create the target
		wtarget = webannot.target
		wtselector = wtarget.resource.selector
		target = Resource(source=wtarget.resource.source, selector_type=wtselector.type,
					selector_conforms_to=wtselector.conforms_to, selector_value=wtselector.value)
		target.save()

		# Create the body
		wbody = webannot.body
		if wbody.type == "resource_body":
			wbselector = wbody.resource.selector
			body = Resource(source=wbody.resource.source, selector_type=wbselector.type,
					selector_conforms_to=wbselector.conforms_to, selector_value=wbselector.value)
			body.save()
			# NB: the annotation model of webannot is ignored, we take the model of the concept istead.
			# There is probably no need to refer tothe annotation model in web annotation, unless
			# two concepts in two distinct models share the same code
			return Annotation (opus=opus, ref = wtselector.value,
								user=user, 
								analytic_concept =  annot_concept,
								target=target,body=body, 
								motivation=webannot.motivation)
		elif wbody.type == "textual_body":
			return Annotation (opus=opus, ref = wtselector.value,
								user=user,
								analytic_concept =  annot_concept,
								target=target, textual_body=wbody.value, 
								motivation=webannot.motivation)

class ScoreFeature():
	''' 
		A class to represent features in the JSON LD export
	'''

	feature_type = ""
	feature_value = ""
	
	def __init__(self, ftype, fvalue):
		self.feature_type = ftype
		self.feature_value = fvalue
		
	def to_json(self):
		return {"type": self.feature_type, "value": self.feature_value}

# Get the Opus ref and extension from a file name
def decompose_zip_name (fname):
	dirname = os.path.dirname(fname)
	dircomp = dirname.split(os.sep)
	basename = os.path.basename(fname)
	components = os.path.splitext(basename) 
	extension = components[len(components)-1]
	opus_ref = ""
	sep = ""
	for i in range(len(components)-1):
		if i >0:
			sep = "-"
		opus_ref += components[i] + sep
	return (opus_ref, extension)
