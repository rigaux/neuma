from django.conf.urls import url

from . import views
from neumautils.views import NeumaView

from .views import QualityView, ModelView

app_name="quality"
urlpatterns = [
    url(r'^$', QualityView.as_view(template_name="quality/index.html"), name='index'),
    url(r'^model$', ModelView.as_view(template_name="quality/model.html"), name='model'),
    url(r'^wildwebmidi.data', views.wildwebdata, name='wildwebdata'),
]