from django.contrib import admin
from .models import Program, ProgramApplication, ProgramBeneficiary

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'program_type', 'status', 'created_by', 'target_beneficiaries', 'application_count', 'created_at']
    list_filter = ['status', 'program_type', 'county', 'is_accepting_applications', 'created_at']
    search_fields = ['name', 'description', 'county', 'sub_county']
    readonly_fields = ['created_at', 'updated_at', 'application_count', 'approved_applications']

    fieldsets = (
        ('Program Information', {
            'fields': ('name', 'description', 'program_type', 'status')
        }),
        ('Program Details', {
            'fields': ('budget', 'target_beneficiaries', 'duration_months')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'application_deadline')
        }),
        ('Location & Management', {
            'fields': ('created_by', 'county', 'sub_county')
        }),
        ('Requirements', {
            'fields': ('eligibility_criteria', 'application_requirements')
        }),
        ('Settings', {
            'fields': ('is_accepting_applications', 'requires_approval')
        }),
        ('Statistics', {
            'fields': ('application_count', 'approved_applications'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ProgramApplication)
class ProgramApplicationAdmin(admin.ModelAdmin):
    list_display = ['household', 'program', 'status', 'application_date', 'reviewed_by', 'approved_by']
    list_filter = ['status', 'application_date', 'review_date', 'approval_date', 'program__status']
    search_fields = ['household__household_head', 'program__name', 'motivation_letter']
    readonly_fields = ['created_at', 'updated_at', 'application_date']

    fieldsets = (
        ('Application Info', {
            'fields': ('program', 'household', 'status', 'application_date')
        }),
        ('Application Details', {
            'fields': ('motivation_letter', 'additional_notes')
        }),
        ('Review Process', {
            'fields': ('reviewed_by', 'review_date', 'review_notes')
        }),
        ('Approval Process', {
            'fields': ('approved_by', 'approval_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ProgramBeneficiary)
class ProgramBeneficiaryAdmin(admin.ModelAdmin):
    list_display = ['household', 'program', 'participation_status', 'enrollment_date', 'benefits_received']
    list_filter = ['participation_status', 'enrollment_date', 'graduation_date', 'program__status']
    search_fields = ['household__household_head', 'program__name']
    readonly_fields = ['created_at', 'updated_at']
