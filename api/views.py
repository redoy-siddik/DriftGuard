from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg, Max, Count
from apps.cluster.models import GPUNode
from apps.alerts.models import Alert
from apps.detection.models import DriftScore, IsolationForestModel
from apps.telemetry.models import TelemetrySnapshot
from .serializers import DashboardSummarySerializer
from apps.cluster.serializers import GPUNodeListSerializer


class DashboardSummaryView(APIView):
    def get(self, request):
        total_nodes = GPUNode.objects.count()
        nodes_normal = GPUNode.objects.filter(current_status='normal').count()
        nodes_warning = GPUNode.objects.filter(current_status='warning').count()
        nodes_critical = GPUNode.objects.filter(current_status='critical').count()
        nodes_offline = GPUNode.objects.filter(current_status='offline').count()

        open_alerts = Alert.objects.filter(status='open').count()
        critical_alerts = Alert.objects.filter(status='open', severity='critical').count()
        warning_alerts = Alert.objects.filter(status='open', severity='warning').count()

        latest_score = DriftScore.objects.order_by('-computed_at').first()
        last_detection_run = latest_score.computed_at if latest_score else None

        avg_composite = DriftScore.objects.aggregate(Avg('composite_score'))['composite_score__avg'] or 0.0
        max_composite = DriftScore.objects.aggregate(Max('composite_score'))['composite_score__max'] or 0.0

        highest_risk_ds = DriftScore.objects.order_by('-composite_score').first()
        highest_risk_node = highest_risk_ds.node.node_id if highest_risk_ds else None

        if_models_trained = IsolationForestModel.objects.filter(status='trained').count()
        total_telemetry = TelemetrySnapshot.objects.count()

        active_nodes = GPUNode.objects.filter(is_active=True).count()
        nodes_with_scores = DriftScore.objects.values('node').distinct().count()
        detection_coverage = (nodes_with_scores / active_nodes * 100.0) if active_nodes > 0 else 0.0

        payload = {
            'total_nodes': total_nodes,
            'nodes_normal': nodes_normal,
            'nodes_warning': nodes_warning,
            'nodes_critical': nodes_critical,
            'nodes_offline': nodes_offline,
            'open_alerts': open_alerts,
            'critical_alerts': critical_alerts,
            'warning_alerts': warning_alerts,
            'last_detection_run': last_detection_run,
            'avg_composite_score': round(avg_composite, 2),
            'max_composite_score': round(max_composite, 2),
            'highest_risk_node': highest_risk_node,
            'if_models_trained': if_models_trained,
            'total_telemetry_snapshots': total_telemetry,
            'detection_coverage_pct': round(detection_coverage, 1),
        }

        serializer = DashboardSummarySerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClusterHealthView(APIView):
    def get(self, request):
        nodes = GPUNode.objects.all().order_by('node_id')
        node_data = []

        for node in nodes:
            latest_ds = node.latest_drift_score
            latest_telemetry = node.telemetry_snapshots.first()

            node_data.append({
                'node_id': node.node_id,
                'hostname': node.hostname,
                'gpu_model': node.gpu_model,
                'current_status': node.current_status,
                'is_active': node.is_active,
                'rack_id': node.rack_id,
                'datacenter': node.datacenter,
                'composite_score': latest_ds.composite_score if latest_ds else 0.0,
                'open_alerts': node.open_alert_count,
                'temperature_c': latest_telemetry.temperature_c if latest_telemetry else None,
                'utilization_pct': latest_telemetry.utilization_pct if latest_telemetry else None,
                'last_seen': node.last_seen
            })

        return Response({'nodes': node_data}, status=status.HTTP_200_OK)
