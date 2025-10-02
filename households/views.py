from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Household, HouseholdMember, HouseholdProgram, PPI, HouseholdSurvey
from .eligibility import EligibilityScorer, HouseholdQualificationTool, batch_eligibility_assessment
from core.models import Village
from core.decorators import role_required

@login_required
def household_list(request):
    """Household list view with role-based filtering"""
    user = request.user

    # Filter households based on user role and permissions
    if user.is_superuser or user.role in ['ict_admin', 'me_staff']:
        # Full access to all households
        households = Household.objects.all()
    elif user.role == 'mentor':
        # Mentors can only see households in their assigned villages
        if hasattr(user, 'profile') and user.profile:
            assigned_villages = user.profile.assigned_villages.all()
            households = Household.objects.filter(village__in=assigned_villages)
        else:
            # No villages assigned, no households visible
            households = Household.objects.none()
    elif user.role == 'field_associate':
        # Field Associates see households in their area (same as mentors for now)
        if hasattr(user, 'profile') and user.profile:
            assigned_villages = user.profile.assigned_villages.all()
            households = Household.objects.filter(village__in=assigned_villages)
        else:
            households = Household.objects.none()
    else:
        # Other roles have no access to households
        households = Household.objects.none()

    households = households.order_by('-created_at')

    context = {
        'households': households,
        'page_title': 'Households',
        'total_count': households.count(),
    }

    return render(request, 'households/household_list.html', context)

@login_required
def household_create(request):
    """Create new household with role-based village filtering"""
    user = request.user

    if request.method == 'POST':
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        village_id = request.POST.get('village')
        subcounty_id = request.POST.get('subcounty')
        national_id = request.POST.get('national_id', '')
        disability = request.POST.get('disability') == 'on'

        # Validate village access for mentors
        if user.role == 'mentor' and village_id:
            if hasattr(user, 'profile') and user.profile:
                assigned_villages = user.profile.assigned_villages.values_list('id', flat=True)
                if int(village_id) not in assigned_villages:
                    messages.error(request, 'You can only create households in your assigned villages.')
                    village_id = None

        if name and village_id and subcounty_id:
            household = Household.objects.create(
                name=name,
                phone_number=phone_number or '',
                village_id=village_id,
                subcounty_id=subcounty_id,
                national_id=national_id,
                disability=disability
            )
            messages.success(request, f'Household "{household.name}" created successfully!')
            return redirect('households:household_detail', pk=household.pk)
        else:
            messages.error(request, 'Household name, sub-county, and village are required.')

    # Filter villages based on user role
    if user.is_superuser or user.role in ['ict_admin', 'me_staff']:
        # Full access to all villages
        villages = Village.objects.select_related('subcounty_obj').all()
        from core.models import SubCounty
        subcounties = SubCounty.objects.select_related('county').all()
    elif user.role in ['mentor', 'field_associate']:
        # Only assigned villages
        if hasattr(user, 'profile') and user.profile:
            villages = user.profile.assigned_villages.select_related('subcounty_obj').all()
            # Get subcounties for assigned villages
            from core.models import SubCounty
            subcounty_ids = villages.values_list('subcounty_obj_id', flat=True).distinct()
            subcounties = SubCounty.objects.filter(id__in=subcounty_ids).select_related('county')
        else:
            villages = Village.objects.none()
            subcounties = []
            messages.warning(request, 'You have no assigned villages. Please contact your administrator.')
    else:
        villages = Village.objects.none()
        subcounties = []
        messages.error(request, 'You do not have permission to create households.')

    context = {
        'villages': villages,
        'subcounties': subcounties,
        'page_title': 'Create Household',
    }
    return render(request, 'households/household_create.html', context)

@login_required
def household_detail(request, pk):
    """Household detail view"""
    household = get_object_or_404(Household, pk=pk)

    # Calculate program participant count
    program_participants_count = household.members.filter(is_program_participant=True).count()

    context = {
        'household': household,
        'program_participants_count': program_participants_count,
        'page_title': f'Household - {household.name}',
    }
    return render(request, 'households/household_detail.html', context)

@login_required
def household_edit(request, pk):
    """Edit household"""
    household = get_object_or_404(Household, pk=pk)

    if request.method == 'POST':
        household.name = request.POST.get('name', household.name)
        household.phone_number = request.POST.get('phone_number', household.phone_number)
        village_id = request.POST.get('village')
        subcounty_id = request.POST.get('subcounty')
        if village_id:
            household.village_id = village_id
        if subcounty_id:
            household.subcounty_id = subcounty_id
        household.national_id = request.POST.get('national_id', household.national_id)
        household.disability = request.POST.get('disability') == 'on'

        household.save()
        messages.success(request, f'Household "{household.name}" updated successfully!')
        return redirect('households:household_detail', pk=household.pk)

    villages = Village.objects.select_related('subcounty_obj').all()
    from core.models import SubCounty
    subcounties = SubCounty.objects.select_related('county').all()

    context = {
        'household': household,
        'villages': villages,
        'subcounties': subcounties,
        'page_title': f'Edit - {household.name}',
    }
    return render(request, 'households/household_edit.html', context)

@login_required
def household_delete(request, pk):
    """Delete household"""
    household = get_object_or_404(Household, pk=pk)

    if request.method == 'POST':
        household_name = household.name
        household.delete()
        messages.success(request, f'Household "{household_name}" deleted successfully!')
        return redirect('households:household_list')

    context = {
        'household': household,
        'page_title': f'Delete - {household.name}',
    }
    return render(request, 'households/household_delete.html', context)

@login_required
def member_create(request, household_pk):
    """Add member to household"""
    household = get_object_or_404(Household, pk=household_pk)

    if request.method == 'POST':
        name = request.POST.get('name')
        gender = request.POST.get('gender')
        age = request.POST.get('age')
        relationship_to_head = request.POST.get('relationship_to_head')
        education_level = request.POST.get('education_level', 'none')
        is_program_participant = request.POST.get('is_program_participant') == 'on'

        if name and gender and age:
            member = HouseholdMember.objects.create(
                household=household,
                name=name,
                gender=gender,
                age=int(age),
                relationship_to_head=relationship_to_head,
                education_level=education_level,
                is_program_participant=is_program_participant
            )
            messages.success(request, f'Member "{member.name}" added to household successfully!')
            return redirect('households:household_detail', pk=household.pk)
        else:
            messages.error(request, 'Name, gender, and age are required.')

    context = {
        'household': household,
        'gender_choices': HouseholdMember.GENDER_CHOICES,
        'relationship_choices': HouseholdMember.RELATIONSHIP_CHOICES,
        'education_choices': HouseholdMember.EDUCATION_CHOICES,
        'page_title': f'Add Member to {household.name}',
    }
    return render(request, 'households/member_create.html', context)

@login_required
def member_edit(request, pk):
    """Edit household member"""
    member = get_object_or_404(HouseholdMember, pk=pk)
    household = member.household

    if request.method == 'POST':
        member.name = request.POST.get('name', member.name)
        member.gender = request.POST.get('gender', member.gender)
        member.age = request.POST.get('age', member.age)
        member.relationship_to_head = request.POST.get('relationship_to_head', member.relationship_to_head)
        member.education_level = request.POST.get('education_level', member.education_level)
        member.is_program_participant = request.POST.get('is_program_participant') == 'on'

        member.save()
        messages.success(request, f'Member "{member.name}" updated successfully!')
        return redirect('households:household_detail', pk=household.pk)

    context = {
        'member': member,
        'household': household,
        'gender_choices': HouseholdMember.GENDER_CHOICES,
        'relationship_choices': HouseholdMember.RELATIONSHIP_CHOICES,
        'education_choices': HouseholdMember.EDUCATION_CHOICES,
        'page_title': f'Edit Member - {member.name}',
    }
    return render(request, 'households/member_edit.html', context)

@login_required
def member_delete(request, pk):
    """Delete household member"""
    member = get_object_or_404(HouseholdMember, pk=pk)
    household = member.household

    if request.method == 'POST':
        member_name = member.name
        member.delete()
        messages.success(request, f'Member "{member_name}" removed from household!')
        return redirect('households:household_detail', pk=household.pk)

    context = {
        'member': member,
        'household': household,
        'page_title': f'Remove Member - {member.name}',
    }
    return render(request, 'households/member_delete.html', context)


@login_required
@role_required(['me_staff', 'field_associate'])
def run_eligibility_assessment(request, household_id):
    """Run comprehensive eligibility assessment for a household"""
    household = get_object_or_404(Household, id=household_id)

    if request.method == 'POST':
        try:
            # Run eligibility assessment
            eligibility_result = household.run_eligibility_assessment()

            messages.success(request, f"Eligibility assessment completed. Score: {eligibility_result['total_score']}")
            return JsonResponse({
                'success': True,
                'result': eligibility_result
            })
        except Exception as e:
            messages.error(request, f"Error running assessment: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return redirect('households:household_detail', pk=household_id)


@login_required
@role_required(['me_staff', 'field_associate'])
def run_qualification_assessment(request, household_id):
    """Run full qualification assessment for UPG program"""
    household = get_object_or_404(Household, id=household_id)

    if request.method == 'POST':
        try:
            # Run qualification assessment
            qualification_result = household.run_qualification_assessment()

            if qualification_result['final_qualification']['qualified']:
                messages.success(request, f"Household qualified for UPG program!")
            else:
                messages.warning(request, f"Household not qualified. Status: {qualification_result['final_qualification']['status']}")

            return JsonResponse({
                'success': True,
                'result': qualification_result
            })
        except Exception as e:
            messages.error(request, f"Error running qualification: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return redirect('households:household_detail', pk=household_id)


@login_required
@role_required(['me_staff'])
def batch_eligibility_report(request):
    """Generate batch eligibility report for multiple households"""
    if request.method == 'POST':
        # Get selected households or all households
        household_ids = request.POST.getlist('household_ids')

        if household_ids:
            households = Household.objects.filter(id__in=household_ids)
        else:
            # Process all households if none selected
            households = Household.objects.all()[:100]  # Limit to prevent timeout

        try:
            # Run batch assessment
            results = batch_eligibility_assessment(households)

            context = {
                'results': results,
                'total_households': len(results),
                'eligible_count': sum(1 for r in results if r['eligible']),
            }

            return render(request, 'households/batch_eligibility_report.html', context)

        except Exception as e:
            messages.error(request, f"Error generating report: {str(e)}")
            return redirect('households:household_list')

    # Show selection form
    households = Household.objects.all().select_related('village')
    return render(request, 'households/batch_eligibility_form.html', {'households': households})


@login_required
def household_eligibility_api(request, household_id):
    """API endpoint for household eligibility data"""
    household = get_object_or_404(Household, id=household_id)

    try:
        eligibility_result = household.run_eligibility_assessment()
        return JsonResponse({
            'success': True,
            'household_id': household.id,
            'household_name': household.name,
            'eligibility_data': eligibility_result
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@role_required(['me_staff'])
def eligibility_dashboard(request):
    """Dashboard showing eligibility statistics and trends"""
    from django.db.models import Count, Avg

    # Get summary statistics
    total_households = Household.objects.count()

    # Get recent assessments (simplified - would cache this in production)
    recent_households = Household.objects.all()[:50]
    assessments = []

    for household in recent_households:
        try:
            result = household.run_eligibility_assessment()
            assessments.append({
                'household_id': household.id,
                'household_name': household.name,
                'score': result['total_score'],
                'level': result['eligibility_level'],
                'eligible': result['eligibility_level'] in ['highly_eligible', 'eligible']
            })
        except:
            continue

    # Calculate statistics
    eligible_count = sum(1 for a in assessments if a['eligible'])
    avg_score = sum(a['score'] for a in assessments) / len(assessments) if assessments else 0

    # Group by eligibility level
    level_counts = {}
    for assessment in assessments:
        level = assessment['level']
        level_counts[level] = level_counts.get(level, 0) + 1

    context = {
        'total_households': total_households,
        'assessed_households': len(assessments),
        'eligible_count': eligible_count,
        'eligibility_rate': (eligible_count / len(assessments) * 100) if assessments else 0,
        'average_score': round(avg_score, 2),
        'level_counts': level_counts,
        'recent_assessments': assessments[:20],
    }

    return render(request, 'households/eligibility_dashboard.html', context)