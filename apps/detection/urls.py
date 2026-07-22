from django.urls import path
from .views import (
    NodeDriftScoreListView,
    NodeBaselineStatsListView,
    DetectionRunView,
    DetectionTrainView
)

app_name = 'detection'

urlpatterns = [
    path('nodes/<str:node_id>/drift-scores/', NodeDriftScoreListView.as_view(), name='node-drift-scores'),
    path('nodes/<str:node_id>/baseline/', NodeBaselineStatsListView.as_view(), name='node-baseline'),
    path('detection/run/', DetectionRunView.as_view(), name='detection-run'),
    path('detection/train/', DetectionTrainView.as_view(), name='detection-train'),
]
