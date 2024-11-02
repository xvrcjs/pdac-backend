from django.conf import settings
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.models import Group as BaseGroup
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import  User, Account

import logging

logger = logging.getLogger('__name__')

# DJANGO PERMISSIONS

    
@admin.register(User)
class UserAdmin(BaseUserAdmin):

    list_display = ['display_name', 'email', 'is_superuser', 'last_login', 'modified_at']
    search_fields = ['email', 'display_name' ]
    ordering = ['email']
    list_filter = ['email',]
    list_display_links = ['display_name']
    

    def has_change_permission(self, request, obj=None):
        if obj != None:
            # Cannot change system users
            if str(obj.pk) in [settings.ADMIN_USER_UUID, settings.SYSTEM_USER_UUID, settings.ANONYMOUS_USER_UUID]:
                return False
            # Only superusers can edit superusers.
            if obj.is_superuser:
                return request.user.is_superuser
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Cannot delete system users
        if obj != None and str(obj.pk) in [settings.ADMIN_USER_UUID, settings.SYSTEM_USER_UUID, settings.ANONYMOUS_USER_UUID]:
            return False
        # Only superusers can delete other users. Non-superusers should set them as not active instead of deleting.
        return request.user.is_superuser

    def get_fieldsets(self, request, obj=None):
        # ADD FIELDSET
        if not obj:
            self.fieldsets = ()
            self.readonly_fields = []
            # Only superusers can create staff and superusers.
            if not request.user.is_superuser:
                self.add_fieldsets = (
                    ('Login Info', {
                        'fields': ('email', 'password1', 'password2',)
                    }),
                    ('Personal Info', {
                       'fields': ('display_name',)
                    }),
                    ('Permissions', {
                        'fields': ('is_active',)
                    }),
                )
            else:
                self.add_fieldsets = (
                    ('Login Info', {
                        'fields': ('email', 'password1', 'password2',)
                    }),
                    ('Personal Info', {
                        'fields': ('display_name', )
                    }),
                    ('Permissions', {
                        'fields': ('is_superuser', 'user_permissions',)
                    }),
                )
            return self.add_fieldsets

        # CHANGE FIELDSET
        self.add_fieldsets = ()
        self.readonly_fields = [
            'last_login', 'last_access', 'created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from'
        ]
        if not request.user.is_superuser:
            # Non superusers can not make staff and superusers, or change email address.
            self.readonly_fields.extend(['email',  'is_superuser','user_permissions',])
            if obj != request.user:
                # Non superusers can only set their own password.
                self.readonly_fields.append('password')
        self.fieldsets = (
            ('Login Info', {
                'fields': ('display_name', 'password')
            }),
            ('Permissions', {
                'fields': ( 'is_superuser', 'user_permissions',)
            }),
            ('Last activities', {
                'fields': ('last_login', 'last_access',)
            }),
            ('Change Log', {
                'classes': ('collapse',),
                'fields': ('created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from',)
            }),
        )

        return self.fieldsets
@admin.register(Account)
class AccountAdmin(ModelAdmin):
    
    # Fields: 'user', 'roles', 'last_login', 'is_active', 'is_admin', 'policies'
    # Common fields: 'uuid',  'created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from'

    list_display = ['id','user','full_name','is_active', 'is_admin','is_deleted', 'last_login', 'modified_at']
    list_display_links = ['user']
    list_filter = ['is_active', 'is_admin']
    search_fields = ['user__display_name', 'full_name', 'user__email', 'roles__name']
    ordering = ['-id']
    filter_horizontal = ['roles',]

    def get_fieldsets(self, request, obj=None):
        # ADD FIELDSET
        if not obj:
            self.readonly_fields = []
            self.fieldsets = (
                (None, {
                    'fields': ('user',)
                }),
                ('Details',{
                    'fields':('full_name','profile_image',)
                }),
                ('Administration',{
                    'fields':('client','roles',)

                }),
                ('Settings', {
                    'fields': ('is_active', 'is_admin','is_deleted' )
                })
            )
        # CHANGE FIELDSET
        else:
            request._obj = obj
            self.readonly_fields = ['id','created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from']
            self.fieldsets = (
                (None, {
                    'fields': ('user',)
                }),
                ('Details',{
                    'fields':('full_name','profile_image',)
                }),
                ('Administration',{
                    'fields':('client','roles',)

                }),
                ('Settings', {
                    'fields': ('is_active', 'is_admin', 'is_deleted', )
                }),
                ('Change Log', {
                    'classes': ('collapse',),
                    'fields': ('created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from',)
                }),
            )
        return self.fieldsets


admin.site.unregister(BaseGroup)
