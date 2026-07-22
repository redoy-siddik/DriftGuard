import random
import numpy as np
from datetime import timedelta
from django.utils import timezone
from apps.telemetry.models import TelemetrySnapshot


class SyntheticTelemetryGenerator:
    METRIC_DEFAULTS = {
        'utilization_pct': {'mean': 65.0, 'std': 12.0, 'min': 0.0,  'max': 100.0},
        'memory_used_gb':  {'mean': 38.0, 'std': 6.0,  'min': 0.0,  'max': 80.0},
        'temperature_c':   {'mean': 72.0, 'std': 3.0,  'min': 40.0, 'max': 95.0},
        'power_draw_w':    {'mean': 280.0,'std': 20.0, 'min': 80.0, 'max': 400.0},
        'ecc_errors':      {'mean': 0.1,  'std': 0.3,  'min': 0.0,  'max': 100.0},
        'fan_speed_pct':   {'mean': 55.0, 'std': 8.0,  'min': 20.0, 'max': 100.0},
        'sm_clock_mhz':    {'mean': 1350.0,'std':50.0, 'min': 800.0,'max': 1600.0},
    }
    DRIFT_RATES = {
        'temperature_c':  0.05,
        'power_draw_w':   0.30,
        'ecc_errors':     0.03,
        'memory_used_gb': 0.05,
        'utilization_pct': 0.02,
    }

    def __init__(self, nodes, days=7, interval_minutes=5, drift_node_ids=None):
        self.nodes = list(nodes)
        self.days = days
        self.interval_minutes = interval_minutes

        if drift_node_ids is not None:
            self.drift_node_ids = set(drift_node_ids)
        else:
            num_drift = max(1, int(len(self.nodes) * 0.2))
            drift_sample = random.sample(self.nodes, num_drift) if self.nodes else []
            self.drift_node_ids = {n.node_id for n in drift_sample}

    def generate(self):
        end_time = timezone.now()
        start_time = end_time - timedelta(days=self.days)
        total_steps = int((self.days * 24 * 60) / self.interval_minutes)

        all_snapshots = []
        created_count = 0

        for node in self.nodes:
            baselines = self._per_node_baseline(node)
            is_drift = node.node_id in self.drift_node_ids
            node_snapshots = self._generate_node_series(
                node=node,
                baselines=baselines,
                drift=is_drift,
                start_time=start_time,
                total_steps=total_steps
            )
            all_snapshots.extend(node_snapshots)

            # Update last_seen on node
            if node_snapshots:
                node.last_seen = node_snapshots[-1].timestamp
                node.save(update_fields=['last_seen'])

            if len(all_snapshots) >= 1000:
                TelemetrySnapshot.objects.bulk_create(all_snapshots, batch_size=1000)
                created_count += len(all_snapshots)
                all_snapshots = []

        if all_snapshots:
            TelemetrySnapshot.objects.bulk_create(all_snapshots, batch_size=1000)
            created_count += len(all_snapshots)

        return created_count

    def _per_node_baseline(self, node):
        baselines = {}
        for metric, conf in self.METRIC_DEFAULTS.items():
            # ±15% variation per node
            variation = random.uniform(-0.15, 0.15)
            adjusted_mean = conf['mean'] * (1.0 + variation)
            adjusted_std = conf['std'] * random.uniform(0.85, 1.15)
            baselines[metric] = {
                'mean': float(adjusted_mean),
                'std': float(adjusted_std),
                'min': conf['min'],
                'max': conf['max']
            }
        return baselines

    def _generate_node_series(self, node, baselines, drift, start_time, total_steps):
        snapshots = []
        drift_start_step = random.randint(int(total_steps * 0.4), int(total_steps * 0.7)) if drift else total_steps + 1

        for step in range(total_steps):
            current_time = start_time + timedelta(minutes=step * self.interval_minutes)
            readings = {}

            # Calculate drift factor if applicable
            drift_steps = max(0, step - drift_start_step) if drift else 0

            for metric, base in baselines.items():
                val = np.random.normal(base['mean'], base['std'])

                if drift and step >= drift_start_step:
                    rate = self.DRIFT_RATES.get(metric, 0.0)
                    val += rate * drift_steps

                readings[metric] = self._clamp(val, base['min'], base['max'])

            # Adjust integer fields
            ecc_val = max(0, int(round(readings['ecc_errors'])))

            is_failure = drift and (step == total_steps - 1)

            snapshot = TelemetrySnapshot(
                node=node,
                timestamp=current_time,
                utilization_pct=readings['utilization_pct'],
                memory_used_gb=readings['memory_used_gb'],
                temperature_c=readings['temperature_c'],
                power_draw_w=readings['power_draw_w'],
                ecc_errors=ecc_val,
                fan_speed_pct=readings['fan_speed_pct'],
                sm_clock_mhz=readings['sm_clock_mhz'],
                is_injected_failure=is_failure
            )
            snapshots.append(snapshot)

        return snapshots

    def _clamp(self, value, min_val, max_val):
        return float(max(min_val, min(max_val, value)))
