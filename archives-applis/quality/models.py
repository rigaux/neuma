from __future__ import unicode_literals

from django.db import models
from manager.models import Opus

# QtDimension, eg. "Completeness" 
class QtDimension(models.Model):
    ref = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(null=True)

    def __str__(self):
       return 'Dimension (%s)' % (self.ref)

    class Meta:
         db_table = "QtDimension"
         
# QtMetric eg. "number of missing meta-data fields"
# referencing a dimension
class QtMetric(models.Model):
    ref = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(null=True)
    dimension = models.ForeignKey(QtDimension, null=True,on_delete=models.PROTECT) 

    def __str__(self):
       return 'Metric (%s)' % (self.ref)

    class Meta:
         db_table = "QtMetric"

# A QtMeasure object is the measurement of a metric for an opus
class QtMeasure(models.Model):
    opus = models.ForeignKey(Opus,on_delete=models.PROTECT)
    metric = models.ForeignKey(QtMetric,on_delete=models.PROTECT)
    value = models.FloatField()
    date = models.DateTimeField('Updated', auto_now=True)
    
    def __str__(self):
        return 'QtMeasure(%s,%s,%f)' % (self.opus.title,self.metric.ref, self.value)
    
    class Meta:
         unique_together = ('opus','metric')
         db_table = "QtMeasure"

# A QtProfile assigns a set of (QtMetric,QtExpectedValue) of a usage
class QtProfile(models.Model):
    usage = models.CharField(max_length=80)
    description = models.TextField(null=True)

    def __str__(self):
        return self.usage

    class Meta:
         db_table = "QtProfile"

# An QtExpectedValue is the expected value of a metric, which is assigned
# to a usage in a QtProfile object
class QtExpectedValue(models.Model):
    metric = models.ForeignKey(QtMetric,on_delete=models.PROTECT)
    profile = models.ForeignKey(QtProfile,on_delete=models.PROTECT)
    expected_value = models.FloatField(null=True)

    def __str__(self):
        return 'QtExpectedValue(%s,%s,%f)' % (self.profile.usage,self.metric.ref,self.expected_value)

    class Meta:
         unique_together = ('metric','profile')
         db_table = "QtExpectedValue"
