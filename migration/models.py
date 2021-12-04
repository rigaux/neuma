# coding: utf-8
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from manager.models import Corpus, Opus
from neuma.rest import Client


class CorpusMigration(models.Model):
    corpus = models.OneToOneField(Corpus, unique=True,on_delete=models.CASCADE)
    tag = models.TextField()
    parent = models.ForeignKey('self', null=True,on_delete=models.CASCADE)
    creation_timestamp = models.DateTimeField('Created',auto_now_add=True)
    update_timestamp = models.DateTimeField('Updated',auto_now=True)

    class Meta:
        db_table = "CorpusMigration"

    def load_corpus_from_neuma(self, neuma_client, dict, recursion=False):
        # Check whether the corpus already exists
        try:
            corpus = Corpus.objects.get(ref=dict["id"])
        except Corpus.DoesNotExist as e:
            corpus = Corpus()
        self.tag = "Initial import"

        # Load and save the corpus
        corpus.load_from_dict(dict)
        if self.parent != None:
            corpus.parent = self.parent.corpus
        corpus.save()
        self.corpus = corpus
        self.save()

        children = []
        if (recursion == True):
            rest_res = neuma_client.get_children_from_corpus(self.corpus.ref)
            neumaChildren = rest_res["corpora"]

            for child in neumaChildren:
                # Get of create a child migration
                try:
                    cmigration = CorpusMigration.objects.get(corpus__ref=child["id"])
                except CorpusMigration.DoesNotExist as e:
                    cmigration = CorpusMigration()
                cmigration.parent = self
                cmigration.tag = "Initial import"
                children.append(cmigration.load_corpus_from_neuma(neuma_client, child, recursion))
                cmigration.save()

        return {"migration": self, "children": children}

    def migrate_opera(self, tag, type):
        '''
          Migrate from Neuma
        '''
        neuma_client = Client.Client()
        rest_res = neuma_client.get_opera_from_corpus(self.corpus.ref)
        opera=[]
        for dict_opus in rest_res['opera']:
            dict_opus["id"] = dict_opus["id"].strip() # Take care...
            try:
                opus = Opus.objects.get(ref=dict_opus["id"])
            except ObjectDoesNotExist as e:
                #print("error, does not exist")
                opus = Opus()
            #except Opus.DoesNotExist as e:
                #opus = Opus()

            if (type == "opus"):
                # Get the migration record, if any
                try:
                    omigration = OpusMigration.objects.get(opus=opus)
                except OpusMigration.DoesNotExist as e:
                    omigration = OpusMigration()

                if (omigration.tag == tag):
                    # Already processed
                    print ("Opus " + dict_opus["id"] + " already imported for tag " + tag)
                    continue
                else:
                    print ("Corpus " + self.corpus.ref + ". Import opus " + dict_opus["id"])

                #Get the files for this Opus
                files = neuma_client.get_files_from_opus(dict_opus["id"])
                # Load Opus content
                opus_url = neuma_client.get_opus_url(dict_opus["id"])
                opus.load_from_dict(self.corpus, dict_opus, files, opus_url)

                opus.save()

                omigration.opus = opus
                omigration.tag = tag
                omigration.save()

                opera.append(opus)
            elif (type=="descriptor"):
                try:
                    opus = Opus.objects.get(ref=dict_opus["id"])
                except Opus.DoesNotExist as e:
                    print("Opus %s does not exist. Please migrate opera first" % dict_opus["id"])

                print ("Corpus " + self.ref + ". Import descriptors for opus " + dict_opus["id"])
                #Get the descriptors for this Opus
                descriptors = neuma_client.get_descriptors_from_opus(opus.ref)
                # Clean the current descriptors
                Descriptor.objects.filter(opus=opus).delete()
                for descr in descriptors:
                    # Store in Postgres
                    descriptor = Descriptor()
                    descriptor.opus = opus
                    descriptor.part = descr["idPart"]
                    descriptor.voice = descr["idVoice"]
                    descriptor.type = descr["type"]
                    descriptor.value = descr["value"]
                    descriptor.save()

                opera.append(opus)

        # Recursive call
        children = self.get_children()
        for item in children:
            # print ("Import for child " + item["migration"].corpus.title + " (ref=" + item["migration"].corpus.ref +")")
            item["migration"].tag = tag
            item["migration"].save()
            item["migration"].migrate_opera(tag, type)
            print("ok")

        return opera

    def count_imported_opera(self):
        imports = OpusMigration.objects.filter(opus__corpus=self.corpus,tag=self.tag).count()
        return imports

    def __str__(self):              # __unicode__ on Python 2
        return self.corpus.title

    def get_children(self):
        children =  CorpusMigration.objects.filter(corpus__parent=self.corpus)

        result = []
        for child in children:
            result.append({"migration": child, "children": child.get_children()})

        return result


class OpusMigration(models.Model):
    opus = models.OneToOneField(Opus,unique=True,on_delete=models.CASCADE)
    tag = models.TextField()
    creation_timestamp = models.DateTimeField('Created',auto_now_add=True)
    update_timestamp = models.DateTimeField('Updated',auto_now=True)

    class Meta:
        db_table = "OpusMigration"

    def __str__(self):              # __unicode__ on Python 2
        return self.opus.title
