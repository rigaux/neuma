
from django.urls import  path, include, re_path
from . import views

from .views import ShowUploads, ListImports

app_name="manager"
urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^corpora/$', views.corpora, name='corpora'),
    re_path(r'^imports/$', ShowUploads.as_view(template_name="manager/imports.html"), name='imports'),
    re_path(r'^content/(?P<upload_id>.+)/(?P<do_import>.+)/$', ListImports.as_view(template_name="manager/list_imports.html"), name='list_imports'),
    re_path(r'^testes/$', views.testes, name='testes')
    ]