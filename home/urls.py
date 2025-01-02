
from django.urls import  path, include, re_path
from django.views.generic import TemplateView
from . import views

from neumautils.views import NeumaView
from .views import *


app_name="home"
urlpatterns = [
    re_path(r'^$', NeumaView.as_view(template_name="home/index.html"), name='index'),
   re_path(r'wildwebmidi.data', views.wildwebdata, name='wildwebdata'),
#
#   Philippe: what is this ???
	re_path (r'(.+\.data)$', views.wildwebdata, name='coco'),
    re_path(r'^presentation$', NeumaView.as_view(template_name="home/presentation.html"), name='presentation'),
    re_path(r'^services$', NeumaView.as_view(template_name="home/services.html"), name='services'),
    re_path(r'^collections$', NeumaView.as_view(template_name="home/collections.html"), name='collections'),
    re_path(r'^contact$', NeumaView.as_view(template_name="home/contact.html"), name='contact'),
	re_path(r'^testVerovio', NeumaView.as_view(template_name="home/testVerovio.html"), name='contact'),
	path('iiif/<str:iiif_id>/<str:viewer>', views.iiif, name='iiif_viewer'),
     re_path(r'^test', NeumaView.as_view(template_name="home/test.html"), name='test'),
   re_path(r'^auth', AuthView.as_view(template_name="home/index.html"), name='auth'),
   re_path(r'^form_login', TemplateView.as_view(template_name="home/form_login.html"), name='form_login'),
    re_path(r'^transcription', NeumaView.as_view(template_name="transcription/index.html"), name='transcription'),
    re_path(r'^keyboard', TemplateView.as_view(template_name="home/keyboard.html"), name='keyboard'),
    # ex: /main/corpus/sequentia/
    re_path(r'^corpus/(?P<corpus_ref>.+)/_export_zip/$', views.export_corpus_as_zip , name='corpus_export_zip'),
    re_path(r'^corpus/(?P<corpus_ref>.+)/_upload_zip/$', views.upload_corpus_zip , name='upload_corpus_zip'),
    re_path(r'^corpus/(?P<corpus_ref>.+)/_create_child/$', CorpusEditView.as_view(template_name="home/corpus_edit.html"), name='create_corpus_child'),
    re_path(r'^corpus/(?P<corpus_ref>.+)/_add_opus/$', views.add_opus , name='add_opus'),
    path('corpus/<str:corpus_ref>/', CorpusView.as_view(template_name="home/corpus.html"), name='corpus'),
    re_path(r'^show_licence/(?P<licence_code>.+)/$', views.show_licence , name='show_licence'),
    re_path(r'^opus/(?P<opus_ref>.+)/_edit/$', views.edit_opus , name='edit_opus'),
	  re_path(r'^opus/(?P<opus_ref>.+)/$', OpusView.as_view(template_name="home/opus.html"), name='opus'),
    re_path(r'^zoom/(?P<score_url>.+)/$', NeumaView.as_view(template_name="home/zoom.html"), name='zoom'),
    re_path(r'^search', SearchView.as_view(template_name="home/search.html"), name='search'),
    re_path(r'^structsearch', StructuredSearchView.as_view(template_name="home/structsearch.html"), name='structsearch'),
]
