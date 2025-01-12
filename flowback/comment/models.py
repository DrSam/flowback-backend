from django.db import models
from flowback.common.models import BaseModel
from flowback.user.models import User


class CommentSection(BaseModel):
    active = models.BooleanField(default=True)


class Comment(BaseModel):
    comment_section = models.ForeignKey(CommentSection, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(max_length=10000)
    edited = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    score = models.IntegerField(default=0)
