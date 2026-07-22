from django.contrib import admin
from .models import BaselineStats, IsolationForestModel, DriftScore


@admin.register(BaselineStats)
class BaselineStatsAdmin(admin.ModelAdmin):
    list_display = ['node', 'metric_name', 'rolling_mean', 'rolling_std', 'sample_count', 'computed_at']
    list_filter = ['node', 'metric_name']
    search_fields = ['node__node_id', 'metric_name']


@admin.register(IsolationForestModel)
class IsolationForestModelAdmin(admin.ModelAdmin):
    list_display = ['node', 'status', 'training_samples', 'contamination', 'trained_at']
    list_filter = ['status']
    search_fields = ['node__node_id']
    readonly_fields = ['trained_at']


@admin.register(DriftScore)
class DriftScoreAdmin(admin.ModelAdmin):
    list_display = ['node', 'composite_score', 'zscore_composite', 'if_is_anomaly', 'status', 'computed_at']
    list_filter = ['status', 'node']
    search_fields = ['node__node_id']
    readonly_fields = ['computed_at']
