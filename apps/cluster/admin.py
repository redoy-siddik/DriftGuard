from django.contrib import admin
from .models import GPUNode


@admin.register(GPUNode)
class GPUNodeAdmin(admin.ModelAdmin):
    list_display = ['node_id', 'hostname', 'gpu_model', 'current_status', 'is_active', 'last_seen']
    list_filter = ['current_status', 'is_active', 'rack_id', 'datacenter']
    search_fields = ['node_id', 'hostname', 'gpu_model', 'rack_id']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['mark_offline', 'mark_active']

    @admin.action(description='Mark selected GPU nodes as offline')
    def mark_offline(self, request, queryset):
        updated = queryset.update(current_status='offline')
        self.message_user(request, f"{updated} nodes marked as offline.")

    @admin.action(description='Mark selected GPU nodes as active (normal)')
    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True, current_status='normal')
        self.message_user(request, f"{updated} nodes marked as active.")
