from django.urls import  path, re_path

from . import views
from neumautils.views import NeumaView

app_name="quality"
urlpatterns = [
    re_path(r'^$', views.QualityView.as_view(template_name="quality/index.html"), name='index'),
    re_path(r'^model$', views.ModelView.as_view(template_name="quality/model.html"), name='model'),
    re_path(r'^wildwebmidi.data', views.wildwebdata, name='wildwebdata'),
]