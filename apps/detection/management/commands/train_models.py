from django.core.management.base import BaseCommand
from apps.cluster.models import GPUNode
from apps.detection.isolation_forest import IsolationForestDetector


class Command(BaseCommand):
    help = 'Train scikit-learn Isolation Forest anomaly detection models per GPU node'

    def add_arguments(self, parser):
        parser.add_argument('--node', type=str, help='Specific node_id to train')

    def handle(self, *args, **options):
        node_id = options.get('node')

        if node_id:
            nodes = GPUNode.objects.filter(node_id=node_id, is_active=True)
            if not nodes.exists():
                self.stderr.write(self.style.ERROR(f"GPU node '{node_id}' not found or inactive."))
                return
        else:
            nodes = GPUNode.objects.filter(is_active=True)

        self.stdout.write(f"Training Isolation Forest models for {nodes.count()} GPU nodes...")

        trained_count = 0
        skipped_count = 0

        for node in nodes:
            detector = IsolationForestDetector(node)
            success = detector.train()
            if success:
                trained_count += 1
                self.stdout.write(self.style.SUCCESS(f"  [OK] Trained model for {node.node_id}"))
            else:
                skipped_count += 1
                self.stdout.write(self.style.WARNING(f"  [SKIP] {node.node_id} (insufficient telemetry samples)"))

        self.stdout.write(self.style.SUCCESS(
            f"Training finished: {trained_count} trained, {skipped_count} skipped."
        ))
