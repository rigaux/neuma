from .Item import Item
import jsonpickle
import string
from fractions import Fraction
from .Distance import *
from .Distance_neuma import *
from django.conf import settings
import music21 as m21

NGRAM_SIZE = 3
INTERVAL_SEPARATOR = "|"
DURATION_UNIT = 16


class Sequence:
    """
        A compact representation of a voice, used
        for search operations
    """
    def __init__(self):
        # A sequence is a list of music items
        self.items = []
        return
        
    def decode(self, json_obj):
        """
        Decode from a JSON object
        """
        for json_item in json_obj["items"]:
            item = Item()
            item.decode(json_item)
            self.add_item(item)

    def encode(self):
        '''Encode in JSON'''
        return jsonpickle.encode(self, unpicklable=False)
 
    def add_item(self, item):
        self.items.append(item)
    
    def get_items_from_sequence(self):
        return self.items

    def set_from_pattern(self, str_pattern):
        """
        Take a string representing the pattern, as supplied by the piano: A4-8;G5-4, etc.
        Create the sequence from this encoding
        """
        if str_pattern == "":
            return ""
        
        # Split the pattern string to identify each note
        split_pattern = str_pattern.split(";")
        
        # Split each note to get the melody and rhythm
        for note in split_pattern:
            decomp_note = note.split("-")
            item = Item()
            # Now, decompose each note
            item.step = decomp_note[0][0]
            if decomp_note[0][1].isdigit():
                item.octave = int(decomp_note[0][1])
                item.alteration = 0
            else:
                if decomp_note[0][1] == 'b':
                    item.alteration = -1
                else:
                    item.alteration = 1
                item.octave = int(decomp_note[0][2])
            item.duration = float(4/float(decomp_note[1][0]))
            self.add_item(item)
        return True

    def get_rhythms(self):
        '''
            Get the list of rhythms.
            Rhythms are encoded as a list of objects (dict). Each object
            contains the pos of the first event, the pos of the last event,
            and the interval value.
        '''
        rhythms = []
        previous_item = None
        # Scan the items
        i_pos = 0
        current_pos = i_pos

        for item in self.items:
                        
            if previous_item is None:
                previous_item = item
            else:
                # Prevent division by zero
                if item.duration == 0 or previous_item.duration == 0:
                    continue
                if item.get_index() == previous_item.get_index():
                    pitch_change = False
                else:
                    pitch_change = True

                #gap is the ratio between the current note length and the previous one
                gap = Fraction(Fraction.from_float(item.duration), Fraction.from_float(previous_item.duration)).limit_denominator(max_denominator=10000)

                rhythm = {"start_pos": str(current_pos), "end_pos": str(i_pos), 
                          "value": str(gap), "pitch_change": pitch_change}

                if item.is_rest != True:
                    rhythms.append(rhythm)
                else:
                    rhythm = {"start_pos": str(current_pos), "end_pos": str(i_pos), 
                          "value": str(100), "pitch_change": pitch_change}
                    #Set value to 100, to make sure that the rest is not ignored, and it disrupts a consecutive "rhythm pattern"
                    rhythms.append(rhythm)

                previous_item = item
                current_pos = i_pos
            i_pos += 1

        return rhythms

    def get_exact_rhythms(self):
        '''
        Some modification on get_rhythms() to encode note lengths instead of ratio between notes.
        Exact rhythmic pattern matches only.
        In the search result, neuma will show one more note than the searched pattern, 
        the first note shown in each pattern should be irrelevant.
        '''
        rhythms = []
        previous_item = None
        # Scan the items
        i_pos = 0
        current_pos = i_pos

        for item in self.items:
            if item.is_rest == True:
                i_pos += 1
                continue

            if previous_item is None:
                previous_item = item
                
            if item.duration == 0:
                continue

            if item.get_index() == previous_item.get_index():
                pitch_change = False
            else:
                pitch_change = True

            curr_len = round(item.duration, 3)

            rhythm = {"start_pos": str(current_pos), "end_pos": str(i_pos), 
                        "value": str(curr_len), "pitch_change": pitch_change}
            
            if item.is_rest != True:
                rhythms.append(rhythm)
            else:
                rhythm = {"start_pos": str(current_pos), "end_pos": str(i_pos), 
                          "value": str(100), "pitch_change": pitch_change}
                #Set value to 100, to make sure that the rest is not ignored, and it disrupts a consecutive "rhythm pattern"
                rhythms.append(rhythm)

            previous_item = item
            current_pos = i_pos

            i_pos += 1

        return rhythms

    def get_intervals(self, descriptor=settings.MELODY_DESCR):
        """
            Get the list of intervals. Ignore repeated notes, grace notes, 
            and rests / silences.

            Intervals are encoded as a list of objects (dict). Each object 
            contains the pos of the first event, the pos of the last event,
            and the interval value.

            The list "diatonic_intervals" stores diatonic intervals(for example, an ascending fifth is a diatonic interval),
            while the list "intervals" stores the number of semitones as value.
        """
        dict_wordtonum = {"Unison": '0', "Second": '2', "Third": '3', "Fourth": '4', "Fifth": '5', "Sixth": '6', "Seventh": '7'}
        intervals = []
        diatonic_intervals = []
        previous_item = None
        # Scan the items
        i_pos = 0
        current_pos = i_pos
        for item in self.items:
            # We ignore rests
            if item.is_rest: 
                # If the rest is a full measure, part of a multi-measure rest: we need to adjust
                i_pos += 1
                continue

            if previous_item is None:
                previous_item = item
            else:
                # Compute the number of semi-tones
                gap = item.get_index() - previous_item.get_index()

                if gap != 0:
                    #if we find a new note with different pitch
                    if gap > 0:
                        #if the semi-tone difference between the current and the previous item > 0, then it is an ascending interval
                        direction = 'A'
                    else:
                        #otherwise, it is a descending interval.
                        direction = 'D'

                    if descriptor == settings.DIATONIC_DESCR:
                        """
                        Get diatonic interval name via music21, and store as a dictionary. 
                        Each object contains the position of the first event, the position of the last event,
                        and diatonic interval name. The interval is reduced to no more than an octave.

                        P.S:
                        For obtaining original interval name(not reduced to an octave), may change "directedsimpleNiceName" to "niceName".
                        For not getting the direction info(descending or ascending), may change "directedSimpleNiceName" to "simpleNiceName".
                        """

                        #Transfer items to music21 note objects
                        m21_item = item.get_music21_note()
                        m21_pre_item = previous_item.get_music21_note()

                        #Calculate interval with music21
                        """
                            "directedSimpleNiceName" examples: "Descending Doubly-Diminished Fifth", "Ascending Perfect Fourth", "Ascending Doubly-Augmented Fourth"
                            "simpleName" examples: dd5, P5, AA4. There's no direction information
                        """
                        m21_interval_directed = m21.interval.Interval(noteStart=m21_pre_item, noteEnd=m21_item).directedSimpleNiceName
                        
                        arr_diatonic = m21_interval_directed.split(" ")
                        """
                        #This part is no longer necessary because we could tell direction by gap value                            
                        if arr_diatonic[0] == "Ascending": direction = 'A'
                        elif arr_diatonic[0] == "Descending": direction = 'D'
                        else: direction = ''
                        """
                        m21_generic = dict_wordtonum[arr_diatonic[-1]]
                        #m21_generic_interval = m21.interval.GenericInterval(arr_diatonic[-1])

                        m21_interval = m21_generic + direction

                        dia_interval = {"start_pos": current_pos, "end_pos": i_pos, "value": m21_interval}
                        diatonic_intervals.append(dia_interval)


                    # For getting semitone numbers of the current interval
                    num_interval = str(abs(gap)) + direction
                    interval = {"start_pos": current_pos, "end_pos": i_pos, "value": num_interval}
                    intervals.append(interval)

                    previous_item = item
                    current_pos = i_pos

            i_pos += 1

        if descriptor == settings.DIATONIC_DESCR:
            #by diatonic interval names
            return diatonic_intervals
        else:
            #by number of semitones
            return intervals

    def get_notes(self):
        #Get notes for exact search
        notes = []
        previous_item = None
        # Scan the items
        i_pos = 0
        current_pos = i_pos
        for item in self.items:
            if previous_item is None:
                previous_item = item
            else:
                # Prevent division by zero
                item_duration = Fraction.from_float(item.duration).limit_denominator(max_denominator=100)
                previous_item_duration = Fraction.from_float(previous_item.duration).limit_denominator(max_denominator=100)
                if item_duration == 0 or previous_item_duration == 0:
                    continue
                rhythm = Fraction(item_duration, previous_item_duration).limit_denominator(max_denominator=100)
                pitch = item.get_index() - previous_item.get_index()
                
                note = {"start_pos": str(current_pos), "end_pos": str(i_pos), "rhythm": str(rhythm), "pitch": str(pitch)}
                notes.append(note)
                previous_item = item
                current_pos = i_pos
            i_pos += 1
        return notes

    @staticmethod
    def get_intervals_as_list(intervals):
        """
            Get intervals value in a list
        """
        interval_list = []
        for interval in intervals:
            interval_list.append(str(interval["value"]))
        return interval_list

    @staticmethod
    def encode_as_string(intervals):
        """
          Encode the intervals as string 
        """
        s_intervals = INTERVAL_SEPARATOR
        for interval in intervals:
            s_intervals = s_intervals + str(interval["value"]) + INTERVAL_SEPARATOR
        return s_intervals
            
    def get_intervals_as_string(self):
        """Used for debugging in templates """
        return self.encode_as_string(self.get_intervals())
    
    def find_positions(self, pattern, search_type, first_position=0):
        """
         Find the position(s) of a pattern in the sequence
        """
        occurrences = []

        if search_type == settings.RHYTHMIC_SEARCH:
            p_intervals = pattern.get_rhythms()
            s_intervals = self.get_rhythms()
        elif search_type == settings.MELODIC_SEARCH:
            p_intervals = pattern.get_intervals(settings.MELODY_DESCR)
            s_intervals = self.get_intervals(settings.MELODY_DESCR)

        elif search_type == settings.EXACT_SEARCH:
            p_intervals = pattern.get_notes()
            s_intervals = self.get_notes()
        elif search_type == settings.DIATONIC_SEARCH:
            p_intervals = pattern.get_intervals(settings.DIATONIC_DESCR)
            s_intervals = self.get_intervals(settings.DIATONIC_DESCR)
        else:
            p_intervals = pattern.get_intervals(settings.MELODY_DESCR)
            s_intervals = self.get_intervals(settings.MELODY_DESCR)

        # Get intervals as list, e.g. ['2', '2', '2']
        if search_type == settings.EXACT_SEARCH:
            p_intervals_list = self.notes_to_symbols(p_intervals)
            s_intervals_list = self.notes_to_symbols(s_intervals)
        else:
            p_intervals_list = pattern.get_intervals_as_list(p_intervals)
            s_intervals_list = pattern.get_intervals_as_list(s_intervals)

        # Find patterns positions in list
        occurrences_indexes = self.find_sub_list(p_intervals_list, s_intervals_list)
        for tuple in occurrences_indexes:
            # Get start and end positions
            occurrences.append(range(int(s_intervals[tuple[0]]["start_pos"]), int(s_intervals[tuple[1]]["end_pos"]) + 1))

        return occurrences

    def get_mirror_intervals(self, intervals):
        """
            Get an interval list(diatonic or melodic), then return the "mirror" of the pattern list.
            In the context of this function, "mirror" refers to go through the original interval list,
            modifying ascending intervals into descending intervals, and vice versa.

            Example: the original representation of an ascending second is "2A", and the mirror representation
            of "2A" is "2D", a.k.a. a descending second.
        """
        
        mirror_intervals = []

        for i in intervals:
            #Get the original intervals one by one
            curr_start_pos = i["start_pos"]
            curr_end_pos = i["end_pos"]
            curr_value = i["value"]
            
            mirror_dir = ''
            if curr_value[-1] == 'A':
                mirror_dir = 'D'
            elif curr_value[-1] == 'D':
                mirror_dir = 'A'
            #Change the direction of the interval
            mirror_value = curr_value[:-1] + mirror_dir

            mirror_interval = {"start_pos": curr_start_pos, "end_pos": curr_end_pos, "value": mirror_value}
            mirror_intervals.append(mirror_interval)

        return mirror_intervals

    def get_melody_encoding(self, mirror_setting = False):
        """
            Get melody and decompose in ngram text for melodic search.
            
            When mirror_setting=True, it means that the search specified to include mirror patterns in the search context,
            this function returns the original melody encodings, and the mirrored melody encodings, both as a list of n-grams.

            Please find definition of "mirror patterns" in description of get_mirror_intervals()

        """
        melody_list = self.get_intervals(settings.MELODY_DESCR)
        melody_encoding = self.intervals_to_ngrams(melody_list)

        if mirror_setting == False:
            return melody_encoding
        elif mirror_setting == True:
            mirror_melody = self.get_mirror_intervals(melody_list)
            return melody_encoding, self.intervals_to_ngrams(mirror_melody)

    def get_diatonic_encoding(self, mirror_setting = False):
        """
            Get diatonic interval names and decompose in ngram text for diatonic search.

            When mirror_setting=True, it means that the search specified to include mirror patterns in the search context,
            this function returns the original diatonic encodings, and the mirrored diatonic encodings, both as a list of n-grams.

        """
        dia_list = self.get_intervals(settings.DIATONIC_DESCR)
        dia_encoding = self.intervals_to_ngrams(dia_list)

        if mirror_setting == False:
            return dia_encoding
        elif mirror_setting == True:
            mirror_dia = self.get_mirror_intervals(dia_list)
            return dia_encoding, self.intervals_to_ngrams(mirror_dia)

    def get_rhythm_encoding(self):
        """
            Get rhythm and decompose in ngram text for rhythmic search
        """
        rhythm_encoding = self.rhythms_to_ngrams(self.get_rhythms())
        return rhythm_encoding

    def get_note_encoding(self):
        """
            Get note and decompose in ngram text for exact search
        """
        note_encoding = self.to_ngrams(self.notes_to_symbols(self.get_notes()))
        return note_encoding

    def rhythms_to_symbols(self, dict):
        symbols = list()
        for r in dict:
            symbols.append("(" + str(r["value"]) + ")")
        return symbols

    def intervals_to_symbols(self, dict):
        symbols = list()
        for interval in dict:
            symbols.append(str(interval["value"]) + ";")
        return symbols

    @staticmethod
    def notes_to_symbols(dict):
        symbols = list()
        for note in dict:
            symbols.append('(' + str(note['pitch']) + '|' + str(note['rhythm']) + ')')
        return symbols

    def rhythms_to_ngrams(self, dict):
        #
        #   Splits rhythms ratios into ngrams with size NGRAM_SIZE, e.g : (3/4)(2/3)(1/2) (2/3)(1/2)(1/2) ...
        #
        nb_codes = len(dict)
        text = ""
        for i in range(nb_codes - NGRAM_SIZE + 1):
            ngram = ""
            for j in range(i, i + NGRAM_SIZE):
                # Surround ratios with parentheses
                ngram += "(" + str(dict[j]["value"]) + ")"
            text += ngram + " "
        return text

    def intervals_to_ngrams(self, dict):
        #
        #   Splits intervals into ngrams with size NGRAM_SIZE, for both melodic and diatonic searches
        #
        nb_codes = len(dict)
        phrase = ""
        for i in range(nb_codes - NGRAM_SIZE + 1):
            #ngram no longer needs to begin with a separator ';' because it's absolute value
            ngram = ""
            for j in range(i, i + NGRAM_SIZE): 
                ngram = ngram + str(dict[j]["value"]) + ";"
            phrase += ngram + " "
        return phrase

    def to_ngrams(self, symbols, hash=False):
        #
        #   Splits symbol list into ngrams with size NGRAM_SIZE, used for exact search
        #
        nb_codes = len(symbols)
        phrase = ""
        for i in range(nb_codes - NGRAM_SIZE + 1):
            # Begin with a separator (otherwise '7' and '-7' both match)
            ngram = ""
            for j in range(i, i + NGRAM_SIZE):
                ngram = ngram + str(symbols[j]) + ""
            if hash:
                phrase += self.hash_ngrams(ngram) + " "
            else:
                phrase += ngram + " "
        return phrase
    
    @staticmethod
    def hash_ngrams(ngram):
        before = {";": "", "-": "m"}
        letters = list(string.ascii_lowercase)  # get list of lowercase letters
        # Build dictionary of type <number> => <letter>
        for i, letter in enumerate(letters):
            if letter != "m":
                before[str(i)] = letter
        
        hashed = ngram
        for c1, c2 in before.items():
            hashed = hashed.replace(c1, c2)
        return hashed
    
    @staticmethod
    def find_sub_list(sub_list, l):
        # Find sublists in list
        # Returns a list of the first and last indexes of the matching sublists
        results = []
        sll = len(sub_list)
        for ind in (i for i, e in enumerate(l) if e == sub_list[0]):
            if l[ind:ind + sll] == sub_list:
                results.append((ind, ind + sll - 1))
        return results

    def __str__(self):
        s = ""
        sep = ""
        for item in self.items:
            s =  s + sep + str(item) 
            sep = ";"
        return s

    def get_rhythmic_distance(self, s1, s2):
        #Get rhythm of both to determine the rhythm distance between two patterns with identical melody 
        """Evaluate the distance between two sequences"""

        r1 = s1.get_rhythms()
        r2 = s2.get_rhythms()
        if not r1 or not r2:
            return 100
        
        score = Distance_neuma.distance(s1, s2)
        print ("Rhythmic distance between the pattern and occurrence " + str(s1) + " : " + str(round(score, 4)))
        return score

    def get_melodic_distance(self, s1, s2):

        #get the diatonic intervals of both to calculate melodic distance
        m1 = s1.get_intervals(settings.DIATONIC_DESCR)
        m2 = s2.get_intervals(settings.DIATONIC_DESCR)
        if not m1 or not m2:
            return 100

        #Get melodic distance, computed by modified edit distance
        m_distance = Distance_neuma.melodic_distance(s1, s2)

        print("Melodic distance between the pattern and occurrence " + str(s1) + " : "+ str(round(m_distance, 4)))
        return m_distance

    def sequence_to_symbols(self):
        notes = list()
        for item in self.items:
            s = str(item.get_index()) + '|' + str(Fraction.from_float(item.duration))
            notes.append(s)
        return notes
