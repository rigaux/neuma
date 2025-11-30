
from django.urls import  path, include, re_path
from . import views

from .views import ShowUploads, ListImports

app_name="manager"
urlpatterns = [
    path('', views.index, name='index'),
    path('corpora', views.corpora, name='corpora'),
	path('tasks/', views.tasks_list, name='tasks_list'),
	path('task/<str:task_id>/', views.task_detail, name='task_detail'),
    path('imports', ShowUploads.as_view(template_name="manager/imports.html"), name='imports'),
    path('content/<str:upload_id>/<str:do_import>', ListImports.as_view(template_name="manager/list_imports.html"), name='list_imports'),
    path('testes', views.testes, name='testes'),
    path('load_images', views.load_images, name='load_images'),
    path('list_images', views.list_images, name='list_images'),
    ]