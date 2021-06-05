from django.conf.urls import url

from . import views

from neumautils.views import NeumaView
from .views import ShowView

app_name="migration"
urlpatterns = [
    url(r'^$', NeumaView.as_view(template_name="migration/index.html"), name='index'),
    url(r'^migrate/$', views.migrate, name='migrate'),
    url(r'^show/$', ShowView.as_view(template_name="migration/show.html"), name='show')
]