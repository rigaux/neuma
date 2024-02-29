from quality.lib.NoteTree_v2 import *
from fractions import Fraction

def check_measure_sum(beam_tree, timeSignature, paddingLeft):
    if Fraction((beam_tree.get_root().get_duration()+ paddingLeft)/4) != Fraction(timeSignature.numerator, timeSignature.denominator):
        print("detected invalid sum or pickup measure")
        return False
    else:
        return True

def divide_measure_rule(beam_tree, timeSignature):
    meter_tuple = (timeSignature.numerator, timeSignature.denominator)
    total_duration = beam_tree.get_root().get_duration()
    #in case of pickup measures, we consider it as the last part of a complete measure
    partial = Fraction(timeSignature.numerator, timeSignature.denominator) * 4 - total_duration

    # discern depending on the meter
    if meter_tuple == (4,4):
        # print('meter: 4/4')
        if len(beam_tree.get_note_nodes()) == 1:
            # exception of the single note
            return (True, [])
        elif len(beam_tree.get_note_nodes()) == 3 and beam_tree.get_note_nodes()[0] == 0.25 and beam_tree.get_note_nodes()[1] == 0.5 and beam_tree.get_note_nodes()[2] == 0.25 :
            # exception of the three notes syncope
            return (True, [])
        elif partial >=  total_duration/2:
            #in case the pickup measure is shorter or equal the half
            return (True, [])
        else: # check the division in half
            for e in beam_tree.get_root().get_children():
            # if there is more than one note
                partial = partial + e.duration
                if partial == total_duration/2:
                    return (True, [])
                elif partial > total_duration/2:
                    return (False, beam_tree.get_note_nodes(local_root= e))

    elif meter_tuple == (3, 4):
        # print('meter: 3/4')
        return (True, [])

    elif meter_tuple == (6, 8):
        # print('meter: 6/8')
        if len(beam_tree.get_note_nodes()) == 1:
            # exception of the single note
            return (True, [])
        elif partial >=  total_duration/2:
            #in case the pickup measure is shorter or equal the half
            return (True, [])
        else: # check the division in half
            for e in beam_tree.get_root().get_children():
            # if there is more than one note
                partial = partial + e.duration
                if partial == total_duration/2:
                    return (True, [])
                elif partial > total_duration/2:
                    return (False, beam_tree.get_note_nodes(local_root=e))

    elif meter_tuple == (2, 2):
        # print('meter: 2/4')
        if len(beam_tree.get_note_nodes()) == 1:
            # exception of the single note
            return (True, [])
        elif partial >=  total_duration/2:
            #in case the pickup measure is shorter or equal the half
            return (True, [])
        else: # check the division in half
            for e in beam_tree.get_root().get_children():
            # if there is more than one note
                partial = partial + e.duration
                if partial == total_duration/2:
                    return True
                elif partial > total_duration/2:
                    return (False, beam_tree.get_note_nodes(local_root=e))

    else:
        #for all other meters
        return (True, [])