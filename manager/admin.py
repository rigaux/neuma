from django.contrib import admin

from mptt.admin import MPTTModelAdmin

from guardian.admin import GuardedModelAdmin
from .models import Corpus, Opus, OpusMeta, Upload, Audio, SimMeasure, AnalyticModel, AnalyticConcept,  Descriptor, Bookmark


class CorpusAdmin(GuardedModelAdmin):
    search_fields = ("ref", "title", "description")


class OpusAdmin(GuardedModelAdmin):
    search_fields = ("ref", "title", "composer")
 

class OpusMetaAdmin(GuardedModelAdmin):
    search_fields = ("meta_key", "meta_value")

class UploadAdmin(GuardedModelAdmin):
    search_fields = ("description", "corpus")


class AudioAdmin(GuardedModelAdmin):
    search_fields = ("description", "opus")

class BookmarAdmin(GuardedModelAdmin):
    search_fields = ("opus")

class DescriptorAdmin(GuardedModelAdmin):
    search_fields = ("opus")
    
class AnalyticModelAdmin(GuardedModelAdmin):
    search_fields = ("name", "description")
 
admin.site.register(Corpus, CorpusAdmin)
admin.site.register(Upload,UploadAdmin)
admin.site.register(Audio,AudioAdmin)
admin.site.register(Opus, OpusAdmin)
admin.site.register(OpusMeta, OpusMetaAdmin)
admin.site.register(AnalyticModel, AnalyticModelAdmin)
admin.site.register(SimMeasure)
admin.site.register(Descriptor)
admin.site.register(Bookmark)
admin.site.register(AnalyticConcept, MPTTModelAdmin)

