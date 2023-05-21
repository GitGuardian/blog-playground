from rest_framework.filters import OrderingFilter

from .filtered import FilteredListReviewsView


class CompleteListReviewsView(FilteredListReviewsView):
    filter_backends = FilteredListReviewsView.filter_backends + (OrderingFilter,)
    ordering_fields = ["written_at", "id", "rating"]
    ordering = ["written_at"]
