from django.urls import path
from .views import DashboardIndexView, NodeDetailView, AlertsView

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardIndexView.as_view(), name='index'),
    path('nodes/<str:node_id>/', NodeDetailView.as_view(), name='node_detail'),
    path('alerts/', AlertsView.as_view(), name='alerts'),
]
