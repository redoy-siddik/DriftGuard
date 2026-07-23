from rest_framework import generics, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from apps.cluster.models import GPUNode
from .models import TelemetrySnapshot
from .serializers import TelemetrySnapshotSerializer, TelemetryGenerateSerializer
from .generator import SyntheticTelemetryGenerator


class TelemetrySnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for TelemetrySnapshot, registered with DefaultRouter."""
    serializer_class = TelemetrySnapshotSerializer
    queryset = TelemetrySnapshot.objects.all().order_by('-timestamp')

    @action(detail=False, methods=['get'], url_path='by-node')
    def by_node(self, request, node_id=None):
        """GET /api/v1/nodes/<node_id>/telemetry"""
        node = get_object_or_404(GPUNode, node_id=node_id)
        hours = int(request.query_params.get('hours', 24))
        limit = int(request.query_params.get('limit', 288))
        cutoff = timezone.now() - timedelta(hours=hours)
        qs = TelemetrySnapshot.objects.filter(
            node=node, timestamp__gte=cutoff
        ).order_by('-timestamp')[:limit]
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """POST /api/v1/telemetry/generate"""
        serializer = TelemetryGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        days = serializer.validated_data['days']
        node_count = serializer.validated_data['nodes']
        drift_pct = serializer.validated_data['drift_pct']
        clear_existing = serializer.validated_data['clear']

        if clear_existing:
            TelemetrySnapshot.objects.all().delete()

        nodes = list(GPUNode.objects.filter(is_active=True)[:node_count])
        if len(nodes) < node_count:
            for i in range(len(nodes) + 1, node_count + 1):
                n, _ = GPUNode.objects.get_or_create(
                    node_id=f"gpu-node-{i:02d}",
                    defaults={
                        'hostname': f"gpu-worker-{i:02d}.cluster.local",
                        'gpu_model': 'NVIDIA A100 80GB',
                        'total_memory_gb': 80.0,
                        'rack_id': f"RACK-{((i - 1) // 4) + 1:02d}",
                        'datacenter': 'DC-01',
                    }
                )
                nodes.append(n)

        generator = SyntheticTelemetryGenerator(
            nodes=nodes,
            days=days,
            interval_minutes=5
        )
        total_created = generator.generate()

        return Response({
            'message': 'Telemetry generation completed',
            'created_snapshots': total_created,
            'node_count': len(nodes),
            'days': days
        }, status=status.HTTP_201_CREATED)


class NodeTelemetryListView(generics.ListAPIView):
    serializer_class = TelemetrySnapshotSerializer

    def get_queryset(self):
        node_id = self.kwargs.get('node_id')
        node = get_object_or_404(GPUNode, node_id=node_id)
        hours = int(self.request.query_params.get('hours', 24))
        limit = int(self.request.query_params.get('limit', 288))

        cutoff = timezone.now() - timedelta(hours=hours)
        qs = TelemetrySnapshot.objects.filter(node=node, timestamp__gte=cutoff).order_by('-timestamp')
        return qs[:limit]


class TelemetryGenerateView(APIView):
    def post(self, request):
        serializer = TelemetryGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        days = serializer.validated_data['days']
        node_count = serializer.validated_data['nodes']
        drift_pct = serializer.validated_data['drift_pct']
        clear_existing = serializer.validated_data['clear']

        if clear_existing:
            TelemetrySnapshot.objects.all().delete()

        # Ensure nodes exist
        nodes = list(GPUNode.objects.filter(is_active=True)[:node_count])
        if len(nodes) < node_count:
            for i in range(len(nodes) + 1, node_count + 1):
                n, _ = GPUNode.objects.get_or_create(
                    node_id=f"gpu-node-{i:02d}",
                    defaults={
                        'hostname': f"gpu-worker-{i:02d}.cluster.local",
                        'gpu_model': 'NVIDIA A100 80GB',
                        'total_memory_gb': 80.0,
                        'rack_id': f"RACK-{((i - 1) // 4) + 1:02d}",
                        'datacenter': 'DC-01',
                    }
                )
                nodes.append(n)

        generator = SyntheticTelemetryGenerator(
            nodes=nodes,
            days=days,
            interval_minutes=5
        )
        total_created = generator.generate()

        return Response({
            'message': 'Telemetry generation completed',
            'created_snapshots': total_created,
            'node_count': len(nodes),
            'days': days
        }, status=status.HTTP_201_CREATED)
