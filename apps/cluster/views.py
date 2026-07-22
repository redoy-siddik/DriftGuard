from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import GPUNode
from .serializers import GPUNodeListSerializer, GPUNodeDetailSerializer


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
