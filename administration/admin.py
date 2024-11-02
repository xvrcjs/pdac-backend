from django.contrib import admin
from .models import Client
from django.contrib.admin import ModelAdmin, TabularInline

# Register your models here.

@admin.register(Client)
class ClientAdmin(ModelAdmin):
    
    list_display = ['name']
    list_display_links = ['name']
    list_filter = ['name']
    filter_horizontal = ['modules']
    search_fields = [ 'name']
    ordering = ['name']

    def get_fieldsets(self, request, obj=None):
        # ADD FIELDSET
        if not obj:
            #self.readonly_fields = ['cant_operator', 'cant_expert']
            self.fieldsets = (
                ('Details', {
                    'fields': ('name','logo', 'phone','address',)
                }),
                ('Administration', {
                    'fields': ('cant_students','owner','modules',)
                }),
                ('Settings',{
                    'fields':('is_deleted',)
                })
            )
        # CHANGE FIELDSET
        else:
            request._obj = obj
           # self.readonly_fields = ['created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from','cant_operator', 'cant_expert']
            self.fieldsets = (
                ('Details', {
                    'fields': ('name','logo', 'phone','address',)
                }),
                ('Administration', {
                    'fields': ('cant_students','owner','modules',)
                }),
                ('Settings',{
                    'fields':('is_deleted',)
                }),
                ('Change Log', {
                    'classes': ('collapse',),
                    'fields': ('created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from',)
                }),
            )
        return self.fieldsets
