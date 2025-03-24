from django.contrib import admin
from .models import Client, Omic, StandardsAndProtocols, TrafficLightSystemTimes
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

@admin.register(TrafficLightSystemTimes)
class TrafficLightSystemTimesAdmin(ModelAdmin):
    
    list_display = ['greenToYellow_c','yellowToRed_c','greenToYellow_ive_hv','yellowToRed_ive_hv','modified_by','modified_at']

    def get_fieldsets(self, request, obj=None):
        # ADD FIELDSET
        if not obj:
            #self.readonly_fields = ['cant_operator', 'cant_expert']
            self.fieldsets = (
                ('Config Claim Common', {
                    'fields': ('greenToYellow_c','yellowToRed_c',)
                }),
                ('Config Claim IVE/HV', {
                    'fields': ('greenToYellow_ive_hv','yellowToRed_ive_hv',)
                }),
            )
        # CHANGE FIELDSET
        else:
            request._obj = obj
           # self.readonly_fields = ['created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from','cant_operator', 'cant_expert']
            self.fieldsets = (
                ('Config Claim Common', {
                    'fields': ('greenToYellow_c','yellowToRed_c',)
                }),
                ('Config Claim IVE/HV', {
                    'fields': ('greenToYellow_ive_hv','yellowToRed_ive_hv',)
                }),
                ('Change Log', {
                    'classes': ('collapse',),
                    'fields': ('created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from',)
                }),
            )
        return self.fieldsets
    
@admin.register(Omic)
class OmicAdmin(ModelAdmin):
    
    list_display = ['name','responsible','opening_hours','phone','address','email']
    ordering = ['name']
    def get_fieldsets(self, request, obj=None):
        # ADD FIELDSET
        if not obj:
            #self.readonly_fields = ['cant_operator', 'cant_expert']
            self.fieldsets = (
                ('Details', {
                    'fields': ('name','responsible','opening_hours','phone','address','email')
                }),
            )
        # CHANGE FIELDSET
        else:
            request._obj = obj
           # self.readonly_fields = ['created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from','cant_operator', 'cant_expert']
            self.fieldsets = (
                ('Details', {
                    'fields': ('name','responsible','opening_hours','phone','address','email')
                }),
                ('Change Log', {
                    'classes': ('collapse',),
                    'fields': ('created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from',)
                }),
            )
        return self.fieldsets
    
@admin.register(StandardsAndProtocols)
class StandardsAndProtocolsAdmin(ModelAdmin):
    
    list_display = ['title','description']

    def get_fieldsets(self, request, obj=None):
        # ADD FIELDSET
        if not obj:
            #self.readonly_fields = ['cant_operator', 'cant_expert']
            self.fieldsets = (
                ('Details', {
                    'fields': ('title','description','file')
                }),
            )
        # CHANGE FIELDSET
        else:
            request._obj = obj
           # self.readonly_fields = ['created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from','cant_operator', 'cant_expert']
            self.fieldsets = (
                ('Details', {
                    'fields': ('title','description','file')
                }),
                ('Change Log', {
                    'classes': ('collapse',),
                    'fields': ('created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from',)
                }),
            )
        return self.fieldsets