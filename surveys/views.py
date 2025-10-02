from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from households.models import HouseholdSurvey, Household
from business_groups.models import BusinessProgressSurvey, BusinessGroup

@login_required
def survey_list(request):
    """Surveys list view"""
    household_surveys = HouseholdSurvey.objects.all().order_by('-survey_date')
    business_surveys = BusinessProgressSurvey.objects.all().order_by('-survey_date')

    context = {
        'household_surveys': household_surveys,
        'business_surveys': business_surveys,
        'page_title': 'Surveys',
    }

    return render(request, 'surveys/survey_list.html', context)

@login_required
def household_survey_create(request):
    """Create household survey - M&E Staff and Admin only"""
    # Check permissions - only M&E staff, ICT admin, and superusers can create surveys
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['me_staff', 'ict_admin']):
        return HttpResponseForbidden("You do not have permission to create surveys. Only M&E staff and system administrators can create surveys and forms.")

    if request.method == 'POST':
        household_id = request.POST.get('household')
        survey_type = request.POST.get('survey_type', 'General')
        notes = request.POST.get('notes', '')

        if household_id:
            household = get_object_or_404(Household, pk=household_id)
            from django.utils import timezone
            survey = HouseholdSurvey.objects.create(
                household=household,
                survey_type=survey_type,
                name=f"{survey_type} Survey",
                survey_date=timezone.now().date(),
                surveyor=request.user
            )
            messages.success(request, f'Household survey created for {household.name}!')
            return redirect('surveys:household_survey_detail', pk=survey.pk)
        else:
            messages.error(request, 'Please select a household.')

    households = Household.objects.all().order_by('name')
    context = {
        'households': households,
        'page_title': 'New Household Survey',
    }
    return render(request, 'surveys/household_survey_create.html', context)

@login_required
def business_survey_create(request):
    """Create business survey - M&E Staff and Admin only"""
    # Check permissions - only M&E staff, ICT admin, and superusers can create surveys
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['me_staff', 'ict_admin']):
        return HttpResponseForbidden("You do not have permission to create surveys. Only M&E staff and system administrators can create surveys and forms.")

    if request.method == 'POST':
        business_group_id = request.POST.get('business_group')
        notes = request.POST.get('notes', '')

        if business_group_id:
            business_group = get_object_or_404(BusinessGroup, pk=business_group_id)
            from django.utils import timezone
            survey = BusinessProgressSurvey.objects.create(
                business_group=business_group,
                survey_date=timezone.now().date(),
                surveyor=request.user
            )
            messages.success(request, f'Business survey created for {business_group.name}!')
            return redirect('surveys:business_survey_detail', pk=survey.pk)
        else:
            messages.error(request, 'Please select a business group.')

    business_groups = BusinessGroup.objects.all().order_by('name')
    context = {
        'business_groups': business_groups,
        'page_title': 'New Business Survey',
    }
    return render(request, 'surveys/business_survey_create.html', context)

@login_required
def household_survey_detail(request, pk):
    """Household survey detail"""
    survey = get_object_or_404(HouseholdSurvey, pk=pk)
    context = {
        'survey': survey,
        'page_title': f'Household Survey - {survey.household.name}',
    }
    return render(request, 'surveys/household_survey_detail.html', context)

@login_required
def business_survey_detail(request, pk):
    """Business survey detail"""
    survey = get_object_or_404(BusinessProgressSurvey, pk=pk)
    context = {
        'survey': survey,
        'page_title': f'Business Survey - {survey.business_group.name}',
    }
    return render(request, 'surveys/business_survey_detail.html', context)

@login_required
def household_survey_edit(request, pk):
    """Edit household survey - M&E Staff and Admin only"""
    # Check permissions - only M&E staff, ICT admin, and superusers can edit surveys
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['me_staff', 'ict_admin']):
        return HttpResponseForbidden("You do not have permission to edit surveys. Only M&E staff and system administrators can edit surveys and forms.")

    survey = get_object_or_404(HouseholdSurvey, pk=pk)

    if request.method == 'POST':
        survey.survey_type = request.POST.get('survey_type', survey.survey_type)
        survey.notes = request.POST.get('notes', survey.notes)
        survey.save()
        messages.success(request, 'Survey updated successfully!')
        return redirect('surveys:household_survey_detail', pk=survey.pk)

    context = {
        'survey': survey,
        'page_title': f'Edit Survey - {survey.household.name}',
    }
    return render(request, 'surveys/household_survey_edit.html', context)

@login_required
def business_survey_edit(request, pk):
    """Edit business survey - M&E Staff and Admin only"""
    # Check permissions - only M&E staff, ICT admin, and superusers can edit surveys
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['me_staff', 'ict_admin']):
        return HttpResponseForbidden("You do not have permission to edit surveys. Only M&E staff and system administrators can edit surveys and forms.")

    survey = get_object_or_404(BusinessProgressSurvey, pk=pk)

    if request.method == 'POST':
        survey.notes = request.POST.get('notes', survey.notes)
        survey.save()
        messages.success(request, 'Survey updated successfully!')
        return redirect('surveys:business_survey_detail', pk=survey.pk)

    context = {
        'survey': survey,
        'page_title': f'Edit Survey - {survey.business_group.name}',
    }
    return render(request, 'surveys/business_survey_edit.html', context)