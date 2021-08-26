
from manager.models import Corpus, Opus, Descriptor, Annotation, AnalyticModel, AnalyticConcept, Patterns
import os
import re
import subprocess
from django.core.files import File
from django.core.files.base import ContentFile
import json
import sys
from neumautils.duration_tree import *
import ast
from scorelib import local_settings

from search.IndexWrapper import IndexWrapper

import zipfile, os.path, io

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


from django.contrib.auth.models import User
from xml.dom import minidom

# To communicate with Neuma
from lib.neuma.rest import Client

from lib.music.Score import *

# Music analysis module
from music21 import converter
import logging
# from lib.music.counterpoint import  pitchCollections, dissonanceAnalysis
from lib.music.counterpoint import  pitchCollections


from django_q.tasks import *
from scorelib.analytic_concepts import *

from quality.lib.Processor import QualityProcessor

from transcription.models import Grammar, GrammarRule


class Workflow:
    """
        Operators triggered when a score is inserted / updated
    """
    
    def __init__(self) :
         return
    

    @staticmethod
    def produce_mei(corpus, recursion=True):
        """
        Produce the MEI file by applying an XSLT tranforsm to the MusicXML doc.
        """
        print("Produce all missing MEI file for corpus " + corpus.title)
        for opus in Opus.objects.filter(corpus__ref=corpus.ref):
            Workflow.produce_opus_mei(opus)
        print("MEI files produced for corpus " + corpus.title)

        # Recursive call
        if recursion:
            children = corpus.get_children(False)
            for child in children:
                Workflow.produce_mei(child, recursion)

    @staticmethod
    def produce_opus_mei(opus, replace=False):
        # First take the script template depending on the OS
        if os.name == 'nt': #Windows
            with open(os.path.join(settings.SCRIPTS_ROOT, 'mxml2mei.bat')) as script_file:
                script_file = script_file.read()
        else:
            with open(os.path.join(settings.SCRIPTS_ROOT, 'mxml2mei.sh')) as script_file:
                script_file = script_file.read()
                
        # Get the script template by replacing the deployment-dependent paths
        sfile = script_file.replace ("{saxon_path}", os.path.join(settings.BASE_DIR, "lib","saxon")).replace("{xsl_path}", settings.SCRIPTS_ROOT).replace("{tmp_dir}", settings.TMP_DIR)

        # Take care: we never replace an existing MEI unless explicitly allowed
        if opus.musicxml and (not opus.mei or replace):
            try:
                with open(opus.musicxml.path) as musicxml_file:
                    musicxml = musicxml_file.read()
                        
                # Remove the DTD: avoids Web accesses, timeouts, etc.
                pattern = re.compile("<!DOCTYPE(.*?)>", re.DOTALL)
                mxml_without_type = re.sub(pattern, "", musicxml)
                # Write the MusicXML without DTD in the tmp area
                mxml_file = open(os.path.join(settings.TMP_DIR, "score.xml"),"w")
                mxml_file.write(mxml_without_type)
                mxml_file.close()
                        
                # Create and run a script to convert the MusicXML with XSLT
                convert_file = sfile.replace ("{musicxml_path}", os.path.join(settings.TMP_DIR,"score.xml")).replace("{opus_ref}", opus.ref)
                if os.name == 'nt':
                    script_name = f = os.path.join(settings.TMP_DIR, "cnv_mei_" + str(opus.id) + ".bat") #for windows
                else:
                    script_name = f = os.path.join(settings.TMP_DIR, "cnv_mei_" + str(opus.id) + ".sh")
                f = open(script_name,"w")
                f.write(convert_file)
                f.close()
                print ("Conversion script created in " + script_name)
                if os.name != 'nt':
                    subprocess.call(["chmod", "a+x", script_name])
                else: #on windows no need to chmod
                    print("Detected OS: Windows")

                # Now, run the script
                if os.name == 'nt': #if it's window
                    result = subprocess.call(script_name)
                else:
                    result = subprocess.call(script_name)
                if result == 0:
                    print ("Success : import the MEI file")
                    with open(os.path.join(settings.TMP_DIR ,"mei.xml")) as mei_file:
                        opus.mei.save ("mei.xml", File(mei_file))
                else:
                    print ("Error converting the MusicXML file")
            except  Exception as ex:
                print ("Exception for opus " + opus.ref + " Message:" + str(ex))
        else:
            logger.info("MEI file already exists: we do not override it")
            
    @staticmethod
    def produce_temp_mei(path_to_musicxml, mei_number):
        """
        Temporary produce and save a MEI file (with name: {mei_name}) from a music xml file.
        This does not involve the database
        mei_name : can be either the integer 1 or 2
        return: the path to the MEI file
        """
        # First take the script template depending on the OS
        if os.name == 'nt': #Windows still to implement
            with open(os.path.join(settings.SCRIPTS_ROOT, 'mxml2mei.bat')) as script_file:
                script_file = script_file.read()
        else:
            with open(os.path.join(settings.SCRIPTS_ROOT, 'mxml2mei_param_name.sh')) as script_file:
                script_file = script_file.read()
        
        #create the correct mei name
        if mei_number == 1:
            mei_name = "comp_temp_mei_1"
        elif mei_number == 2:
            mei_name = "comp_temp_mei_2"
        else:
             raise Exception("mei_name can be either the integer 1 or 2")
        # Get the script template by replacing the deployment-dependent paths
        # WARNING: Highly risky function because it will delete files from the memory
        sfile = script_file.replace ("{saxon_path}", os.path.join(settings.BASE_DIR, "lib","saxon")).replace("{xsl_path}", settings.SCRIPTS_ROOT).replace("{tmp_dir}", settings.TMP_DIR).replace("{mei_name}", mei_name)


        # Produce the MEI
        try:
            with open(path_to_musicxml) as musicxml_file: #check if the file exist
                musicxml = musicxml_file.read()
            
            # Remove the DTD: avoids Web accesses, timeouts, etc.
            pattern = re.compile("<!DOCTYPE(.*?)>", re.DOTALL)
            mxml_without_type = re.sub(pattern, "", musicxml)
            # Write the MusicXML without DTD in the tmp area
            mxml_file = open(os.path.join(settings.TMP_DIR, "temp_xml_score.xml"),"w")
            mxml_file.write(mxml_without_type)
            mxml_file.close()
                    
            # Create and run a script to convert the MusicXML with XSLT
            if os.name == 'nt':
                script_name = f = os.path.join(settings.TMP_DIR, "cnv_temp_mei.bat") #for windows
            else:
                script_name = f = os.path.join(settings.TMP_DIR, "cnv_temp_mei.sh")
            with open(script_name,"w") as f:
                f.write(sfile)
            if os.name != 'nt':
                subprocess.call(["chmod", "a+x", script_name])
            else: #on windows no need to chmod
                print("Detected OS: Windows")

            # Now, run the script
            if os.name == 'nt': #if it's window
                result = subprocess.call(script_name)
            else:
                result = subprocess.call(script_name)
            if result == 0:
                print ("Success : created the temporary MEI file for comparison")
                return {"path_to_temp_mei": str(os.path.join(settings.TMP_DIR ,mei_name + ".xml"))}
        except  Exception as ex:
            print ("Exception: " + str(ex))

    @staticmethod
    def index_corpus(corpus, recursion=True):
        """
        (Re)create the index for all the opuses of a corpus (and its descendants
        if the recursion parameter is True)
        """

        for opus in Opus.objects.filter(corpus__ref=corpus.ref):
            Workflow.index_opus(opus)

        # Recursive call
        if recursion:
            children = corpus.get_children(False)
            for child in children:
                Workflow.index_corpus(child, recursion)

    @staticmethod
    def index_opus(opus):
        '''
           Index an opus
           
           This functions produces the Opus descriptors which are
           stored in the DB. It then scans these descriptors and
           sends them to ElasticSearch
        '''
        
        # Produce the Opus descriptors
        Workflow.produce_opus_descriptor(opus)
        
        # Store the descriptors in Elastic Search
        index_wrapper = IndexWrapper()
        index_wrapper.index_opus(opus)

    @staticmethod
    def patterns_statistics_analyze(corpus, mel_dict, dia_dict, rhy_dict):
        """
        Analyze statistics based on all patterns in the opus/corpus/library, 
        such as top 15 common patterns, patterns that appeared more than 50 times
        """

        print("Finished analysis of corpus:" + corpus.title)

        print("Top 15 melodic patterns appeared in corpus(so far):")
        cnt = 0
        #sort elements by their occurrance
        for ele in sorted(mel_dict, key=mel_dict.get, reverse=True):
            print(ele, mel_dict[ele])
            cnt += 1
            #only print the top 15 results
            if cnt >= 15: break

        print("Top 15 diatonic patterns appeared in corpus(so far):")
        cnt = 0
        #sort elements by their occurrance
        for ele in sorted(dia_dict, key=dia_dict.get, reverse=True):
            print(ele, dia_dict[ele])
            cnt += 1
            #only print the top 15 results
            if cnt >= 15: break

        print("Top 15 rhythmic patterns appeared in corpus(so far):")
        cnt = 0
        #sort elements by their occurrance
        for ele in sorted(rhy_dict, key=rhy_dict.get, reverse=True):
            print(ele, rhy_dict[ele])
            cnt += 1
            #only print the top 15 results
            if cnt >= 15: break
        
        '''
        #print all patterns that appeared more than 200 times

        print("Melodic patterns that appeared more than 200 times in corpus so far:")
        for ele in sorted(mel_dict, key=mel_dict.get, reverse=True):
            if mel_dict[ele] >= 200:
                print(ele, mel_dict[ele])
            else:
                break
        
        print("Diatonic patterns that appeared more than 200 times in corpus so far:")
        for ele in sorted(dia_dict, key=dia_dict.get, reverse=True):
            if dia_dict[ele] >= 200:
                print(ele, dia_dict[ele])
            else:
                break

        print("Rhythmic patterns that appeared more than 200 times in corpus so far:")
        for ele in sorted(rhy_dict, key=rhy_dict.get, reverse=True):
            if rhy_dict[ele] >= 200:
                print(ele, rhy_dict[ele])
            else:
                break
        '''

        """
        #Print all patterns existing 
        
        print("All melodic patterns: ", mel)
        print("All diatonic patterns:", dia)
        print("All rhythmic patterns:", rhy)
        """

    @staticmethod
    def analyze_patterns(corpus, recursion = True):
        '''
        Analyze all pattern to get statistical data of frequent patterns
        '''
        for opus in Opus.objects.filter(corpus__ref=corpus.ref):
            #Avoid an opus with error
            if opus.ref == "composers:praetorius:terpsichore:195": continue
            mel_pat_dict, dia_pat_dict, rhy_pat_dict = Workflow.analyze_patterns_in_opus(opus)

        # Recursive call
        if recursion:
            children = corpus.get_children(False)
            for child in children:
                Workflow.analyze_patterns(child, recursion)

        try:
            Workflow.patterns_statistics_analyze(corpus, mel_pat_dict, dia_pat_dict, rhy_pat_dict)
        except:
            #When the analysis finish, no value would be assigned to mel_pat_dict etc.. thus simply return void
            return

    @staticmethod
    def analyze_patterns_in_opus(opus):
        '''
        Analyze melodic, diatonic and rhythmic patterns within an opus and store statistics
        '''
        print ("Analyze patterns in opus " + opus.ref)

        score = opus.get_score()

        # First, compute the music summary and store it as a file
        music_summary = score.get_music_summary()
        music_summary.opus_id = opus.ref
        opus.summary.save("summary.json", ContentFile(music_summary.encode()))

        # Find patterns within each Voice of an Opus
        for part_id, part in music_summary.parts.items():
            for voice_id, voice in part.items():
                # Melody descriptor
                mel_descr = voice.get_melody_encoding()

                # 'N' is used as segregation between patterns in descriptor
                pattern_list = mel_descr.split("N")

                mel_pat_dict = Workflow.get_patterns_from_descr(pattern_list, opus, part_id, voice_id, settings.MELODY_DESCR)

                #Diatonic descriptor
                dia_descr = voice.get_diatonic_encoding()
                        
                pattern_list = dia_descr.split("N")

                dia_pat_dict = Workflow.get_patterns_from_descr(pattern_list, opus, part_id, voice_id, settings.DIATONIC_DESCR)
 
                # Rhythm descriptor
                rhy_descr = voice.get_rhythm_encoding()
                        
                pattern_list = rhy_descr.split("N")
                        
                rhy_pat_dict = Workflow.get_patterns_from_descr(pattern_list, opus, part_id, voice_id, settings.RHYTHM_DESCR)

        return mel_pat_dict, dia_pat_dict, rhy_pat_dict

    @staticmethod
    def get_patterns_from_descr(pattern_list, opus, part_id, voice_id, descriptor):
        """
        Iterate over the list of patterns to get statistical information of every pattern in a voice
        """
        #if pattern list is empty, return:
        if pattern_list == [""]:
            return

        for curr_pattern in pattern_list:
            #if it is an invalid pattern, skip
            if curr_pattern == '' or curr_pattern == ' ': continue
                        
            pattern = Patterns()
            pattern.opus = opus
            pattern.part = part_id
            pattern.voice = voice_id
            pattern.content_type = descriptor
            
            #Strip spaces in the beginning and the end to get the pattern in a "clean" way
            clean_pat = curr_pattern
            clean_pat = clean_pat.strip()
            pattern.value = clean_pat

            if descriptor == settings.MELODY_DESCR:
                #If the pattern is already in dictionary, total number +=1
                if clean_pat in pattern.mel_pattern_dict:
                    pattern.mel_pattern_dict[clean_pat] += 1
                    #Otherwise save the pattern
                else:
                    pattern.mel_pattern_dict[clean_pat] = 1
                    #pattern.save()
                
            elif descriptor == settings.DIATONIC_DESCR:
                #If the pattern is already in dictionary, total number +=1
                if clean_pat in pattern.dia_pattern_dict:
                    pattern.dia_pattern_dict[clean_pat] += 1
                    #Otherwise save the pattern
                else:
                    pattern.dia_pattern_dict[clean_pat] = 1
                    #pattern.save()
                
            elif descriptor == settings.RHYTHM_DESCR:
                #If the pattern is already in dictionary, total number +=1
                if clean_pat in pattern.rhy_pattern_dict:
                    pattern.rhy_pattern_dict[clean_pat] += 1
                    #Otherwise save the pattern
                else:
                    pattern.rhy_pattern_dict[clean_pat] = 1
                    #pattern.save()

        try:
            if descriptor == settings.MELODY_DESCR:
                return pattern.mel_pattern_dict

            elif descriptor == settings.DIATONIC_DESCR:
                return pattern.dia_pattern_dict

            elif descriptor == settings.RHYTHM_DESCR:
                return pattern.rhy_pattern_dict

        except Exception as ex:
            print ("Exception for opus " + opus.ref + " Message:" + str(ex))
    
    @staticmethod
    def produce_descriptors(corpus, recursion=True):
        """
        Produce the descriptors used for indexing the opuses of a corpus
        
        """
        for opus in Opus.objects.filter(corpus__ref=corpus.ref):
            Workflow.produce_opus_descriptor(opus)

        # Recursive call
        if recursion:
            children = corpus.get_children(False)
            for child in children:
                Workflow.produce_descriptors(child, recursion)

    @staticmethod
    def produce_opus_descriptor(opus, affiche=False):
        """
        Produce the descriptors for an opus.
        
        A "music summary" containing all the necessary info to perform
        searches is stored as a JSON file with the Opus. From
        this summary, descriptors are extracted for each voice
        and stored in the DB.
        
        In its current implementation, the only descriptors is related to the
        melodic profile of each voice. Optionally, we also store the lyrics if present.
        """
        print ("Produce descriptors for opus " + opus.ref)
        try:
                score = opus.get_score()
        
                # First, compute the music summary and store it as a file
                music_summary = score.get_music_summary()
                music_summary.opus_id = opus.ref
                opus.summary.save("summary.json", ContentFile(music_summary.encode()))
                #print (json.dumps(json_summary, indent=4, separators=(',', ': ')))

                descriptors_dict = {}
                types = "melodic", "diatonic", "rhythmic", "notes"
                for atype in types:
                    descriptors_dict[atype] = {}

                # Clean the current descriptors
                Descriptor.objects.filter(opus=opus).delete()
        
                # Next, compute the descriptors for each Voice
                for part_id, part in music_summary.parts.items():
                    for voice_id, voice in part.items():
                        # Melody descriptor
                        music_descr = voice.get_melody_encoding()
                        # print ("Voice " + str(voice_id)) # + " NGRAM encoding: " + music_descr)
                        # Store in Postgres
                        descriptor = Descriptor()
                        descriptor.opus = opus
                        descriptor.part = part_id
                        descriptor.voice = voice_id
                        descriptor.type = settings.MELODY_DESCR
                        descriptor.value = music_descr
                        if not affiche:
                            descriptor.save()
                        else:
                            # print(descriptor.to_dict())
                            descriptors_dict["melodic"][str(voice_id)]=descriptor.to_dict()

                        #Diatonic descriptor, store in Postgres
                        diatonic_descr = voice.get_diatonic_encoding()
                        descriptor = Descriptor()
                        descriptor.opus = opus
                        descriptor.part = part_id
                        descriptor.voice = voice_id
                        descriptor.type = settings.DIATONIC_DESCR
                        descriptor.value = diatonic_descr
                        if not affiche:
                            descriptor.save()
                        else:
                            # print(descriptor.to_dict())
                            descriptors_dict["diatonic"][str(voice_id)]=descriptor.to_dict()
                        
                        # Rhythm descriptor
                        rhythm_descr = voice.get_rhythm_encoding()
                        descriptor = Descriptor()
                        descriptor.opus = opus
                        descriptor.part = part_id
                        descriptor.voice = voice_id
                        descriptor.type = settings.RHYTHM_DESCR
                        descriptor.value = rhythm_descr
                        if not affiche:
                            descriptor.save()
                        else:
                            # print(descriptor.to_dict())
                            descriptors_dict["rhythmic"][str(voice_id)]=descriptor.to_dict()
                        
                        # Notes descriptor
                        notes_descr = voice.get_note_encoding()
                        descriptor = Descriptor()
                        descriptor.opus = opus
                        descriptor.part = part_id
                        descriptor.voice = voice_id
                        descriptor.type = settings.NOTES_DESCR
                        descriptor.value = notes_descr
                        if not affiche:
                            descriptor.save()
                        else:
                            # print(descriptor.to_dict())
                            descriptors_dict["notes"][str(voice_id)]=descriptor.to_dict()
               
                # Hack: the M21 parser does not supply lyrics. Use the MusicXML for the moment                   
                
                if opus.musicxml:
                    score = Score()
                    score.load_from_xml(opus.musicxml.path, "musicxml")
                
                voices = score.get_all_voices()
                for voice in voices:
                        if voice.has_lyrics():
                            # Store in Postgres
                            descriptor = Descriptor()
                            descriptor.opus = opus
                            descriptor.part = settings.ALL_PARTS
                            descriptor.voice = voice.id
                            descriptor.type = settings.LYRICS_DESCR
                            descriptor.value = voice.get_lyrics()
                            descriptor.save()

        except  Exception as ex:
            print ("Exception for opus " + opus.ref + " Message:" + str(ex))
            print ("Are you running elasticsearch?")
        return descriptors_dict

    @staticmethod 
    def import_zip(upload, do_import=True):
        # Check the zip
        if zipfile.is_zipfile(upload.zip_file.path):
            zf = zipfile.ZipFile(upload.zip_file.path, 'r')
            opus_files = {}
            
            # Scan the content of the ZIP file to find the list of opus
            for fname in zf.namelist():
                opus_ref, extension = decompose_zip_name (fname)
                # Skip files with weird names
                if opus_ref == "" or opus_ref.startswith('_') or  opus_ref.startswith('.'):
                    continue
                # OK, there is an Opus there
                opus_files[opus_ref] = {"mei": "", 
                                   "musicxml": "",
                                   "compressed_xml": "",
                                   "json": ""}
            # Second scan: we note the files present for each opus
            for fname in zf.namelist():
                (opus_ref, extension) = decompose_zip_name (fname)
                if opus_ref=='' or  opus_ref.startswith('_') or  opus_ref.startswith('.'):
                    continue
                if extension == '.mxl':
                     opus_files[opus_ref]["compressed_xml"] = fname
                elif (extension == '.xml' or extension == '.musicxml'):
                    opus_files[opus_ref]["musicxml"] = fname
                elif extension == '.mei':
                    opus_files[opus_ref]["mei"] = fname
                elif extension == '.json':
                    opus_files[opus_ref]["json"] = fname

        # OK, now in opus_files, we know whether we have the MusicXML, MEI or both
        list_imported = []
        for opus_ref, opus_files_desc in opus_files.items():            
                print ("Import opus with ref " + opus_ref + " in corpus " + upload.corpus.ref)
                full_opus_ref = upload.corpus.ref + settings.NEUMA_ID_SEPARATOR + opus_ref
                try:
                    opus = Opus.objects.get(ref=full_opus_ref)
                except Opus.DoesNotExist as e:
                    # Create the Opus
                    opus = Opus(corpus=upload.corpus, ref=full_opus_ref, title=opus_ref)
                list_imported.append(opus)

                # If a json exists, then it should contain the relevant metadata
                if opus_files_desc["json"] != "":
                    logger.info ("Found JSON metadata file %s" % opus_files_desc["json"])
                    json_file = zf.open(opus_files_desc["json"])
                    json_doc = json_file.read()
                    opus.load_from_dict (upload.corpus, json.loads(json_doc.decode('utf-8')))
                if opus_files_desc["compressed_xml"] != "":
                    logger.info ("Found compressed MusicXML content")
                    # Compressed XML
                    container = io.BytesIO(zf.read(opus_files_desc["compressed_xml"]))
                    xmlzip = zipfile.ZipFile(container)
                    # Keep the file in the container with the same basename
                    for name2 in xmlzip.namelist():
                        basename2 = os.path.basename(name2)
                        ref2 = os.path.splitext(basename2)[0]
                        if opus_files_desc["opus_ref"]  == ref2:
                            xml_content = xmlzip.read(name2)
                    opus.musicxml.save("score.xml", ContentFile(xml_content))
                if opus_files_desc["musicxml"] != "":
                    logger.info ("Found MusicXML content")
                    xml_content = zf.read(opus_files_desc["musicxml"])
                    opus.musicxml.save("score.xml", ContentFile(xml_content))
                if opus_files_desc["mei"] != "":
                    logger.info ("Found MEI content")
                    # Add the MEI file
                    try:
                            mei_file = zf.open(opus_files_desc["mei"])
                            mei_raw  = mei_file.read()
                            encoding = "utf-8"
                            try:
                                logger.info("Attempt to read in UTF 8")
                                mei_raw.decode(encoding)
                            except Exception as ex:
                                logger.info("Read in UTF 16")
                                encoding = "utf-16"
                                mei_raw.decode(encoding)
                            logger.info("Correct encoding: " + encoding)
                            mei_content = mei_raw.decode(encoding)
                            logger.info ("Save the MEI file.")
                            opus.mei.save("mei.xml", ContentFile(mei_content))
                    except Exception as ex:
                            logger.error ("Error processing MEI  " + str(ex))
                else:
                    # Produce the MEI from the MusicXML
                    logger.info ("Apply XSLT to produce the MEI.")
                    Workflow.produce_opus_mei(opus)     

                # Now try to obtain metadata
                if opus_files_desc["compressed_xml"]!="" or opus_files_desc["musicxml"]!="":
                    # Get MusicXML metadata
                    doc = minidom.parseString(xml_content)
                    titles = doc.getElementsByTagName("movement-title")
                    for title in titles:
                        for txtnode in title.childNodes:
                            opus.title = str(txtnode.data)
                            break
                        break
                try:
                    if opus.title == opus_ref:
                        #print ("Title = " + opus.title + " Try to obtain metadata")
                        # Try to find metadata in the XML file with music21
                        score = opus.get_score()
                        if score.get_title() != None and len(score.get_title()) > 0:
                            opus.title = score.get_title()
                        if score.get_composer() != None and len(score.get_composer()) > 0:
                            opus.composer = score.get_composer()
                            
                    # Produce descriptors and index the opus in ElasticSearch
                    Workflow.index_opus(opus)
                    
                    if do_import:
                        opus.save()
                except Exception as ex:
                    print ("Error processing MEI  " + str(ex))
                    logger.error ("Error processing MEI  " + str(ex))
                    
                print ("Opus ref " + opus_ref + " imported in corpus " + upload.corpus.ref+ "\n")
 
        return list_imported
    
    @staticmethod
    def async_import (upload):
        """Create a task to run the import asynchrionuously """
        
        #task_id = async("workflow_import_zip", upload)
        
        
    @staticmethod
    def cpt_opus_dissonances (opus):
        # Get the counterpoint analytic model
        dissonance_types_dict = {"SU": AC_SUSPENSION,
                                 "PN": AC_PASSING_NOTE,
                                 "AN": AC_ANTICIPATION,
                                  "NN": AC_NEIGHBOR_NOTE,
                                  "EN": AC_ESCAPE_NOTE,
                                  "CN": AC_CONSONANCE
                                 }
        # Get the analytic model
        try:
            db_model = AnalyticModel.objects.get(code=AMODEL_COUNTERPOINT)
        except AnalyticModel.DoesNotExist:
            print ("Unknown AnalyticModel : " + AMODEL_COUNTERPOINT)
            exit

        # Get the computer user
        try:
            db_user = User.objects.get(username=settings.COMPUTER_USER_NAME)
        except User.DoesNotExist:
            print ("Unknown user : " + settings.COMPUTER_USER_NAME + ". Run the setup_neuma script")
            exit

        # Only if there is a MEI file
        if os.path.isfile(opus.mei.path):
            print ("Compute dissonances for Opus " +  opus.title + " (" + opus.ref +") " + opus.mei.path)
            score = Score()
            score.load_from_xml(opus.mei.path, "mei")
            ''' @ Philippe: get analyzed pitches : a list of analyzed pitch objects containing id, type, subtype etc. etc.  (returns object AnalyzedPitch)''' 
            analyzedPitchList = []
            
            # Atention, chemin en dur dans DissonanceAnalysis: changer comme ceci
            #from django.conf import settings
            #self.modelPath = settings.BASE_DIR + '/static/dissonanceNeuralNetwork/model.h5'
            # Récupération des verticalités et des séquences
            pitchCollectionSequences = pitchCollections.PitchCollectionSequences(score.m21_score)
            ''' dissonance analysis '''
            dissonanceAnal = dissonanceAnalysis.DissonanceAnalysis(pitchCollectionSequences)
            
            # OK, analysis done, we remove existing annotations
            all_concepts = AnalyticConcept.objects.filter(model=db_model)
            Annotation.objects.filter(opus=opus,analytic_concept__in=all_concepts,is_manual=False).delete()

            # Pitch collection = toutes les notes d'une verticalité
            for pitchCollection in pitchCollectionSequences.pitchCollSequence.explainedPitchCollectionList:
             for analyzedPitch in pitchCollection.analyzedPitchList:
              
              # Pour l'offset, on cherche une des notes de la verticalité qui débute 
               offsetId = ""
               for pitchTS in analyzedPitch.verticalities[1].startTimespans:
                offsetId = pitchTS.element.id
                break
                
               if analyzedPitch.id == None or analyzedPitch.pitchType == None: 
                    print ("Invalid / incomplete analysis result")
                    continue
                    
               try:
                    db_concept = AnalyticConcept.objects.get(code=dissonance_types_dict[analyzedPitch.pitchType])
                    if not db_concept.name == "Consonance":
                     	print ("Offset = " + str(offsetId))
                     	print ("Dissonance " + db_concept.name +  " found at note " + str(analyzedPitch.id))
                    #				diss.note1.id + " " + diss.note2.id)
                     	print ("Analyzed dissonance :" + str(analyzedPitch.pitchType) + " at offset " + offsetId)
                    fragment = [analyzedPitch.id]
                    annot = Annotation(opus=opus, analytic_concept=db_concept, ref=analyzedPitch.id, 
                                   offset=offsetId, m21_offset=analyzedPitch.offset,
                                   fragment= json.dumps(fragment), user=db_user,
                                   model_ref= settings.COUNTERPOINT_MODEL)
                    annot.save()
               except AnalyticConcept.DoesNotExist:
                    print ("Unknown concept : " + diss.pitchType)
                    exit
        else:
            print ("Cannot compute dissonances for Opus " +  opus.title + " (" + opus.ref +"): no MEI")

    @staticmethod
    def quality_check(opus):

        # try:
        QualityProcessor.applyToOpus(opus)

    # except Exception as e:
    #    print("Following error encountered on Opus "+str(opus))
    #    print("    > "+str(e))

    @staticmethod
    def compute_grammar(corpus):
        grammar = Grammar.objects.filter(corpus=corpus)[0]
        print("Retrieving grammar representation from database")
        grammar_str = grammar.get_str_repr(allow_zero_weights= True)
        print("Retrieving the rules from database")
        rules = GrammarRule.objects.filter(grammar=grammar).order_by('creation_timestamp')
        rules_size = rules.count()

        with open(os.path.join('transcription', 'grammars', 'grammar.txt'), 'w') as f:
            f.write(grammar_str)
        print("Grammar Written")
        failure_counter = 0  # to keep track of the number of failure
        opera = corpus.get_opera()
        flatMeasuresDurations = []
        time_signature = []  # initialized empty, it is update in the first bar
        for opus in opera:
            score = Score()
            print("Title : " + opus.title)
            score.load_from_xml(opus.mei.path, "mei")

            # save the duration tree for each bar
            for part_index, part in enumerate(score.m21_score.parts):  # loop through parts
                for measure_index, measure_with_rests in enumerate(part.getElementsByClass('Measure')):
                    if measure_with_rests.timeSignature is not None:  # update the time_signature if there is a time_signature change
                        time_signature.append(measure_with_rests.timeSignature)
                    if len(measure_with_rests.voices) == 0:  # there is a single Voice ( == for the library there are no voices)
                        measure = delete_rests(measure_with_rests)
                        flatMeasuresDurations.append(
                            list(measure.getElementsByClass('GeneralNote')))
                    else:  # there are multiple voices (or an array with just one voice)
                        for voice_with_rest in measure_with_rests.voices:
                            voice = delete_rests(voice_with_rest)
                            # print(list(voice.getElementsByClass('GeneralNote')))
                            flatMeasuresDurations.append(
                                list(voice.getElementsByClass('GeneralNote')))

        # process and sum over all the bars
        time_signature_str = str(time_signature[0].numerator) + "/" + str(time_signature[0].denominator)
        print("Number of rules: " + str(rules_size))
        sum_rule = {}  # long enough vector. zip will cut it

        for dur in flatMeasuresDurations:
            try:
                nested_list_dur = notes_to_nested_list(dur, std_div=std_div1, tempo=time_signature_str)
                num_list = dur_to_number(nested_list_dur)
                c_input = preprocess_number_list(num_list)
                grammar_input_path = local_settings.GRAMMAR_INPUT_PATH
                script_path = local_settings.SCHEMAS_PATH
                config_path= local_settings.QPARSELIB_CONFIG_PATH
                unix_command = "{0} -i {1} -tree \"{2}\" -config {3} -v 0".format(script_path, grammar_input_path,
                                                                          c_input, config_path)
                print(unix_command)
                if os.name == 'nt': #on windows, we call the ubuntu bash
                    # print("windows system detected")
                    c_output = subprocess.check_output(["bash", "-c", unix_command])
                else:
                    # print("Unix system detected")
                    c_output = subprocess.check_output(unix_command, shell=True)
                # print(c_output.decode("utf-8").splitlines()[2])
                rule_list = json.loads(c_output.decode("utf-8").splitlines()[2]) #some useless stuff in the first 2 rows
                # print(rule_list)
                sum_rule = { k: sum_rule.get(k, 0) + rule_list.get(k, 0) for k in set(sum_rule) | set(rule_list) } #"sum" the two dictionaries
                # print("Did it!")
            except:
                print("Parsing failed for durations: ")
                print([e.duration.quarterLength for e in dur])
                failure_counter += 1

        # add the not-normalized weigth to the grammar
        for i, r in enumerate(rules):
            if str(i) not in sum_rule:
                r.weight = 0
                r.save()
            else:
                r.weight = sum_rule[str(i)]
                r.save()
        # normalize the weight for each head
        heads = GrammarState.objects.filter(grammar=grammar)
        for head in heads:
            rules = GrammarRule.objects.filter(grammar=grammar, head=head).all()
            weight_sum = sum([rule.weight for rule in rules])
            for i, r in enumerate(rules):
                unnormalized_weight = r.weight
                if unnormalized_weight != 0:  # that is true only if weight sum is >0, so that shoul avoid divisions by 0
                    r.weight = unnormalized_weight / weight_sum
                    r.save()
        # save the number of failures
        grammar.parse_failures_ratio = failure_counter / len(flatMeasuresDurations)
        print("Failure counter= " + str(failure_counter / len(flatMeasuresDurations)))
        grammar.save()

        # print the weighted grammar
        grammar_str = Grammar.objects.filter(corpus=corpus)[0].get_str_repr()

        with open(os.path.join('transcription', 'grammars', 'weighted_grammar.txt'), 'w') as f:
            f.write(grammar_str)

def createJsonDescriptors(opus):
        """returns the Json representation of an opus"""
        opusdict = {}
        opusdict["opusref"] = str(opus.ref)
        opusdict["opusurl"] = "http://neuma.huma-num.fr/home/opus/"+str(opus.ref)

        types = "melodic", "diatonic", "rhythmic", "notes"

        descriptors = Workflow.produce_opus_descriptor(opus,affiche=True)
        # print(descriptors.items())

        for atype in types: 
            l = []
            for voice, descrip in descriptors[atype].items():
                l.append(descrip["value"])

            opusdict[atype] = l

        # Serializing json 
        json_object = json.dumps(opusdict, indent = 4)
        # Writing to sample.json
        filename = str(opus.ref).replace(":", "-") + ".json"
        with open(filename, "w") as outfile:
            outfile.write(json_object)

#
# A top level function that calls import zip. Necessary for multi thearing, otherwise
# we get a pickle erro

def workflow_import_zip(upload, do_import=True):
    Workflow.import_zip(upload, do_import)

# Get the Opus ref and extension from a file name
def decompose_zip_name (fname):
    basename = os.path.basename(fname)
    components = os.path.splitext(basename) 
    extension = components[len(components)-1]
    opus_ref = ""
    sep = ""
    for i in range(len(components)-1):
        if i >0:
            sep = "-"
        opus_ref += components[i] + sep
    return (opus_ref, extension)
