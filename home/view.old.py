from io import BytesIO
import logging, json
import os
from pprint import pprint  # debug only
import zipfile

from Cython.Compiler.Buffer import context
from django.conf import settings
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
import requests

import lxml.etree as etree
from manager.models import Corpus, Opus, Upload, Audio, Bookmark, SimMeasure, SimMatrix, Annotation, AnalyticModel, AnalyticConcept
from music import *
from music.Concordance import *
from neuma.rest import Client
from search.IndexWrapper import IndexWrapper
from search.MusicSummary import  MusicSummary
from search.SearchContext import SearchContext
from search.Sequence import Sequence
from neumautils.views import NeumaView
import xml.etree.ElementTree as ET

from .forms import *


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

        corpus = self.kwargs['corpus_ref']

        # default result (or empty block?)
        default_result_path = "static/scoreqldefault.xml"
        with open(default_result_path,  "r", encoding='utf8') as defaultFile:
            result = defaultFile.read()

        context["results"] = result

        # Are we in search mode
        if request.session["search_context"].in_search_mode():
            print ("We are in search mode. Ref " + request.session["search_context"].ref)
            url = reverse('home:search', args=(), kwargs={})
            return HttpResponseRedirect(url)
 
        return render(request, "home/corpus.html", context)

    def post(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        s = requests.session()
        q = request.POST.get('query')
        context["query"] = q
        context["scoreql"] = True
        queryurl = "http://cchum-kvm-scorelibneuma.in2p3.fr/ScoreQL/rest/query"
        querydic = { "query": q}

        result = s.post(queryurl, data=querydic)
        parser = etree.XMLParser(remove_blank_text=True)
        rawxml = etree.XML(result.text, parser)
        reparsed = etree.tostring(rawxml, pretty_print=True)
        context["results"] = reparsed

        return render(request, "home/corpus.html", context=context)

    def get_context_data(self, **kwargs):
        # Call the parent method
        context = super(CorpusView, self).get_context_data(**kwargs)

        # Get the corpus
        corpus_ref = self.kwargs['corpus_ref']
        corpus = Corpus.objects.get(ref=corpus_ref)
        # Load the corpus opera and children
        nb_opera = corpus.get_nb_opera()
        nb_children = corpus.get_nb_children()
        all_opera = corpus.get_opera()
        paginator = Paginator(all_opera, settings.ITEMS_PER_PAGE)

        # Record the corpus as the contextual one
        self.request.session["search_context"].ref = corpus.ref
        self.request.session["search_context"].type = settings.CORPUS_TYPE

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

        # Get the measure for which neighbors must be shown
        if 'sim_measure' in self.request.GET and 'nb_class' in self.request.GET:
            context['measure'] = self.request.GET['sim_measure']
            context['nbclass'] = int(self.request.GET['nb_class'])
            context['current_tab'] =  2
        else:
            # Default
            context['measure'] = 'pitches'
            context['nbclass'] = 8

        if not context['nbclass'] in range(5,11):
            context['nbclass'] = 8

        # We need all the measures eto choose
        context['measures'] = SimMeasure.objects.all()

        measure = SimMeasure.objects.get(code=context['measure'])

       # Add upload files
        context['uploads'] = corpus.upload_set.all()

        # Get a matrix for some measure
        context['matrix_pitches'] = corpus.get_matrix_data(measure)

        context['medoids'] = list(map(
            lambda x:(x.title,x.get_score().get_all_voices()[0].get_histogram(measure)),
            corpus.get_medoids(measure,int(context['nbclass']))
        ))

        #
        # Philippe: does not work when no connection
        #

        s = requests.session()
        mappingsreq = "http://cchum-kvm-scorelibneuma.in2p3.fr/ScoreQL/rest/mapping"
        try:
            mappings = s.get(mappingsreq)
            xmlmappings = ET.fromstring(mappings.text)
            mappinglist = []

            for child in xmlmappings:
               mappinglist.append(child.attrib['corpus'])
               context["mappings"] = mappinglist
        except:
            pass

        try:
            functionsreq = "http://cchum-kvm-scorelibneuma.in2p3.fr/ScoreQL/rest/query/functions"
            functions = s.get(functionsreq)
            xmlfunctions = ET.fromstring(functions.text)
            functionslist = []
            exclude = ["loggerBaseXError","projectByNum","main","Score"]
            for func in xmlfunctions:
               if func.attrib["name"] not in exclude:
                   functionslist.append(func.attrib["name"])
            functionslist.append("Score") # ce n'est pas propre, à enlever de exclude ci-dessus
            context["functions"] = sorted(functionslist, key=lambda s: s.lower())
        except:
            pass

        #templates
        incipitTemplate = """import module namespace s = \"fr.cnam.vertigo.scoreql.ScoreQL\";\\n"""
        templates = { "1st voice (default query)": incipitTemplate + """let $j := for $i in fn:collection(\"ScoreMView\")/score[contains(@id, \"Neuma:"""+ corpus_ref + """\")]\\nreturn $i\\nreturn s:Score(\"1st voice\", $j[1]/music/*[1])""",
                    "trimMeasure" : incipitTemplate + """ let $j := fn:collection(\"ScoreMView\")/score[contains(@id, \"Neuma:""" + corpus_ref + """\")]\\n
let $l := for $i in $j[1]/music/*    return s:trim($i,0,2) \\n return s:Score("TrimMeasure", ($l))""",
                     "mergeScores" : incipitTemplate + """let $j := fn:collection(\"ScoreMView\")/score[contains(@id, \"Neuma:""" + corpus_ref + """\")]\\n
let $score1v1 := $j[1]/music/*[1]\\n let $score2v1 := $j[2]/music/*[1]\\n return s:Score("MergeScore", ($score1v1, $score2v1))""",
        }
        context["templates"] = templates

        # print ("Search context now = " + self.request.session["search_context"].ref)
        return context


def export_opus_as_zip (request, opus_ref):
    """ Export the list of files of this opus"""
 
    return  HttpResponse("TODO")


def export_corpus_as_zip (request, corpus_ref):
    """ Export the list of XML files of this corpus"""
    
    corpus = Corpus.objects.get(ref=corpus_ref)
    zip_filename = Corpus.local_ref (corpus.ref) + ".zip"

    # Write the ZIP file in memory
    s = BytesIO()

    # The zip compressor
    zf = zipfile.ZipFile(s, "w")
    
    opera = Opus.objects.filter(corpus=corpus)
    for opus in opera:
         # Add MusicXML file
         if opus.musicxml:
          	if os.path.exists(opus.musicxml.path):
                zf.write(opus.musicxml.path, opus.local_ref() + ".xml")
         if os.path.exists(opus.mei.path):
             zf.write(opus.mei.path, opus.local_ref() + ".mei")
         # Add a JSON file with meta data
         opus_json = json.dumps(opus.to_json())
         zf.writestr(opus.local_ref() + ".json", opus_json)
         
    zf.close()

    resp = HttpResponse(s.getvalue(), content_type = "application/x-zip-compressed")
    resp["Content-Disposition"] = "attachment; filename=%s" % zip_filename

    return resp


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
                child.ref= child.make_ref_from_local_and_parent(local_ref, parent_ref)
                print ("Corpus ref = " + child.ref)
                child.save()
        return render(request, "home/corpus_edit.html", context=context)
    
class OpusView(NeumaView):
    
    """ Display an opus """
    def get_context_data(self, **kwargs):
        # Get the opus
        opus_ref = self.kwargs['opus_ref']
        opus = Opus.objects.get(ref=opus_ref)

        # Initialize context
        context = super(OpusView, self).get_context_data(**kwargs)

        # Record the opus as the contextual one
        self.request.session["search_context"].ref = opus.ref
        self.request.session["search_context"].type = settings.OPUS_TYPE

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

        #NOT necessary because the keyword is already saved in self.request.session["search_context"].keywords
        #self.request.GET and self.request.POST are empty

        if self.request.session["search_context"].keywords != "":
            #There is a keyword to search
            matching_ids = []
            keyword_in_search = self.request.session["search_context"].keywords
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
            #Could be improved if necessary: context["occurrences"] in the same format as what it is for pattern search,
            #speicifying the voices and occurrences in each voices instead of a total number of occurrences
            context["occurrences"] = len(matching_ids)
            context["matching_ids"] = mark_safe(json.dumps(matching_ids))
        
        # Looking for the pattern if any
        if self.request.session["search_context"].pattern != "":
            pattern_sequence = Sequence()
            pattern_sequence.set_from_pattern(self.request.session["search_context"].pattern)

            msummary = MusicSummary()
            if opus.summary:
                with open(opus.summary.path, "r") as summary_file:
                    msummary_content = summary_file.read()
                msummary.decode(msummary_content)
            else:
                logger.warning ("No summary for Opus " + opus.ref)

            search_type = self.request.session["search_context"].search_type
            mirror_setting = self.request.session["search_context"].mirror_search

            occurrences = msummary.find_positions(pattern_sequence, search_type, mirror_setting)
            matching_ids = msummary.find_matching_ids(pattern_sequence, search_type, mirror_setting)
            
            context["msummary"] = msummary
            context["pattern"] = self.request.session["search_context"].pattern
            context["occurrences"] = occurrences
            context["matching_ids"] = mark_safe(json.dumps(matching_ids))
        
        # Analyze the score
        score = opus.get_score()
        context["opus"] = opus
        context["score"] = score

        # get meta values 
        context["meta_values"] = opus.get_metas()
        
        # Get the measure for which neighbors must be shown
        if 'sim_measure' in self.request.GET:
            context['measure'] = self.request.GET['sim_measure']
            # We show the second tab
            context['tab'] = 2
        else:
            # Default
            context['measure'] = 'pitches'
        # We need all the measures eto choose
        context['measures'] = SimMeasure.objects.all()
        
        measure = SimMeasure.objects.get(code=context['measure'])

        context['neighbors'] = []
        context['neighbor_voices'] = list()

        # Add the analytic models
        context['analytic_models'] = AnalyticModel.objects.all()
        context['analytic_concepts'] = AnalyticConcept.objects.all()

       # Add audio files
        context['audio_files'] = opus.audio_set.all()

        # FIXME : need to do 'x + (y - x)' w/ opus1, opus2
        #context['neighbors'] = SimMatrix.objects.filter(sim_measure=measure,
        #                                opus1=opus).order_by("value")[:settings.NB_NEIGHBORS]

        # FIXME : Hard coding of voice 0. How can we fix that?
       # context['neighbor_voices'] = list(map(
       #     lambda x:(x.opus2.title,x.opus2.get_score().get_all_voices()[0].get_histogram(measure)),
        #    context['neighbors'])
        #)

        # Show detail on the sequence and matching
        if "explain" in self.request.GET:
            context["explain"] = True
        else:
            context["explain"] = False

        return context


def upload_opus_audio (request, opus_ref):
    """ Upload an file for an Opus"""
    
    opus = Opus.objects.get(ref=opus_ref)
    corpus = opus.corpus
    
    if request.method == 'POST' and "opus_audiofile" in request.FILES:
        description = request.POST["description"]
        audio_file = request.FILES["opus_audiofile"]
        
        audio = Audio (opus=opus, filename=audio_file.name, description=description,audio_file=audio_file)
        audio.save()
    else:
        logger.warning ("No file transmitted for opus " + corpus.ref)
       
    url = reverse('home:opus', args=(), kwargs={"opus_ref": opus_ref})
    return HttpResponseRedirect(url)


class SearchView(NeumaView):
    """Carry out a search"""

    def get(self, request, **kwargs):
        # Get the search context
        search_context = self.request.session["search_context"]

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
            search_context.pattern = self.request.GET['pattern']
            # Check that the pattern is long enough
            if not search_context.check_pattern_length():
                if search_context.keywords != "":
                    print("We are in keyword search mode")
                else:
                    print ("Pattern ignored : it must contain at least three intervals")
                    search_context.info_message  = "Pattern ignored : it must contain at least three intervals"
                search_context.pattern = ""

        #Initialize search_context.mirror_search according to the search request
        if 'mirror_search' in self.request.GET:
            if self.request.GET['mirror_search'] == "yes":
                search_context.mirror_search = True
            elif self.request.GET['mirror_search'] == "no":
                search_context.mirror_search = False
        else:
            search_context.mirror_search = False

        # If the context is an Opus, we redirect to the Opus view
        if search_context.is_opus():
            url = reverse('home:opus', args=(), kwargs={'opus_ref': search_context.ref})
            return HttpResponseRedirect(url)

        # If the criteria are empty, then forward to the corpus page
        if not search_context.in_search_mode():
            url = reverse('home:corpus', args=(), kwargs={'corpus_ref': search_context.ref})
            return HttpResponseRedirect(url)

        # OK, carry out the search
        context = self.get_context_data(**kwargs)
        return render(request, "home/search.html", context)
            
    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        search_context = self.request.session["search_context"]
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
                    #    Return a 'disabled account' error message
            else:
                # Return an 'invalid login' error message.
                context["invalid_login"] = 1

        return render(request, "home/index.html", context)
    