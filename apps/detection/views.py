from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
import pandas as pd

from apps.cluster.models import GPUNode
from .models import DriftScore, BaselineStats
from .serializers import DriftScoreSerializer, BaselineStatsSerializer, RealtimePredictionSerializer
from .engine import run_detection_all_nodes
from .isolation_forest import IsolationForestDetector
from .model_store import ModelStore


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


class RealtimePredictionView(APIView):
    """
    POST /api/v1/detection/predict/<node_id>/

    Accepts raw telemetry payload for a single GPU node and returns
    an immediate drift/anomaly prediction without storing to DB.

    Request body:
    {
        "utilization_pct": 78.3,
        "memory_used_gb": 42.1,
        "temperature_c": 81.5,
        "power_draw_w": 310.2,
        "ecc_errors": 0,
        "fan_speed_pct": 67.0,
        "sm_clock_mhz": 1380.0
    }

    Response:
    {
        "node_id": "gpu-node-07",
        "zscore_composite": 3.21,
        "z_scores": {
            "utilization_pct": 1.02,
            "temperature_c": 3.81,
            "power_draw_w": 2.44,
            "memory_used_gb": 0.88,
            "ecc_errors": 0.12
        },
        "if_is_anomaly": true,
        "if_anomaly_score": -0.183,
        "composite_score": 2.99,
        "status": "warning",
        "recommendation": "GPU temperature z-score elevated (3.81). Isolation Forest confirms anomaly. Monitor closely."
    }
    """

    def post(self, request, node_id):
        node = get_object_or_404(GPUNode, node_id=node_id, is_active=True)

        serializer = RealtimePredictionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': True, 'detail': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        payload = serializer.validated_data

        # Z-score against stored baseline
        from apps.detection.zscore import ZScoreDriftDetector
        from apps.detection.models import BaselineStats

        baselines = {
            b.metric_name: (b.rolling_mean, b.rolling_std)
            for b in BaselineStats.objects.filter(node=node)
        }

        if not baselines:
            return Response(
                {'error': True, 'detail': 'No baseline stats found for this node. Run detection first.'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        METRICS = ['utilization_pct', 'temperature_c', 'power_draw_w', 'memory_used_gb', 'ecc_errors']
        WEIGHTS = {
            'utilization_pct': 0.10,
            'temperature_c':   0.30,
            'power_draw_w':    0.25,
            'memory_used_gb':  0.10,
            'ecc_errors':      0.25,
        }

        z_scores = {}
        for metric in METRICS:
            if metric in baselines:
                mean, std = baselines[metric]
                std = std if std > 0.001 else 0.001
                z_scores[metric] = abs((payload[metric] - mean) / std)
            else:
                z_scores[metric] = 0.0

        zscore_composite = sum(
            z_scores[m] * WEIGHTS.get(m, 0) for m in z_scores
        )

        # Isolation Forest prediction
        if_is_anomaly = None
        if_score = None
        try:
            store = ModelStore(node)
            pipeline, db_model = store.load()
            if pipeline is not None:
                features = [payload.get(f, 0.0) for f in IsolationForestDetector.FEATURES]
                import numpy as np
                X = np.array(features).reshape(1, -1)
                pred = pipeline.predict(X)[0]
                if_score = float(pipeline.decision_function(X)[0])
                if_is_anomaly = bool(pred == -1)
        except Exception:
            pass

        # Fuse scores
        if_penalty = 2.5 if if_is_anomaly else 0.0
        if if_is_anomaly is not None:
            composite = 0.7 * zscore_composite + 0.3 * if_penalty
        else:
            composite = zscore_composite

        if composite >= 3.5:
            status_label = 'critical'
        elif composite >= 2.0:
            status_label = 'warning'
        else:
            status_label = 'normal'

        # Build human-readable recommendation
        top_metric = max(z_scores, key=z_scores.get)
        recommendation = self._build_recommendation(
            top_metric, z_scores[top_metric], if_is_anomaly, status_label
        )

        return Response({
            'node_id': node_id,
            'zscore_composite': round(zscore_composite, 4),
            'z_scores': {k: round(v, 4) for k, v in z_scores.items()},
            'if_is_anomaly': if_is_anomaly,
            'if_anomaly_score': round(if_score, 4) if if_score is not None else None,
            'composite_score': round(composite, 4),
            'status': status_label,
            'recommendation': recommendation,
        })

    def _build_recommendation(self, top_metric, top_z, if_is_anomaly, status):
        metric_labels = {
            'temperature_c': 'temperature',
            'power_draw_w': 'power draw',
            'ecc_errors': 'ECC error rate',
            'memory_used_gb': 'memory usage',
            'utilization_pct': 'GPU utilization',
        }
        label = metric_labels.get(top_metric, top_metric)
        msg = f"GPU {label} z-score elevated ({top_z:.2f})."
        if if_is_anomaly:
            msg += " Isolation Forest confirms anomaly."
        if status == 'critical':
            msg += " Immediate inspection recommended."
        elif status == 'warning':
            msg += " Monitor closely and prepare maintenance window."
        else:
            msg += " Within acceptable range."
        return msg


# Aliases for api/urls.py imports
TrainModelsView = DetectionTrainView
DriftScoreListView = NodeDriftScoreListView
BaselineStatsView = NodeBaselineStatsListView
