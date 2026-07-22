from django.urls import path
from .views import AlertListView, AlertAcknowledgeView, AlertResolveView

app_name = 'alerts'

urlpatterns = [
    path('alerts/', AlertListView.as_view(), name='alert-list'),
    path('alerts/<int:pk>/acknowledge/', AlertAcknowledgeView.as_view(), name='alert-acknowledge'),
    path('alerts/<int:pk>/resolve/', AlertResolveView.as_view(), name='alert-resolve'),
]
