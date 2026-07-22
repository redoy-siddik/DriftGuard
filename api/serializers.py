from rest_framework import serializers


class DashboardSummarySerializer(serializers.Serializer):
    total_nodes = serializers.IntegerField()
    nodes_normal = serializers.IntegerField()
    nodes_warning = serializers.IntegerField()
    nodes_critical = serializers.IntegerField()
    nodes_offline = serializers.IntegerField()
    open_alerts = serializers.IntegerField()
    critical_alerts = serializers.IntegerField()
    warning_alerts = serializers.IntegerField()
    last_detection_run = serializers.DateTimeField(allow_null=True)
    avg_composite_score = serializers.FloatField()
    max_composite_score = serializers.FloatField()
    highest_risk_node = serializers.CharField(allow_null=True)
    if_models_trained = serializers.IntegerField()
    total_telemetry_snapshots = serializers.IntegerField()
    detection_coverage_pct = serializers.FloatField()
