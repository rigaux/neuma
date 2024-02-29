

from lib.music.Score import *
from scorelib.analytic_concepts import *

from manager.models import Corpus, Opus, Descriptor, Annotation, AnalyticModel, AnalyticConcept

from django.contrib.auth.models import User

from quality.lib.LyricsQuality import  *
from quality.lib.MetricQuality import *

class QualityProcessor:
    """
        This class is a set of static functions to evaluate
        the quality of a score
    """
        
    @staticmethod
    def applyToOpus(opus):
        """ Apply the quality processor to an Opus"""
        
        score = Score()
        score.load_from_xml(opus.mei.path, "mei")

        try:
        # Lyrics indicators
            QualityProcessor.evaluateQualitymeasure(opus, score, AC_QUAL_MISSING_LYRICS)
            QualityProcessor.evaluateQualitymeasure(opus, score, AC_QUAL_INVALID_LYRICS)
            QualityProcessor.evaluateQualitymeasure(opus, score, AC_QUAL_INVALID_SYLLAB_METADATA)
            # Rhythm indicators
            QualityProcessor.evaluateQualitymeasure(opus, score, AC_QUAL_INCOMPLETE_BARS)
            #Beaming indicators
            QualityProcessor.evaluateQualitymeasure(opus, score, AC_QUAL_INVALID_BEAMING_SUBDIVISION)
        except Exception as ex:
            print ("Error evaluateQualitymeasure: " + str(ex))



    @staticmethod
    def evaluateQualitymeasure(opus, score, indicator_code):
        """ Evaluate a specific quality measure for an Opus
        
        This methods calls a specific quality evaluation function
        depending on the required quality measure. It always returns
        a set of annotations.

        NB: quality indicator codes are enumerated in analytic_concepts.py
        """

        # First, get the concept
        try:
            db_concept = AnalyticConcept.objects.get(code=indicator_code)
        except AnalyticConcept.DoesNotExist:
            raise ValueError('Unknown concept: ' + indicator_code )

        # Get the computer user
        try:
            db_user = User.objects.get(username=settings.COMPUTER_USER_NAME)
        except User.DoesNotExist:
            raise ValueError("Unknown user : " + settings.COMPUTER_USER_NAME + ". Run the setup_neuma script")
            print ("Unknown user : " + settings.COMPUTER_USER_NAME + ". Run the setup_neuma script")
            exit

        # Drop all automatic annotations for this opus and this quality measure
        Annotation.objects.filter(opus=opus,analytic_concept=db_concept,  is_manual=False).delete()

        # Each function returns a list of Annotation objects
        annotations = list()

        # Check which indicator is required
        if indicator_code == AC_QUAL_MISSING_LYRICS:
            # Loop on the voices
            voices =  score.get_all_voices()
            for voice in voices:
                if voice.has_lyrics():
                    annotations += LyricsQuality.missing_lyrics(opus, voice)
        elif indicator_code == AC_QUAL_INVALID_LYRICS:
            # Loop on the voices
            voices =  score.get_all_voices()
            for voice in voices:
                if voice.has_lyrics():
                    annotations += LyricsQuality.invalid_lyrics(opus, voice)
        elif indicator_code == AC_QUAL_INVALID_SYLLAB_METADATA:
            # Loop on the voices
            voices =  score.get_all_voices()
            for voice in voices:
                if voice.has_lyrics():
                    annotations += LyricsQuality.invalid_syllab_metadata(opus, voice)
        elif indicator_code == AC_QUAL_INCOMPLETE_BARS:
            annotations += MetricQuality.score_measure_sum(score)
        elif indicator_code == AC_QUAL_INVALID_BEAMING_SUBDIVISION:
            annotations += MetricQuality.score_beaming(score)
        else:
            raise ValueError('No evaluator for quality indicator code ' + indicator_code + " seems to be unknown")

        # Allright, now insert the annotation in the DB
        print ("Insert " + str(len( annotations)) + " annotations for opus " + opus.ref + "  and concept " + db_concept.description)
        for annotation in annotations:
            annotation.analytic_concept = db_concept
            annotation.comment=db_concept.description
            annotation.opus = opus
            annotation.user = db_user
            annotation.save()
