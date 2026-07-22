from django.urls import path
from .views import GPUNodeListView, GPUNodeDetailView, GPUNodeToggleActiveView

app_name = 'cluster'

urlpatterns = [
    path('nodes/', GPUNodeListView.as_view(), name='node-list'),
    path('nodes/<str:node_id>/', GPUNodeDetailView.as_view(), name='node-detail'),
    path('nodes/<str:node_id>/toggle-active/', GPUNodeToggleActiveView.as_view(), name='node-toggle-active'),
]
