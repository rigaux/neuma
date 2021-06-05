from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.conf import settings

import json

from neumautils.views import NeumaView

from manager.models import Opus, Corpus

class SchemaView(NeumaView):
    """Display the list of corpora"""

    def get_context_data(self, **kwargs):
        context = super(SchemaView, self).get_context_data(**kwargs)

        context['dimensions'] = {}
        for dimension in QtDimension.objects.all():
            context['dimensions'][dimension.ref] = {}
            context['dimensions'][dimension.ref]['dimension'] = dimension
            context['dimensions'][dimension.ref]['metrics'] = QtMetric.objects.filter(dimension=dimension)
            
        return context
