import pandas as pd
import numpy as np
from apps.telemetry.models import TelemetrySnapshot
from apps.detection.models import BaselineStats


class ZScoreDriftDetector:
    METRICS = ['utilization_pct', 'temperature_c', 'power_draw_w', 'memory_used_gb', 'ecc_errors']
    WEIGHTS = {
        'utilization_pct': 0.10,
        'temperature_c':   0.30,
        'power_draw_w':    0.25,
        'memory_used_gb':  0.10,
        'ecc_errors':      0.25,
    }
    WARNING_THRESHOLD = 2.0
    CRITICAL_THRESHOLD = 3.5
    BASELINE_WINDOW = 144   # 144 × 5min = 12 hours
    CURRENT_WINDOW = 12     # 12 × 5min = 1 hour

    def __init__(self, node):
        self.node = node

    def run(self):
        df = self._load_dataframe()
        if df.empty or len(df) < (self.BASELINE_WINDOW + self.CURRENT_WINDOW):
            # Fallback if insufficient data
            z_scores = {m: 0.0 for m in self.METRICS}
            return {
                'z_scores': z_scores,
                'composite_score': 0.0,
                'status': 'normal',
                'baseline_stats': {},
                'df': df,
                'window_start': None,
                'window_end': None
            }

        # Split into baseline and current windows
        # Note: df ordered by timestamp ascending
        baseline_df = df.iloc[-(self.BASELINE_WINDOW + self.CURRENT_WINDOW):-self.CURRENT_WINDOW]
        current_df = df.iloc[-self.CURRENT_WINDOW:]

        baseline_stats = self._compute_baseline(baseline_df)
        z_scores = self._compute_z_scores(baseline_stats, current_df)
        composite_score = self._composite(z_scores)
        status = self._classify(composite_score)
        self._save_baseline_stats(baseline_stats)

        window_start = current_df['timestamp'].min()
        window_end = current_df['timestamp'].max()

        return {
            'z_scores': z_scores,
            'composite_score': composite_score,
            'status': status,
            'baseline_stats': baseline_stats,
            'df': df,
            'window_start': window_start,
            'window_end': window_end
        }

    def _load_dataframe(self):
        total_samples = self.BASELINE_WINDOW + self.CURRENT_WINDOW
        qs = TelemetrySnapshot.objects.filter(node=self.node).order_by('-timestamp')[:total_samples]
        snapshots = list(qs)
        if not snapshots:
            return pd.DataFrame()

        data = [{
            'timestamp': s.timestamp,
            'utilization_pct': s.utilization_pct,
            'temperature_c': s.temperature_c,
            'power_draw_w': s.power_draw_w,
            'memory_used_gb': s.memory_used_gb,
            'ecc_errors': s.ecc_errors,
            'fan_speed_pct': s.fan_speed_pct,
            'sm_clock_mhz': s.sm_clock_mhz,
        } for s in snapshots]

        df = pd.DataFrame(data)
        df.sort_values('timestamp', inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def _compute_baseline(self, baseline_df):
        stats = {}
        for metric in self.METRICS:
            mean = baseline_df[metric].mean()
            std = baseline_df[metric].std()
            # Avoid division by zero
            if pd.isna(std) or std < 1e-4:
                std = 1e-4
            stats[metric] = {
                'mean': float(mean),
                'std': float(std),
                'count': len(baseline_df)
            }
        return stats

    def _compute_z_scores(self, baseline_stats, current_df):
        z_scores = {}
        for metric in self.METRICS:
            cur_mean = current_df[metric].mean()
            b_mean = baseline_stats[metric]['mean']
            b_std = baseline_stats[metric]['std']
            z = (cur_mean - b_mean) / b_std
            z_scores[metric] = float(z)
        return z_scores

    def _composite(self, z_scores):
        weighted_sum = sum(abs(z_scores[m]) * self.WEIGHTS[m] for m in self.METRICS)
        return float(weighted_sum)

    def _classify(self, score):
        if score >= self.CRITICAL_THRESHOLD:
            return 'critical'
        elif score >= self.WARNING_THRESHOLD:
            return 'warning'
        return 'normal'

    def _save_baseline_stats(self, baseline_stats):
        for metric, stats in baseline_stats.items():
            BaselineStats.objects.update_or_create(
                node=self.node,
                metric_name=metric,
                defaults={
                    'rolling_mean': stats['mean'],
                    'rolling_std': stats['std'],
                    'sample_count': stats['count'],
                    'window_hours': 12,
                }
            )
