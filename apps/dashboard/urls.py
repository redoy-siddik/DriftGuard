from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardIndexView.as_view(), name='index'),
    path('nodes/<str:node_id>/', views.NodeDetailView.as_view(), name='node_detail'),
    path('alerts/', views.AlertsView.as_view(), name='alerts'),
    path('metrics/', views.UnifiedMetricsView.as_view(), name='metrics'),
]
