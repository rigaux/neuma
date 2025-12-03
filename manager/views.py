from django.shortcuts import render
from django.conf import settings

# To communicate with ElasticSearch
from neumasearch.IndexWrapper import IndexWrapper

from neumautils.views import NeumaView
import zipfile, io

import PIL as pillow

import json
import os  
from pathlib import Path


# Create your views here.
from django.http import HttpResponse

from .models import Image, Opus, Corpus, Descriptor, Upload

from django_celery_results.models import TaskResult

def index(request):	
	
	return render(request, 'manager/index.html')

def tasks_list(request):
	'''Display Celery tasks'''

	context = {"tasks": TaskResult.objects.all()}
	return render(request, 'manager/tasks_list.html', context)

def task_detail(request,task_id):
	'''Display details on a task'''
	
	context = {"task": TaskResult.objects.get(id=task_id)}

	return render(request, 'manager/task_detail.html', context)

def corpora(request):
	'''Display a tree of corpora with related actions'''
	top_level = Corpus.objects.filter(parent__isnull=True)
	for corpus in top_level:
		corpus.get_children()
	context = {"corpora": top_level}
	
	return render(request, 'manager/corpora.html', context)

def testes(request):
	'''Test ElasticSearch connection'''

	search = IndexWrapper()
	corpora = search.get_all_corpora()
	
	context = {"hits": corpora}
	return render(request, 'manager/testes.html', context)


def load_images(request):
	'''Load IIIF images'''

	context = {"images": []}
	
	directory = 'data/imgs'  # IIIF images are locally stored there
	remote_dir = "imgs%2F" # Images are stored there in the IIIF server 
	for entry in os.scandir(directory):  
		if entry.is_file():  # check if it's a file
			if Path(entry.path).suffix in [".svg", ".png", ".jpg", ".jpeg"]:
				file_id = Path(entry.path).stem
				file_name = Path(entry.path).name
				
				img = pillow.Image.open(entry.path)
				width, height= img.size
				iiif_url = settings.IIIF2_SERVER + remote_dir + file_id

				try:
					db_img = Image.objects.get(iiif_url=iiif_url)
				except Image.DoesNotExist:
					print (f"Unknown Image {{iiif_url}}")
					db_img = Image (iiif_id=file_id, 
							iiif_url=iiif_url,width=width,height=height)
					db_img.save()

				context['images'].append({"file_name": file_name,
								"iiif_url": iiif_url, 
								"width": width, "height":height})
		
	return render(request, 'manager/load_images.html', context)

def list_images(request):
	'''List IIIF images'''

	context = {"images": []}
	for img in Image.objects.all():
		context['images'].append(img)
		
	return render(request, 'manager/list_images.html', context)


class ShowUploads(NeumaView):
	"""Display the list of uploads"""

	def get_context_data(self, **kwargs):

		 # Initialize context
		context = super(ShowUploads, self).get_context_data(**kwargs)

		context['uploads'] = Upload.objects.filter().order_by("update_timestamp")
		return context


class ListImports(NeumaView):
	"""Display the list of files in an Upload"""

	def get_context_data(self, **kwargs):
		 # Initialize context
		context = super(ListImports, self).get_context_data(**kwargs)
		# Get the upload
		upload_id = self.kwargs['upload_id']
		do_import = self.kwargs['do_import']
		upload = Upload.objects.get(id=upload_id)
		context['upload'] = upload
		context['do_import'] = do_import

		# Check the zip
		if zipfile.is_zipfile(upload.zip_file.path):
			context['message'] = 'Correct zip file'
			zf = zipfile.ZipFile(upload.zip_file.path, 'r')
			xml_files = []
			for fname in zf.namelist():
				basename = os.path.basename(fname)
				extension =  os.path.splitext(basename)[1]
				ref = os.path.splitext(basename)[0]
				if not fname.startswith('_') and (extension=='.xml' or extension ==".mei" or extension=='.mxl'):
					
					if extension == '.mxl':
						# Compressed XML
						container = io.BytesIO(zf.read(fname))
						xmlzip = zipfile.ZipFile(container)
						# Keep the file in the container with the same basename
						for name2 in xmlzip.namelist():
							basename2 = os.path.basename(name2)
							ref2 = os.path.splitext(basename2)[0]
							if ref == ref2:
								 xml_data = xmlzip.read(name2)
					else:
						xml_data = zf.read(fname)
					# And now instantiate the Opus
					#opus = Opus.createFromMusicXML(upload.corpus, ref, xml_data)
					
					#if do_import:
					#	opus.save()
					xml_files.append(basename)
					#break
			context['filenames']= xml_files
			
		else:
			context['message'] = 'Invalid zip file'
		return context
