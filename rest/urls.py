from rest_framework import routers
from . import views
from django.views.decorators.csrf import csrf_exempt


from django.urls import  path, include, re_path

from .views import *


from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

#from rest_framework.documentation import include_docs_paths

#router = routers.DefaultRouter()

#router.register(r'source', views.Source, base_name='rest_source')
app_name="rest"


schema_view = get_schema_view(
   openapi.Info(
      title="Neuma REST API",
      default_version='v1',
      description="List and usage of Neuma REST services",
   ),
   public=False,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    # Welcome message
     path('', views.welcome, name='welcome'),

   #### Swagger documentation
   #re_path('apidoc/', include_docs_paths(title='Neuma REST API documentation')),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
  re_path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    ###############
    ## MISC SERVICE
    ###############
    path('misc/user/$', views.handle_user_request, name='handle_user_request'),
    ###############
    ## META DATA
    ###############
    path('analysis/_models/<str:model_code>/_concepts/_all/$', views.handle_concepts_request, name='handle_concepts_request'),
    re_path(r'^analysis/_models/(?P<model_code>.+)/_concepts/(?P<concept_code>.+)/_all/$', views.handle_concepts_request, name='handle_concepts_request'),
    #re_path(r'^analysis/models/(?P<model_code>.+)/concepts/(?P<encoding>.+)/$', views.handle_concepts_request, name='handle_concepts'),
    ################
    # SOURCES
    ################
    # POST a source file to a source
    re_path(r'collections/(?P<full_neuma_ref>(.*))/_sources/(?P<source_ref>[-\w]+)/_file/$',views.handle_source_file_request, name='handle_source_file_request'),
    # GET a source description, or POST an update on a source
    re_path(r'collections/(?P<full_neuma_ref>(.*))/_sources/(?P<source_ref>[-\w]+)/$',views.handle_source_request, name='handle_source_request'),
    # PUT a new source or GET the list of sources of an Opus
    re_path(r'collections/(?P<full_neuma_ref>(.*))/_sources/$',views.handle_sources_request, name='handle_sources_request'),
    ################
    # ANNOTATIONS
    ################
    # Get stats on annotations for an object
    re_path (r'^collections/(?P<full_neuma_ref>(.*))/_annotations/_stats/$', views.handle_stats_annotations_request, name='handle_annotations_stats'),
    # Get/Update a specific annotation 
    re_path (r'^collections/(?P<full_neuma_ref>(.*))/_annotations/(?P<annotation_id>[-\w]+)/$', views.handle_annotation_request, name='handle_annotation_request'),
    # Put a new annotation 
    re_path (r'^collections/(?P<full_neuma_ref>(.*))/_annotations/$', views.put_annotation_request, name='put_annotation_request'),
     # Get stats for an object and a model
    re_path (r'^collections/(?P<full_neuma_ref>(.*))/_annotations/(?P<model_code>[-\w]+)/_stats/$', views.handle_stats_annotations_request, name='handle_annotations_model_stats'),
     # Get or delete the list of annotations for an object and a model
    re_path (r'^collections/(?P<full_neuma_ref>(.*))/_annotations/(?P<model_code>[-\w]+)/_all/$', views.handle_annotations_request, name='handle_annotations_model_request'),
    # Get or delete the list of annotations for an object, a model and a concept
    re_path (r'^collections/(?P<full_neuma_ref>(.*))/_annotations/(?P<model_code>[-\w]+)/(?P<concept_code>.+)/_all/$', views.handle_annotations_request, name='handle_annotations_concept_request'),
    #################
    # Transcription
    #################
    # Access to a grammar by its name
    re_path('transcription/_qparse/', views.qparse, name='grammars'),
    re_path('transcription/grammars/', views.grammars, name='grammars'),
    re_path('transcription/grammars/<str:grammar_name>/', views.grammar, name='grammar'),

    ################
    # OPUS / CORPUS
    ################    
    path('collections/', views.welcome_collections, name='welcome_collections'),
    path('collections/_corpora/$', views.TopLevelCorpusList.as_view(), name='handle_tl_corpora_request'),
    re_path(r'^collections/(?P<full_neuma_ref>(.+))/_corpora/$', views.CorpusList.as_view(), name='handle_corpora_request'),
    re_path(r'collections/(?P<full_neuma_ref>(.*))/_opera/$', views.handle_opera_request, name='handle_opera_request'),
    re_path(r'collections/(?P<full_neuma_ref>(.*))/_files/$',views.handle_files_request, name='handle_files_request'),
   re_path(r'collections/(?P<full_neuma_ref>(.*))/_uploads/(?P<upload_id>(.*))/_import/$',views.handle_import_request, name='handle_import_request'),
    # Request for a specific file
    re_path (r'^collections/(?P<full_neuma_ref>(.*))/*.xml$', views.handle_neuma_ref_request, name='handle_files_reauest'),
    # Generic request to a corpus or an opus 
    re_path (r'^collections/(?P<full_neuma_ref>(.*))/$', views.handle_neuma_ref_request, name='handle_neuma_ref_request'),
    # OTF Transcription
    re_path(r'transcription/midi_message', views.receive_midi_messages, name="midi_message"),
    re_path(r'transcription/test_midi_message', views.test_midi_messages, name='test_midi_message'),
]