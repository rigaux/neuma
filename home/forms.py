from django import forms

from manager.models import Annotation, Corpus

class StructuredQueryForm(forms.Form):
    query_text = forms.CharField(label="Enter your query", widget=forms.Textarea)
    

class CorpusForm(forms.ModelForm):

    class Meta:
        model = Corpus
        fields = ('title', 'ref', 'short_title', 'description', 'short_description', 'is_public', 'cover')