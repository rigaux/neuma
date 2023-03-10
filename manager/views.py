from django.shortcuts import render
from django.conf import settings

# To communicate with Neuma
from neuma.rest import Client
# To communicate with ElasticSearch
from neumasearch.IndexWrapper import IndexWrapper

from neumautils.views import NeumaView
import zipfile, os.path, io

import json

# Create your views here.
from django.http import HttpResponse

from .models import Opus, Corpus, Descriptor, Upload

def index(request):    
    
    return render(request, 'manager/index.html')


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
                    #    opus.save()
                    xml_files.append(basename)
                    #break
            context['filenames']= xml_files
            
        else:
            context['message'] = 'Invalid zip file'
        return context
