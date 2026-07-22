from django.contrib import admin
from django.utils import timezone
from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['node', 'severity', 'status', 'triggered_at', 'acknowledged_by']
    list_filter = ['severity', 'status']
    search_fields = ['node__node_id', 'message', 'acknowledged_by']
    readonly_fields = ['triggered_at', 'acknowledged_at', 'resolved_at']
    actions = ['bulk_acknowledge', 'bulk_resolve']

    @admin.action(description='Acknowledge selected alerts')
    def bulk_acknowledge(self, request, queryset):
        updated = queryset.filter(status='open').update(
            status='acknowledged',
            acknowledged_at=timezone.now(),
            acknowledged_by=request.user.username or 'admin'
        )
        self.message_user(request, f"{updated} alerts acknowledged.")

    @admin.action(description='Resolve selected alerts')
    def bulk_resolve(self, request, queryset):
        updated = queryset.exclude(status='resolved').update(
            status='resolved',
            resolved_at=timezone.now(),
            resolution_note='Resolved via bulk admin action'
        )
        self.message_user(request, f"{updated} alerts resolved.")
