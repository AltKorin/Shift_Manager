from django.contrib import admin
from .models import Employee, Shift, ShiftChangeRequest


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['user', 'position', 'supervisor', 'is_supervisor']
    list_filter = ['is_supervisor', 'position']
    search_fields = ['user__first_name', 'user__last_name', 'position']
    raw_id_fields = ['user', 'supervisor']


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'shift_type', 'start_time', 'end_time']
    list_filter = ['shift_type', 'date']
    search_fields = ['employee__user__first_name', 'employee__user__last_name']
    date_hierarchy = 'date'
    raw_id_fields = ['employee']


@admin.register(ShiftChangeRequest)
class ShiftChangeRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'request_type', 'status', 'created_at', 'reviewed_by']
    list_filter = ['status', 'request_type', 'created_at']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'reason']
    date_hierarchy = 'created_at'
    raw_id_fields = ['employee', 'shift', 'swap_with_employee', 'swap_shift', 'reviewed_by']
    readonly_fields = ['created_at', 'reviewed_at']
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('employee', 'request_type', 'status', 'reason')
        }),
        ('Szczegóły zmiany', {
            'fields': ('shift', 'swap_with_employee', 'swap_shift', 
                      'new_date', 'new_start_time', 'new_end_time', 'new_shift_type')
        }),
        ('Rozpatrzenie', {
            'fields': ('reviewed_by', 'review_notes', 'reviewed_at', 'created_at')
        }),
    )
