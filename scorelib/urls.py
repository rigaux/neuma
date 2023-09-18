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

from django.urls import  path, re_path, include

from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings

from neumautils.views import NeumaView


import home.views

urlpatterns = [
    re_path(r'^$', NeumaView.as_view(template_name="home/index.html"), name='index'),
    re_path (r'^neumadmin/', admin.site.urls),
    re_path(r'^manager/', include('manager.urls', namespace="manager")),
    re_path(r'^home/', include('home.urls', namespace="home")),
    re_path(r'^quality/', include('quality.urls', namespace="quality")),
    re_path(r'^rest/', include('rest.urls', namespace="rest")),
   ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)