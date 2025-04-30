from django.contrib import admin

from django.contrib.admin import ModelAdmin

from tickets.models import File, Ticket

# Register your models here.
@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    list_display = ['id', 'claim', 'assigned','status']
    ordering = ['-id']
    
    def get_fieldsets(self, request, obj=None):
        if not obj:
            self.readonly_fields = []
            self.fieldsets = (
                (None, {
                    'fields': ('id', 'claim', 'assigned','status','support_level', 'problem_description', 'tasks','activity',)
                }),
            )
        else:
            request._obj = obj
            self.readonly_fields = ['id', 'created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from']
            self.fieldsets = (
                (None, {
                    'fields': ('id', 'claim', 'assigned','status','support_level', 'problem_description', 'tasks','activity',)
                }),
                ('Change Log', {
                    'classes': ('collapse',),
                    'fields': ('created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from',)
                })
            )
        return self.fieldsets
@admin.register(File)
class FileAdmin(ModelAdmin):
    list_display = ['file', 'file_name', 'ticket']
    
    def get_fieldsets(self, request, obj=None):
        if not obj:
            self.readonly_fields = []
            self.fieldsets = (
                (None, {
                    'fields': ('file', 'file_name', 'ticket',)
                }),
            )
        else:
            request._obj = obj
            self.readonly_fields = ['id', 'created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from']
            self.fieldsets = (
                (None, {
                    'fields': ('file', 'file_name', 'ticket',)
                }),
                ('Change Log', {
                    'classes': ('collapse',),
                    'fields': ('created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from',)
                })
            )
        return self.fieldsets