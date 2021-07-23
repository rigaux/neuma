from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from manager.models import Corpus, Opus

from django.contrib.auth.models import User, Group
from guardian.shortcuts import assign_perm

from workflow.Workflow import Workflow
#from dmining.models import StatsDesc
import string
import os
import re
import subprocess
from django.core.files import File
import csv

from lib.music.Score import *
from lib.music.Voice import IncompleteBarsError

# List of actions

TO_MEI_ACTION = "mei"
INDEX_ACTION="index"
INDEX_ALL_ACTION = "index_all"
LILYPOND_ACTION="lilypond"
COMPILE_ACTION="compile"
CHORALS_ACTION="chorals"
STATS_ACTION="stats"
TITLE_ACTION="title"
DISSONANCE_ACTION="dissonance"
CPTDIST="cptdist"
KMEANS="kmeans"# -c corpus -k nb_class -t tag(id) -d descriptor -m metric
QUALEVAL="qualeval"
FIX_PERMISSIONS_ACTION="fix_permissions"
CPT_GRAMMAR="cptgrammar"
DESCRIPTORJSON_ACTION="descriptorjson"

class Command(BaseCommand):
    """Scan a corpus specified as input, and apply some action"""

    help = 'Scan a corpus specified as input, and apply some action'

    def add_arguments(self, parser):
        parser.add_argument('-c', dest='corpus_ref')
        parser.add_argument('-a', dest='action')
        parser.add_argument('-o', dest='opus_ref')
        parser.add_argument('-k', dest='class_number')
        parser.add_argument('-t', dest='tag')
        parser.add_argument('-d', dest='descriptor')
        parser.add_argument('-m', dest='metric')

    def handle(self, *args, **options):
        action = options['action']

        # Actions that do not need corpus argument
        if action == INDEX_ALL_ACTION:
            corpora = Corpus.objects.all()
            for c in corpora:
                if not c.parent_ref(c.ref):
                    Workflow.index_corpus(c)
            return True

        try:
            corpus = Corpus.objects.get(ref=options['corpus_ref'])
            opusref = options['opus_ref']
        except Corpus.DoesNotExist:
                raise CommandError('Corpus "%s" does not exist' % options['corpus_ref'])

#        exit(1)

        if not opusref:  # on travaille sur tout un corpus
            # print("coucou")
            # corpora = Corpus.objects.all()
            # for c in corpora:
                # print(c.ref)
                # opera = c.get_opera()
                # for opus in opera:
                    # print(opus.ref)

            if action is None:
                self.stdout.write("Please supply an action ")
                return
            self.stdout.write('Scanning corpus "%s" with action: %s' % (corpus.title,action))            

            if action == TO_MEI_ACTION:
                Workflow.produce_mei(corpus)
                print ("MEI conversion completed for " + corpus.title)
            elif action == INDEX_ACTION:
                Workflow.index_corpus(corpus)
                print ("Indexing completed for corpus '" + corpus.title + "'")
            elif action == COMPILE_ACTION:
                try:
                    Workflow.compile(corpus)
                except  Exception as ex:
                    print ("Exception for corpus " + corpus.ref + " Message:" + str(ex))
                print ("Compilation completed for " + corpus.title)
            elif action == CHORALS_ACTION:
                print ("Collect chorals titles")
                with open(settings.BASE_DIR +  '/static/chorals_titles.txt') as titles_file:
                    titlereader = csv.reader(titles_file, delimiter=';')  
                    i = 1
                    for row in titlereader:
                        title = row[0]
                        pos_virg = row[1].find(',')
                        if pos_virg == -1: 
                            bvw = row[1]
                        else:
                            bvw = row[1][0:pos_virg]
                        clean = bvw.replace(' ', '').replace(')', '').lower()
                        print ("Searching opus " + clean)
                        try:
                            opus = Opus.objects.filter(ref__contains=clean).first()
                            opus.title = title
                            opus.save()
                            print ("Found !!!")
                        except:
                            print ("Unable to find opus with ref " + clean)
            elif action == TITLE_ACTION:        
                for opus in Opus.objects.filter(corpus__ref=corpus.ref):
                    self.stdout.write("Found opus " + opus.title)
                    score = opus.get_score()

                    self.stdout.write("Score title " + score.get_title())
                    if score.get_title() != None and len(score.get_title()) > 0:
                        opus.title = score.get_title()
                        opus.save()
                    if score.get_composer() != None and len(score.get_composer()) > 0:
                        opus.composer = score.get_composer()
                        opus.save()
                        
            elif action == STATS_ACTION:
                for opus in Opus.objects.filter(corpus__ref=corpus.ref):
                    self.stdout.write("Found opus " + opus.title)
                    if opus.musicxml:
                        if os.path.isfile( opus.musicxml.path):
                            musicxml = opus.musicxml.read()
                            self.stdout.write("Size of MusicXML file for " + opus.title + " = " + str(len(musicxml)))
                            self.stdout.write("Essai de stats")
                            stats = StatsDesc(opus)
                            self.stdout.write(stats.name)
                        else:
                            self.stdout.write("Warning: invalid MusicXML file path for " + opus.title)
                    else:
                        self.stdout.write("Warning: no MusicXML for opus " + opus.title)
            elif action == CPTDIST:
                print("Generating SimMatrix ... this may takes a while")
                try: 
                    corpus.generate_sim_matrix()
                except Exception as e:
                    print ("Something wrong with corpus " + corpus.ref +  " : "
                           + str(e))
                print("done.")
            elif action == KMEANS:
                try:
                    class_number = options['class_number']
                except:
                    class_number = 8
                    print("Note : nb_class not specified, will use default = 8")

                try:
                    measure = options['measure']
                except:
                    measure = 'pitches'
                    print("Note : measure not specified, will use default = pitches")

                print("Computing Kmeans for corpus ... this may takes a while")
                corpus.generate_kmeans(measure,class_number)
            elif action == QUALEVAL:
                """Evaluate the quality of a corpus"""
                opera = corpus.get_opera()
                valid = total = 0
                for opus in opera:
                    Workflow.quality_check(opus)
                print("Done. ")
            elif action == CPT_GRAMMAR:
                """Evaluate the quality of a corpus"""
                Workflow.compute_grammar(corpus)
                print("Done. ")
            elif action == DISSONANCE_ACTION:
                """ Compute the dissonances of a Corpus"""
                opera = corpus.get_opera()
                for opus in opera:
                    print ("Dissonances computed for " + opus.title + " (" + opus.ref +")")
                    Workflow.cpt_opus_dissonances(opus)
                    print("Done. ")
            elif action == FIX_PERMISSIONS_ACTION:
                group_editor = Group.objects.get(name=settings.EDITOR_GROUP)
                group_visitor = Group.objects.get(name=settings.VISITOR_GROUP)
                for corpus in Corpus.objects.all():                      
                    print ("Fix permissions for corpus" + corpus.title)
                    assign_perm('edit_corpus', group_editor, corpus)
                    assign_perm('view_corpus', group_editor, corpus)
                    if corpus.is_public:
                        assign_perm('view_corpus', group_visitor, corpus)
                        print ("Corpus is public")

                print("Done. ")
            else:
                self.stdout.write("Warning: unknown action : " +  action)
        else: # il y a un opus précis sur lequel travailler

            # opera = corpus.get_opera()
            # for opus in opera:
                # print(opus.ref)
            try:
                # opusref = options['corpus_ref'] + ":" + opusref
                opus = Opus.objects.get(ref=opusref)
            except Opus.DoesNotExist:
                raise CommandError('Opus "%s" does not exist' % opusref)
                exit
                
            self.stdout.write ("Found opus " + opus.title)

            if action == DISSONANCE_ACTION:
                #try:
                Workflow.cpt_opus_dissonances(opus)
                #except  Exception as ex:
                #    print ("Exception for opus " + opus.ref + " Message:" + str(ex))
                print ("Dissonances computed for " + opus.title + " (" + opus.ref +")")

            elif action == STATS_ACTION:
                if os.path.isfile( opus.musicxml.path):
                    self.stdout.write("Essai de stats")
                    stats = StatsDesc(opus)
                    dico = stats.computeStats()
                    for k,v in dico.items():
                        if isinstance(v, str):
                            self.stdout.write(k+" "+v)
                        else:
                            # distribution de notes
                            self.stdout.write(k)
                            self.stdout.write("  "+" ".join([str(a[0])+","+str(a[1]) for a in v]))
                else:
                    self.stdout.write("Warning: invalid MusicXML file path for " + opus.title)
            elif action == QUALEVAL:
                """Evaluate the quality of an opus"""
                Workflow.quality_check(opus)
                print("Done. ")
            elif action == DESCRIPTORJSON_ACTION:
                """Produces a file with the descriptors, in json format"""
                Workflow.createJsonDescriptors(opus)
                print("Done. ")
            elif action == INDEX_ACTION:
                """Index a specific opus"""
                Workflow.index_opus(opus)
                print("Done. ")
            else:
                    self.stdout.write("Warning: invalid action for opus " + opus.title + " : " + action)
