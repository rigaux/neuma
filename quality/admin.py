from django.contrib import admin

from guardian.admin import GuardedModelAdmin

from .models import QtDimension, QtMetric, QtMeasure

admin.site.register(QtDimension)
admin.site.register(QtMetric)
admin.site.register(QtMeasure)