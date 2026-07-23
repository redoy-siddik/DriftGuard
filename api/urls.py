from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.cluster.views import GPUNodeViewSet
from apps.telemetry.views import TelemetrySnapshotViewSet
from apps.alerts.views import AlertViewSet
from apps.detection.views import (
    DetectionRunView,
    TrainModelsView,
    DriftScoreListView,
    BaselineStatsView,
    RealtimePredictionView,
)
from api.views import DashboardSummaryView, ClusterHealthView

router = DefaultRouter(trailing_slash=False)
router.register(r'nodes', GPUNodeViewSet, basename='node')
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'telemetry', TelemetrySnapshotViewSet, basename='telemetry')

urlpatterns = [
    # Auto-registered CRUD routes
    path('', include(router.urls)),

    # Detection
    path('detection/run',         DetectionRunView.as_view(),         name='detection-run'),
    path('detection/train',       TrainModelsView.as_view(),           name='detection-train'),
    path('detection/predict/<str:node_id>', RealtimePredictionView.as_view(), name='detection-predict'),

    # Per-node sub-resources
    path('nodes/<str:node_id>/telemetry',    TelemetrySnapshotViewSet.as_view({'get': 'by_node'}),  name='node-telemetry'),
    path('nodes/<str:node_id>/drift-scores', DriftScoreListView.as_view(),                          name='node-drift-scores'),
    path('nodes/<str:node_id>/baseline',     BaselineStatsView.as_view(),                           name='node-baseline'),

    # Alert actions
    path('alerts/<int:pk>/acknowledge', AlertViewSet.as_view({'post': 'acknowledge'}), name='alert-acknowledge'),
    path('alerts/<int:pk>/resolve',     AlertViewSet.as_view({'post': 'resolve'}),     name='alert-resolve'),

    # Dashboard aggregations
    path('dashboard/summary',        DashboardSummaryView.as_view(),  name='dashboard-summary'),
    path('dashboard/cluster-health', ClusterHealthView.as_view(),     name='cluster-health'),

    # Telemetry generation
    path('telemetry/generate', TelemetrySnapshotViewSet.as_view({'post': 'generate'}), name='telemetry-generate'),
]
