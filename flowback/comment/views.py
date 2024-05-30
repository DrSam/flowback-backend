# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from flowback.comment.selectors import comment_list
from flowback.comment.services import comment_create, comment_delete, comment_update
from flowback.common.pagination import LimitOffsetPagination, get_paginated_response
from flowback.comment.serializers import (CommentListOutputSerializer,
                                          CommentDetailOutputSerializer,
                                          CommentFilterSerializer,
                                          CommentCreateInputSerializer,
                                          CommentUpdateInputSerializer)


class CommentListAPI(APIView):
    lazy_action = comment_list

    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100



    def get(self, request, *args, **kwargs):
        serializer = CommentFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        comments = self.lazy_action.__func__(fetched_by=request.user,
                                             filters=serializer.validated_data,
                                             *args,
                                             **kwargs)

        return get_paginated_response(pagination_class=self.Pagination,
                                      serializer_class=CommentListOutputSerializer,
                                      queryset=comments,
                                      request=request,
                                      view=self)


class CommentDetailAPI(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100

    def get(self, request, *args, **kwargs):
        comment = self.lazy_action.__func__(fetched_by=request.user,
                                             filters=kwargs,
                                             *args,
                                             **kwargs)

        include_descendants = request.query_params.get('include_descendants', False)
        include_ancestors = request.query_params.get('include_ancestors', False)
        if not any([include_ancestors, include_descendants]):
            return Response(data=CommentDetailOutputSerializer(comment).data)

        elif all([include_descendants, include_ancestors]):
            return Response(
                data={"message": "Can only request one of `include_descendants` or `include_descendants` and not both."},
                status=status.HTTP_400_BAD_REQUEST)
        else:
            if include_descendants:
                replies = comment.descendants(include_self=True)
            elif include_ancestors:
                replies = comment.ancestors(include_self=True).extra(order_by=["-created_at"])
                # change the ordering so that the results does not cut out the comment we are fetching ancestors for
            return get_paginated_response(pagination_class=self.Pagination,
                                      serializer_class=CommentListOutputSerializer,
                                      queryset=replies,
                                      request=request,
                                      view=self)

class CommentCreateAPI(APIView):
    lazy_action = comment_create

    def post(self, request, *args, **kwargs):
        serializer = CommentCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = self.lazy_action.__func__(*args,
                                            author_id=request.user.id,
                                            **kwargs,
                                            **serializer.validated_data)

        return Response(status=status.HTTP_200_OK, data=comment.id)


class CommentUpdateAPI(APIView):
    lazy_action = comment_update

    def post(self, request, *args, **kwargs):
        serializer = CommentUpdateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.lazy_action.__func__(*args,
                                  **kwargs,
                                  fetched_by=request.user.id,
                                  data=serializer.validated_data)

        return Response(status=status.HTTP_200_OK)


class CommentDeleteAPI(APIView):
    lazy_action = comment_delete

    def post(self, request, *args, **kwargs):
        self.lazy_action.__func__(*args,
                                  **kwargs,
                                  fetched_by=request.user)

        return Response(status=status.HTTP_200_OK)
