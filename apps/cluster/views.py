from rest_framework import generics, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import GPUNode
from .serializers import GPUNodeListSerializer, GPUNodeDetailSerializer


class GPUNodeViewSet(viewsets.ModelViewSet):
    """ViewSet for GPUNode CRUD, registered with DefaultRouter."""
    queryset = GPUNode.objects.all().order_by('node_id')
    lookup_field = 'node_id'

    def get_serializer_class(self):
        if self.action == 'list':
            return GPUNodeListSerializer
        return GPUNodeDetailSerializer

    @action(detail=True, methods=['put'])
    def toggle_active(self, request, node_id=None):
        node = self.get_object()
        node.is_active = not node.is_active
        node.save()
        serializer = GPUNodeDetailSerializer(node)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GPUNodeListView(generics.ListCreateAPIView):
    queryset = GPUNode.objects.all()
    serializer_class = GPUNodeListSerializer


class GPUNodeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GPUNode.objects.all()
    serializer_class = GPUNodeDetailSerializer
    lookup_field = 'node_id'


class GPUNodeToggleActiveView(APIView):
    def put(self, request, node_id):
        node = get_object_or_404(GPUNode, node_id=node_id)
        node.is_active = not node.is_active
        node.save()
        serializer = GPUNodeDetailSerializer(node)
        return Response(serializer.data, status=status.HTTP_200_OK)
