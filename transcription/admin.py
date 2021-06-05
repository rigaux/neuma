from django.contrib import admin

from .models import Grammar, GrammarRule

# Register your models here.
admin.site.register(Grammar)
admin.site.register(GrammarRule)