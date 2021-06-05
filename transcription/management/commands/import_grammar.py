from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from manager.models import Corpus
from transcription.models import *

from transcription.models import Grammar, GrammarRule, GrammarState

import string
from django.core.files import File
import os
import json

#call it with "python manage.py import_grammar -f grammar_name"
#be sure to change the name of the corpus in the settings.transcription

class Command(BaseCommand):
    """Import a grammar file in the transcription corpus"""

    help = 'Import a grammar file in the transcription corpus'

    def add_arguments(self, parser):
        parser.add_argument('-f', dest='file_name')

    def handle(self, *args, **options):
        if options["file_name"] == None:
            print ("Please supply a file name with -f")
            exit(1)
        try:
            transcription = Corpus.objects.get(ref=settings.NEUMA_TRANSCRIPTION_CORPUS_REF)
        except Corpus.DoesNotExist:
                raise CommandError('Transcription corpus does not exist. Run setup_neuma first.')
                exit(1)
                
        print ("Loading grammar file " + options["file_name"])
        path = os.path.join(os.path.dirname(settings.BASE_DIR), 'scorelib', 'transcription', 'grammars', options["file_name"])
        
        try:
            with open(path) as f:
               grammar  = json.loads(f.read())
            
            print ("Grammar name " + grammar["name"] + ". Meter: " +str( grammar["meter_nb_beats"]) + "/" 
                   + str(grammar["meter_beat_unit"]))
            
            # Delete the existing one
            try:
                db_grammar = Grammar.objects.get(name=grammar["name"])
                GrammarRule.objects.filter(grammar=db_grammar).delete()
                GrammarState.objects.filter(grammar=db_grammar).delete ()
                db_grammar.delete()
                print ("Previous DB grammar deleted")
            except Grammar.DoesNotExist:
                # No pb
                pass
            
            # Create a new one
            print("Creating the grammar")
            db_grammar = Grammar (name= grammar["name"], ns = grammar["namespace"],
                    meter_nb_beats = grammar["meter_nb_beats"], meter_beat_unit = grammar["meter_beat_unit"],
                    parse_failures_ratio=grammar["parse_failures_ratio"], corpus = transcription)
            db_grammar.save()
            print("Grammar saved")


            # Compute the list of states
            print("Creating the states")
            list_states = {}
            for state in grammar["states"]:
                print ("Found state " + state["name"])
                if state["type"] == "non-terminal":
                    list_states[state["name"]] = {"type": NON_TERMINAL_STATE, "nb_grace_notes": 0}
                elif state["type"] == "cont":
                    list_states[state["name"]] = {"type": TERMINAL_STATE, "nb_grace_notes": 0}
                elif state["type"] == "note":
                    list_states[state["name"]] = {"type": TERMINAL_STATE, "nb_grace_notes": state["nb_grace_notes"]}
                else:
                    raise ValueError(
                        'Incorrect grammar-json: a state cannot have the type ' + state["type"])

            # Insert the states
            for symbol, descr in list_states.items():
                print ("State : " + symbol + " Type = " + descr["type"])
                state = GrammarState (grammar = db_grammar, 
                                      symbol = db_grammar.full_symbol (symbol),
                                    type =  descr["type"],
                                    nb_grace_notes = descr["nb_grace_notes"])
                state.save()
            print("States saved")
                
            # Insert the rules
            print("Creating the rules")
            for rule in grammar["rules"]:
                rule_head = GrammarState.objects.get(symbol=db_grammar.full_symbol(rule["head"]))
                # Take the body
                body = []
                assert isinstance(rule["body"], list) #check that the json is formatted correctly
                for s in rule["body"]:
                    body.append(db_grammar.full_symbol(s))
                rule_weight = rule["weight"]

                # Instantiate the rule
                db_rule = GrammarRule (grammar = db_grammar,
                                       head = rule_head,
                                       body= body,
                                       weight = rule_weight)
                db_rule.save()
            print("Rules saved")
                
            print ("Grammar import is completed!")
        except Exception as e:
            print ("Exception met: " + str(e))
        