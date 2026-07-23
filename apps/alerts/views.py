from rest_framework import generics, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Alert
from .serializers import AlertSerializer, AlertAcknowledgeSerializer, AlertResolveSerializer


class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Alert CRUD, registered with DefaultRouter."""
    serializer_class = AlertSerializer
    queryset = Alert.objects.select_related('node', 'drift_score').order_by('-triggered_at')

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        severity_param = self.request.query_params.get('severity')
        node_param = self.request.query_params.get('node')
        if status_param:
            qs = qs.filter(status=status_param)
        if severity_param:
            qs = qs.filter(severity=severity_param)
        if node_param:
            qs = qs.filter(node__node_id=node_param)
        return qs

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        serializer = AlertAcknowledgeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        alert.status = 'acknowledged'
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = serializer.validated_data.get('acknowledged_by', 'ops-team')
        alert.save()
        return Response(AlertSerializer(alert).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        alert = self.get_object()
        serializer = AlertResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.resolution_note = serializer.validated_data.get('resolution_note', '')
        alert.save()
        return Response(AlertSerializer(alert).data, status=status.HTTP_200_OK)


class AlertListView(generics.ListAPIView):
    serializer_class = AlertSerializer

    def get_queryset(self):
        qs = Alert.objects.select_related('node', 'drift_score').all()
        status_param = self.request.query_params.get('status')
        severity_param = self.request.query_params.get('severity')
        node_param = self.request.query_params.get('node')

        if status_param:
            qs = qs.filter(status=status_param)
        if severity_param:
            qs = qs.filter(severity=severity_param)
        if node_param:
            qs = qs.filter(node__node_id=node_param)

        return qs


class AlertAcknowledgeView(APIView):
    def post(self, request, pk):
        alert = get_object_or_404(Alert, pk=pk)
        serializer = AlertAcknowledgeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        alert.status = 'acknowledged'
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = serializer.validated_data.get('acknowledged_by', 'ops-team')
        alert.save()

        return Response(AlertSerializer(alert).data, status=status.HTTP_200_OK)


class AlertResolveView(APIView):
    def post(self, request, pk):
        alert = get_object_or_404(Alert, pk=pk)
        serializer = AlertResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.resolution_note = serializer.validated_data.get('resolution_note', '')
        alert.save()

        return Response(AlertSerializer(alert).data, status=status.HTTP_200_OK)
