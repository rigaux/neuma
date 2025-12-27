
#
# General purpose Python imports
#
from datetime import datetime, date
from urllib.request import urlopen
import io
import sys
import json
import jsonref
import jsonschema
import requests
import zipfile
import os
import shortuuid
from xml.dom import minidom
from natsort import natsorted

import music21 as m21
import verovio

#
# Django packages imports
#
from django.db import models
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.core.files.base import ContentFile, File
from django.contrib.auth.models import User
from django.db.models import Count
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
#from django.urls import reverse_lazy
from django.conf import settings
# For tree models
from mptt.models import MPTTModel, TreeForeignKey

#
# Local imports
#
from .utils import OverwriteStorage

#
# My music model
#

from lib.music.constants import *
from lib.music.Score import *
from lib.music.jsonld import JsonLD
import lib.music.annotation as annot_mod
import lib.music.source as source_mod
import lib.music.collection as collection_mod
import lib.music.opusmeta as opusmeta_mod
import lib.music.constants as constants_mod

import lib.iiif.IIIF2 as iiif2_mod
import lib.iiif.IIIF3 as iiif3_mod

# DMOS parser
import lib.collabscore.parser as parser_mod
from lib.collabscore.parser import CollabScoreParser, OmrScore
from lib.collabscore.editions import Edition

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

#################
class Config(models.Model):
	"""
		Global configuration object
	"""
	
	CODE_DEFAULT_CONFIG = "default"
	code = models.CharField(max_length=20, default="default", primary_key=True)
	
	#
	# Configuration of DMOS parsing
	
	log_level = models.IntegerField(default=logging.WARNING)
	page_min = models.IntegerField(default=0)
	page_max = models.IntegerField(default=32767)
	system_min = models.IntegerField(default=0)
	system_max = models.IntegerField(default=32767)
	measure_min = models.IntegerField(default=0)
	measure_max = models.IntegerField(default=32767)

	# Do we ensure that each measure does not overflow ?	
	ensure_measure_duration = models.BooleanField(default=True)

	# Do we rely on caching to show a score?	
	enable_score_caching = models.BooleanField(default=True)

	class Meta:
		db_table = "Config"

	def __str__(self):			  # __unicode__ on Python 2
		return self.code

	def __init__(self, *args, **kwargs):
		super(Config, self).__init__(*args, **kwargs)
	
	def to_dict (self):
		return {"log_level": self.log_level,
				"page_min": self.page_min, "page_max": self.page_max,
				"system_min": self.system_min, "system_max": self.system_max,
				"measure_min": self.measure_min, "measure_max": self.measure_max,
				"ensure_measure_duration": self.ensure_measure_duration
				}

class Image(models.Model):
	iiif_id = models.CharField(unique=True,max_length=30, verbose_name=_("IIIF ID"))
	iiif_url = models.URLField(unique=True, max_length=512, verbose_name=_("IIIF URL"))
	width = models.PositiveIntegerField(default=0, verbose_name=_("Width"))
	height = models.PositiveIntegerField(default=0, verbose_name=_("Height"))

	class Meta:
		verbose_name = _("Image")
		verbose_name_plural = _("Images")

	def url_default(self):
		return self.iiif_url + "/full/max/0/default.png"

	def to_dict (self):
		return {"id": self.iiif_id, "url": self.iiif_url,
					"url_default": self.url_default(),
					"width": self.width, "height": self.height}
					
	def __str__(self):
		return f"{self.iiif_id} ({self.width},{self.height})"

	@staticmethod
	def default_image():
		return Image.objects.get(iiif_id=settings.DEFAULT_IMAGE)

class Organization (models.Model):
	''' 
		Descriptions of institutions that provide
		music resources. based on IIIF provide
		property https://iiif.io/api/presentation/3.0/#provider
	'''
	name = models.CharField(max_length=100)
	homepage = models.CharField(max_length=100)
	logo = models.ForeignKey(Image,
			on_delete=models.SET_NULL, null=True, blank=True,
			related_name="organizations", verbose_name=_("Logo"),
	)

	class Meta:
		db_table = "Organization"

	def __str__(self):  # __unicode__ on Python 2
		return self.name
	
	def to_dict (self):
		if self.logo is not None:
			dict_logo = self.logo.to_dict()
		else:
			dict_logo = None
		return {"name": self.name,
			"logo": dict_logo,
			"homepage": self.homepage
			}

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
	
	def name_and_dates (self):
		# Normalized representation of a person' 
		full_name = str(self)
		if self.year_birth is None:
			birth = "-"
		else:
			birth = self.year_birth
		if self.year_death is None:
			death = "-"
		else:
			death = self.year_death
			
		lifespan = f"({birth}, {death})"
		return full_name + " " + lifespan
	def to_dict (self):
		return {"first_name": self.first_name,
			"last_name": self.last_name,
			"name_and_dates": self.name_and_dates(),
			"year_birth": self.year_birth,
			"year_death": self.year_death,
			"dbpedia_uri": self.dbpedia_uri			
			}
	@staticmethod
	def from_dict(pers_dict):
		person = Person(first_name = pers_dict["first_name"])
		person.last_name = pers_dict["last_name"]
		person.year_birth = pers_dict["year_birth"]
		person.year_death = pers_dict["year_death"]
		person.dbpedia_uri = pers_dict["dbpedia_uri"]

	def json (self):
		return json.dumps(self.to_dict())

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

	def to_dict(self):
		return {"code": self.code, "name": self.name,
				"url": self.url, "notice": self.notice}
				
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
	# Organization responsible for the Corpus
	organization = models.ForeignKey(Organization, null=True,blank=True,on_delete=models.SET_NULL)
	# An image than can be used to represent the Corpus
	thumbnail = models.ForeignKey(Image,
			on_delete=models.SET_NULL, null=True, blank=True,
			related_name="corpuses", verbose_name=_("Thumbnail"),
	)

	def upload_path(self, filename):
		'''Set the path where corpus-related files must be stored'''
		return 'corpora/%s/%s' % (self.ref.replace(settings.NEUMA_ID_SEPARATOR, "/"), filename)
	cover = models.FileField(upload_to=upload_path,null=True,storage=OverwriteStorage())

	def __init__(self, *args, **kwargs):
		super(Corpus, self).__init__(*args, **kwargs)
		# Non persistent fields
		self.children = []

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
	def get_iiif_collection_url(self):
		"""
			Get the URL to the Web corpus page, taken from urls.py
		"""
		return settings.NEUMA_BASE_URL + reverse('home:iiif_collection', args=[self.ref])[1:]
	def is_collabscore_corpus(self):
		return "collabscore" in self.ref
	
	def from_dict(self, dict_corpus):
		"""Load content from a dictionary."""
		
		# First convert the dict to a collection
		collection = collection_mod.Collection.from_dict(dict_corpus)
		# Then load from the collection
		self.from_collection(collection)

	def from_collection(self, collection):
		"""Load content from a collection."""
		self.title = collection.title
		self.short_title = collection.short_title
		self.description = collection.description
		self.short_description = collection.short_description
		self.is_public = collection.is_public
		self.copyright = collection.copyright
		self.supervisors = collection.supervisors
		if collection.licence is not None:  
			try:
				self.licence = Licence.objects.get(code=collection.licence["code"])
			except Licence.DoesNotExist:
				print (f"Unknown licence {collection.licence['code']}. Ignored. Did you run setup_neuma?")
		if collection.composer is not None:  
			try:
				self.composer = Person.objects.get(dbpedia_uri=collection.composer["dbpedia_uri"])
			except Person.DoesNotExist:
				print (f"Unknown composer {collection.composer['dbpedia_uri']}. Ignored. Did you run setup_neuma?")
		if collection.thumbnail is not None:  
			try:
				self.thumbnail = Image.objects.get(iiif_id=collection.thumbnail["id"])
			except Image.DoesNotExist:
				print (f"Unknown image {collection.thumbnail['id']}. Ignored. Did you run setup_neuma?")
		if collection.organization is not None:  
			try:
				self.organization = Organization.objects.get(homepage=collection.organization["homepage"])
			except Image.DoesNotExist:
				print (f"Unknown organization {collection.organization['homepage']}. Ignored.")
		return
	
	def to_collection(self):
		# Remove '/' both ends to get_url()
		uri = settings.NEUMA_BASE_URL + self.get_url()[1:-1]
		collection = collection_mod.Collection (uri, 
				self.ref, self.title, self.short_title,
				self.description, self.short_description, 
				self.is_public, self.composer, 
				self.licence, self.copyright, 
				self.supervisors, self.thumbnail,
				self.organization)
				
		return collection
	def to_dict(self):
		return self.to_collection().to_dict()
	def json(self):
		return self.to_collection().json()
	def to_json(self):
		return self.json()

	def get_children(self, recursive=True):
		self.children = Corpus.objects.filter(parent=self).order_by("ref")
		for child in self.children:
			child.get_children(recursive)
		return self.children
	
	def parse_dmos(self, dmos_source_ref, iiif_source_ref, 
					just_annotations = False, just_score=False):
		for opus in Opus.objects.filter(corpus=self).order_by("ref"):
			print (f"\n\nProcessing DMOS source {dmos_source_ref} in opus {opus.ref}.")
			try:
				opus.parse_dmos(dmos_source_ref, iiif_source_ref,
					just_annotations, just_score)
			except Exception as e:
				print (f"Error when trying to convert DMOS file for opus {opus.ref}:{e}")

	def get_direct_children(self):
		return self.get_children(False)
	def get_nb_children(self):
		return Corpus.objects.filter(parent=self).count()
	def get_nb_opera(self):
		return Opus.objects.filter(corpus=self).count()
	def get_nb_opera_and_descendants(self):
		return Opus.objects.filter(ref__startswith=self.ref).count()
	def get_opera(self):
		return Opus.objects.filter(corpus=self).order_by('ref')

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
		zf.writestr("corpus.json", self.json())
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
				if source.iiif_manifest:
					if "\{\}" in source.iiif_manifest.path:
						nb_source_files += 1
						source_compressor.write(source.iiif_manifest.path, 
							source.ref + "_iiif_mnf." + source.iiif_manifest.path.split(".")[-1])
					else:
						print (f"Error {opus.ref}: iiif_manifest is empty")
			source_compressor.close()
			if nb_source_files > 0:
				source_file = opus.local_ref() +  '.szip'
				#source_file = opus.local_ref() +  '.source_files.zip'
				zf.writestr( source_file, source_bytes.getvalue())

			# Add a JSON file with meta data
			opus_json = opus.json()
			zf.writestr(opus.local_ref() + ".json", opus_json)
		zf.close()
		
		return s

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
			corpus_dict = {"local_ref": zip_name, 
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
		logger.info ("Importing corpus %s in %s" % (corpus_dict['local_ref'], parent_corpus.ref) )
		print ("Importing corpus %s in %s" % (corpus_dict['local_ref'], parent_corpus.ref) )
		full_corpus_ref = Corpus.make_ref_from_local_and_parent(corpus_dict['local_ref'], parent_corpus.ref)
		try:
			corpus = Corpus.objects.get(ref=full_corpus_ref)
		except Corpus.DoesNotExist as e:
			# Create this corpus
			corpus = Corpus (parent=parent_corpus, ref=full_corpus_ref)
	
		# Load / replace content from the dictionary
		corpus.from_dict(corpus_dict)
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
					opus.from_dict (corpus, json.loads(json_doc.decode('utf-8')))
					
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
								if base == source.ref + "_mnf":
									# The file contains the source manifest
									print ("Import manifest")
									manifest_content = source_zip.read(fname)
									source.manifest.save(fname, ContentFile(manifest_content))
								if base == source.ref + "_iiif_mnf":
									# The file contains the IIIF source manifest
									print ("Import IIIF manifest")
									manifest_content = source_zip.read(fname)
									source.iiif_manifest.save(fname, ContentFile(manifest_content))
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
	
	def stats_editions(self):
		# Group all opus editions by type and return a dict with 
		# stats on each edition type
		stats_corpus = {"nb_opera": self.get_nb_opera(), "nb_annotated": 0}
		for opus in self.get_opera():
			iiif_source = opus.get_source(source_mod.ItemSource.IIIF_REF)
			if iiif_source is not None:
				stats_opus = iiif_source.stats_editions()
				if not stats_opus:
					continue
				# This opus has been annotated
				stats_corpus["nb_annotated"] += 1
				for edition_name in stats_opus.keys():
					if edition_name in stats_corpus.keys():
						stats_corpus[edition_name] += stats_opus[edition_name]
					else:
						stats_corpus[edition_name] = 1
		return stats_corpus
####################################################

class Opus(models.Model):
	corpus = models.ForeignKey(Corpus,on_delete=models.CASCADE)
	title = models.CharField(max_length=255)
	subtitle = models.CharField(max_length=255, null=True,blank=True)
	description = models.TextField(null=True, blank=True)
	composer = models.ForeignKey(Person, null=True,blank=True,on_delete=models.PROTECT)
	ref = models.CharField(max_length=255,unique=True)
	# We can enrich the Opus description with free data
	metadata = models.JSONField(blank=True,default=list)
	# Feature = computed property (eg tonality)
	features = models.JSONField(blank=True,default=list)

	# .Files names
	FILE_NAMES = {"score.xml": "musicxml", 
				   "mei.xml": "mei",
				   "summary.json": "summary"}

	def upload_path(self, filename):
		'''Set the path where opus-related files must be stored'''
		return 'corpora/%s/%s' % (self.ref.replace(settings.NEUMA_ID_SEPARATOR, "/"), filename)

	def __init__(self, *args, **kwargs):
		super(Opus, self).__init__(*args, **kwargs)
		# Non persistent fields

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

	def get_composer(self):
		"""
		  If the composer is not set at the Opus level, get
		  it from the Corpus (if any)
		"""
		if self.composer is not None:
			return self.composer
		elif self.corpus.composer is not None:
			return self.corpus.composer
		else:
			return None

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

	def add_feature (self, mkey, mvalue):
		"""Add a (key, value) pair as an ad-hoc attribute"""
		# The key must belongs to the list of pre-deefined accepted values
		if mkey not in constants_mod.META_KEYS:
			raise Exception(f"Sorry, the key {mkey} does not belong to the accepted feature keys")
		# Search if exists
		if mkey in self.features:
			self.features[mkey] = mvalue 
		else:
			self.features.append({"key": mkey, "value": mvalue})
		self.save()

	def add_meta (self, mkey, mvalue):
		"""Add a (key, value) pair as an ad-hoc attribute"""
		# The key must belongs to the list of pre-deefined accepted values
		if mkey not in constants_mod.META_KEYS:
			raise Exception(f"Sorry, the key {mkey} does not belong to the accepted meta keys")
		
		# Search if exists
		if mkey in self.metadata:
			self.metadata[mkey] = mvalue 
		else:
			self.metadata.append({"key": mkey, "value": mvalue})
		self.save()

	def add_opus_source (self, new_source):
		"""Add a source to the opus 
			from a serializable source item"""
		
		if new_source is None:
			# Pb....
			return 
		# Search if exists
		try:
			old_source = OpusSource.objects.get(opus=self,ref=new_source.ref)
			# Oups it already exists: we update the values
			old_source.description = new_source.description
			old_source.url=new_source.url
			if new_source.thumbnail is not None:
				old_source.thumbnail=new_source.thumbnail
			if new_source.licence is not None:
				old_source.licence=new_source.licence
			if new_source.organization is not None:
				old_source.organization=new_source.organization
			# And more....
			old_source.save()
			return old_source
		except OpusSource.DoesNotExist as e:
			# Ok we can save the new source, which is then added to the Opus
			new_source.save()
			return new_source
		except Exception as e:
			print (f"Error when adding source {new_source.ref} to opus {self.ref}: {e}")

	def get_source (self, source_ref):
		"""Get  a source from the opus"""
		
		# Search if exists
		try:
			return OpusSource.objects.get(opus=self,ref=source_ref)
		except OpusSource.DoesNotExist as e:
			return None

	def get_source_with_type (self, source_type):
		"""Get  a source from the opus"""
		
		stype = SourceType (code=source_type)
		# Search if exists
		try:
			return OpusSource.objects.get(opus=self,source_type=stype)
		except OpusSource.DoesNotExist as e:
			return None

	def copy_mei_as_source(self):
		# Save the MEI file as a reference source 
		if self.mei:
			source_dict = {"ref": "ref_mei", 
						"source_type": SourceType.STYPE_MEI,
						"description": "Référence MEI",
						"url": ""}
			item_source = source_mod.ItemSource.from_dict(source_dict)
			opus_source = OpusSource.from_item_source(item_source)
			source = self.add_opus_source (opus_source)
			source.source_file.save("ref_mei.xml", File(self.mei))

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

	def delete_index(self):
		#
		#   Delete opus in ElasticSearch
		#   Called by signal delete_index_opus
		#
		opus = OpusIndex.get(id=self.id, index=settings.ELASTIC_SEARCH["index"])
		result = opus.delete()
		return result

		
	def to_collection_item(self):
		" Produce a Collection item from the Opus data"
		
		# Remove first and last '/' from the URL
		item_id = settings.NEUMA_BASE_URL + self.get_url()[1:-1]
		# safety
		
		coll_item = collection_mod.CollectionItem (
						item_id, 
						self.corpus.ref, self.ref,
						self.title, self.subtitle,
						self.get_composer(), 
						self.description, self.metadata,
						self.features)
			
		# Adding sources
		for source in self.opussource_set.all ():
			coll_item.add_source(source.to_item_source())

		# Adding files
		for fname, fattr in Opus.FILE_NAMES.items():
			the_file = getattr(self, fattr)
			if the_file:
				opus_file = opusmeta_mod.OpusFile (fname, settings.NEUMA_BASE_URL + the_file.url)
				coll_item.add_file(opus_file)
		return coll_item
	
	def from_dict (self, corpus, dict_opus, files={}, opus_url=""):
		"""Load content from a dictionary.

		The dictionary is commonly a decrypted JSON object, coming
		either from the Neuma REST API or from ElasticSearch

		"""
		# First create a collection item from the dictionary
		item = collection_mod.CollectionItem.from_dict(dict_opus)
		# Then load the opus from the item
		self.from_collection_item(item)
		
	def from_collection_item (self, item):
		" Feed an opus from data in a coll. item"
		
		# We create the full ref from the local ref and the current corpus
		self.ref = Corpus.make_ref_from_local_and_parent(item.local_ref.strip(), self.corpus.ref)
		self.title = item.title
		self.description = item.description
		if item.composer is not None:  
			try:
				self.composer = Person.objects.get(dbpedia_uri=item.composer["dbpedia_uri"])
			except Person.DoesNotExist:
				print (f"Unknown composer {item.composer['dbpedia_uri']}. Ignored. Did you run setup_neuma?")
		self.features = item.features
		
		self.metadata = item.metadata
		# Mandatory before instanciating a source
		self.save()
		for item_source in item.sources:
			opus_source = OpusSource.from_item_source(self, item_source)
			self.add_opus_source (opus_source)

		""" Cas particulier d'un import du fichier IReMus.
		    Ne plus utiliser. Si n"cessaire faire une conversion
		    au préalable
		if ("sources" in dict_opus.keys() 
		         and isinstance(dict_opus["sources"], str)):
			source_dict = {"ref": "iiif", 
						"source_type": "JPEG",
						"description": "Lien Gallica",
						"url": dict_opus["sources"]}
			self.add_source (source_dict)
			print ("Source Gallica: " + dict_opus["sources"] )
		"""
		
		# Get the Opus files
		for f  in item.files:
			fname = f["name"]
			url = f["url"]
			if (fname in Opus.FILE_NAMES):
				print ("Found " + fname + " at URL " + opus_url + fname)
				# Take the score
				file_temp = NamedTemporaryFile()
				f = urlopen(opus_url + fname)
				content = f.read()
				file_temp.write(content)
				file_temp.flush()
				getattr(self, Opus.FILE_NAMES[fname]).save(fname, File(file_temp))
		return

	def to_dict(self, absolute_url):
		return self.to_collection_item().to_dict()
	def to_serializable(self, absolute_url):
		# DEPRECATED
		return self.to_dict ()
	def json(self, indent=2):
		return self.to_collection_item().json(indent)

	def to_json(self, request):
		# DEPRECATED
		return self.json()
		
	def create_source_with_file(self, source_ref, source_type_code,
							url, file_path=None, 
							file_name=None, file_mode="r"):
		
		"""
		   Create of replace a source description and files
		"""
		try:
			source = OpusSource.objects.get(opus=self,ref=source_ref)
		except OpusSource.DoesNotExist:
			description = f"{source_type_code} file created on {date.today()}", 
			source = OpusSource (opus=self,ref=source_ref,
								url = url)
		source.url = url 
		#source.description = description
		source.source_type = SourceType.objects.get(code=source_type_code)
		source.save()
		
		if file_path is not None:
			with open(file_path,file_mode) as f:
				print (f"Replace  file for source {source_ref}")
				source.source_file.save(file_name, File(f))
				source.save()
				
		return source
		
	def replace_musicxml (self, mxml_file):
		with open(mxml_file) as f:
			self.musicxml = File(f,name="score.xml")
			self.save()
		return  self.create_source_with_file(source_mod.ItemSource.MUSICXML_REF, 
					SourceType.STYPE_MXML, "", mxml_file, "score.xml")

	def replace_mei (self, mei_file):
		with open(mei_file) as f:
			print ("Replace MEI file")
			self.mei = File(f,name="mei.xml")
			self.save()	
		return self.create_source_with_file("mei", SourceType.STYPE_MEI,
							"", mei_file, "score.mei")

	def parse_dmos(self, dmos_source_ref, iiif_source_ref, 
					just_annotations = False, just_score=False):
		"""
		  Parse a DMOS file containing OMR extraction of
		  images in a IIIF image source
		"""
		dmos_dir = os.path.join("file://" + settings.BASE_DIR, 'static/json/', 'dmos')
		
		# In case we just want to test annotations
		
		parser_mod.logger.warning ("")
		parser_mod.logger.warning (f"Parsing DMOS source {dmos_source_ref} for IIIF source {iiif_source_ref} for opus {self.ref}, {self.title}")
		parser_mod.logger.warning ("")
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
		dmos_source = self.get_source (dmos_source_ref)
		if dmos_source is None:
			print (f"Unable to find DMOS source {dmos_source_ref}")
			return None
		iiif_source = self.get_source (iiif_source_ref)
		if iiif_source is None:
			print (f"Unable to find IIIF source {iiif_source_ref}")
			return None
		if dmos_source.source_file:
			dmos_data = json.loads(dmos_source.source_file.read())
		else:
			print (f"Unable to find the DMOS file in source {dmos_source_ref}")
			return None
			
		for json_edition in dmos_source.operations:
				editions.append (Edition.from_json(json_edition))
		if dmos_data == None:
			print ("Unable to find the DMOS file ??")
			return "Unable to find the DMOS file ??"
		try:
			parser.validate_data (dmos_data)
		except Exception as ex:
			return "DMOS file validation error : " + str(ex)
		
		# Get the global configuration
		config = Config.objects.get(code=Config.CODE_DEFAULT_CONFIG)

		# Parse DMOS data
		omr_score = OmrScore (self.get_url(), dmos_data, 
						config.to_dict(), editions)
		score = omr_score.get_score()
		
		# Store the MusicXML file in the opus
		if not just_annotations:
			print ("Replace XML file")
			mxml_file = "/tmp/" + shortuuid.uuid() + ".xml"
			omr_score.write_as_musicxml (mxml_file)
			mxml_source = self.replace_musicxml(mxml_file)
			# Generate and store the MEI file as a source and main file
			# Create the file
			mei_file = "/tmp/" + shortuuid.uuid() + "_mei.xml"
			omr_score.write_as_mei (mxml_file, mei_file)
			mei_source = self.replace_mei (mei_file)
			# Write as pickle (for debugging)
			pickle_file = "/tmp/" + self.local_ref() + ".pickle"
			omr_score.write_as_pickle (pickle_file)
			# Generate the MIDI file
			print ("Produce MIDI file")
			midi_file = "/tmp/score.midi"
			score.write_as_midi (midi_file)
			self.create_source_with_file(source_mod.ItemSource.MIDI_REF, 
									SourceType.STYPE_MIDI,
							"", midi_file, "score.midi", "rb")
	
			# Get the IIIF manifest for image infos
			# New version: we always refresh the IIIF manifest
			if True :
#			if not (iiif_source.iiif_manifest) or iiif_source.iiif_manifest == {}:
				# Get the manifest
				print (f"Get the IIIF manifest at URL {iiif_source.url}")
				r = requests.get(iiif_source.url)
				r.raise_for_status()
				# It should alway be a V3 manifest
				iiif_manifest = iiif3_mod.Manifest.load_from_dict(r.json())
				# Save locally
				iiif_source.iiif_manifest = ContentFile(iiif_manifest.json(), name="iiif_manifest.json")
				iiif_source.save()
			else:
				print (f"Take the manifest from the source")
				with open(iiif_source.iiif_manifest.path, "r") as f:
					iiif_manifest = iiif3_mod.Manifest.load_from_dict(json.load(f))
			
			print (f"Got the IIIF manifest. Nb canvases {iiif_manifest.nb_canvases()}")
			omr_score.manifest.add_image_info (iiif_manifest.get_images()) 
			
			# Trick: ensure that each pages refers to the
			# IIIF service
			i_img = 1
			for image in iiif_manifest.get_images():
				first_music_page = omr_score.manifest.first_music_page 
				if (i_img >= first_music_page
						and i_img <= omr_score.manifest.last_music_page):
					mnf_page = omr_score.manifest.pages[i_img-first_music_page]
					mnf_page.set_iiif_service(image.service)
					print (f"Add image {mnf_page.url} to the source manifest")
				i_img += 1

			iiif_source.manifest.id = iiif_source.full_ref()
			print (f"Save the manifest with id {iiif_source.manifest.id}")
			iiif_source.manifest = ContentFile(json.dumps(omr_score.manifest.to_json()), name="score_manifest.json")

			# Add metadata to the source
			serveur_url, iiif_id = iiif3_mod.decompose_url(iiif_source.url)
			iiif_source.add_meta("first_page_of_music", omr_score.manifest.first_music_page)
			iiif_source.add_meta("last_page_of_music", omr_score.manifest.last_music_page)
			iiif_source.add_meta("nb_pages_of_music", omr_score.manifest.nb_pages_of_music())
			iiif_source.add_meta("iiif_provider_url", serveur_url)
			iiif_source.add_meta("iiif_provider_id", iiif_id)
			iiif_source.add_meta("nb_parts", omr_score.manifest.nb_parts())
			iiif_source.save()
		
			# Now we know the full url of the MEI document
			score.uri = mei_source.source_file.url
		else:
			score.uri = "Undetermined: change the 'just_annotations' setting"

		if not just_score:
			# Clean existing annotations for image-region model
			print ("Cleaning existing annotations")
			image_model = AnalyticModel.objects.get(code=AM_IMAGE_REGION)
			Annotation.objects.filter(opus=self).filter(analytic_concept__model=image_model).delete()
			error_model = AnalyticModel.objects.get(code=AM_OMR_ERROR)
			Annotation.objects.filter(opus=self).filter(analytic_concept__model=error_model).delete()

			print (f'Inserting annotations')
			user_annot = User.objects.get(username=settings.COMPUTER_USER_NAME)
			for annotation in score.annotations:
				annotation.target.resource.source = score.uri
				db_annot = Annotation.create_from_web_annotation(user_annot, 
															self, annotation)
				if db_annot is not None:
					db_annot.target.save()
					if db_annot.body is not None:
						db_annot.body.save()
					db_annot.save()

		return score

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
	STYPE_PDF = "PDF"
	# Images, audio and videos
	STYPE_JPEG = "JPEG"
	STYPE_MP3 = "MP3"
	STYPE_MP4 = "MP4"
	# Combined manifest
	STYPE_SYNC = "SYNC"
	# A supprimer
	STYPE_IIIF = "IIIF"
		
	class Meta:
		db_table = "SourceType"	

	def __str__(self):  # __unicode__ on Python 2
		return self.description + " (" + self.code + ")"

class SourceMetaKeys (models.TextChoices):
	"""
		List of allowed keys for meta key/value pairs in a source
	"""
	FIRST_PAGE_OF_MUSIC = "first_page_of_music", _("First page of music")
	LAST_PAGE_OF_MUSIC = "last_page_of_music", _("Last page of music")
	NB_PAGES_OF_MUSIC = "nb_pages_of_music", _("Number of music pages")
	IIIF_PROVIDER_URL = "iiif_provider_url", _("URL of IIIF documents provider")
	IIIF_PROVIDER_ID = "iiif_provider_id", _("ID of the document at provider")
	NB_PARTS = "nb_parts", _("Number of parts")

class OpusSource (models.Model):
	'''A link to a source that contains the representation of an Opus.
	   Evolution to clarify:
	       A source is contained in a file. The file can be local
	       or known by its URL. We should never have both, or at
	       least they must be consistent (the file being a cache
	       of the remote resource)
	       I will add a Boolean field 'iiif'. If true, the source
	       file is a manifest which is either stored remotely (eg Gallica)
	       or locally (Royaumont, or the combined manifest).
	       
	       The source can have an "internal" manifest that describes
	       its structure, for instance pages/systems/staves for score
	       images, of list of time frames for audio or videos. Currently
	       it is named "manifest". Ok, or rename ?
	       
	       The field iiif_manifest can be dropped. It is redundant
	       with the source_file
	       
	       I can add a REST service 'manifest.json' which will return
	       an error for non-iiif sources 
	       
	       DMOS file should become again a specific source. The file
	       should refer to the IIIF image source used as input
	       
	       Regarding types and other properties. There is an IIIF
	       model (https://iiif.io/api/presentation/3.0/#32-technical-properties)
	       for type. The current list is more detailed than the IIIF one.
	       I can keep it, and add the IIIF type as a type attr. (probably not important)
	       
	       It would be useful to ensure that the source ref is unique. Solution
	       add a 'full_ref' field in the DB, with UNIQUE property.
	       
	       Technical properties (duration..) should be put in the metadata field.
	'''
	opus = models.ForeignKey(Opus,on_delete=models.CASCADE)
	ref =   models.CharField(max_length=25)
	# The full reference of the source (sth like opus_ref/_sources/source_ref)
	# Used to ensure unicity
	# Complicated, due to existing rows
	# full_ref = models.CharField(max_length=255,unique=True,default=uuid.uuid4)
	description =   models.TextField()
	source_type = models.ForeignKey(SourceType,on_delete=models.PROTECT)
	url = models.CharField(max_length=255,blank=True,null=True)
	is_iiif = models.BooleanField(default=False)
	# A set of operations applied to the source file. Example: post-OMR processing
	operations = models.JSONField(blank=True,default=list)
	# Meta data 
	metadata = models.JSONField(blank=True, default=dict)
	licence = models.ForeignKey(Licence, null=True,blank=True,on_delete=models.PROTECT)
	copyright = models.CharField(max_length=255,null=True,blank=True)
	# Organization responsible for the source
	organization = models.ForeignKey(Organization, null=True,blank=True,on_delete=models.SET_NULL)
	# An image than can be used to represent the source
	thumbnail = models.ForeignKey(Image,
			on_delete=models.SET_NULL, null=True, blank=True,
			related_name="sources", verbose_name=_("Thumbnail"),
	)

	creation_timestamp = models.DateTimeField('Created', auto_now_add=True)
	update_timestamp = models.DateTimeField('Updated', auto_now=True)

	def upload_path(self, filename):
		'''Set the path where source files must be stored'''
		source_path = self.opus.ref.replace(settings.NEUMA_ID_SEPARATOR, "-") + "/" + self.ref
		return 'sources/' + source_path + '/' + filename
	source_file = models.FileField(upload_to=upload_path,blank=True,null=True,storage=OverwriteStorage())
	manifest = models.FileField(upload_to=upload_path,blank=True,null=True,storage=OverwriteStorage())
	# For IIIF sources, we store locally the IIIF manifest
	iiif_manifest = models.FileField(upload_to=upload_path,blank=True,null=True,storage=OverwriteStorage())

	class Meta:
		db_table = "OpusSource"	

	def __str__(self):  # __unicode__ on Python 2
		return "(" + self.opus.ref + ") " + self.ref

	def get_url(self):
		"""
			Get the URL to the Web source page, taken from urls.py
		"""
		return reverse('home:source', args=[self.opus.ref, self.ref])

	def full_ref(self):
		return self.opus.ref + '/_sources/' + self.ref 
		
	def to_item_source(self):
		"""
		  Create an object that can be serialized for JSON exports
		"""
		
		# Following IIIF principles, the ID is a dereferencable URL
		source_id = settings.NEUMA_BASE_URL + reverse('home:source', args=[self.opus.ref,self.ref])

		item_source = source_mod.ItemSource(source_id,
					self.ref, self.source_type.code, 
					self.source_type.mime_type, 
					self.url, self.metadata,
					self.licence, self.copyright,
					self.thumbnail, self.organization)
		item_source.description = self.description
		
		# We send the path in order to give a way to download the source file
		if self.source_file:
			item_source.file_path =  self.source_file.url
		if self.manifest:
			item_source.has_manifest =  True			
		if self.iiif_manifest:
			item_source.has_iiif_manifest =  True	
		return item_source

	@staticmethod
	def from_item_source(opus, item_source):
		"""
		  Create a DB source from a serializable source item 
		"""
		
		#print (f"Searching source type {item_source.source_type}")
		try:
			source_type = SourceType.objects.get(code=item_source.source_type)
		except SourceType.DoesNotExist:
			print (f"Unknown source type {item_source.source_type}. Ignored. Did you run setup_neuma?")
			return None

		source = OpusSource(opus=opus,
							ref=item_source.ref,
							description=item_source.description,
							source_type=source_type,
							url=item_source.url,
							metadata=item_source.metadata
							)
		if item_source.licence is not None:
			try:
				source.licence = Licence.objects.get(code=item_source.licence["code"])
			except Licence.DoesNotExist:
				print (f"Unknown licence {item_source.licence['code']}. Ignored. Did you run setup_neuma?")
		if item_source.thumbnail is not None:  
			try:
				source.thumbnail = Image.objects.get(iiif_id=item_source.thumbnail["id"])
				print (f"Thumbnail found for source {item_source.thumbnail['id']}")
			except Image.DoesNotExist:
				print (f"Unknown image {item_source.thumbnail['id']}. Ignored. Did you run setup_neuma?")
		if item_source.organization is not None:  
			try:
				source.organization = Organization.objects.get(homepage=item_source.organization["homepage"])
			except Image.DoesNotExist:
				print (f"Unknown organization {item_source.organization['homepage']}. Ignored.")

		return source

	def to_dict(self):
		return self.to_item_source().to_dict()
	def to_serialisable(self, abs_url):
		# Deprecated
		return self.to_dict()
	def json(self):
		"""
		  Produces a JSON representation (useful for REST services)
		"""
		return self.to_item_source().json()
	def to_json(self, request):
		# DEPRECATED
		return self.json()

	def add_meta (self, mkey, mvalue):
		"""Add a (key, value) pair as an ad-hoc attribute"""
		# The key must belongs to the list of pre-deefined accepted values
		if mkey not in SourceMetaKeys.values:
			raise Exception(f"Sorry, the key {mkey} does not belong to the accepted meta keys")
		
		self.metadata[mkey] = mvalue 
		self.save()

	def file_rest_url (self):
		return reverse ('rest:handle_source_file_request', args=[self.opus.ref, self.ref])

	def decode_editions(self):
		# Decode the list of JSON editions as a list of objects
		editions = []
		for json_ed in self.operations:
			editions.append(Edition.from_json(json_ed))
		return editions

	def add_editions(self, new_editions):
		# We start from the current list of editions
		editions_to_apply = self.decode_editions()
		# We add the new edition (allows to find duplicates)
		for edition in new_editions:
			editions_to_apply = Edition.add_edition_to_list(editions_to_apply,edition)
		# We serialize to JSON
		json_editions = []
		for ed in editions_to_apply:
			json_editions.append (ed.to_json())
		self.operations = json_editions
		self.save()
		
	def apply_editions(self, new_editions=[], page_range={}):
		"""
		  Produces a MusicXML file from the DMOS file, after applying editions
		"""
		
		# Page range is not provided ? Take the max
		if page_range == {}:
			page_range = {"page_min": 0, "page_max": 999999}

		if not (self.ref == source_mod.ItemSource.IIIF_REF):
			raise Exception ("Can  only apply editions to an IIIF source ")
		if self.source_file:
			dmos_data = json.loads(self.source_file.read())
		else:
			raise Exception ("This IIIF does not have a DMOS file")	
		
		# We start from the current list of editions
		editions_to_apply = self.decode_editions()
		# We add each of the received list of editions
		for edition in new_editions:
			print (f"Applying edition {edition}")
			editions_to_apply = Edition.add_edition_to_list(editions_to_apply, edition)

		omr_score = OmrScore ("", dmos_data, page_range, editions_to_apply)
	
		# Store the MusicXML file in the opus
		mxml_file = "/tmp/" + shortuuid.uuid() + ".xml"
		omr_score.write_as_musicxml (mxml_file)
		self.opus.replace_musicxml(mxml_file)
		# Same for MEI
		# Crashes on Mac OS X...
		#mei_file = "/tmp/" + shortuuid.uuid() + "_mei.xml"
		#omr_score.write_as_mei (mxml_file, mei_file)
		#self.opus.replace_mei (mei_file)

		# Return a temporary source, it can be the result a the REST service
		tmp_src = self.opus.create_source_with_file(source_mod.ItemSource.TMP_REF, 
									SourceType.STYPE_MXML,
							"", mxml_file, "tmp.xml")

		return tmp_src

	def convert_file_to_audio_manifest(self):
		"""
			A file has been uploaded in an Audio source: it 
			os either an Audacity TXT file, or a Dezrann file.
			We convert it to an audio manifest
		"""
		if (self.source_type.code != SourceType.STYPE_MP3 and 
				self.source_type.code != SourceType.STYPE_MP4):
			raise Exception (f"Source::convert_file_to_audio cannot be applied to a source of type {self.source_type.code}.")

		name, extension = os.path.splitext(self.source_file.name)
		audio_manifest = source_mod.AudioManifest(self.opus.ref, self.ref)
		if extension == ".txt":
			# Should be an Audacity file. We convert to a JSON
			audio_manifest.load_from_audacity(self.source_file.path)
		elif extension == ".drz":
			# Should be a Dezrann file. We convert to a JSON
			audio_manifest.load_from_dezrann(self.source_file.path)
		else:
			raise Exception (f"Source::convert_file_to_audio unknown file extension '{extension}'")
		# And we create the manifest	
		self.manifest.save("manifest.json", 
					ContentFile(json.dumps(audio_manifest.to_dict())))
					
		# I makes sense to re-compute annotations
		self.create_audio_annotations()
		return audio_manifest

	def create_audio_annotations(self):
		# Now create annotations for an audio source from an audio
		# manifest
		if (self.source_type.code != SourceType.STYPE_MP3 and 
				self.source_type.code != SourceType.STYPE_MP4):
			raise Exception (f"Source::create_audio_annotations cannot be applied to a source of type {self.source_type.code}.")
		
		user_annot = User.objects.get(username=settings.COMPUTER_USER_NAME)
		audio_concept = AnalyticConcept.objects.get(code=constants_mod.TFRAME_MEASURE_CONCEPT)
		
		# Remove existing annotations
		Annotation.objects.filter(opus=self.opus).filter(analytic_concept=audio_concept).delete()
		creator = annot_mod.Creator ("collabscore", 
						annot_mod.Creator.SOFTWARE_TYPE, "collabscore")
		
		audio_manifest = source_mod.AudioManifest.from_json (json.loads(self.manifest.read()))
		for tframe in audio_manifest.time_frames:
				measure = str(tframe.id)
				time_frame = "t=" + str(tframe.begin) + "," + str(tframe.end)
				annotation = annot_mod.Annotation.create_annot_from_xml_to_audio(creator, self.opus.musicxml.url, 
								measure, self.url, time_frame, 
								constants_mod.TFRAME_MEASURE_CONCEPT)
				db_annot = Annotation.create_from_web_annotation(user_annot, 
															self.opus, annotation)
				if db_annot is not None:
					db_annot.target.save()
					if db_annot.body is not None:
						db_annot.body.save()
					db_annot.save()

	def stats_editions(self):
		# Group editions by type and return a dict with 
		# stats on each edition type
		stats = {}
		for op in self.operations:
			if op['name'] in stats.keys():
				stats[op['name']] += 1
			else:
				stats[op['name']] = 1
		return stats
		
	#def save(self, *args, **kwargs):
	#	print (f"Saving OpusSource {self.ref}")
	#	super(OpusSource, self).save(*args, **kwargs)

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
			return
		
		# Create the target
		wtarget = webannot.target		
		wtselector = wtarget.resource.selector
		if wtselector.value is None:
			# logger.error (f"Selector value is empty for annotation of type {webannot.annotation_concept}?! Cannot keep this annotation")
			return None
		else:
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

	@staticmethod
	def for_opus_and_concept(opus, concept_code):
		db_annotations = Annotation.objects.filter(
					opus=opus, analytic_concept__code=concept_code
				)
		annotations = {}
		for annotation in db_annotations:
			annotations[annotation.ref]= annotation
		return annotations


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
