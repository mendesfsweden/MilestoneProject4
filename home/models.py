from django.db import models
from checkout.models import UserProfile


class Review(models.Model):
    text = models.CharField(max_length=250, null=False, editable=False)
    user_profile = models.ForeignKey(UserProfile, on_delete=models.SET_NULL,
                                     null=True, blank=True,
                                     related_name='reviews')

    def __str__(self):
        return self.text
