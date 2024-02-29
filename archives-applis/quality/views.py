import hashlib
import json
import os
import urllib
from xml.dom import minidom

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import render
from lxml import etree

from neumautils.views import NeumaView
from manager.models import Corpus, Opus, Annotation, AnalyticModel, AnalyticConcept
from scorelib import analytic_concepts
from scorelib.analytic_concepts import *
from neumasearch.SearchContext import SearchContext
from workflow.Workflow import Workflow, workflow_import_zip

from .models import QtDimension, QtMetric


class SchemaView(NeumaView):
    """Display the list of corpora"""

    def get_context_data(self, **kwargs):
        context = super(SchemaView, self).get_context_data(**kwargs)

        context['dimensions'] = {}
        for dimension in QtDimension.objects.all():
            context['dimensions'][dimension.ref] = {}
            context['dimensions'][dimension.ref]['dimension'] = dimension
            context['dimensions'][dimension.ref]['metrics'] = QtMetric.objects.filter(dimension=dimension)
            
        return context


class QualityView(NeumaView):
    """Display a score with its quality indicators"""

    def get_context_data(self, **kwargs):
        context = super(QualityView, self).get_context_data(**kwargs)

        # For tracking in the Neuma menu
        context["current_view"] = "quality:index"
        
        # Get the quality test suite
        corpus_test_suite = Corpus.objects.get(ref=settings.NEUMA_QUALITY_CORPUS_REF)
        # next line : ugly workaround to get an opus to display
        default_quality_score = "http://"+self.request.get_host()+"/media/corpora/qualeval/jesu_meines_herzens_freud.mei"
        
        context["test_suite"] = []
        for opus_test in Opus.objects.filter(corpus=corpus_test_suite):
             context["test_suite"].append({"url" : self.request.build_absolute_uri(opus_test.mei.url),"label": opus_test.title})
             default_quality_score = self.request.build_absolute_uri(opus_test.mei.url)
        
            
        if "url_score" in  self.request.GET:
            url_score = self.request.GET['url_score']
        else:
            url_score = default_quality_score
        
        context["url_score"] = url_score
        
        # OK we have a score URL. Let's try to get it
        try:
            response = urllib.request.urlopen(url_score)
            data = response.read()
            # The score is stored in the external corpus
            external = Corpus.objects.get(ref=settings.NEUMA_EXTERNAL_CORPUS_REF)
            # The reference of the opus is a hash of the URL
            hash_object = hashlib.sha256(data).hexdigest()
            opus_ref = settings.NEUMA_EXTERNAL_CORPUS_REF + settings.NEUMA_ID_SEPARATOR + hash_object[:16]
            
            doc = minidom.parseString(data)
            root = doc.documentElement
            if root.nodeName == "mei":
                try:
                    opus = Opus.objects.get(ref=opus_ref)
                except Opus.DoesNotExist as e:
                    opus = Opus()
                opus.corpus = external
                opus.ref = opus_ref # Temporary
                opus.mei.save("mei.xml", ContentFile(data))
            else:
                # Hope this is a mMusicXML file
                opus = Opus.createFromMusicXML(external, opus_ref, data)
                # Produce the MEI file
                Workflow.produce_opus_mei(opus)
       
            opus.external_link = url_score
            opus.save()
            
            # Now analyze the score quality
            # Workflow.quality_check (opus)
        except Exception as ex:
            context["error_message"] =  str(ex)
            context["invalid_url"] =  url_score
            return context
            
        print ("Opus created. Ref =" + opus.ref)
        context["opus"] = opus
        
        quality_model = AnalyticModel.objects.get(code=analytic_concepts.AMODEL_QUALITY)
        context['analytic_concepts'] = AnalyticConcept.objects.filter(model=quality_model)

        # Initialize the context.
        self.request.session["search_context"] = SearchContext()

        return context
    

class ModelView(NeumaView):
    """Display a score with its quality indicators"""

    def get_context_data(self, **kwargs):
        context = super(ModelView, self).get_context_data(**kwargs)
        
        try:
            db_model = AnalyticModel.objects.get(code=AMODEL_QUALITY)
            context["concepts"]  = AnalyticConcept.objects.filter(model=db_model,parent=None)
        except AnalyticModel.DoesNotExist:
            return context

        return context

def wildwebdata(request):
    """ Serves the wildwebmidi.data sample from any .data URL"""
    path = os.path.dirname(os.path.abspath(__file__)) + "/../static/wildwebmidi.data"
    image_data = open(path, "rb").read()
    return HttpResponse(image_data, content_type="image/png")
