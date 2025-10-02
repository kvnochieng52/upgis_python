"""
Admin configuration for UPG Grants
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import SBGrant, PRGrant, GrantDisbursement


@admin.register(SBGrant)
class SBGrantAdmin(admin.ModelAdmin):
    list_display = [
        'business_group', 'program', 'get_grant_amount', 'status',
        'disbursement_status', 'application_date', 'approval_date'
    ]
    list_filter = [
        'status', 'disbursement_status', 'program__name',
        'application_date', 'approval_date'
    ]
    search_fields = [
        'business_group__name', 'program__name',
        'business_group__members__name'
    ]
    readonly_fields = ['application_date', 'disbursement_percentage']

    fieldsets = (
        ('Grant Information', {
            'fields': ('program', 'business_group', 'base_grant_amount', 'calculated_grant_amount', 'final_grant_amount', 'status', 'disbursement_status')
        }),
        ('Application Details', {
            'fields': ('application_date', 'business_plan', 'projected_income')
        }),
        ('Review Process', {
            'fields': ('reviewed_by', 'review_date', 'review_notes'),
            'classes': ('collapse',)
        }),
        ('Approval Process', {
            'fields': ('approved_by', 'approval_date'),
            'classes': ('collapse',)
        }),
        ('Disbursement', {
            'fields': ('disbursement_date', 'disbursed_amount', 'disbursed_by', 'disbursement_percentage'),
            'classes': ('collapse',)
        }),
        ('Utilization', {
            'fields': ('utilization_report', 'utilization_date'),
            'classes': ('collapse',)
        }),
    )

    def get_grant_amount(self, obj):
        """Display the effective grant amount"""
        return f"KES {obj.get_grant_amount():,.2f}"
    get_grant_amount.short_description = "Grant Amount"
    get_grant_amount.admin_order_field = 'final_grant_amount'

    def get_queryset(self, request):
        """Only show SB grants for UPG programs"""
        return super().get_queryset(request).select_related(
            'program', 'business_group', 'reviewed_by', 'approved_by', 'disbursed_by'
        )


@admin.register(PRGrant)
class PRGrantAdmin(admin.ModelAdmin):
    list_display = [
        'business_group', 'program', 'grant_amount', 'status',
        'performance_rating', 'application_date', 'approval_date'
    ]
    list_filter = [
        'status', 'performance_rating', 'program__name',
        'application_date', 'approval_date'
    ]
    search_fields = [
        'business_group__name', 'program__name',
        'business_group__members__name'
    ]
    readonly_fields = ['application_date', 'is_eligible']

    fieldsets = (
        ('Grant Information', {
            'fields': ('program', 'business_group', 'sb_grant', 'grant_amount', 'status')
        }),
        ('Application Details', {
            'fields': ('application_date', 'is_eligible')
        }),
        ('Performance Assessment', {
            'fields': ('performance_score', 'performance_rating', 'performance_assessment'),
        }),
        ('Business Metrics', {
            'fields': ('revenue_generated', 'jobs_created', 'savings_accumulated'),
            'classes': ('collapse',)
        }),
        ('Assessment Process', {
            'fields': ('assessed_by', 'assessment_date'),
            'classes': ('collapse',)
        }),
        ('Approval Process', {
            'fields': ('approved_by', 'approval_date'),
            'classes': ('collapse',)
        }),
        ('Disbursement', {
            'fields': ('disbursement_date', 'disbursed_by'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Only show PR grants for UPG programs"""
        return super().get_queryset(request).select_related(
            'program', 'business_group', 'sb_grant', 'assessed_by', 'approved_by', 'disbursed_by'
        )


@admin.register(GrantDisbursement)
class GrantDisbursementAdmin(admin.ModelAdmin):
    list_display = [
        'get_grant_name', 'disbursement_type', 'amount',
        'disbursement_date', 'method', 'processed_by'
    ]
    list_filter = [
        'disbursement_type', 'method', 'disbursement_date'
    ]
    search_fields = [
        'sb_grant__business_group__name', 'pr_grant__business_group__name',
        'recipient_name', 'reference_number'
    ]
    readonly_fields = ['get_grant_name']

    fieldsets = (
        ('Disbursement Information', {
            'fields': ('get_grant_name', 'disbursement_type', 'amount', 'disbursement_date', 'method')
        }),
        ('Grant References', {
            'fields': ('sb_grant', 'pr_grant'),
            'classes': ('collapse',)
        }),
        ('Transaction Details', {
            'fields': ('reference_number', 'recipient_name', 'recipient_contact')
        }),
        ('Processing', {
            'fields': ('processed_by', 'notes')
        }),
    )

    def get_grant_name(self, obj):
        """Get the business group name from either SB or PR grant"""
        if obj.sb_grant:
            return obj.sb_grant.business_group.name
        elif obj.pr_grant:
            return obj.pr_grant.business_group.name
        return "N/A"
    get_grant_name.short_description = "Business Group"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'sb_grant__business_group', 'pr_grant__business_group', 'processed_by'
        )