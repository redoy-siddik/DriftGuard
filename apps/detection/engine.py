import logging
from django.utils import timezone
from apps.cluster.models import GPUNode
from apps.detection.models import DriftScore
from apps.alerts.models import Alert
from apps.detection.zscore import ZScoreDriftDetector
from apps.detection.isolation_forest import IsolationForestDetector

logger = logging.getLogger(__name__)


class DriftDetectionEngine:
    def __init__(self, node):
        self.node = node

    def run(self):
        # 1. Z-Score Layer
        z_detector = ZScoreDriftDetector(self.node)
        z_res = z_detector.run()

        z_scores = z_res['z_scores']
        zscore_composite = z_res['composite_score']
        current_df = z_res['df']

        window_start = z_res['window_start'] or timezone.now()
        window_end = z_res['window_end'] or timezone.now()

        # 2. Isolation Forest Layer
        if_detector = IsolationForestDetector(self.node)
        if_is_anomaly, if_anomaly_score = if_detector.predict(current_df)

        # 3. Score Fusion
        fused_score = self._fuse_scores(zscore_composite, if_is_anomaly)

        # 4. Reclassify
        if fused_score >= 3.5:
            final_status = 'critical'
        elif fused_score >= 2.0:
            final_status = 'warning'
        else:
            final_status = 'normal'

        # 5. Save DriftScore record
        drift_score = DriftScore.objects.create(
            node=self.node,
            window_start=window_start,
            window_end=window_end,
            z_utilization=z_scores.get('utilization_pct', 0.0),
            z_temperature=z_scores.get('temperature_c', 0.0),
            z_power=z_scores.get('power_draw_w', 0.0),
            z_memory=z_scores.get('memory_used_gb', 0.0),
            z_ecc=z_scores.get('ecc_errors', 0.0),
            zscore_composite=zscore_composite,
            if_anomaly_score=if_anomaly_score,
            if_is_anomaly=if_is_anomaly,
            composite_score=fused_score,
            status=final_status
        )

        # 6. Update GPUNode status
        self._update_node_status(final_status)

        # 7. Maybe create Alert
        self._maybe_create_alert(drift_score, final_status, z_scores, if_is_anomaly)

        return drift_score

    def _fuse_scores(self, zscore_composite, if_is_anomaly):
        if if_is_anomaly is None:
            return zscore_composite

        if_penalty = 2.5 if if_is_anomaly else 0.0
        fused = 0.7 * zscore_composite + 0.3 * if_penalty
        return float(fused)

    def _update_node_status(self, status):
        self.node.current_status = status
        self.node.save(update_fields=['current_status', 'updated_at'])

    def _maybe_create_alert(self, drift_score, status, z_scores, if_is_anomaly):
        if status in ['warning', 'critical']:
            open_alerts = Alert.objects.filter(node=self.node, status='open')
            if not open_alerts.exists():
                message = self._build_alert_message(drift_score, z_scores, if_is_anomaly)
                Alert.objects.create(
                    node=self.node,
                    drift_score=drift_score,
                    severity=status,
                    status='open',
                    message=message
                )

    def _build_alert_message(self, drift_score, z_scores, if_is_anomaly):
        # Identify top metric contributing to z-score
        max_metric = max(z_scores.items(), key=lambda x: abs(x[1])) if z_scores else ('temperature_c', 0.0)
        m_name, m_z = max_metric

        if_note = " Isolation Forest confirms multi-variate anomaly." if if_is_anomaly else ""

        return (
            f"GPU {self.node.node_id}: {m_name} z-score {m_z:.2f} "
            f"({drift_score.status.upper()}) with composite drift score {drift_score.composite_score:.2f}."
            f"{if_note} Immediate inspection recommended."
        )


def run_detection_all_nodes():
    nodes = GPUNode.objects.filter(is_active=True)
    processed = 0
    results = {}
    errors = {}

    for node in nodes:
        try:
            engine = DriftDetectionEngine(node)
            score = engine.run()
            results[node.node_id] = score.status
            processed += 1
        except Exception as e:
            logger.exception(f"Error running detection engine for node {node.node_id}: {e}")
            errors[node.node_id] = str(e)

    return {
        'processed': processed,
        'results': results,
        'errors': errors
    }
