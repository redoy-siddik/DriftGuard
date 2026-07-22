from django.db import models


class Alert(models.Model):
    SEVERITY_CHOICES = [('warning', 'Warning'), ('critical', 'Critical')]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
    ]
    node = models.ForeignKey(
        'cluster.GPUNode',
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    drift_score = models.ForeignKey(
        'detection.DriftScore',
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    message = models.TextField()
    triggered_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.CharField(max_length=100, blank=True)
    resolution_note = models.TextField(blank=True)

    class Meta:
        ordering = ['-triggered_at']
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['node', 'status']),
        ]

    def __str__(self):
        return f"[{self.severity.upper()}] {self.node.node_id} — {self.status}"
