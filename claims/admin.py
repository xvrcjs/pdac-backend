from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import Supplier, Claimer, File, ClaimRegular

@admin.register(Supplier)
class SupplierAdmin(ModelAdmin):
    list_display = ['fullname', 'cuil', 'address', 'city', 'zip_code']
    search_fields = ['fullname', 'cuil', 'city']

@admin.register(Claimer)
class ClaimerAdmin(ModelAdmin):
    list_display = ['fullname', 'dni', 'cuit', 'email', 'gender']
    search_fields = ['fullname', 'dni', 'cuit', 'email']

@admin.register(File)
class FileAdmin(ModelAdmin):
    list_display = ['file_name', 'file']
    search_fields = ['file_name']

@admin.register(ClaimRegular)
class ClaimRegularAdmin(ModelAdmin):
    list_display = ['id', 'claimer', 'claim_status', 'category', 'heading', 'subheading']
    search_fields = ['id', 'claimer__fullname', 'claim_status', 'category', 'heading']
    ordering = ['-id']
    filter_horizontal = ['suppliers', 'files']
    
    def get_fieldsets(self, request, obj=None):
        if not obj:
            self.readonly_fields = []
            self.fieldsets = (
                (None, {
                    'fields': ('id', 'claimer', 'suppliers', 'problem_description', 
                               'activity','files')
                }),
                ('General Information', {
                    'fields': ('claim_access', 'type_of_claim', 'claim_status', 'category', 'heading', 'subheading')
                }),
                ('Processing', {
                    'fields': ('transfer_to_company', 'derived_to_omic','derived_to_user', 'transfer_to_the_consumer',
                               'conciliation_hearing', 'imputation', 'resolution', 'monetary_agreement')
                })
            )
        else:
            request._obj = obj
            self.readonly_fields = ['id', 'created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from']
            self.fieldsets = (
                (None, {
                    'fields': ('id', 'claimer', 'suppliers', 'problem_description', 'activity','files')
                }),
                ('General Information', {
                    'fields': ('claim_access', 'type_of_claim', 'claim_status', 'category', 'heading', 'subheading')
                }),
                ('Processing', {
                    'fields': ('transfer_to_company', 'derived_to_omic','derived_to_user','transfer_to_the_consumer',
                               'conciliation_hearing', 'imputation', 'resolution', 'monetary_agreement')
                }),
                ('Change Log', {
                    'classes': ('collapse',),
                    'fields': ('created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from',)
                })
            )
        return self.fieldsets