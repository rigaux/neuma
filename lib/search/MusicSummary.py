# coding: utf-8
from django.conf import settings

import jsonpickle, json
from operator import itemgetter
from .Sequence import Sequence
from .Distance import *


# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)
        
class MusicSummary:
    """
        Lightweight representation of a music score. Used for pattern search.
        
        A music summary object gives a barebne representation of a music piece. It consists
        of *parts*, which themselves consist of *voices*. Finally each voice
        if a *sequence* of *items*.
        
        MS objects are serialized in JSON for storaae with and Opus. The music summary
        associated with an Opus is then loaded as search time to identify occurrences
        of pattern searches.
    """
    def __init__(self) :
        self.opus_id = ""
        self.parts = {}
        
    def decode(self, json_string):
        '''
           Decode a music summary from its JSON representation 
        '''
        json_obj = json.loads(json_string)
        if "opus_id" in json_obj.keys():
            self.opus_id = json_obj["opus_id"]
            # Music = set of parts
            for part_id in json_obj["parts"].keys():
                part = json_obj["parts"][part_id]
                self.parts[part_id] = {}
                # Parts = set of voices
                for voice_id in part.keys():
                    voice = part[voice_id]
                    self.parts[part_id][voice_id] = Sequence()
                    # Decode the sequence from the voice
                    self.parts[part_id][voice_id].decode(voice)

    def add_part(self, part_id):
        '''Initializes a part'''
        self.parts[part_id] = {}
        
    def add_voice_to_part(self, part_id, voice_id, voice):
        '''Add a voice to a part'''
        self.parts[part_id][voice_id] = voice.convert_to_sequence()
        
    def encode(self):
        '''
           Encode a music summary in in JSON
        '''
        return jsonpickle.encode(self, unpicklable=False)

    
    def find_positions(self, pattern, search_type, mirror_setting = False):
        """ 
            Find the position of a pattern in the voices
            
            The pattern parameter is a Sequence object
            If 'rhythm' is True, the pattern will be decoded as a rhythm, otherwise, as a melody
            Called by views.py
        """
        occurrences = dict()
        for part_id, part in self.parts.items():
            occurrences[part_id] = dict()
            for voice_id, voice in part.items():
                #Calling find_positions() in Sequence.py
                occurrences[part_id][voice_id] = voice.find_positions(pattern, search_type, mirror_setting)
        return occurrences

    def find_matching_ids(self, pattern, search_type, mirror_setting = False):

        ids = list()
        for part_id, part in self.parts.items():
            for voice_id, voice in part.items():
                #Calling find_positions() in Sequence.py
                occurrences = voice.find_positions(pattern, search_type, mirror_setting)
                for occ in occurrences: 
                    for i in occ:
                        # print ("Item match  " + str(i) + " : " + str(voice.items[i]))
                        ids.append(voice.items[i].id)
        return ids

    def find_sequences(self, pattern, search_type, mirror_setting = False):

        sequences = list()
        for part_id, part in self.parts.items():
            #Iterate over parts in MusicSummary
            for voice_id, voice in part.items():
                '''
                    In every part, iterate over sequences of several voices
                    Note that the "voice" here is not a Voice object, but a "Sequence"
                    If iterating over items within sequence is needed,
                    Use "for item in voice.get_items_from_sequence()"
                '''
                #Calling find_positions() in Sequence.py
                occurrences = voice.find_positions(pattern, search_type, mirror_setting)
                for o in occurrences:
                    s = Sequence()
                    for ir in o:
                        s.add_item(voice.items[ir])
                    sequences.append(s)
        return sequences
    
    def find_exact_matches(self, pattern, search_type):
        # Find sequences that match
        occurrences = self.find_sequences(pattern, search_type, False)

        # If there is a match in the opus
        if occurrences != None:
        # TODO TIANGE: it should be if len(occurrences) > 0 but occurrences is empty []
            print("#######################################")
            print("Found exact match in opus_id:  ", self.opus_id)

        return occurrences

    def get_best_occurrence(self, pattern, search_type, mirror_setting = False):
        """
          Get the best matching occurrence (wrt its distance from pattern)
          When it is a pattern search, i.e. melodic search, rhythmic search, diatonic search
        """

        occurrences = self.find_sequences(pattern, search_type, mirror_setting)
        distances = list()

        # If there is a match in the opus
        if len(occurrences) > 0 :
            print("#######################################")
            print("Found occurrence in opus:  " + self.opus_id)

        # Iterate over all the matches in an opus
        for o in occurrences:
            print ("Check occurrence " + str(o))
            try:
                #Get rhythmic distance for melodic type of search for the current match
                if search_type == settings.MELODIC_SEARCH or search_type == settings.DIATONIC_SEARCH:
                    d = (o, o.get_rhythmic_distance(o, pattern))

                #Otherwise, get melodic distance for rhythmic search for the current match
                elif search_type == settings.RHYTHMIC_SEARCH:
                    d = (o, o.get_melodic_distance(o, pattern))

                distances.append(d)

            except ValueError as e:
                logger.error ("Opus " + self.opus_id + " and pattern " + str([pattern]) + ": " + str(e))
                #print("Error during distance computation: " + str(e))
        #
        # We can do better by counting the number of occurrences wit the minimal distance
        #
        if len(distances) > 0:
            best_occurrence, distance = min(distances, key=itemgetter(1))
            return best_occurrence, distance
        else:
            #logger.error ("Opus " + self.opus_id + " and pattern " + str([pattern]) + ": no occurrence found?")
            return "", 1000000
 