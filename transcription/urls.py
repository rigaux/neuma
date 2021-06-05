from django.conf.urls import url
from django.views.generic import TemplateView
from . import views

from neumautils.views import NeumaView
from .views import *

app_name="transcription"
urlpatterns = [
    url(r'^$', NeumaView.as_view(template_name="transcription/index.html"), name='index'),
    # url(r'^corpus/(?P<corpus_ref>.+)/$', CorpusView.as_view(template_name="transcription/corpus.html"), name='corpus'),
    url(r'^opus/(?P<opus_ref>.+)/(?P<pattern>.*)/$', OpusView.as_view(template_name="transcription/opus.html"), name='opus'),
    url(r'^opus/(?P<opus_ref>.+)/$', OpusView.as_view(template_name="transcription/opus.html"), name='opus'),
    url(r'^opus/(?P<opus_ref>.+)/(?P<audio_id>.+)', OpusView.as_view(template_name="transcription/opus.html"), name='opus'),
]
