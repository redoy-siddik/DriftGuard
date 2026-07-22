from django.core.management.base import BaseCommand
from apps.cluster.models import GPUNode
from apps.detection.engine import DriftDetectionEngine, run_detection_all_nodes


class Command(BaseCommand):
    help = 'Run two-layer AI drift detection engine on active GPU telemetry'

    def add_arguments(self, parser):
        parser.add_argument('--node', type=str, help='Specific GPU node_id to evaluate')

    def handle(self, *args, **options):
        node_id = options.get('node')

        if node_id:
            try:
                node = GPUNode.objects.get(node_id=node_id, is_active=True)
                engine = DriftDetectionEngine(node)
                score = engine.run()
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully ran detection for {node.node_id}: "
                    f"composite_score={score.composite_score:.2f}, status={score.status}"
                ))
            except GPUNode.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Active GPU node '{node_id}' not found."))
        else:
            self.stdout.write("Running detection pipeline across all active GPU nodes...")
            results = run_detection_all_nodes()
            self.stdout.write(self.style.SUCCESS(
                f"Completed detection run for {results['processed']} nodes. "
                f"Errors: {len(results['errors'])}"
            ))
            for nid, status in results['results'].items():
                color = self.style.SUCCESS if status == 'normal' else (self.style.WARNING if status == 'warning' else self.style.ERROR)
                self.stdout.write(color(f"  Node {nid}: {status}"))
