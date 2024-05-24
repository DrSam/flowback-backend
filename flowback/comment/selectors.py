import django_filters

from flowback.comment.models import Comment
from flowback.user.models import User


class BaseCommentFilter(django_filters.FilterSet):
    order_by = django_filters.OrderingFilter(
        fields=(('created_at', 'created_at_asc'),
                ('-created_at', 'created_at_desc'),
                ('total_replies', 'total_replies_asc'),
                ('-total_replies', 'total_replies_desc'),
                ('score', 'score_asc'),
                ('-score', 'score_desc'))
    )

    has_attachments = django_filters.BooleanFilter(method='has_attachments_filter')

    class Meta:
        model = Comment
        fields = dict(id=['exact'],
                      message=['icontains'],
                      author_id=['exact', 'in'],
                      parent_id=['exact'],
                      score=['gt', 'lt'])


# TODO group parents together
def comment_list(*, fetched_by: User, comment_section_id: int, comment_id=None, filters=None):
    filters = filters or {}

    qs = Comment.objects.filter(comment_section_id=comment_section_id).all()
    if comment_id:
        qs = qs.filter(id=comment_id)

    return BaseCommentFilter(filters, qs).qs
