from django.conf.urls import url

from . import views
from neumautils.views import NeumaView
from .views import SchemaView

app_name="scoreql"
urlpatterns = [
    url(r'^$', SchemaView.as_view(template_name="scoreql/index.html"), name='index')
]
