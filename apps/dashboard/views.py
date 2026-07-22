import json
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from apps.cluster.models import GPUNode
from apps.alerts.models import Alert
from apps.detection.models import DriftScore, IsolationForestModel
from apps.telemetry.models import TelemetrySnapshot


def _global_context():
    """Shared context data injected into every dashboard view (navbar + sidebar)."""
    open_alerts = Alert.objects.filter(status='open').count()
    latest_score = DriftScore.objects.order_by('-computed_at').first()
    last_detection_run = latest_score.computed_at if latest_score else None
    return {
        'open_alerts': open_alerts,
        'last_detection_run': last_detection_run,
    }


class DashboardIndexView(TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_global_context())

        total_nodes = GPUNode.objects.count()
        nodes_normal = GPUNode.objects.filter(current_status='normal').count()
        nodes_warning = GPUNode.objects.filter(current_status='warning').count()
        nodes_critical = GPUNode.objects.filter(current_status='critical').count()
        nodes_offline = GPUNode.objects.filter(current_status='offline').count()

        critical_alerts = Alert.objects.filter(status='open', severity='critical').count()
        warning_alerts = Alert.objects.filter(status='open', severity='warning').count()

        recent_alerts = Alert.objects.select_related('node').order_by('-triggered_at')[:10]
        nodes = GPUNode.objects.all().order_by('node_id')

        context.update({
            'total_nodes': total_nodes,
            'nodes_normal': nodes_normal,
            'nodes_warning': nodes_warning,
            'nodes_critical': nodes_critical,
            'nodes_offline': nodes_offline,
            'critical_alerts': critical_alerts,
            'warning_alerts': warning_alerts,
            'recent_alerts': recent_alerts,
            'nodes': nodes,
        })
        return context


class NodeDetailView(TemplateView):
    template_name = 'dashboard/node_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_global_context())

        node_id = self.kwargs.get('node_id')
        node = get_object_or_404(GPUNode, node_id=node_id)

        cutoff = timezone.now() - timedelta(hours=48)
        drift_scores = DriftScore.objects.filter(node=node, computed_at__gte=cutoff).order_by('computed_at')

        chart_data = {
            'labels': [ds.computed_at.strftime('%m-%d %H:%M') for ds in drift_scores],
            'composite_scores': [ds.composite_score for ds in drift_scores],
            'z_scores': [ds.zscore_composite for ds in drift_scores],
            'if_scores': [ds.if_anomaly_score if ds.if_anomaly_score is not None else 0 for ds in drift_scores],
            'statuses': [ds.status for ds in drift_scores]
        }

        try:
            if_model = node.isolation_forest_model
            if_status = if_model.status
        except IsolationForestModel.DoesNotExist:
            if_status = 'not_trained'

        alerts = Alert.objects.filter(node=node).order_by('-triggered_at')[:15]

        context.update({
            'node': node,
            'if_status': if_status,
            'chart_data_json': json.dumps(chart_data),
            'alerts': alerts,
        })
        return context


class AlertsView(TemplateView):
    template_name = 'dashboard/alerts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_global_context())

        alerts = Alert.objects.select_related('node', 'drift_score').order_by('-triggered_at')
        nodes = GPUNode.objects.all().order_by('node_id')

        context.update({
            'alerts': alerts,
            'nodes': nodes,
            'status_choices': Alert.STATUS_CHOICES,
            'severity_choices': Alert.SEVERITY_CHOICES,
        })
        return context
