from rest_framework import serializers
from .models import TelemetrySnapshot


class TelemetrySnapshotSerializer(serializers.ModelSerializer):
    node_id = serializers.CharField(source='node.node_id', read_only=True)

    class Meta:
        model = TelemetrySnapshot
        fields = [
            'id', 'node_id', 'timestamp',
            'utilization_pct', 'memory_used_gb',
            'temperature_c', 'power_draw_w',
            'ecc_errors', 'fan_speed_pct',
            'sm_clock_mhz', 'is_injected_failure'
        ]


class TelemetryGenerateSerializer(serializers.Serializer):
    days = serializers.IntegerField(default=7, min_value=1, max_value=30)
    nodes = serializers.IntegerField(default=10, min_value=1, max_value=100)
    drift_pct = serializers.FloatField(default=0.2, min_value=0.0, max_value=1.0)
    clear = serializers.BooleanField(default=False)
