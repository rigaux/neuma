from lib.search import IndexWrapper
from manager.models import *

indexwrapper = IndexWrapper()

currentopus = Opus.objects.filter(corpus="all:composers:sequentia").delete()
print(currentopus.title)
indexwrapper.index_opus(currentopus)

