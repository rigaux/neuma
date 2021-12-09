from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from manager.models import Corpus, Opus, Upload, SimMeasure, AnalyticModel, AnalyticConcept, Licence
from lib.workflow.Workflow import Workflow
import string
from django.core.files import File
import os

from scorelib import analytic_concepts

from django.contrib.auth.models import User, Group

from colorutils import random_web

from lxml import etree
import xml.etree.ElementTree as ET

class Command(BaseCommand):
	"""Create some mandatory objects in the DB"""

	help = 'Create some mandatory objects in the DB'

	# List of colors
	palette =  {}
	# List of icons
	icons = {}
	
	def add_arguments(self, parser):
		pass

	def handle(self, *args, **options):
		
		# Anonymous user
		try:
			anon = User.objects.get(username='anonymous')
		except User.DoesNotExist:
			anon = User(first_name='Anonymous',last_name='Neuma', username='anonymous')
			anon.save()
			print ("Creating anonymous user")
			
		# Computer user
		try:
			computer = User.objects.get(username=settings.COMPUTER_USER_NAME)
		except User.DoesNotExist:
			computer = User(first_name='',last_name='Neuma', username=settings.COMPUTER_USER_NAME)
			computer.save()
			print ("Creating computer user")
		
		# Groups
		for group_name in settings.NEUMA_GROUPS:
			try:
				group = Group.objects.get(name=group_name)
				print ("Group " + group_name + " already exists")
			except Group.DoesNotExist:
				print ("Creating group " + group_name)
				group  = Group(name=group_name)
				group.save()
				
		# Create a root corpus
		try:
			root = Corpus.objects.get(ref=settings.NEUMA_ROOT_CORPUS_REF)
		except Corpus.DoesNotExist:
			print ("Creating external corpus")
			root = Corpus(ref=settings.NEUMA_ROOT_CORPUS_REF)
			root.title = "Collections - Neuma"
			root.short_title = "All"
			root.short_description = "All collections"
			root.is_public = True
			root.save()
			
		# Create a, external corpus for all scores not directly managed by Neuma
		try:
			external = Corpus.objects.get(ref=settings.NEUMA_EXTERNAL_CORPUS_REF)
		except Corpus.DoesNotExist:
			print ("Creating external corpus")
			external = Corpus(ref=settings.NEUMA_EXTERNAL_CORPUS_REF)
			external.title = "External Collections - Neuma"
			external.short_title = "External"
			external.short_description = "External collections"
			external.is_public = False
			external.save()
		# Create a corpus for quality management
		try:
			external = Corpus.objects.get(ref=settings.NEUMA_QUALITY_CORPUS_REF)
		except Corpus.DoesNotExist:
			print ("Creating quality evaluation corpus")
			external = Corpus(ref=settings.NEUMA_QUALITY_CORPUS_REF)
			external.title = "Quality evaluation - Neuma"
			external.short_title = "Quality evaluation"
			external.short_description = "Quality evaluation"
			external.is_public = False
			external.save()
		# Create a transcription corpus for all scores produced by a transcription process
		try:
			transcription = Corpus.objects.get(ref=settings.NEUMA_TRANSCRIPTION_CORPUS_REF)
		except Corpus.DoesNotExist:
			transcription = Corpus(ref=settings.NEUMA_TRANSCRIPTION_CORPUS_REF)
			transcription.title = "Transcription Collections - Neuma"
			transcription.short_title = "Transcriptions"
			transcription.short_description = "Transcription collections"
			transcription.is_public = False
			transcription.save()

		# Similarity measures
		for measure_code in settings.SIMILARITY_MEASURES:
			try:
				measure = SimMeasure.objects.get(code=measure_code)
			except SimMeasure.DoesNotExist:
				print ("Creating similarity measure '" + measure_code + "'")
				measure = SimMeasure(code=measure_code)
				measure.save()

		# Load the palette file
		static_dir = os.path.join(settings.BASE_DIR, "static")
		palette_file =  etree.parse(static_dir + "/analytic_models/palette_neuma.xml")
		self.palette = {}
		# Load the colors
		colors = palette_file.xpath("//colors/color")
		for color in colors:
			# Extract values
			color_name = str(color.xpath("./@name")[0])
			self.palette[color_name] = {"h": color.xpath("./@h")[0],
				 "s": color.xpath("./@s")[0],
				 "l": color.xpath("./@l")[0],
				 }
		# Load the icons file
		static_dir = os.path.join(settings.BASE_DIR, "static")
		icons_file =  etree.parse(static_dir + "/analytic_models/icons_neuma.xml")
		self.icons = {}
		# Load the colors
		icons = icons_file.xpath("//icons/icon")
		for icon in icons:
			# Extract values
			icon_name = str(icon.xpath("./@name")[0])
			print ("Icones " + icon_name)
			for node in icon.iter("*"):
				print ("Tag:" + etree.QName(node).localname)
				if etree.QName(node).localname == "path":
					self.icons[icon_name] = {"svg_path": node.xpath("@d")[0]}

		# Analytic models
		self.load_model ("counterpoint_model.xml")
		self.load_model ("quality_model.xml")
		self.load_model("comparison_model.xml")
		
		self.load_licences()
		print ("Done !")
		

	def load_model (self, xml_file):
		static_dir = os.path.join(settings.BASE_DIR, "static")
 
		# Parse the file
		counterpoint_model = etree.parse(static_dir + "/analytic_models/" + xml_file)

		# Get the model description
		model_id = counterpoint_model.xpath("./@id")[0]
		description = counterpoint_model.find("description").text.strip()
		name = counterpoint_model.find("name").text.strip()

		try:
			db_model = AnalyticModel.objects.get(code=model_id)
			print ("Analytic model '" + model_id + " already exists")
		except AnalyticModel.DoesNotExist:
			print ("Creating analytic model '" + model_id + "'")
			db_model = AnalyticModel(code=model_id, name=name, description=description)
			db_model.save()
		
		# Now loop recursively on the concepts
		concepts = counterpoint_model.xpath("./concepts/concept")
		self.load_concepts (db_model, concepts, None)
 
	def load_concepts (self, db_model, concepts, parent):
				

		for concept in concepts:
		   # Extract values
			concept_id = concept.xpath("./@id")[0]
			description = concept.find("description").text.strip()
			name = concept.find("name").text.strip()
			concept_color = concept.find("color")
			concept_icon = concept.find("icon")

			if parent is not None:
			   print ("Process concept, " + concept_id + " child of " + parent.code)
			
			if concept_color is not None:
				color_name = concept_color.xpath("./@name")[0]
				if color_name not in self.palette.keys():
					print ("ERROR: unknown color name " + color_name)
					exit(1)
				else:
					color = self.palette[color_name]
					display_option = "hsl(" + color["h"] + "," + color["s"] + "%," + color["l"]  + "%)"
			elif parent is not None:
				print ("Take the parent display option ")
				display_option = parent.display_options
			else:
				display_option = random_web()
			
			if concept_icon is not None:
				icon_name = concept_icon.xpath("./@name")[0]
				if icon_name not in self.icons.keys():
					print ("ERROR: unknown icon name " + icon_name)
					exit(1)
				else:
					icon = self.icons[icon_name]
					svg_path = icon["svg_path"]
			else:
				# Draw a circle
				icon = self.icons["spade"]
				svg_path = icon["svg_path"]

			try:
				db_concept = AnalyticConcept.objects.get(code=concept_id)
				print ("Analytic concept '" + concept_id + "' already exists")
				db_concept.name = name
				db_concept.description = description
			except AnalyticConcept.DoesNotExist:
				print ("Creating analytic concept '" + concept_id + "'")
					
				db_concept = AnalyticConcept(model=db_model,code=concept_id, 
											 name=name, 
											 parent = parent,
											 description=description
											 )
			# Set the display option
			#print ("Display option for concept " + db_concept.code  + " = " + display_option)
			db_concept.display_options = display_option
			db_concept.icon = svg_path
			db_concept.save()
			
			# Recursive call
			children = concept.xpath("./concepts/concept")
			self.load_concepts (db_model, children, db_concept)
			
	def load_licences (self):
		static_dir = os.path.join(settings.BASE_DIR, "static")
 
		# Parse the file
		licences_doc = etree.parse(static_dir + "/licences/licences.xml" )
		licences = licences_doc.xpath("./licence")
		for licence in licences:
		   # Extract values
			code = licence.xpath("./@code")[0]
			name = licence.find("name").text.strip()
			url = licence.find("url").text.strip()
			notice = licence.find("notice")
			full_text = licence.find("full_text")
			notice = ET.tostring(notice).decode().replace("<notice>","").replace("</notice>","").strip()
			full_text = ET.tostring(full_text).decode().replace("<full_text />","").replace("<full_text>","").replace("</full_text>","").strip()
			
			try:
				db_licence = Licence.objects.get(code=code)
				print ("Licence  '" + name + "' already exists")
				db_licence.notice= notice 
				db_licence.full_text = full_text
				db_licence.save()
			except Licence.DoesNotExist:
				print ("Creating licence '" + name + "'")
				licence = Licence (code=code,name=name,url=url,
								notice=notice,full_text=full_text)
				licence.save()

