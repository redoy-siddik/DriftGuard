import logging
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from apps.cluster.models import GPUNode
from apps.detection.models import DriftScore, IsolationForestModel
from apps.alerts.models import Alert
from apps.telemetry.models import TelemetrySnapshot

logger = logging.getLogger(__name__)


class DashboardIndexView(TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        nodes = GPUNode.objects.filter(is_active=True)

        ctx['summary'] = {
            'total_nodes':    nodes.count(),
            'nodes_normal':   nodes.filter(current_status='normal').count(),
            'nodes_warning':  nodes.filter(current_status='warning').count(),
            'nodes_critical': nodes.filter(current_status='critical').count(),
            'nodes_offline':  nodes.filter(current_status='offline').count(),
            'open_alerts':    Alert.objects.filter(status='open').count(),
            'critical_alerts':Alert.objects.filter(status='open', severity='critical').count(),
            'warning_alerts': Alert.objects.filter(status='open', severity='warning').count(),
            'if_models_trained': IsolationForestModel.objects.filter(status='trained').count(),
            'total_snapshots':   TelemetrySnapshot.objects.count(),
        }

        ctx['nodes'] = nodes.prefetch_related('drift_scores', 'alerts')
        ctx['recent_alerts'] = (
            Alert.objects
            .select_related('node')
            .filter(status='open')
            .order_by('-triggered_at')[:10]
        )
        return ctx


class NodeDetailView(TemplateView):
    template_name = 'dashboard/node_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        node = get_object_or_404(GPUNode, node_id=kwargs['node_id'])
        since = timezone.now() - timedelta(hours=48)

        # Drift score history as list of dicts for Chart.js
        drift_history = list(
            DriftScore.objects
            .filter(node=node, computed_at__gte=since)
            .order_by('computed_at')
            .values(
                'computed_at', 'composite_score',
                'z_temperature', 'z_power', 'z_ecc',
                'if_is_anomaly', 'status'
            )
        )

        # Telemetry history as list of dicts for Chart.js
        telemetry_history = list(
            TelemetrySnapshot.objects
            .filter(node=node, timestamp__gte=since)
            .order_by('timestamp')
            .values(
                'timestamp', 'utilization_pct', 'temperature_c',
                'power_draw_w', 'memory_used_gb', 'ecc_errors'
            )
        )

        # IF model status
        try:
            if_model = IsolationForestModel.objects.get(node=node)
        except IsolationForestModel.DoesNotExist:
            if_model = None

        ctx.update({
            'node': node,
            'if_model': if_model,
            'drift_history': drift_history,
            'telemetry_history': telemetry_history,
            'alert_history': (
                Alert.objects
                .filter(node=node)
                .order_by('-triggered_at')[:20]
            ),
            'latest_drift': DriftScore.objects.filter(node=node).first(),
            'latest_telemetry': TelemetrySnapshot.objects.filter(node=node).first(),
        })
        return ctx


class AlertsView(TemplateView):
    template_name = 'dashboard/alerts.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = Alert.objects.select_related('node').order_by('-triggered_at')

        status_filter   = self.request.GET.get('status')
        severity_filter = self.request.GET.get('severity')
        node_filter     = self.request.GET.get('node')

        if status_filter:
            qs = qs.filter(status=status_filter)
        if severity_filter:
            qs = qs.filter(severity=severity_filter)
        if node_filter:
            qs = qs.filter(node__node_id__icontains=node_filter)

        ctx.update({
            'alerts': qs[:200],
            'status_choices':   Alert.STATUS_CHOICES,
            'severity_choices': Alert.SEVERITY_CHOICES,
            'active_filters': {
                'status': status_filter,
                'severity': severity_filter,
                'node': node_filter,
            },
            'summary': {
                'open':         Alert.objects.filter(status='open').count(),
                'acknowledged': Alert.objects.filter(status='acknowledged').count(),
                'resolved':     Alert.objects.filter(status='resolved').count(),
            }
        })
        return ctx


class UnifiedMetricsView(TemplateView):
    """
    Consolidated metrics view at /metrics/ — aggregates across
    telemetry, alerts, detection, and cluster for a single-page ops overview.
    """
    template_name = 'dashboard/metrics.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d  = now - timedelta(days=7)

        nodes = GPUNode.objects.filter(is_active=True)

        ctx['metrics'] = {
            # Cluster
            'cluster': {
                'total_nodes':    nodes.count(),
                'active_nodes':   nodes.filter(is_active=True).count(),
                'status_breakdown': {
                    s: nodes.filter(current_status=s).count()
                    for s in ['normal', 'warning', 'critical', 'offline']
                },
            },
            # Telemetry
            'telemetry': {
                'total_snapshots':    TelemetrySnapshot.objects.count(),
                'snapshots_24h':      TelemetrySnapshot.objects.filter(timestamp__gte=last_24h).count(),
                'injected_failures':  TelemetrySnapshot.objects.filter(is_injected_failure=True).count(),
            },
            # Detection
            'detection': {
                'total_scores':      DriftScore.objects.count(),
                'scores_24h':        DriftScore.objects.filter(computed_at__gte=last_24h).count(),
                'if_models_trained': IsolationForestModel.objects.filter(status='trained').count(),
                'status_breakdown_7d': {
                    s: DriftScore.objects.filter(
                        status=s, computed_at__gte=last_7d
                    ).count()
                    for s in ['normal', 'warning', 'critical']
                },
            },
            # Alerts
            'alerts': {
                'open':             Alert.objects.filter(status='open').count(),
                'acknowledged':     Alert.objects.filter(status='acknowledged').count(),
                'resolved':         Alert.objects.filter(status='resolved').count(),
                'critical_open':    Alert.objects.filter(status='open', severity='critical').count(),
                'triggered_24h':    Alert.objects.filter(triggered_at__gte=last_24h).count(),
                'resolved_7d':      Alert.objects.filter(
                    status='resolved', resolved_at__gte=last_7d
                ).count(),
            },
        }
        return ctx
