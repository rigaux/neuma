from django.conf.urls import url

from . import views

from .views import ShowUploads, ListImports

app_name="manager"
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^corpora/$', views.corpora, name='corpora'),
    url(r'^imports/$', ShowUploads.as_view(template_name="manager/imports.html"), name='imports'),
    url(r'^content/(?P<upload_id>.+)/(?P<do_import>.+)/$', ListImports.as_view(template_name="manager/list_imports.html"), name='list_imports'),
    url(r'^testes/$', views.testes, name='testes')
    ]