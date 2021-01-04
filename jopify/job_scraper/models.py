from django.db import models
from django.contrib.postgres.fields import ArrayField


class Job(models.Model):
    url = models.CharField(max_length=255, unique=True)
    company_name = models.CharField(max_length=100, null=True)
    job_title = models.CharField(max_length=100, null=True)
    location = models.CharField(max_length=100, null=True)
    language = ArrayField(models.CharField(max_length=50), null=True)
    framework = ArrayField(models.CharField(max_length=50), null=True)
    database = ArrayField(models.CharField(max_length=50), null=True)
    tool = ArrayField(models.CharField(max_length=50), null=True)

    date_created = models.DateField(auto_now_add=True)

