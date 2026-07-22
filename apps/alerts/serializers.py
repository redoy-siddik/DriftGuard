from rest_framework import serializers
from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    node_id = serializers.CharField(source='node.node_id', read_only=True)
    composite_score = serializers.FloatField(source='drift_score.composite_score', read_only=True)

    class Meta:
        model = Alert
        fields = [
            'id', 'node_id', 'drift_score', 'composite_score',
            'severity', 'status', 'message', 'triggered_at',
            'acknowledged_at', 'resolved_at', 'acknowledged_by',
            'resolution_note'
        ]


class AlertAcknowledgeSerializer(serializers.Serializer):
    acknowledged_by = serializers.CharField(max_length=100, default='ops-team')


class AlertResolveSerializer(serializers.Serializer):
    resolution_note = serializers.CharField(required=False, allow_blank=True, default='')
