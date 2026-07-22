from django.urls import path
from .views import NodeTelemetryListView, TelemetryGenerateView

app_name = 'telemetry'

urlpatterns = [
    path('nodes/<str:node_id>/telemetry/', NodeTelemetryListView.as_view(), name='node-telemetry'),
    path('telemetry/generate/', TelemetryGenerateView.as_view(), name='telemetry-generate'),
]
