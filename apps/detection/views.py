from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from apps.cluster.models import GPUNode
from .models import DriftScore, BaselineStats
from .serializers import DriftScoreSerializer, BaselineStatsSerializer
from .engine import run_detection_all_nodes
from .isolation_forest import IsolationForestDetector


class NodeDriftScoreListView(generics.ListAPIView):
    serializer_class = DriftScoreSerializer

    def get_queryset(self):
        node_id = self.kwargs.get('node_id')
        node = get_object_or_404(GPUNode, node_id=node_id)
        hours = int(self.request.query_params.get('hours', 48))

        cutoff = timezone.now() - timedelta(hours=hours)
        return DriftScore.objects.filter(node=node, computed_at__gte=cutoff).order_by('computed_at')


class NodeBaselineStatsListView(generics.ListAPIView):
    serializer_class = BaselineStatsSerializer

    def get_queryset(self):
        node_id = self.kwargs.get('node_id')
        node = get_object_or_404(GPUNode, node_id=node_id)
        return BaselineStats.objects.filter(node=node)


class DetectionRunView(APIView):
    def post(self, request):
        results = run_detection_all_nodes()
        return Response({
            'message': 'Detection pipeline executed successfully',
            'processed': results['processed'],
            'results': results['results'],
            'errors': results['errors']
        }, status=status.HTTP_200_OK)


class DetectionTrainView(APIView):
    def post(self, request):
        node_id = request.data.get('node_id')
        if node_id:
            node = get_object_or_404(GPUNode, node_id=node_id)
            detector = IsolationForestDetector(node)
            success = detector.train()
            return Response({
                'node_id': node_id,
                'trained': success,
                'message': 'Model trained successfully' if success else 'Insufficient samples to train model'
            }, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)

        # Train all active nodes
        nodes = GPUNode.objects.filter(is_active=True)
        trained = []
        skipped = []
        for n in nodes:
            det = IsolationForestDetector(n)
            if det.train():
                trained.append(n.node_id)
            else:
                skipped.append(n.node_id)

        return Response({
            'message': 'Training pass completed',
            'trained_nodes': trained,
            'skipped_nodes': skipped
        }, status=status.HTTP_200_OK)
