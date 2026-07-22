from django.contrib import admin
from .models import TelemetrySnapshot


@admin.register(TelemetrySnapshot)
class TelemetrySnapshotAdmin(admin.ModelAdmin):
    list_display = ['node', 'timestamp', 'utilization_pct', 'temperature_c', 'power_draw_w', 'is_injected_failure']
    list_filter = ['node', 'is_injected_failure']
    date_hierarchy = 'timestamp'
    search_fields = ['node__node_id']
    readonly_fields = ['created_at']
