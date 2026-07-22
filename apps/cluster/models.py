from django.db import models


class GPUNode(models.Model):
    STATUS_CHOICES = [
        ('normal', 'Normal'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
        ('offline', 'Offline'),
    ]
    node_id = models.CharField(max_length=50, unique=True)
    hostname = models.CharField(max_length=100)
    gpu_model = models.CharField(max_length=100)
    total_memory_gb = models.FloatField()
    rack_id = models.CharField(max_length=50)
    datacenter = models.CharField(max_length=100, default='DC-01')
    is_active = models.BooleanField(default=True)
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='normal')
    last_seen = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['node_id']
        verbose_name = 'GPU Node'
        verbose_name_plural = 'GPU Nodes'

    def __str__(self):
        return f"{self.node_id} ({self.gpu_model})"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('dashboard:node_detail', kwargs={'node_id': self.node_id})

    @property
    def latest_drift_score(self):
        return self.drift_scores.first()

    @property
    def open_alert_count(self):
        return self.alerts.filter(status='open').count()
