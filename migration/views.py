from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.conf import settings
# To communicate with Neuma
from neuma.rest import Client
# To communicate with ElasticSearch
from search.IndexWrapper import IndexWrapper

import json


from neumautils.views import NeumaView

from .models import Opus, Corpus
from .models import OpusMigration, CorpusMigration

def migrate(request):
    '''Send REST queries to Neuma to get the tree of public corpora, import
    them in Postgres/Django'''
    neuma_client = Client.Client()
    # Get top level corpora, convert to Corpus instances, display
    rest_res = neuma_client.get_top_level_corpora()
    migrations = []
    for dict_corpus in rest_res:
        # Get or create the migration action
        try:
            cmigration = CorpusMigration.objects.get(corpus__ref=dict_corpus["id"])
        except CorpusMigration.DoesNotExist as e:
            cmigration = CorpusMigration()

        migration_dict = cmigration.load_corpus_from_neuma(neuma_client, dict_corpus, True)
        cmigration.save()
                
        migrations.append(migration_dict)
        
    context = {"migrations": migrations, "neuma_url": settings.NEUMA_URL}
 
    return render(request, 'migration/migrate.html', context)


class ShowView(NeumaView):
    """Display the list of corpora"""

    def get_context_data(self, **kwargs):

        migrations = CorpusMigration.objects.filter(corpus__parent=None).order_by("update_timestamp")
        # Initialize context
        context = super(ShowView, self).get_context_data(**kwargs)

        context['migrations'] = []
        for migration in migrations:
            context['migrations'].append({"migration": migration, "children": migration.get_children()})

        return context


def migropera_deprecated(request, corpus_ref):
    '''Implemented as a script'''
    neuma_client = Client.Client()
    
    try:
        corpus = Corpus.objects.get(ref=corpus_ref)
    except Corpus.DoesNotExist as e:
        return HttpResponse("Corpus %s does not exist %s." % corpus_ref)

    # Get opera
    rest_res = neuma_client.get_opera_from_corpus(corpus_ref)
    opera = []
    for dict_opus in rest_res['opera']:
        
        try:
            opus = Opus.objects.get(ref=dict_opus["id"])
        except Opus.DoesNotExist as e:
            opus = Opus()

        #Get the files for this Opus
        files = neuma_client.get_files_from_opus(opus.ref)
        # Load Opus content
        opus_url = neuma_client.get_opus_url(opus.ref)
        opus.load_from_dict(corpus, dict_opus, files, opus_url)        

        opus.save()
                
        opera.append(opus)
    context = {"opera": opera}

    return render(request, 'manager/migropera.html', context)
