from django.db import models


class BaselineStats(models.Model):
    node = models.ForeignKey(
        'cluster.GPUNode',
        on_delete=models.CASCADE,
        related_name='baselines'
    )
    metric_name = models.CharField(max_length=50)
    rolling_mean = models.FloatField()
    rolling_std = models.FloatField()
    sample_count = models.IntegerField()
    window_hours = models.IntegerField(default=12)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['node', 'metric_name']
        verbose_name = 'Baseline Stats'
        verbose_name_plural = 'Baseline Stats'

    def __str__(self):
        return f"{self.node.node_id} - {self.metric_name} (mean={self.rolling_mean:.2f})"


class IsolationForestModel(models.Model):
    STATUS_CHOICES = [('trained', 'Trained'), ('stale', 'Stale'), ('failed', 'Failed')]
    node = models.OneToOneField(
        'cluster.GPUNode',
        on_delete=models.CASCADE,
        related_name='isolation_forest_model'
    )
    model_blob = models.BinaryField()           # Pickled sklearn model
    feature_names = models.JSONField()          # List of feature column names used
    training_samples = models.IntegerField()
    contamination = models.FloatField(default=0.05)
    trained_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trained')

    class Meta:
        verbose_name = 'Isolation Forest Model'
        verbose_name_plural = 'Isolation Forest Models'

    def __str__(self):
        return f"IF Model — {self.node.node_id} ({self.status})"


class DriftScore(models.Model):
    STATUS_CHOICES = [
        ('normal', 'Normal'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    node = models.ForeignKey(
        'cluster.GPUNode',
        on_delete=models.CASCADE,
        related_name='drift_scores'
    )
    window_start = models.DateTimeField()
    window_end = models.DateTimeField()
    computed_at = models.DateTimeField(auto_now_add=True)

    # Z-score layer
    z_utilization = models.FloatField()
    z_temperature = models.FloatField()
    z_power = models.FloatField()
    z_memory = models.FloatField()
    z_ecc = models.FloatField()
    zscore_composite = models.FloatField()

    # Isolation Forest layer
    if_anomaly_score = models.FloatField(null=True, blank=True)
    if_is_anomaly = models.BooleanField(null=True, blank=True)

    # Final fused score and classification
    composite_score = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='normal')

    class Meta:
        ordering = ['-computed_at']
        indexes = [
            models.Index(fields=['node', 'computed_at']),
        ]
        verbose_name = 'Drift Score'
        verbose_name_plural = 'Drift Scores'

    def __str__(self):
        return f"{self.node.node_id} drift={self.composite_score:.2f} ({self.status})"
