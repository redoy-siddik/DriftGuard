from django.urls import path, include
from api.views import DashboardSummaryView, ClusterHealthView

app_name = 'api'

urlpatterns = [
    # Cluster Endpoints
    path('', include('apps.cluster.urls')),

    # Telemetry Endpoints
    path('', include('apps.telemetry.urls')),

    # Detection Endpoints
    path('', include('apps.detection.urls')),

    # Alert Endpoints
    path('', include('apps.alerts.urls')),

    # Dashboard Aggregations
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('dashboard/cluster-health/', ClusterHealthView.as_view(), name='dashboard-cluster-health'),
]
