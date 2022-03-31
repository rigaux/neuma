"""scorelib URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings

from neumautils.views import NeumaView

import home.views

urlpatterns = [
    url(r'^$', NeumaView.as_view(template_name="home/index.html"), name='index'),
    url (r'^neumadmin/', admin.site.urls),
    url(r'^manager/', include('manager.urls', namespace="manager")),
    url(r'^home/', include('home.urls', namespace="home")),
    url(r'^quality/', include('quality.urls', namespace="quality")),
    url(r'^scoreql/', include('scoreql.urls', namespace="scoreql")),
    url(r'^rest/', include('rest.urls', namespace="rest")),
    url(r'^migration/', include('migration.urls', namespace="migration")),
    url(r'^transcription/', include('transcription.urls', namespace="transcription")),
	url(r'^collabscore/', include('collabscore.urls', namespace="collabscore")),
   ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
