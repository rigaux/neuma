from django.db import models
from django.contrib.postgres.fields import ArrayField

from manager.models import Corpus, Opus

from django.conf import settings

from django.utils.timezone import now

NON_TERMINAL_STATE = "NT"
TERMINAL_STATE = "T"
CONTINUATION_STATE = "cont"
RANDOM_STATE = "rand"

WEIGHT_PROBA = "proba"
WEIGHT_COST = "penalty"
TYPES_WEIGHT = (
    (WEIGHT_PROBA, "Probability"),
    (WEIGHT_COST, "Penalty"),
)


class TranscribedOpus(models.Model):
    def __init__(self, opus, *args, **kwargs):
        super(TranscribedOpus, self).__init__(*args, **kwargs)
        self.opus = opus
        self.name = opus.title + "_transcription"
        self.ref = opus.ref

    opus = models.ForeignKey(Opus, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    # TODO : add a ref field linking with Audiofile


class Grammar(models.Model):
    """
      Representation of a Grammar
      
      mjokk^k
    """

    # Give a name, or by default the time signature
    name = models.CharField(max_length=255, primary_key=True)
    # Namespace, to identify rules of a grammar
    ns = models.CharField(max_length=4, unique=True)
    # How many beats: 1, 2, 3, etc: the numerator
    meter_numerator = models.IntegerField()
    # Beat unit: 1, 2, 4, 8: the denominator
    meter_denominator = models.IntegerField()
    # Initial state
    initial_state = models.IntegerField()
    # Type de poids
    type_weight = models.CharField(
        max_length=30, choices=TYPES_WEIGHT, default=WEIGHT_PROBA,
    )

    def __init__(self, *args, **kwargs):
        super(Grammar, self).__init__(*args, **kwargs)

    class Meta:
        db_table = "Grammar"

    def local_symbol(self, full_symbol):
        """
            Get the local symbol from the full symbol
        """
        if settings.NEUMA_ID_SEPARATOR in full_symbol:
            # Find the last occurrence of the separator
            last_pos = full_symbol.rfind(settings.NEUMA_ID_SEPARATOR)
            return full_symbol[last_pos + 1 :]
        else:
            # Top-level corpus
            print("Suspect full symbol: cannot find the namespace ")
            return full_symbol

    def full_symbol(self, local_symbol):
        """
            Make the full symbol from the local one
        """

        return self.ns + settings.NEUMA_ID_SEPARATOR + local_symbol

    def __str__(self):  # __unicode__ on Python 2
        # return "Grammar " + name
        return "Grammar " + self.name

    def get_json(self):
        query_rules = GrammarRule.objects.filter(grammar=self).all()
        rules = []
        for r in query_rules:
            rules.append(r.get_json())
        json_out = {
            "name": self.name,
            "initial_state": self.initial_state,
            "meter_numerator": self.meter_numerator,
            "meter_denominator": self.meter_denominator,
            "type_weight": self.type_weight,
            "ns": self.ns,
            "rules": rules,
        }
        return json_out

    def get_str_repr(self):
        str_out = "//Grammar {0}\n".format(self.name)
        str_out += "[{}]\n".format(
            self.type_weight
        )  # TODO: link that to the grammar value
        str_out += "[timesig {} {}]\n".format(
            self.meter_numerator, self.meter_denominator
        )
        query_rules = GrammarRule.objects.filter(grammar=self).all()
        # now transform them in a string
        for i, r in enumerate(query_rules):
            str_out += "{}\n".format(r.get_str_repr())
        return str_out


class GrammarState(models.Model):
    """List of states of a grammar"""

    # The grammar the state belongs to
    # grammar = models.ForeignKey(Grammar,on_delete=models.PROTECT)
    # The (wrt grammar) symbol that characterizes the state. Mus be of the form ns:symbol,
    # where ns is the grammar namescape
    symbol = models.CharField(max_length=40, unique=True)
    # The type of the symbol: terminal (T) or not (NT)
    type = models.CharField(max_length=2, default="NT")
    # The number of grace notes
    nb_grace_notes = models.IntegerField(default=0)

    class Meta:
        db_table = "GrammarState"

    def __str__(self):  # __unicode__ on Python 2
        return "Grammar " + self.grammar.name + ", state symbol " + self.symbol


class GrammarRule(models.Model):
    """A derivation rule, of the form head -> [state1, state2, ...]"""

    # The grammar the rule belongs to
    grammar = models.ForeignKey(Grammar, on_delete=models.CASCADE)
    # The weight of the rule in a given context (a corpus)
    weight = models.FloatField(default=0.0)
    # Head of the rule
    head = models.IntegerField()
    # Body of the rule = an array of state form the same grammar, referred to by their symbol.
    # No referential integrity checking here, should be ok.
    body = ArrayField(models.IntegerField())
    # Nb occurrences of each state in the body
    occurrences = ArrayField(models.IntegerField())
    # Symbol (types of relationships for the body rules)
    symbol = models.CharField(max_length=20)

    class Meta:
        db_table = "GrammarRule"

    def __str__(self):  # __unicode__ on Python 2
        return "Rule " + str(self.head) + " Body: " + str(self.body)

    def get_str_repr(self):
        out = "{} -> {}(".format(self.head, self.symbol)
        # add for each element in the body
        for b, occ in zip(self.body, self.occurrences):
            out += "{}:{},".format(b, occ)
        # remove last comma and add parenthesis
        out = out[:-1] + ")"
        # add weight
        out += " {}".format(self.weight)
        return out

    def get_json(self):
        body_array = []
        # BEWARE: assumes that boddy and occurrences have the same size
        for i in range(len(self.body)):
            body_array.append({"state": self.body[i], "occ": self.occurrences[i]})
        json_out = {
            "head": self.head,
            "body": body_array,
            "weight": self.weight,
            "symbol": self.symbol,
        }
        return json_out


class QParse:
    """ 
        A class with static methods to interact with the QParse program
    """

    @staticmethod
    def encodeInputVoiceAsText(jsonMessage):
        """
          Transform a voice from the JSON message sent to the REST server into a 
          text sent to the QParse program
          """
        out = ""
        for e in jsonMessage:  # iterate over all musical events in the voice
            out += "{}/{}\n".format(
                e["duration"]["numerator"], e["duration"]["denominator"]
            )
        return out

    @staticmethod
    def decodeOutput(textOutput):
        """
          Transform the text output produced by the QParse program
          into a list that will be later merged in a json output for the API return message
          """
        out_list = []
        for line in textOutput.split("\n"):
            if len(line) > 3:  # avoid problems with empty lines
                out_list.append(line[3:])
        return out_list

