from math import sqrt

from django.db import models
from django.db.models import Q, Count
from django.db.models.signals import post_save, post_delete
from tree_queries.models import TreeNode

from flowback.common.models import BaseModel
from flowback.files.models import FileCollection
from flowback.user.models import User


class CommentSection(BaseModel):
    active = models.BooleanField(default=True)


class Comment(BaseModel, TreeNode):
    comment_section = models.ForeignKey(CommentSection, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(max_length=10000, null=True, blank=True)
    attachments = models.ForeignKey(FileCollection, on_delete=models.SET_NULL, null=True, blank=True)
    edited = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    score = models.DecimalField(default=0, max_digits=17, decimal_places=10)

    class Meta:
        constraints = [models.CheckConstraint(check=Q(attachments__isnull=False) | Q(message__isnull=False),
                                              name='temp_comment_data_check')]


class CommentVote(BaseModel):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    vote = models.BooleanField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['comment', 'created_by'], name='comment_vote_unique')]
