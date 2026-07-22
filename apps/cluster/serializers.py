from rest_framework import serializers
from .models import GPUNode


class GPUNodeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPUNode
        fields = [
            'id', 'node_id', 'hostname', 'gpu_model',
            'total_memory_gb', 'rack_id', 'datacenter',
            'is_active', 'current_status', 'last_seen'
        ]


class GPUNodeDetailSerializer(serializers.ModelSerializer):
    latest_composite_score = serializers.SerializerMethodField()
    open_alert_count = serializers.IntegerField(read_only=True)
    if_model_trained = serializers.SerializerMethodField()

    class Meta:
        model = GPUNode
        fields = [
            'id', 'node_id', 'hostname', 'gpu_model',
            'total_memory_gb', 'rack_id', 'datacenter',
            'is_active', 'current_status', 'last_seen',
            'created_at', 'updated_at',
            'latest_composite_score', 'open_alert_count',
            'if_model_trained'
        ]

    def get_latest_composite_score(self, obj):
        latest = obj.latest_drift_score
        return latest.composite_score if latest else None

    def get_if_model_trained(self, obj):
        return hasattr(obj, 'isolation_forest_model') and obj.isolation_forest_model.status == 'trained'
