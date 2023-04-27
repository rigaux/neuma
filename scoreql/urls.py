from django.urls import  path, re_path

from . import views
from neumautils.views import NeumaView
from .views import SchemaView

app_name="scoreql"
urlpatterns = [
    re_path(r'^$', SchemaView.as_view(template_name="scoreql/index.html"), name='index')
]
