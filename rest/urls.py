from rest_framework import routers
from . import views
from django.urls import  path, include, re_path

from rest_framework import permissions
from rest_framework.urlpatterns import format_suffix_patterns

app_name="rest"

urlpatterns = [
    # Welcome message
     path('', views.welcome, name='welcome'),
    ###############
    ## MISC SERVICE
    ###############
    path('misc/user/', views.handle_user_request, name='handle_user_request'),
    ###############
    ## META DATA
    ###############
	path('analysis/_models/', views.ModelList.as_view(), name='handle_models_request'),
	path('analysis/_models/<str:code>/', views.ModelDetail.as_view(), name='handle_model_request'),
	path('analysis/_models/<str:model_code>/<str:concept_code>/', views.ConceptDetail.as_view(), name='handle_concept_request'),
    #re_path(r'^analysis/models/(?P<model_code>.+)/concepts/(?P<encoding>.+)/$', views.handle_concepts_request, name='handle_concepts'),
    ################
    # SOURCES
    ################
    # POST a source file to a source
    #re_path(r'collections/(?P<full_neuma_ref>(.*))/_sources/(?P<source_ref>[-\w]+)/_file/$',views.handle_source_file_request, name='handle_source_file_request'),
	# GET or POST a file of a source
	re_path(r'collections/(?P<full_neuma_ref>(.*))/_sources/(?P<source_ref>[-\w]+)/_file/$',views.SourceFile.as_view(), name='handle_source_manifest_request'),
	# GET the manifest of a source
	re_path(r'collections/(?P<full_neuma_ref>(.*))/_sources/(?P<source_ref>[-\w]+)/_manifest/$',views.SourceManifest.as_view(), name='handle_source_manifest_request'),
    # GET a source description, or POST an update on a source
    re_path(r'collections/(?P<full_neuma_ref>(.*))/_sources/(?P<source_ref>[-\w]+)/$',views.Source.as_view(), name='handle_source_request'),
    # PUT a new source or GET the list of sources of an Opuss
    re_path('collections/(?P<full_neuma_ref>(.*))/_sources/',views.SourceList.as_view(), name='handle_sources_list_request'),
    ################
    # ANNOTATIONS
    ################
    # Get stats on annotations for an object
    path ('collections/<str:full_neuma_ref>/_annotations/_stats/', views.AnnotationStats.as_view(), name='opus_annotations_stats'),
	 # Get stats for an object and a model
	path ('collections/<str:full_neuma_ref>/_annotations/<str:model_code>/_stats/', views.AnnotationStats.as_view(), name='model_annotations_stats'),
    # Get/Update a specific annotation 
    path ('collections/<str:full_neuma_ref>/_annotations/<str:annotation_id>/', views.AnnotationDetail.as_view(), name='handle_annotation_detail'),
    # Put a new annotation 
    path ('collections/<str:full_neuma_ref>/_annotations/', views.AnnotationDetail.as_view(), name='put_annotation_request'),
     # Get or delete the list of annotations for an object and a model
    path ('collections/<str:full_neuma_ref>/_annotations/<str:model_code>/_all/', views.AnnotationList.as_view(), name='handle_annotations_model_list'),
    # Get or delete the list of annotations for an object, a model and a concept
    path ('collections/<str:full_neuma_ref>/_annotations/<str:model_code>/<str:concept_code>/_all/',  views.AnnotationList.as_view(), name='handle_annotations_concept_list'),
    ################
    # OPUS / CORPUS
    ################    
    path('collections/', views.welcome_collections, name='welcome_collections'),
    path('collections/_corpora/', views.TopLevelCorpusList.as_view(), name='handle_tl_corpora_request'),
    path('collections/<str:full_neuma_ref>/_corpora/', views.CorpusList.as_view(), name='handle_corpora_request'),
    path(r'collections/<str:full_neuma_ref>/_opera/', views.OpusList.as_view(), name='handle_opera_request'),
    #re_path(r'collections/(?P<full_neuma_ref>(.*))/_uploads/(?P<upload_id>(.*))/_import/$',views.handle_import_request, name='handle_import_request'),
     # Generic request to a corpus or an opus 
    path ('collections/<str:full_neuma_ref>/', views.Element.as_view(), name='handle_neuma_ref_request'),

    #  ArkIndex API implementation
    path('retrieve_corpus/<str:id>/', views.RetrieveCorpus.as_view(), name='retrieve_corpus'),
   path('list_elements/<str:corpus>/', views.ArkIdxListElements.as_view(), name='list_element'),
   path('list_element_children/<str:id>/', views.ArkIdxListElementChildren.as_view(), name='list_element_children'),
    path('list_element_metadata/<str:id>/', views.ArkIdxListElementMetaData.as_view(), name='list_element_children'),
	path('get_element_file/<str:id>/', views.ArkIdxGetElementFile.as_view(), name='retrieve_element_file'),
 
]
