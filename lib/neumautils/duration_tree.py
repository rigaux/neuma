
import fractions
import re
from neumautils.math_utils import *
import copy
from neumautils.m21utils import get_ties
from music21 import tie

def notes_to_nested_list(note_list, std_div=None, tempo='', order_string="asc" ):
    """The general function that transform a note list from a xml score to a nested list. order_string can be asc or desc"""
    if order_string == "asc":
        order = 1
    elif order_string == "desc":
        order = -1
    else:
        raise ValueError('order has not a valid value (it can take only asc or desc)')

    if isinstance(std_div, dict) and tempo != '' and std_div.get(tempo) is not None:
        std_div_list = std_div.get(tempo)
    else:
        std_div_list = {}
        print('Tempo not defined')

    ties_list = get_ties(note_list)
    frac_dur = [fractions.Fraction(n.duration.quarterLength) for n in note_list]  # transform all the durations in fractions
    dur = [d / sum(frac_dur) for d in frac_dur]  # normalize the duration

    dur_dict = []
    for i,d in enumerate(dur):
        dur_dict.append({'duration': d, 'is_tied': ties_list[i]})
    # print(dur_dict)
    return recursive_partition(dur_dict, 0, std_div_list, order)

def durations_to_nested_list(raw_dur, std_div=None, tempo='', order_string="asc"):
    """The general function that transform the durations from a xml score to a nested list. order_string can be asc or desc"""
    if order_string == "asc":
        order = 1
    elif order_string == "desc":
        order = -1
    else:
        raise ValueError('order has not a valid value (it can take only asc or desc)')

    if isinstance(std_div, dict) and tempo != '' and std_div.get(tempo) is not None:
        std_div_list = std_div.get(tempo)
    else:
        std_div_list = {}
        print('Tempo not defined')

    frac_dur = [fractions.Fraction(d) for d in raw_dur]  # transform all the durations in fractions
    dur = [d / sum(frac_dur) for d in frac_dur]  # normalize the duration

    dur_dict = []
    for d in dur:
        dur_dict.append({'duration': d, 'is_tied': False})

    return recursive_partition(dur_dict, 0, std_div_list, order)


def is_divisible(dur_dict, number_of_parts):
    """check is a list of durations is simple divisible"""
    dur_list = [d['duration'] for d in dur_dict]
    # dur_list must be a fraction
    total = sum(dur_list)  # the total duration of the sequence

    partial = fractions.Fraction(0, 1)  # variable that store a partial summation, initialized to 0
    last_index = 0
    for i, d in enumerate(dur_list):
        partial = partial + d
        if partial > total / number_of_parts:
            return False
        elif partial == total / number_of_parts:
            partial = fractions.Fraction(0, 1)  # reset to 0

    return True


def partition(dur_dict, number_of_parts):
    """From a list of durations return a list of list. Each sublist has the same duration. """
    out = []

    dur_list = [d['duration'] for d in dur_dict]

    total = sum(dur_list)  # the total duration of the sequence

    partial = fractions.Fraction(0, 1)  # variable that store a partial summation, initialized to 0
    last_index = 0
    for i, d in enumerate(dur_list):
        partial = partial + d
        if partial > total / number_of_parts:
            raise ValueError('the dur_list is not simple divisible by number_of_parts')
        elif partial == total / number_of_parts:
            out.append(dur_dict[last_index:i + 1])
            last_index = i + 1
            partial = fractions.Fraction(0, 1)  # reset to 0

    return out


def force_split(dur_dict, number_of_parts):
    """Split durations to make possible to simple divide by number_of_parts. """
    dur_list = [d['duration'] for d in dur_dict]

    total = sum(dur_list)  # the total duration of the sequence
    partial = fractions.Fraction(0, 1)  # variable that store a partial summation, initialized to 0

    new_dur_dict = []
    for i, d in enumerate(dur_list):
        if partial + d > total / number_of_parts:  # if we are going over the point where we expect to divide
            first_part = fractions.Fraction((total / number_of_parts) - partial)
            new_dur_dict.append(
                {'duration': first_part, 'is_tied': dur_dict[0]['is_tied']})  # append to arrive at the new point of division
            second_part = fractions.Fraction(d - first_part)
            for ii in range(number_of_parts)[::-1]:
                if second_part == ii * total / number_of_parts:  # check if we is exactly a multiple of total/number_of_parts, starting from the bigger
                    for _ in range(ii):
                        new_dur_dict.append({'duration': total / number_of_parts, 'is_tied': True})
                    partial = fractions.Fraction(0, 1)
                    break
                elif second_part > ii * total / number_of_parts:
                    for _ in range(ii):
                        new_dur_dict.append({'duration': total / number_of_parts, 'is_tied': True})
                    new_dur_dict.append({'duration': second_part - (ii * total / number_of_parts), 'is_tied': True})
                    partial = fractions.Fraction(second_part - (ii * total / number_of_parts))
                    break
        elif partial + d == total / number_of_parts:  # if we are exactly where we expect to divide
            new_dur_dict.append({'duration': d, 'is_tied': False})
            partial = 0
        else:  #if we are before the point where we expect to divide
            new_dur_dict.append({'duration': d, 'is_tied': False})
            partial = partial + d

    return new_dur_dict


def recursive_partition(dur_dict, depth, std_div_list, order):
    dur_list = [d['duration'] for d in dur_dict]
    """take a list and simple partition it when it is possible. When it's not possible it split the durations """
    dur_list_norm = [d / sum(dur_list) for d in dur_list]
    division_values = pfactors(lcm([d.denominator for d in dur_list_norm]))[::order]

    if len([d for d in dur_list if d != 0]) == 1:
        return dur_dict
    elif std_div_list.get(depth) is not None and is_divisible(dur_dict, std_div_list.get(depth)):

        return [recursive_partition(p, depth + 1, std_div_list, order) for p in
                partition(dur_dict, std_div_list.get(depth))]
    else:
        for v in division_values:
            if is_divisible(dur_dict, v):
                return [recursive_partition(p, depth + 1, std_div_list, order) for p in partition(dur_dict, v)]

        # go here only if it's not simple divisible
        if std_div_list.get(depth) is not None and std_div_list.get(depth) in division_values:
            div_val = std_div_list.get(depth)  # force partition with the standard value
        else:
            div_val = division_values[0]  # force partition with the first factor of the lcm of the denominators
        new_dur_list = force_split(dur_dict, div_val)
        return [recursive_partition(p, depth + 1, std_div_list, order) for p in
                partition(new_dur_list, division_values[0])]

        raise ValueError('Something went wrong with the force_split')


std_div1 = {
    '2/2': {0: 2},
    '3/2': {0: 3},
    '4/2': {0: 2, 1: 2},
    '2/4': {0: 2},
    '3/4': {0: 3},
    '4/4': {0: 2, 1: 2},
    '3/8': {0: 3},
    '6/8': {0: 2, 1: 3},
    '9/8': {0: 3, 1: 3},
    '12/8': {0: 4, 1: 3}
}

#functions to transform the duration tree list of list in a string usable by the C++ program

def dur_to_number(nest_list):
    """From a nested list of dur_dict, to a nested list of int"""
    if not any(isinstance(l, list) for l in nest_list):  # if it is a leaf
        if len(nest_list) > 1:  # we have grace notes
            return len(nest_list)
        elif nest_list[0]['is_tied'] == False:
            return 1
        else:
            return 0
    else:
        return [dur_to_number(l) for l in nest_list]


def square_to_round(_string):
    """change all the square parentesis to round parentesis and remove the commas"""
    new_string = _string.replace('[', '(').replace(']', ')').replace(',', '')
    return new_string


def delete_parentesis_around_numbers(_string):
    return re.sub('\[(\d+)\]', r'\1', _string)


def preprocess_number_list(number_list):
    temp = delete_parentesis_around_numbers(str(number_list))
    return square_to_round(temp)


def delete_rests(bar):
    new_bar = copy.deepcopy(bar)
    # in case there is just one event, return with no changes
    if len(new_bar.getElementsByClass('GeneralNote')) <= 1:
        return new_bar
    else:
        #if the first element on the bar is a rest, we treat it as a a note tied to the previous bar
        note= new_bar.getElementsByClass('GeneralNote')[0]
        if note.isRest:
            note.tie= tie.Tie('stop')
        i = 1  # we now start from the second element
        while True:
            note = new_bar.getElementsByClass('GeneralNote')[i]
            if note.isRest:
                rest_duration = note.duration.quarterLength
                new_bar.remove(note)
                # print(new_bar.getElementsByClass('GeneralNote')[i - 1].duration.quarterLength)
                new_bar.getElementsByClass('GeneralNote')[i - 1].duration.quarterLength += rest_duration
                # print(new_bar.getElementsByClass('GeneralNote')[i - 1].duration.quarterLength)
            else:
                i += 1
            if i == len(new_bar.getElementsByClass('GeneralNote')):
                break
        return new_bar

