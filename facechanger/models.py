from django.db import models


class MyModel(models.Model):
    original_model = models.ImageField()
    faceselected_model = models.TextField()
    faceshuffled_model = models.ImageField()