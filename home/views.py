from io import BytesIO
import logging, json
import os
from pprint import pprint  # debug only
import zipfile
import verovio
from natsort import natsorted

#from Cython.Compiler.Buffer import context
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.core.files.base import ContentFile, File

import requests

import lxml.etree as etree
from manager.models import (Corpus, 
						Opus, Upload, Bookmark, 
						Config, Licence, Annotation, 
						AnalyticModel, AnalyticConcept, Image)

from music import *

from neumasearch.IndexWrapper import IndexWrapper
from neumasearch.MusicSummary import  MusicSummary
from neumasearch.SearchContext import SearchContext
from neumasearch.Sequence import Sequence
from neumautils.views import NeumaView
import xml.etree.ElementTree as ET

from .forms import *

# Music model modules
import lib.music.source as source_mod
import lib.music.constants as constants_mod
import lib.iiif.IIIF2 as iiif2_mod
import lib.iiif.IIIF3 as iiif3_mod
import lib.iiif.helpers as iiif3_helpers

# Create your views here.
# To communicate with ElasticSearch
# Get an instance of a logger
logger = logging.getLogger(__name__)

def wildwebdata(request):
	""" Serves the wildwebmidi.data sample from any .data URL"""
	path = os.path.dirname(os.path.abspath(__file__)) + "/../static/wildwebmidi.data"
	print  ("Path for wildweblidi  " + path)
	image_data = open(path, "rb").read()
	return HttpResponse(image_data, content_type="image/png")


class CorpusView(NeumaView):
	"""Display a corpus with children and opera"""

	def get(self, request, **kwargs):
		context = self.get_context_data(**kwargs)

		# Are we in search mode
		if self.search_context.in_search_mode():
			url = reverse('home:search', args=(), kwargs={})
			return HttpResponseRedirect(url)
		else:
			self.search_context.info_message = ""
 
		return render(request, "home/corpus.html", context)


	def get_context_data(self, **kwargs):
		# Call the parent method
		context = super(CorpusView, self).get_context_data(**kwargs)

		# Get the corpus
		corpus_ref = self.kwargs['corpus_ref']
		corpus = Corpus.objects.get(ref=corpus_ref)

		# Set the HTML page title to the corpus title		
		context["page_title"] = corpus.short_title

		# Load the corpus opera and children
		nb_opera = corpus.get_nb_opera()
		nb_children = corpus.get_nb_children()
		all_opera = corpus.get_opera()
		paginator = Paginator(all_opera, settings.ITEMS_PER_PAGE)

		# Record the corpus as the contextual one
		self.search_context.ref = corpus.ref
		self.search_context.type = settings.CORPUS_TYPE
		self.request.session["search_context"] = self.search_context.toJSON()

		# Paginator data
		page = self.request.GET.get('page')

		try:
			opera = paginator.page(page)
		except PageNotAnInteger:
			# If page is not an integer, deliver first page.
			opera = paginator.page(1)
		except EmptyPage:
			# If page is out of range (e.g. 9999), deliver last page of results.
			opera = paginator.page(paginator.num_pages)

		# We show the Opus tab if we do not have sub-corpus
		current_tab = 0
		if nb_children == 0:
			current_tab = 1

		context['corpus'] = corpus
		context['corpus_cover'] = corpus.get_cover()
		context['children'] = corpus.get_children()
		context['nb_children'] = nb_children
		context['nb_opera'] = nb_opera
		context['opera'] = opera
		context['current_tab'] = current_tab
		context['neuma_url'] = settings.NEUMA_URL
		context['class_number_range'] = range(5,11)
		context["stats_editions"] = corpus.stats_editions()
		# Add upload files
		context['uploads'] = corpus.upload_set.all()

		return context

def show_licence (request, licence_code):
	""" Show a licence"""
	
	context["licence"] = Licence.objects.get(code=licence_code)
	return render(request, 'home/show_licence.html', context)

def iiif (request, iiif_id, viewer):
	""" Display a viewer on a IIIF resource"""
	
	# Format attendu par Gallica
	source = OpusSource.objects.get(id=iiif_id)

	context = {"iiif_ref": source.iiif_manifest.url}
	if viewer == "uv":
		return render(request, 'home/univ-viewer.html', context)
	else:
		return render(request, 'home/mirador.html', context)
		
def export_corpus_as_zip (request, corpus_ref):
	""" Export the list of XML files of this corpus"""
	
	corpus = Corpus.objects.get(ref=corpus_ref)
	if "mode" in request.GET:
		mode = request.GET.get("mode")
	else:
		mode = "json"

	zip_bytes = corpus.export_as_zip(request,mode)
	resp = HttpResponse(zip_bytes.getvalue(), content_type = "application/x-zip-compressed")
	resp["Content-Disposition"] = "attachment; filename=%s.zip" % Corpus.local_ref(corpus_ref) 

	return resp

def iiif_collection (request, corpus_ref):
	""" Produce the IIIF collection of a corpus"""
	
	#
	# Todo: by default we put the manifest of SYNC sources in 
	# the collection. We  add a URL param 'source_type' that woul
	# allow to get also images, etc.
	#
	corpus = Corpus.objects.get(ref=corpus_ref)
	if "source_type" in request.GET:
		# Check that we received sth that makes sense....
		source_type = request.GET.get("source_type")
	else:
		# Default : we produce the collection of 
		source_type = SourceType.STYPE_SYNC
	
	collection = corpus.to_collection()
	#return HttpResponse(collection.json(2), content_type = "application/json")
	iiif_collection  = iiif3_helpers.create_collection (collection)

	# Now look on the list of opera
	for opus in corpus.get_opera():
		sync_source = opus.get_source_with_type(source_type)
		if sync_source is not None:
			if not bool(sync_source.thumbnail):
				print ("Missing thumbnail. There shoud be a default one ")
				thumbnail =  iiif3_helpers.create_image_item(Image.default_image().to_dict())
				
			else:
				thumbnail =  iiif3_helpers.create_image_item(sync_source.thumbnail.to_dict())
			manifest_url = settings.NEUMA_BASE_URL + reverse('home:iiif_manifest', args=[opus.ref])[1:]
			manifest_ref = iiif3_mod.ManifestRef (manifest_url, 
				opus.title, thumbnail)
			iiif_collection.add_manifest_ref (manifest_ref)

	return HttpResponse(iiif_collection.json(2), content_type = "application/json")

def iiif_manifest (request, opus_ref):
	""" 
		Find a source and return its IIIF manifest
	"""
	opus = Opus.objects.get(ref=opus_ref)
	if "source_type" in request.GET:
		# Check that we received sth that makes sense....
		source_type = request.GET.get("source_type")
	else:
		# Default : we produce the collection of 
		source_type = SourceType.STYPE_SYNC
	if "force" in request.GET:
		print ("The manifest must be replaced")
		recompute = True
	else:
		recompute = False
		print ("Return the stored manifest is present")
		
	# Convert to a collection item 
	item = opus.to_collection_item()

	#return  HttpResponse(item.json(), content_type = "application/json")

	# Find the source given the type
	sync_source = opus.get_source_with_type(source_type)
	if sync_source is None:
		# Not found
		return HttpResponseNotFound("<h1>Source {source_type} not found</h1>")
	#return  HttpResponse(sync_source.json(), content_type = "application/json")

	print (f"We found a sync source for opus {opus.ref}")
	
	# If the manifest is already there, and 'force' is not set,
	# we take the stored file
	if bool(sync_source.source_file) and recompute is False:
		with open(sync_source.source_file.path,"r") as f:
			return  HttpResponse(f.read(), content_type = "application/json")

	# Else we compute or re-compute the manifest
	if "image_source" in sync_source.metadata:
		image_source = OpusSource.objects.get(opus=opus,
						ref=sync_source.metadata["image_source"])
	else:
		# By default we take the source with ref iiiif
		image_source =  OpusSource.objects.get(opus=opus,
				ref=source_mod.OpusSource.IIIF_REF)
		print (f"iiif_combined_manifest Warning: the 'image_source' field is undefined. taking 'iiif' by default")
	if "audio_source" in sync_source.metadata:
		audio_source = OpusSource.objects.get(opus=opus,ref=sync_source.metadata["audio_source"])
	else:
		# By default we take the source with ref audio
		audio_source =  OpusSource.objects.get(opus=opus,
						ref=source_mod.OpusSource.AUDIO_REF)


	#return  HttpResponse(audio_source.json(), content_type = "application/json")
	#return  HttpResponse(image_source.json(), content_type = "application/json")

	# Get the images URLs from the IIIF image manifest
	print (f"Take the image manifest from the source")	
	if not (image_source.iiif_manifest) or image_source.iiif_manifest == {}:
		raise Exception (f"Missing manifest in the IIIF image source for opus {self.ref}. Synchronization aborted")
		return
	with open(image_source.iiif_manifest.path, "r") as f:
		iiif_doc = iiif2_mod.Document(json.load(f))
	images = iiif_doc.get_images()

	# Get annotations both are dictionary indexed by the measure id
	annotations_images = Annotation.for_opus_and_concept(opus,
				constants_mod.IREGION_MEASURE_CONCEPT)
	annotations_audio = Annotation.for_opus_and_concept(opus,
					constants_mod.TFRAME_MEASURE_CONCEPT)
	sorted_images = dict(natsorted(annotations_images.items())) 
	sorted_audio = dict(natsorted(annotations_audio.items())) 

	iiif_manifest  = iiif3_helpers.create_combined_manifest (item, 
							sync_source.to_item_source(),
							audio_source.to_item_source(), 
							image_source.to_item_source(),
							images,
							sorted_images, sorted_audio)

	# Add some links to other sources
	musicxml_source = opus.get_source(source_mod.OpusSource.MUSICXML_REF)
	if musicxml_source is not None:
		rest_url = settings.NEUMA_BASE_URL + musicxml_source.file_rest_url()
		musixml_meta =  iiif3_mod.Metadata (iiif3_mod.Property("MusicXML"), 
								iiif3_mod.Property(rest_url))
		iiif_manifest.add_metadata (musixml_meta)
	mei_source = opus.get_source(source_mod.OpusSource.MEI_REF)
	if mei_source is not None:
		rest_url = settings.NEUMA_BASE_URL + mei_source.file_rest_url()
		mei_meta =  iiif3_mod.Metadata (iiif3_mod.Property("MEI"), 
								iiif3_mod.Property(rest_url))
		iiif_manifest.add_metadata (mei_meta)

	# Put the manifest in the Sync source
	file_name = "combined_manifest.json"
	sync_source.source_file.save(file_name, ContentFile(iiif_manifest.json (2)))
	sync_source.save()

	return  HttpResponse(iiif_manifest.json(), content_type = "application/json")

def upload_corpus_zip (request, corpus_ref):
	""" Upload a zip file with a set of XML files"""
	
	corpus = Corpus.objects.get(ref=corpus_ref)
	
	if request.method == 'POST' and "corpus_zipfile" in request.FILES:
		description = request.POST["description"]
		zip = request.FILES["corpus_zipfile"]
	
		if not zip.name.endswith(".zip"):
			logger.warning ("Attempt to load a non-zip file for " + corpus.ref)  
		else:	  
			upload = Upload (corpus=corpus, description=description,zip_file=zip)
			upload.save()
	else:
		logger.warning ("No ZIP file transmetted for corpus " + corpus.ref)
	   
	url = reverse('home:corpus', args=(), kwargs={"corpus_ref": corpus_ref})
	return HttpResponseRedirect(url)


class CorpusEditView(NeumaView):
	""" Create and edit a corpus"""
	
	def get_context_data(self, **kwargs):
		# Call the parent method
		context = super(CorpusEditView, self).get_context_data(**kwargs)

		# Get the corpus
		corpus_ref = self.kwargs['corpus_ref']
		parent = Corpus.objects.get(ref=corpus_ref)
		# For access rights checking
		context["corpus"] = parent 
		return context

	def get(self, request, **kwargs):
		context = self.get_context_data(**kwargs)
		context['corpus_form']  = CorpusForm()
		return render(request, "home/corpus_edit.html", context=context)

	def post(self, request, **kwargs):
		context = self.get_context_data(**kwargs)
		
		context['corpus_form']  = CorpusForm(request.POST,  request.FILES)
		if context['corpus_form'].is_valid():
				child = context['corpus_form'].save(commit=False)
				local_ref = request.POST['ref']
				parent_ref = self.kwargs['corpus_ref']
				child.parent =  Corpus.objects.get(ref=parent_ref)
				child.ref= Corpus.make_ref_from_local_and_parent(local_ref, parent_ref)
				child.save()
		return render(request, "home/corpus_edit.html", context=context)
	
class OpusView(NeumaView):
	
	""" 
		Any information displayed is put in the context array by this function 
	"""
	def get_context_data(self, **kwargs):
		# Get the opus
		opus_ref = self.kwargs['opus_ref']
		opus = Opus.objects.get(ref=opus_ref)

		# Initialize context
		context = super(OpusView, self).get_context_data(**kwargs)

		#  Put the config in the context
		context["config"] = Config.objects.get(code=Config.CODE_DEFAULT_CONFIG)

		# Set the HTML page title to the corpus title		
		context["page_title"] = opus.title
		context["my_url"] =  self.request.build_absolute_uri("/")[:-1]
		# Record the opus as the contextual one
		self.search_context.ref = opus.ref
		self.search_context.type = settings.OPUS_TYPE
		self.request.session["search_context"] = self.search_context.toJSON()

		# Record the fact the user accessed the Opus
		if self.request.user.is_authenticated:
			current_user = self.request.user
		else:
			# Take the anonymous user
			current_user = User.objects.get(username='AnonymousUser')
			# current_user = User.objects.get(username='anonymous')
			if current_user is None:
				raise ObjectDoesNotExist("No anonymous user. Please create it")

		# We shoud have the current user
		bookmark = Bookmark()
		bookmark.user = current_user
		bookmark.opus = opus
		bookmark.save()

		# By default, the tab shown is the first one (with the score)
		context['tab'] = 0
		#initialize ?
		context["matching_ids"] = ""

		# The pattern: it comes either from the search form (and takes priority)
		# or from the session

		if self.search_context.keywords != "":
			#There is a keyword to search
			matching_ids = []
			keyword_in_search = self.search_context.keywords
			score = opus.get_score()
			for voice in score.get_all_voices():
				#get lyrics of the current voice
				curr_lyrics = voice.get_lyrics()
				if curr_lyrics != None:
					#There is a match within the current lyrics
					if keyword_in_search in curr_lyrics:
						occurrences, curr_matching_ids = voice.search_in_lyrics(keyword_in_search)
						if occurrences > 0:
							for m_id in curr_matching_ids:
								matching_ids.append(m_id)
			context["msummary"] = ""
			context["pattern"] = ""
			# Could be improved if necessary: context["occurrences"] in the 
			# same format as what it is for pattern search,
			# speicifying the voices and occurrences in each voices instead of a total 
			# number of occurrences
			context["occurrences"] = len(matching_ids)
			context["matching_ids"] = mark_safe(json.dumps(matching_ids))
		
		# Looking for the pattern if any
		if self.search_context.pattern != "":
			pattern_sequence = Sequence()
			pattern_sequence.set_from_pattern(self.search_context.pattern)

			msummary = MusicSummary()
			if opus.summary:
				with open(opus.summary.path, "r") as summary_file:
					msummary_content = summary_file.read()
				msummary.decode(msummary_content)
			else:
				logger.warning ("No summary for Opus " + opus.ref)

			search_type = self.search_context.search_type
			mirror_setting = False 

			occurrences = msummary.find_positions(pattern_sequence, search_type, mirror_setting)
			matching_ids = msummary.find_matching_ids(pattern_sequence, search_type, mirror_setting)
			
			context["msummary"] = msummary
			context["pattern"] = self.search_context.pattern
			context["occurrences"] = occurrences
			context["matching_ids"] = mark_safe(json.dumps(matching_ids))
		
		#
		if "convert_dmos" in self.request.GET:
			opus.parse_dmos()
			context["result_dmos"] = "Calculé"
		else:
			context["result_dmos"] = "None"
			
		# Analyze the score
		score = opus.get_score()
		context["opus"] = opus
		context["score"] = score
		# We use the service to provide file, in order to avoid caching
		context["opus_file_url"] = reverse("rest:opus_file_request", kwargs={"full_neuma_ref": opus.ref})
		
		# get meta values 
		context["meta_values"] = opus.metadata
		
		# Add the analytic models
		context['analytic_models'] = AnalyticModel.objects.all()
		context['analytic_concepts'] = AnalyticConcept.objects.all()
		context["annotation_models"] = AnalyticModel.objects.all()
		
		# For for editing sources
		context["source_form"] = OpusSourceForm()

		# Show detail on the sequence and matching
		if "explain" in self.request.GET:
			context["explain"] = True
		else:
			context["explain"] = False

		return context

	def get(self, request, *args, **kwargs):
		context = self.get_context_data(**kwargs)
		
		if 'edit_source' in request.GET:
			context["edit_source"] = 1
			source = OpusSource.objects.get(id=request.GET["source_id"])
			
			# To introduce the id in the form, teelling that we are in update mode
			OpusSourceForm.id_source = source.id
			context["source_form"] = OpusSourceForm(instance=source)
			# reset the static info
			OpusSourceForm.id_source = None
		else:
			context["edit_source"] = 0

		return self.render_to_response(context)
	
	def post (self, request, *args, **kwargs):
		""" Add a source to an Opus"""
		context = self.get_context_data(**kwargs)
		context["edit_source"] = 1
		
		# Get the opus
		opus_ref = self.kwargs['opus_ref']
		opus = Opus.objects.get(ref=opus_ref)
		
		if request.POST["id_source"] != '':
			# Update mode
			source = OpusSource.objects.get(id=request.POST["id_source"])
			form = OpusSourceForm(data=request.POST, files=request.FILES, instance=source)
		else:
			#Create mode
			form = OpusSourceForm(data=request.POST,files=request.FILES)

		if form.is_valid():
			opus_source = form.save(commit=False)
			opus_source.opus = opus
			opus_source.save()
			return  self.render_to_response(context)
		else:
			# Reaffichage avec l'erreur
			print ("Erreur validation")
			context["source_form"] = form
			return  self.render_to_response(context)

class SourceView(NeumaView):
	
	""" 
		Any information displayed is put in the context array by this function 
	"""
	def get_context_data(self, **kwargs):
		# Get the opus
		opus_ref = self.kwargs['opus_ref']
		opus = Opus.objects.get(ref=opus_ref)
		# Get the source
		source_ref = self.kwargs['source_ref']
		try:
			source = OpusSource.objects.get(opus=opus, ref=source_ref)
		except OpusSource.DoesNotExist:
			raise Http404

		# Initialize context
		context = super(SourceView, self).get_context_data(**kwargs)
		context["opus"] = opus
		context["source"] = source
		context["stats_editions"] = source.stats_editions()
		
		# Set the HTML page title to the corpus title		
		context["page_title"] = f"Source {source.ref} opus {opus.title}"

		# By default, the tab shown is the first one (with the score)
		context['tab'] = 0

		return context

	def get(self, request, *args, **kwargs):
		context = self.get_context_data(**kwargs)
		if 'rebuild_score' in request.GET:
			context['source'].apply_editions()
			context['message'] = 'The score has been rebuilt'
		if 'compute_annotations' in request.GET:
			# Create annotations
			audio_manifest = context['source'].create_audio_annotations()			
			context['message'] = 'Annotations have been rebuilt'
		if 'rebuild_combined_manifest' in request.GET:
			# Create a combined manifest
			combined_manifest = context['source'].rebuild_combined_manifest()			
			context['message'] = 'The combined manifest has been rebuilt'
		return self.render_to_response(context)

class OpusEditView(NeumaView):
	""" Create and edit an Opus"""
	
	def get_context_data(self, **kwargs):
		# Call the parent method
		context = super(CorpusEditView, self).get_context_data(**kwargs)

		# Get the corpus
		corpus_ref = self.kwargs['corpus_ref']
		parent = Corpus.objects.get(ref=corpus_ref)
		# For access rights checking
		context["corpus"] = parent 
		return context

	def get(self, request, **kwargs):
		context = self.get_context_data(**kwargs)
		context['corpus_form']  = CorpusForm()
		return render(request, "home/corpus_edit.html", context=context)

	def post(self, request, **kwargs):
		context = self.get_context_data(**kwargs)
		
		context['corpus_form']  = CorpusForm(request.POST,  request.FILES)
		if context['corpus_form'].is_valid():
				child = context['corpus_form'].save(commit=False)
				local_ref = request.POST['ref']
				parent_ref = self.kwargs['corpus_ref']
				child.parent =  Corpus.objects.get(ref=parent_ref)
				child.ref= Corpus.make_ref_from_local_and_parent(local_ref, parent_ref)
				child.save()
		return render(request, "home/corpus_edit.html", context=context)


def add_opus (request, corpus_ref):
	""" Form to add an opus"""
	
	context = {}
	context["corpus"] = Corpus.objects.get(ref=corpus_ref)
	OpusForm.corpus_ref = context["corpus"].ref
	if request.method == "POST":
		form = OpusForm(request.POST, request.FILES)
		if form.is_valid():
			opus = form.save(commit=False)
			opus.ref = Corpus.make_ref_from_local_and_parent(Corpus.local_ref(opus.ref), context["corpus"].ref)
			opus.corpus = context["corpus"]
			opus.save()
			if bool(opus.musicxml)  and not bool(opus.mei):
				tk = verovio.toolkit()
				tk.loadFile(opus.musicxml.path)
				mei_content = tk.getMEI()
				opus.mei.save("mei.xml", ContentFile(mei_content))
			return redirect ('home:edit_opus', opus_ref=opus.ref)
		else:
			print ("Problème")
	else:
		context["opusForm"] = OpusForm()
		context["mode"] = "insert"
	return render(request, 'home/edit_opus.html', context)


def edit_opus (request, opus_ref):
	""" Form to edit an opus"""
	
	context = {}
	context["opus"] = Opus.objects.get(ref=opus_ref)
	context["corpus"] = context["opus"].corpus
	context["mode"] = "update"
	OpusForm.corpus_ref = context["corpus"].ref

	if request.method == "POST":
		context["opusForm"] = OpusForm(instance=context["opus"], data=request.POST, files=request.FILES)
		if context["opusForm"].is_valid():
			opus = context["opusForm"].save(commit=False)
			opus.ref = Corpus.make_ref_from_local_and_parent(Corpus.local_ref(opus.ref), context["corpus"].ref)
			opus.corpus = context["corpus"]
			opus.save()
			
			if bool(opus.musicxml)  and not bool(opus.mei):
				tk = verovio.toolkit()
				tk.loadFile(opus.musicxml.path)
				mei_content = tk.getMEI()
				opus.mei.save("mei.xml", ContentFile(mei_content))
			context["message"] = "Opus updated ! "
		else:
			# Reaffichage avec l'erreur
			return render(request, 'home/edit_opus.html', context)
	else:
		context["opusForm"] = OpusForm(instance=context["opus"])

	return render(request, 'home/edit_opus.html', context)


class SearchView(NeumaView):
	"""Carry out a search"""

	def get(self, request, **kwargs):
		
		# Security : we create a SearchContext from scratch or from the session
		if "search_context" not in self.request.session:
			self.search_context = SearchContext()
		else:
			self.search_context = SearchContext.fromJSON(self.request.session["search_context"])
			print (f"After decoding search context: {self.search_context} ") 

		search_context = self.search_context
		search_context.info_message = ""

		# Update the search from the request arguments
		if 'keywords' in self.request.GET:
			search_context.keywords = self.request.GET['keywords']

		# Check the type of pattern search, melody or rhythm
		if 'searchType' in self.request.GET:
			search_context.search_type = self.request.GET['searchType']
		if search_context.search_type is None:
			search_context.search_type = settings.MELODIC_SEARCH

		# The pattern: it comes either from the search form (and takes priority)
		# of from the session
		if 'pattern' in self.request.GET:
			# Put in the session until it is cleared or replaced
			search_context.pattern = self.request.GET["pattern"] 
			# Check that the pattern is long enough
			if not search_context.check_pattern_length():
				search_context.info_message  = "Pattern ignored : it must contain at least three intervals"
				search_context.pattern = ""

		#Initialize search_context.mirror_search according to the search request
		search_context.mirror_search = False

		# If the context is an Opus, we redirect to the Opus view
		if search_context.is_opus():
			url = reverse('home:opus', args=(), kwargs={'opus_ref': search_context.ref})
			return HttpResponseRedirect(url)

		# OK store back the search context in the session
		self.request.session["search_context"] = self.search_context.toJSON()

		# If the criteria are empty, then forward to the corpus page
		if not search_context.in_search_mode():
			url = reverse('home:corpus', args=(), kwargs={'corpus_ref': search_context.ref})
			return HttpResponseRedirect(url)


		# Now, carry out the search
		context = self.get_context_data(**kwargs)
		return render(request, "home/search.html", context)
			
	def get_context_data(self, **kwargs):
		context = super(SearchView, self).get_context_data(**kwargs)

		search_context = self.search_context
		#print(dir(search_context))
		
		# The context should always be a corpus
		context["corpus"] = Corpus.objects.get(ref=search_context.ref)
		context["corpus_cover"] = context["corpus"].get_cover()

		# Run the search
		index = IndexWrapper()
		all_opera = index.search(search_context)

		paginator = Paginator(all_opera, settings.ITEMS_PER_PAGE)
		page = self.request.GET.get('page')
		try:
			opera = paginator.page(page)
		except PageNotAnInteger:
			# If page is not an integer, deliver first page.
			opera = paginator.page(1)
		except EmptyPage:
			# If page is out of range (e.g. 9999), deliver last page of results.
			opera = paginator.page(paginator.num_pages)

		context["searchType"] = search_context.search_type
		context["nbHits"] = len(all_opera)
		context["opera"] = opera
		return context


class StructuredSearchView(NeumaView):
	"""Show the structured search view functionalities"""
	#opus.simpleM21Stat(opus.url_musicxml)

	def get_context_data(self, **kwargs):
		 # Initialize context
		context = super(StructuredSearchView, self).get_context_data(**kwargs)
		
		# For tracking in the Neuma menu
		context["current_view"] = "home:structsearch"

		if self.request.method == 'POST':
			# create a query form instance and populate it with data from the request:
			query_form = StructuredQueryForm(self.request.POST)
			# check whether it's valid:
			if query_form.is_valid():
				print ("Query form OK")
				context["query_submitted"] = True
				context["query_text"] = query_form.cleaned_data['query_text']
		else:
			query_form = StructuredQueryForm()
			
		context['form'] = query_form
		return context

	def post(self, request, *args, **kwargs):
		context = self.get_context_data()
		if context["form"].is_valid:
			print ('yes done')
			#save your model
			#redirect
		return super(NeumaView, self).render(request, context)

class AuthView(NeumaView):	 
	"""Manage authentification"""

	def get (self, request, **kwargs):
		
		context = self.get_context_data()

		if ("logout" in request.GET):
			logout(request)

		# Request Already authenticated?
		if (request.user.is_authenticated):
			 return render(request, "home/index.html", context)

		if ("login" in request.GET):
			# Form submitted
			username = request.GET['login']
			password = request.GET['password']
			user = authenticate(username=username, password=password)
			if user is not None:
				if user.is_active:
					 login(request, user)
					 # Redirect to a success page.
				else:
					pass
					#	Return a 'disabled account' error message
			else:
				# Return an 'invalid login' error message.
				context["invalid_login"] = 1

		return render(request, "home/index.html", context)
	
