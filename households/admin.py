from django.contrib import admin
from .models import Household, HouseholdMember, PPI, HouseholdSurvey, HouseholdProgram

@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ('name', 'village', 'national_id', 'phone_number', 'created_at')
    list_filter = ('village', 'disability', 'created_at')
    search_fields = ('name', 'national_id', 'phone_number')

@admin.register(HouseholdMember)
class HouseholdMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'household', 'gender', 'age', 'relationship_to_head')
    list_filter = ('gender', 'relationship_to_head', 'is_program_participant')

@admin.register(PPI)
class PPIAdmin(admin.ModelAdmin):
    list_display = ('household', 'name', 'eligibility_score', 'assessment_date')
    list_filter = ('assessment_date',)

@admin.register(HouseholdProgram)
class HouseholdProgramAdmin(admin.ModelAdmin):
    list_display = ('household', 'program', 'participation_status', 'mentor')
    list_filter = ('participation_status', 'program')