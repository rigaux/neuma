

from django.views.generic import TemplateView
from . import views

from django.urls import path, re_path
from .views import *

app_name="collabscore"


urlpatterns = [
	#url -> re_path because django 4 no longer support
	path('',  TemplateView.as_view(template_name="collabscore/index.html"), name='index'),
	path('tests/', views.tests, name='tests'),

]

