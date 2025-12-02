from django.contrib import admin

from mptt.admin import MPTTModelAdmin

from guardian.admin import GuardedModelAdmin
from .models import (Corpus, Opus, Upload, 
					AnalyticModel, Bookmark, Config,
					AnalyticConcept, Annotation, Resource, 
					Descriptor,  Organization, Licence, Person, Image,
					SourceType, OpusSource)

class CorpusAdmin(GuardedModelAdmin):
    search_fields = ("ref", "title", "description")

class OpusAdmin(GuardedModelAdmin):
    search_fields = ("ref", "title", "composer")
 
class OpusSourceAdmin(GuardedModelAdmin):
    search_fields = ("opus__ref", "ref",  "url")



class UploadAdmin(GuardedModelAdmin):
    search_fields = ("description", "corpus")


class AudioAdmin(GuardedModelAdmin):
    search_fields = ("description", "opus")

class BookmarAdmin(GuardedModelAdmin):
    search_fields = ["opus"]

class DescriptorAdmin(GuardedModelAdmin):
    search_fields = ("opus")
    
class AnalyticModelAdmin(GuardedModelAdmin):
    search_fields = ("name", "description")
 
admin.site.register(Corpus, CorpusAdmin)
admin.site.register(Upload,UploadAdmin)
admin.site.register(Bookmark, BookmarAdmin)
admin.site.register(Opus, OpusAdmin)
admin.site.register(AnalyticModel, AnalyticModelAdmin)
admin.site.register(SourceType)
admin.site.register(OpusSource,OpusSourceAdmin)
admin.site.register(Annotation)
admin.site.register(Resource)
admin.site.register(Descriptor)
admin.site.register(Organization)
admin.site.register(Licence)
admin.site.register(Config)
admin.site.register(Image)
admin.site.register(Person)
admin.site.register(AnalyticConcept, MPTTModelAdmin)

