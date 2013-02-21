from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserFile(models.Model):
    user=models.ForeignKey(User)
    Path=models.CharField(max_length=200)
    
class Job(models.Model):
    user=models.ForeignKey(User)
    status=models.CharField(max_length=20)
    ref_genome=models.CharField(max_length=10)
    cell_line=models.CharField(max_length=10)
    sampleFiles=models.TextField()
    controlFiles=models.TextField()
    submitDate=models.DateTimeField("date submitted")
    jobtitle=models.CharField(max_length=200)
    def __unicode__(self):
                return self.jobtitle
    
class PipelineJob(models.Model):
    user=models.ForeignKey(User)
    status=models.CharField(max_length=20)
    ref_genome=models.CharField(max_length=10)
    cell_line=models.CharField(max_length=10)
    sampleFiles=models.TextField()
    controlFiles=models.TextField()
    submitDate=models.DateTimeField("date submitted")
    jobtitle=models.CharField(max_length=200)
    def __unicode__(self):
                return self.jobtitle
