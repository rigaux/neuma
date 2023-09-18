from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from manager.models import Corpus
from transcription.models import *

import string
from django.core.files import File
import os
import json

#call it with "python manage.py create_long_grammar -f grammar_name"


class Command(BaseCommand):
    """Create an unweighted grammar json for the training"""

    help = 'Creating a generic grammar json'

    def add_arguments(self, parser):
        parser.add_argument('-f', dest='file_name')

    def handle(self, *args, **options):
        if options["file_name"] == None:
            print("Please supply a file name with -f")
            exit(1)

        print("Creating generic grammar " + options["file_name"])
        path = os.path.join(os.path.dirname(settings.BASE_DIR), 'scorelib', 'transcription', 'grammars',
                            options["file_name"])

        #Setting the options
        name = "16grammar44"
        namespace = "16grammar44"
        meter_nb_beats = 4
        meter_beat_unit = 4
        levels = 4  #how many time non terminal symbols can be transformed in other non terminal
        grace_notes = 1 #maximum number of grace notes allowed
        list_of_divisions = [2,3] #list_of_division must contain only prime numbers. We can add 11, 13, etc. if we need complex tuplets
        nb_parse_fail = 0

        #create the json
        json_grammar = {
            "name": name,
            "namespace": namespace,
            "meter_nb_beats": meter_nb_beats,
            "meter_beat_unit": meter_beat_unit,
            "parse_failures_ratio": nb_parse_fail,
            "states": [],
            "rules": []

        }
        ## Create States
        # Create Terminal States
        json_grammar["states"].append({"name": "N0", "type": "cont", "nb_grace_notes":0})
        for ii in range(grace_notes + 1):
            json_grammar["states"].append(
                {"name": "N{0}".format(ii + 1), "type": "note", "nb_grace_notes": ii})
        ##Create non terminal states and rules with the recursive funcion
        first_state = {"name": "S1", "type": "non-terminal"}
        recursive_output = self.recursive_state_creation(first_state, list_of_divisions, 1, levels, grace_notes)
        json_grammar["states"].append(first_state)
        json_grammar["states"].extend(recursive_output[0])
        json_grammar["rules"].extend(recursive_output[1])

        # Add non-meaningful weights

        n_of_rules = len(json_grammar["rules"])
        for r in json_grammar["rules"]:
            r["weight"] = 1/n_of_rules

        try:
            with open(path, 'w') as f:
                json.dump(json_grammar, f)

            print("Generic grammar named " + options["file_name"] + " created")


        except Exception as e:
            print("Exception met: " + str(e))


    def recursive_state_creation(self, old_state, list_of_divisions, level, max_level, n_grace_notes):
        ##Create Non Terminal States
        new_states = []  # vector to temporary store states to apply recursion
        new_rules = []
        # append the rule for terminal
        for i in range(n_grace_notes + 2):
            new_rules.append({"head": old_state["name"], "body": ["N{0}".format(i)]})
        ##chose if going on or stop the recursion
        if level > max_level: #stop the recursion
            return new_states, new_rules
        else:
            for d in list_of_divisions:
                rule_body = []
                for n in range(d):
                    new_name = "{0}{1}{2}".format(old_state["name"], d, n + 1)
                    new_states.append({"name": new_name, "type": "non-terminal"})
                    ##append the rules
                    # create the rule body for the old state for non-terminal
                    rule_body.append(new_name)
                new_rules.append({"head": old_state["name"], "body": rule_body}) #append the body to the rule
            ##Call the recursive funcion to each element of new states
            new_new_states = new_states[:] #needed otherwise we are incrementing the list where we loop
            for s in new_states:
                recursion_output = self.recursive_state_creation(s, list_of_divisions, level+1, max_level, n_grace_notes)
                new_new_states.extend(recursion_output[0])
                new_rules.extend(recursion_output[1])
            return  new_new_states, new_rules
