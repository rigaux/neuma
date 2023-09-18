from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from manager.models import Corpus
from transcription.models import *

import string
from django.core.files import File
import os
import json

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
        name = "test"
        namespace = "tst"
        meter_nb_beats = 4
        meter_beat_unit = 4
        levels = 7  #how many time non terminal symbols can be transformed in other non terminal
        grace_notes = 3 #maximum number of grace notes allowed
        list_of_divisions = [2,3,5,7] #list_of_division must contain only prime numbers. We can add 11, 13, etc. if we need complex tuplets
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
        # Create States
        # Create Terminal States
        json_grammar["states"].append({"name": "N0", "type": "cont", "nb_grace_notes":0})
        for ii in range(grace_notes + 1):
            json_grammar["states"].append(
                {"name": "N{0}".format(ii + 1), "type": "note", "nb_grace_notes": ii})
        #Create Non Terminal States
        for i in range(levels ):
            json_grammar["states"].append({"name": "S{0}".format(i), "type": "non-terminal"})
        # Fill the rules
        for i in range(levels):
            # Terminal symbols production
            json_grammar["rules"].append({"head": "S{0}".format(i), "body": ["N0"]})
            for ii in range(grace_notes + 1):
                json_grammar["rules"].append({"head": "S{0}".format(i), "body": ["N{0}".format(ii+1)]})
            # Non-terminal symbols production
            for ii in list_of_divisions:
                json_grammar["rules"].append({"head": "S{0}".format(i), "body": []})
                for _ in range(ii):
                    json_grammar["rules"][-1]["body"].append("S{0}".format(i + 1))
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

