from django.db import models


class TelemetrySnapshot(models.Model):
    node = models.ForeignKey(
        'cluster.GPUNode',
        on_delete=models.CASCADE,
        related_name='telemetry_snapshots'
    )
    timestamp = models.DateTimeField(db_index=True)
    utilization_pct = models.FloatField()
    memory_used_gb = models.FloatField()
    temperature_c = models.FloatField()
    power_draw_w = models.FloatField()
    ecc_errors = models.IntegerField(default=0)
    fan_speed_pct = models.FloatField(default=0.0)
    sm_clock_mhz = models.FloatField(default=0.0)
    is_injected_failure = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['node', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        verbose_name = 'Telemetry Snapshot'
        verbose_name_plural = 'Telemetry Snapshots'

    def __str__(self):
        return f"{self.node.node_id} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
