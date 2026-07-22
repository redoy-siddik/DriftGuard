from rest_framework import serializers
from .models import BaselineStats, IsolationForestModel, DriftScore


class BaselineStatsSerializer(serializers.ModelSerializer):
    node_id = serializers.CharField(source='node.node_id', read_only=True)

    class Meta:
        model = BaselineStats
        fields = [
            'id', 'node_id', 'metric_name',
            'rolling_mean', 'rolling_std',
            'sample_count', 'window_hours', 'computed_at'
        ]


class IsolationForestModelSerializer(serializers.ModelSerializer):
    node_id = serializers.CharField(source='node.node_id', read_only=True)

    class Meta:
        model = IsolationForestModel
        fields = [
            'id', 'node_id', 'feature_names',
            'training_samples', 'contamination',
            'trained_at', 'status'
        ]


class DriftScoreSerializer(serializers.ModelSerializer):
    node_id = serializers.CharField(source='node.node_id', read_only=True)

    class Meta:
        model = DriftScore
        fields = [
            'id', 'node_id', 'window_start', 'window_end',
            'computed_at', 'z_utilization', 'z_temperature',
            'z_power', 'z_memory', 'z_ecc', 'zscore_composite',
            'if_anomaly_score', 'if_is_anomaly',
            'composite_score', 'status'
        ]
