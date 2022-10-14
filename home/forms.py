from django import forms
from django.forms import ModelForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.forms.widgets import *
from django.forms.models import inlineformset_factory
# https://dev.to/zxenia/django-inline-formsets-with-class-based-views-and-crispy-forms-14o6
from crispy_forms.layout import Layout, Fieldset, Submit, Row, Column, Div, Field
from crispy_forms.layout import LayoutObject, TEMPLATE_PACK

from django.template.loader import render_to_string


from manager.models import Corpus, OpusSource, SourceType

class StructuredQueryForm(forms.Form):
    query_text = forms.CharField(label="Enter your query", widget=forms.Textarea)
    

class CorpusForm(forms.ModelForm):

    class Meta:
        model = Corpus
        fields = ('title', 'ref', 'short_title', 'description', 'short_description', 'is_public', 'cover')


class OpusSourceForm(ModelForm):
 
    id_source = None

    class Meta:
        model = OpusSource
        fields = "__all__"
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-OpusSourceForm'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'
        
        # Pour éviter le rejet par is_valid()
        self.fields['opus'].required = False
        self.fields['url'].required = False
        self.fields['source_file'].required = False
        #self.fields['creation_timestamp'].required = False
        #self.fields['update_timestamp'].required = False
        self.fields['source_type'] = forms.ModelChoiceField(queryset=SourceType.objects.all())
        self.fields['description'] = forms.CharField(widget=forms.Textarea(attrs={"rows":3, "cols":20}))

        self.fields["id_source"] = forms.CharField(widget=forms.HiddenInput(),initial=OpusSourceForm.id_source)
        self.fields['id_source'].required = False
        
        self.helper.layout = Layout(
            'ref',
            'source_type',
            'description',
            'url',
            'source_file', 
            "id_source",
            Submit('submit', 'Sauvegarder')
         )
        
    def get_queryset(self):
        return super(MyFormset, self).get_queryset().order_by('ref')
