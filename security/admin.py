from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import Module, Policy, Role

# Register your models here.

@admin.register(Module)
class ModuleAdmin(ModelAdmin):
    # Fields: 'parents', 'name', 'mapping_key', 'content_types'
    # Common fields: 'uuid', 'created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from'

    list_display = ['name', 'mapping_key', 'modified_at']
    list_display_links = ['name']
    #list_filter = ['content_types']
    search_fields = ['parents__name', 'name', 'mapping_key', 'content_types__app_label', 'content_types__model']
    ordering = ['name']
    filter_horizontal = ['parents', 'content_types']

    def get_fieldsets(self, request, obj=None):
        # ADD FIELDSET
        if not obj:
            self.readonly_fields = []
            self.fieldsets = (
                (None, {
                    'fields': ('name', 'mapping_key',)
                }),
                ('Settings', {
                    'fields': ('parents', 'content_types',)
                }),
            )
        # CHANGE FIELDSET
        else:
            request._obj = obj
            self.readonly_fields = ['created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from']
            self.fieldsets = (
                (None, {
                    'fields': ('name', 'mapping_key',)
                }),
                ('Settings', {
                    'fields': ('parents', 'content_types',)
                }),
                ('Change Log', {
                    'classes': ('collapse',),
                    'fields': ('created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from',)
                }),
            )
        return self.fieldsets

@admin.register(Role)
class RoleAdmin(ModelAdmin):
    # Fields: 'name', 'description', 'policies'
    # Common fields: 'uuid', 'created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from'

    list_display = ['name', 'modified_at']
    list_display_links = ['name']
    search_fields = ['name']
    ordering = ['name']
    filter_horizontal = ['policies']

    def get_fieldsets(self, request, obj=None):
        # ADD FIELDSET
        if not obj:
            self.readonly_fields = []
            self.fieldsets = (
                (None, {
                    'fields': ('name', 'description',)

                }),
                ('Settings', {
                    'fields': ('policies',)
                })
            )
        # CHANGE FIELDSET
        else:
            request._obj = obj
            self.readonly_fields = ['created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from']
            self.fieldsets = (
                (None, {
                    'fields': ('name', 'description',)
                }),
                ('Settings', {
                    'fields': ('policies',)
                }),
                ('Change Log', {
                    'classes': ('collapse',),
                    'fields': ('created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from',)
                }),
            )
        return self.fieldsets
    
@admin.register(Policy)
class PolicyAdmin(ModelAdmin):
    # Fields: 'name', 'module', 'view_permission', 'add_permission', 'modify_permission', 'delete_permission'
    # Common fields: 'uuid', 'created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from'

    list_display = ['name', 'module', 'view_permission', 'add_permission', 'modify_permission', 'delete_permission', 'modified_at']
    list_display_links = ['name']
    list_filter = ['module', 'view_permission', 'add_permission', 'modify_permission', 'delete_permission']
    search_fields = ['module__name', 'name', 'module__content_types__app_label', 'module__content_types__model']
    ordering = ['name']

    def get_fieldsets(self, request, obj=None):
        # ADD FIELDSET
        if not obj:
            self.readonly_fields = []
            self.fieldsets = (
                (None, {
                    'fields': ('name', 'module', )
                }),
                ('Settings', {
                    'fields': ('view_permission', 'add_permission', 'modify_permission', 'delete_permission',)
                })
            )
        # CHANGE FIELDSET
        else:
            request._obj = obj
            self.readonly_fields = ['created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from']
            self.fieldsets = (
                (None, {
                    'fields': ('name', 'module', )
                }),
                ('Settings', {
                    'fields': ('view_permission', 'add_permission', 'modify_permission', 'delete_permission',)
                }),
                ('Change Log', {
                    'classes': ('collapse',),
                    'fields': ('created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from',)
                }),
            )
        return self.fieldsets
        
