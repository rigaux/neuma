#-*- coding: utf-8 -*-
from django import forms

class TranscriptionSettingsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.possiblegrammars = kwargs.pop("possiblegrammars")
        super(TranscriptionSettingsForm, self).__init__(*args, **kwargs)
        self.fields["grammar"].choices = [(g.id, g.name) for g in self.possiblegrammars]

    grammar = forms.ChoiceField(label=u'Grammar')
    bar_duration = forms.IntegerField(label=u'Bar duration')
    bar_metric_denominator = forms.IntegerField(label=u'Bar metric denominator')
    time_signature = forms.CharField(label=u'Time Signature')


