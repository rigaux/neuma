
from django.urls import  path, include, re_path

from . import views

from neumautils.views import NeumaView
from .views import ShowView

app_name="migration"
urlpatterns = [
    re_path(r'^$', NeumaView.as_view(template_name="migration/index.html"), name='index'),
    re_path(r'^migrate/$', views.migrate, name='migrate'),
    re_path(r'^show/$', ShowView.as_view(template_name="migration/show.html"), name='show')
]