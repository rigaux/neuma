from lib.music.Score import *
from scorelib.analytic_concepts import *
from manager.models import Annotation, AnalyticModel, AnalyticConcept
from music21 import *
from quality.lib.NoteTree_v2 import FullNoteTree
from quality.lib.quality_rules import check_measure_sum, divide_measure_rule
import json

class MetricQuality:
    """
        This class is a set of static functions to evaluate
        the quality of the rhythmic notation
    """


    @staticmethod
    def score_measure_sum(score):
        annotations = list()
        time_signature = None  # initialized empty, it is update in the first bar

        for part_index, part in enumerate(score.m21_score.parts):  # loop through parts
            for measure_index, measure in enumerate(part.getElementsByClass('Measure')):
                is_correct = True

                if measure.timeSignature is not None:  # update the time_signature if there is a time_signature change
                    time_signature = measure.timeSignature

                if measure_index== 0: #the first measure can be a pickup measure
                    is_correct=True
                elif len(measure.voices) == 0:  # there is a single Voice ( == for the library there are no voices)
                    my_trees = FullNoteTree(measure)
                    my_trees.beams_tree.compute_internal_node_duration()
                    is_correct = check_measure_sum(my_trees.beams_tree, measure.paddingLeft)
                else:  # there are multiple voices (or an array with just one voice)
                    for voice in measure.voices:
                        my_trees = FullNoteTree(voice)
                        my_trees.beams_tree.compute_internal_node_duration()
                        is_correct = check_measure_sum(my_trees.beams_tree, time_signature, measure.paddingLeft )

                if not is_correct:  # if the bar contains an invalid beaming
                    is_score_correct = False
                    print('Sum Error in measure ' + str(measure_index))
                    # save the output for each bar
                    try:
                        annot = Annotation(ref=my_trees.beams_tree.get_note_nodes()[0].get_note().id, fragment=json.dumps([n.get_note().id for n in my_trees.beams_tree.get_note_nodes()]))
                        # annot = Annotation(ref=my_trees.beams_tree.get_note_nodes()[0].get_note().id, fragment=json.dumps([my_trees.beams_tree.get_note_nodes()[0].get_note().id]))
                        annotations.append(annot)
                    except AnalyticConcept.DoesNotExist:
                        print("Unknown concept : " + AC_QUAL_INCOMPLETE_BARS)
 
        return annotations


    @staticmethod
    def score_beaming(score):
        annotations = list()

        time_signature = None  # initialized empty, it is update in the first bar

        for part_index, part in enumerate(score.m21_score.parts):  # loop through parts
            for measure_index, measure in enumerate(part.getElementsByClass('Measure')):
                is_correct = True

                if measure.timeSignature is not None:  # update the time_signature if there is a time_signature change
                    time_signature = measure.timeSignature

                if len(measure.voices) == 0:  # there is a single Voice ( == for the library there are no voices)
                    my_trees = FullNoteTree(measure)
                    my_trees.beams_tree.compute_internal_node_duration()
                    result = divide_measure_rule(my_trees.beams_tree, time_signature)
                    is_correct = result[0]
                else:  # there are multiple voices (or an array with just one voice)
                    for voice in measure.voices:
                        my_trees = FullNoteTree(voice)
                        my_trees.beams_tree.compute_internal_node_duration()
                        result = divide_measure_rule(my_trees.beams_tree, time_signature)
                        is_correct = result[0]


                if not is_correct:
                    print('Beaming Error in measure ' + str(measure_index))
                    # save the output for each bar
                    try:
                        db_concept = AnalyticConcept.objects.get(code=AC_QUAL_INVALID_BEAMING_SUBDIVISION)
                        annot = Annotation(ref=result[1][0].get_note().id, fragment=json.dumps([n.get_note().id for n in result[1]]))
                        # annot = Annotation(ref=result[1][0].get_note().id,fragment=json.dumps([result[1][0].get_note().id]))
                        annotations.append(annot)
                    except AnalyticConcept.DoesNotExist:
                        print("Unknown concept : " + AC_QUAL_INVALID_BEAMING_SUBDIVISION)
                else:
                    print('correct Beaming in measure ' + str(measure_index))

        return annotations
