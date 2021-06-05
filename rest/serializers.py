from rest_framework import serializers
from manager import models


class Annotation(serializers.ModelSerializer):
    class Meta:
        model = models.Annotation
        fields= ['id', 'analytic_concept']