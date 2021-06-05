
from lib.music.Score import *
from scorelib.analytic_concepts import *

from manager.models import Annotation, AnalyticModel, AnalyticConcept


SYLLAB_SINGLE = 'single'
SYLLAB_BEGIN = 'begin'
SYLLAB_MIDDLE = 'middle'
SYLLAB_END = 'end'

class LyricsQuality:
    """
        This class is a set of static functions to evaluate
        the quality of lyrics
    """
   
    @staticmethod
    def missing_lyrics(opus, voice):
        """ Missing lyrics metrics"""

        annotations = list()
        beginMode = False
        for event in voice.m21_stream.notes:
            if not event.hasLyrics():
                if not beginMode:
                    # We did not find a begin before: this is a mistake
                    annotations.append(Annotation(ref=event.id, fragment= json.dumps([event.id])))
            else:
                beginMode = False
                for lyric in event.lyrics:
                    if lyric.number == 1 and lyric.syllabic == SYLLAB_BEGIN:
                        # We can accept no lyrics on the next note
                        beginMode = True

        return annotations
    
       
    @staticmethod
    def invalid_syllab_metadata(opus, voice):
        """ Check syllab metadata"""

        annotations = list()
        currentSyllabicMode = "" 
        for event in voice.m21_stream.notes:
            if event.hasLyrics():
                 for lyric in event.lyrics:
                    if currentSyllabicMode == "":
                        currentSyllabicMode = lyric.syllabic
                    if currentSyllabicMode == SYLLAB_BEGIN and lyric.syllabic ==  SYLLAB_SINGLE:
                        # Found a a single syllable inside a word
                        annotations.append(Annotation(ref=event.id, fragment= json.dumps([event.id])))
                    if currentSyllabicMode == SYLLAB_SINGLE and lyric.syllabic ==  SYLLAB_END:
                        # Cannot find END without negin
                        annotations.append(Annotation(ref=event.id, fragment= json.dumps([event.id])))
                    if currentSyllabicMode == SYLLAB_SINGLE and lyric.syllabic ==  SYLLAB_MIDDLE:
                        # Cannot find MIDDLE without negin
                        annotations.append(Annotation(ref=event.id, fragment= json.dumps([event.id])))
                    if currentSyllabicMode == SYLLAB_MIDDLE and lyric.syllabic ==  SYLLAB_BEGIN:
                        # Cannot find BEGIN without END 
                        annotations.append(Annotation(ref=event.id, fragment= json.dumps([event.id])))

        return annotations

    @staticmethod
    def invalid_lyrics(opus, voice):
        """ Invalid lyrics metrics"""
        
        annotations = list()
        for event in voice.m21_stream.notes:
            for lyric in event.lyrics:
                text_to_search = lyric.rawText #[1:len(lyric.text)]
                # if lyric.number == 1:
                if text_to_search.find("_") > -1 or text_to_search.find("-") > -1 :
                    #print ("Event " + event.id + " in voice " + voice.id + " has invalid lyrics " + lyric.text + " syll " + lyric.syllabic
                    #         + " " + str(lyric.number))
                    annotations.append(Annotation(ref=event.id, fragment= json.dumps([event.id])))

        return annotations

