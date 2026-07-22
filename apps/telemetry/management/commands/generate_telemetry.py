from django.core.management.base import BaseCommand
from apps.cluster.models import GPUNode
from apps.telemetry.models import TelemetrySnapshot
from apps.telemetry.generator import SyntheticTelemetryGenerator
import random


class Command(BaseCommand):
    help = 'Generate synthetic GPU telemetry data'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help='Days of telemetry data (default: 7)')
        parser.add_argument('--nodes', type=int, default=10, help='Number of GPU nodes to create/use (default: 10)')
        parser.add_argument('--interval', type=int, default=5, help='Telemetry interval in minutes (default: 5)')
        parser.add_argument('--drift-pct', type=float, default=0.2, help='Percentage of nodes with injected drift (default: 0.2)')
        parser.add_argument('--clear', action='store_true', help='Wipe all existing telemetry before generating')
        parser.add_argument('--gpu-model', type=str, default='NVIDIA A100 80GB', help='GPU model string')

    def handle(self, *args, **options):
        days = options['days']
        node_count = options['nodes']
        interval = options['interval']
        drift_pct = options['drift_pct']
        clear_existing = options['clear']
        gpu_model = options['gpu_model']

        if clear_existing:
            deleted, _ = TelemetrySnapshot.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Cleared {deleted} existing telemetry snapshots.'))

        # Ensure GPU nodes exist
        nodes = []
        for i in range(1, node_count + 1):
            node_id = f"gpu-node-{i:02d}"
            hostname = f"gpu-worker-{i:02d}.cluster.local"
            rack_id = f"RACK-{((i - 1) // 4) + 1:02d}"
            node, _ = GPUNode.objects.get_or_create(
                node_id=node_id,
                defaults={
                    'hostname': hostname,
                    'gpu_model': gpu_model,
                    'total_memory_gb': 80.0,
                    'rack_id': rack_id,
                    'datacenter': 'DC-01',
                    'is_active': True,
                    'current_status': 'normal',
                }
            )
            nodes.append(node)

        # Select drift nodes
        num_drift = max(1, int(len(nodes) * drift_pct))
        drift_nodes = random.sample(nodes, num_drift)
        drift_node_ids = [n.node_id for n in drift_nodes]

        self.stdout.write(
            f"Generating {days} days of telemetry for {len(nodes)} nodes "
            f"({len(drift_node_ids)} with injected drift: {', '.join(drift_node_ids)})..."
        )

        generator = SyntheticTelemetryGenerator(
            nodes=nodes,
            days=days,
            interval_minutes=interval,
            drift_node_ids=drift_node_ids
        )
        total_created = generator.generate()

        self.stdout.write(self.style.SUCCESS(
            f"Successfully generated {total_created} telemetry snapshots across {len(nodes)} GPU nodes!"
        ))
