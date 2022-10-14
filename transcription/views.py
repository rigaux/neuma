from django.shortcuts import render
from neumautils.views import NeumaView
from manager.models import (
    Corpus,
    Opus
)
from django.conf import settings
from .forms import TranscriptionSettingsForm
from .models import TranscribedOpus
import subprocess, os, ntpath


class OpusView(NeumaView):
    def get_context_data(self, **kwargs):
        # Get the opus
        opus_ref = self.kwargs["opus_ref"]
        opus = Opus.objects.get(ref=opus_ref)
        audiofile = ""
        audio_ref = ""

        try:
            audio_ref = int(self.kwargs["audio_id"])
        except:
            print("ERROR: audio_ref error in transcription views:", audio_ref)
        if isinstance(audio_ref, int):
            audiofile = Audio.objects.get(id=audio_ref)

        # Initialize context
        context = super(OpusView, self).get_context_data(**kwargs)

        # Record the fact the user accessed the Opus
        if self.request.user.is_authenticated():
            current_user = self.request.user
        else:
            # Take the anonymous user
            current_user = User.objects.get(username="AnonymousUser")
            # current_user = User.objects.get(username='anonymous')
            if current_user is None:
                raise ObjectDoesNotExist("No anonymous user. Please create it")

        # By default, the tab shown is the first one
        context["tab"] = 0

        # Analyze the score
        score = opus.get_score()
        context["opus"] = opus
        context["score"] = score
        context["audiofile"] = audiofile
        context["grammars"] = list(opus.corpus.get_grammars())

        # Add audio files
        context["audio_files"] = opus.audio_set.all()

        return context

    def get(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        context["transcription_form"] = TranscriptionSettingsForm(
            possiblegrammars=context["grammars"]
        )
        return render(request, "transcription/opus.html", context=context)

    def post(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        context["transcription_form"] = TranscriptionSettingsForm(
            request.POST, possiblegrammars=context["grammars"]
        )
        form = context["transcription_form"]

        if form.is_valid():
            # get form values
            context["grammar"] = form.cleaned_data["grammar"]
            context["bar_duration"] = form.cleaned_data["bar_duration"]
            context["bar_metric_denominator"] = form.cleaned_data[
                "bar_metric_denominator"
            ]
            context["time_signature"] = form.cleaned_data["time_signature"]

            script_fullpath = (
                "/home/raph/Recherche/Scorelib/qparselib/test/run_quant_scorelib.sh"
            )
            midi_filename = context["audiofile"].audio_file.path
            for g in context["grammars"]:
                if str(g.id) == str(context["grammar"]):
                    grammar_name = g.name
            grammar_file = (
                "/home/raph/Enseignement/vertigo_svn/scorelib/app/scorelib/transcription/grammars/"
                + grammar_name
            )
            outfile = (
                settings.MEDIA_ROOT
                + "/"
                + os.path.splitext(ntpath.basename(midi_filename))[0]
                + "_quant.mei"
            )
            bar_duration = str(context["bar_duration"])
            bar_metric_denominator = str(context["bar_metric_denominator"])
            time_signature = str(context["time_signature"])

            # result = subprocess.call ([script_fullpath, midi_filename, grammar_file, outfile, bar_duration, bar_metric_denominator, time_signature])
            # l'appel ci-dessus ne fonctionne pas, à débugger avec Francesco

            # on continue, avec un faux mei
            # /home/raph/Enseignement/vertigo_svn/scorelib/app/media/corpora/transcriptions//beethoven_trio_midi_quant.mei
            outfile = "/home/raph/Enseignement/vertigo_svn/scorelib/app/media/corpora/transcriptions/beethoven_trio_midi_quant.mei"
            with open(outfile, "r") as new_mei:
                transcribed_opus = TranscribedOpus(context["opus"], new_mei)
            context["transcribed_opus"] = transcribed_opus

        return render(request, "transcription/result.html", context=context)

