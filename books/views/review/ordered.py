from rest_framework.filters import OrderingFilter

from .simple import ListReviewsView


class OrderedListReviewsView(ListReviewsView):
    filter_backends = (OrderingFilter,)
    ordering_fields = ["written_at", "id", "rating"]
    ordering = ["written_at"]
