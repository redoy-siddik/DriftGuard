from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.cluster.models import GPUNode
from apps.telemetry.models import TelemetrySnapshot
from apps.detection.engine import DriftDetectionEngine
from apps.detection.isolation_forest import IsolationForestDetector

class DetectionEngineTest(TestCase):
    def setUp(self):
        self.node = GPUNode.objects.create(
            node_id='test-gpu-02',
            hostname='test-host-02',
            gpu_model='NVIDIA H100 80GB HBM3',
            total_memory_gb=80.0
        )
        # Create baseline snapshots
        now = timezone.now()
        snapshots = []
        for i in range(220):
            snapshots.append(TelemetrySnapshot(
                node=self.node,
                timestamp=now - timedelta(minutes=5 * (220 - i)),
                utilization_pct=50.0 + (i % 5),
                memory_used_gb=40.0 + (i % 2),
                temperature_c=65.0 + (i % 3),
                power_draw_w=300.0 + (i % 10),
                ecc_errors=0,
                fan_speed_pct=50.0,
                sm_clock_mhz=1410
            ))
        TelemetrySnapshot.objects.bulk_create(snapshots)

    def test_isolation_forest_training_and_detection(self):
        detector = IsolationForestDetector(self.node)
        trained = detector.train()
        self.assertTrue(trained)

        engine = DriftDetectionEngine(self.node)
        drift_score = engine.run()
        self.assertIsNotNone(drift_score)
        self.assertIn(drift_score.status, ['normal', 'warning', 'critical'])
