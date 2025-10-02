"""
Enhanced Household Eligibility and Scoring System
Implements sophisticated scoring algorithms for household qualification
"""

from decimal import Decimal
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class EligibilityScorer:
    """
    Advanced eligibility scoring system for household qualification
    """

    # Scoring weights for different criteria
    SCORING_WEIGHTS = {
        'poverty_index': 0.30,      # 30% - PPI score
        'income_level': 0.25,       # 25% - Income assessment
        'asset_ownership': 0.15,    # 15% - Asset evaluation
        'social_factors': 0.15,     # 15% - Social vulnerability
        'geographic': 0.10,         # 10% - Geographic factors
        'demographic': 0.05,        # 5% - Age, family size, etc.
    }

    # Scoring thresholds
    ELIGIBILITY_THRESHOLDS = {
        'highly_eligible': 80,      # 80+ score
        'eligible': 60,             # 60-79 score
        'marginally_eligible': 40,  # 40-59 score
        'not_eligible': 0,          # Below 40
    }

    def __init__(self, household):
        self.household = household
        self.scores = {}
        self.total_score = 0
        self.eligibility_level = 'not_eligible'

    def calculate_comprehensive_score(self):
        """Calculate comprehensive eligibility score"""
        self.scores = {
            'poverty_index': self._score_poverty_index(),
            'income_level': self._score_income_level(),
            'asset_ownership': self._score_asset_ownership(),
            'social_factors': self._score_social_factors(),
            'geographic': self._score_geographic_factors(),
            'demographic': self._score_demographic_factors(),
        }

        # Calculate weighted total score
        self.total_score = sum(
            score * self.SCORING_WEIGHTS[category]
            for category, score in self.scores.items()
        )

        # Determine eligibility level
        if self.total_score >= self.ELIGIBILITY_THRESHOLDS['highly_eligible']:
            self.eligibility_level = 'highly_eligible'
        elif self.total_score >= self.ELIGIBILITY_THRESHOLDS['eligible']:
            self.eligibility_level = 'eligible'
        elif self.total_score >= self.ELIGIBILITY_THRESHOLDS['marginally_eligible']:
            self.eligibility_level = 'marginally_eligible'
        else:
            self.eligibility_level = 'not_eligible'

        return {
            'total_score': round(self.total_score, 2),
            'eligibility_level': self.eligibility_level,
            'category_scores': self.scores,
            'recommendation': self._get_recommendation(),
            'improvement_areas': self._get_improvement_areas(),
        }

    def _score_poverty_index(self):
        """Score based on Poverty Probability Index (PPI)"""
        ppi_score = self.household.latest_ppi_score
        if ppi_score:

            # Convert PPI score to 0-100 scale (lower PPI = higher poverty = higher eligibility)
            if ppi_score <= 20:
                return 100  # Extremely poor - highest eligibility
            elif ppi_score <= 40:
                return 80   # Very poor
            elif ppi_score <= 60:
                return 60   # Moderately poor
            elif ppi_score <= 80:
                return 30   # Less poor
            else:
                return 10   # Least poor - lowest eligibility

        return 50  # Default score if PPI not available

    def _score_income_level(self):
        """Score based on household income"""
        monthly_income = getattr(self.household, 'monthly_income', 0) or 0

        # Kenya poverty line considerations (approximate figures)
        extreme_poverty_line = 2500   # KES per month
        poverty_line = 5000          # KES per month

        if monthly_income <= extreme_poverty_line:
            return 100  # Extreme poverty - highest eligibility
        elif monthly_income <= poverty_line:
            return 80   # Below poverty line
        elif monthly_income <= poverty_line * 1.5:
            return 60   # Vulnerable
        elif monthly_income <= poverty_line * 2:
            return 40   # Low income
        else:
            return 20   # Above target income level

    def _score_asset_ownership(self):
        """Score based on asset ownership"""
        assets = getattr(self.household, 'assets', {}) or {}

        # Define asset categories and weights
        basic_assets = ['bicycle', 'radio', 'mobile_phone']
        productive_assets = ['livestock', 'land', 'business_equipment']
        luxury_assets = ['car', 'motorcycle', 'television', 'refrigerator']

        basic_count = sum(1 for asset in basic_assets if assets.get(asset, False))
        productive_count = sum(1 for asset in productive_assets if assets.get(asset, False))
        luxury_count = sum(1 for asset in luxury_assets if assets.get(asset, False))

        # Calculate score (fewer assets = higher eligibility)
        if luxury_count > 2:
            return 10   # Too many luxury assets
        elif luxury_count > 0 or productive_count > 2:
            return 30   # Some valuable assets
        elif productive_count > 0 or basic_count > 2:
            return 60   # Few basic assets
        elif basic_count > 0:
            return 80   # Very few assets
        else:
            return 100  # No recorded assets - highest eligibility

    def _score_social_factors(self):
        """Score based on social vulnerability factors"""
        score = 50  # Base score

        # Female-headed household
        if getattr(self.household, 'head_gender', '') == 'female':
            score += 15

        # Elderly head of household
        head_age = getattr(self.household, 'head_age', 0)
        if head_age >= 65:
            score += 10
        elif head_age >= 55:
            score += 5

        # Presence of disabled members
        disabled_members = getattr(self.household, 'disabled_members_count', 0)
        if disabled_members > 0:
            score += 15

        # Single-parent household
        if getattr(self.household, 'is_single_parent', False):
            score += 10

        # Number of dependents
        total_members = getattr(self.household, 'total_members', 1)
        working_members = getattr(self.household, 'working_members_count', 1)
        dependency_ratio = (total_members - working_members) / max(working_members, 1)

        if dependency_ratio >= 3:
            score += 15
        elif dependency_ratio >= 2:
            score += 10
        elif dependency_ratio >= 1:
            score += 5

        return min(score, 100)  # Cap at 100

    def _score_geographic_factors(self):
        """Score based on geographic location and accessibility"""
        location = getattr(self.household, 'location', '') or ''
        village = getattr(self.household, 'village', None)

        score = 50  # Base score

        # Remote/rural areas get higher scores
        if any(keyword in location.lower() for keyword in ['remote', 'rural', 'isolated']):
            score += 20

        # Distance to markets, schools, health facilities
        if hasattr(village, 'distance_to_market'):
            market_distance = getattr(village, 'distance_to_market', 0)
            if market_distance > 20:  # km
                score += 15
            elif market_distance > 10:
                score += 10
            elif market_distance > 5:
                score += 5

        # Infrastructure access
        has_electricity = getattr(self.household, 'has_electricity', False)
        has_water_access = getattr(self.household, 'has_clean_water', False)

        if not has_electricity:
            score += 10
        if not has_water_access:
            score += 15

        return min(score, 100)

    def _score_demographic_factors(self):
        """Score based on demographic characteristics"""
        score = 50  # Base score

        # Household size
        total_members = getattr(self.household, 'total_members', 1)
        if total_members >= 8:
            score += 20  # Large households
        elif total_members >= 6:
            score += 15
        elif total_members >= 4:
            score += 10
        elif total_members <= 2:
            score -= 10  # Small households might be less vulnerable

        # Children under 5
        children_under_5 = getattr(self.household, 'children_under_5_count', 0)
        if children_under_5 >= 3:
            score += 15
        elif children_under_5 >= 2:
            score += 10
        elif children_under_5 >= 1:
            score += 5

        # Education level of head
        head_education = getattr(self.household, 'head_education_level', 'none')
        if head_education in ['none', 'primary_incomplete']:
            score += 15
        elif head_education == 'primary_complete':
            score += 10
        elif head_education == 'secondary_incomplete':
            score += 5

        return min(max(score, 0), 100)

    def _get_recommendation(self):
        """Get recommendation based on eligibility level"""
        recommendations = {
            'highly_eligible': "Highly recommended for immediate enrollment. This household meets all criteria for ultra-poor graduation program.",
            'eligible': "Recommended for enrollment. This household would benefit significantly from the UPG program.",
            'marginally_eligible': "Consider for enrollment based on program capacity. May need additional assessment of specific vulnerabilities.",
            'not_eligible': "Not recommended for ultra-poor graduation program. Consider referral to other appropriate programs.",
        }
        return recommendations.get(self.eligibility_level, "Unable to determine recommendation.")

    def _get_improvement_areas(self):
        """Identify areas where household could improve eligibility"""
        areas = []

        for category, score in self.scores.items():
            if score < 60:  # Low scoring areas
                if category == 'poverty_index':
                    areas.append("Consider updated PPI assessment")
                elif category == 'income_level':
                    areas.append("Income documentation may need verification")
                elif category == 'asset_ownership':
                    areas.append("Asset assessment may need review")
                elif category == 'social_factors':
                    areas.append("Social vulnerability factors need assessment")
                elif category == 'geographic':
                    areas.append("Geographic accessibility factors")
                elif category == 'demographic':
                    areas.append("Demographic characteristics assessment")

        return areas

    def is_eligible_for_program(self, program_type='graduation'):
        """Check if household is eligible for specific program type"""
        result = self.calculate_comprehensive_score()

        if program_type == 'graduation':
            # Ultra-poor graduation program
            return result['eligibility_level'] in ['highly_eligible', 'eligible']
        elif program_type == 'general':
            # General poverty alleviation programs
            return result['eligibility_level'] != 'not_eligible'

        return False


class HouseholdQualificationTool:
    """
    Tool for qualifying households with detailed assessment
    """

    def __init__(self, household):
        self.household = household
        self.scorer = EligibilityScorer(household)

    def run_qualification_assessment(self):
        """Run comprehensive qualification assessment"""
        # Get eligibility score
        eligibility_result = self.scorer.calculate_comprehensive_score()

        # Additional qualification checks
        qualification_checks = {
            'geographic_eligibility': self._check_geographic_eligibility(),
            'program_capacity': self._check_program_capacity(),
            'previous_participation': self._check_previous_participation(),
            'consent_and_commitment': self._check_consent_commitment(),
        }

        # Final qualification decision
        final_qualification = self._make_final_decision(
            eligibility_result, qualification_checks
        )

        return {
            'eligibility_assessment': eligibility_result,
            'qualification_checks': qualification_checks,
            'final_qualification': final_qualification,
            'next_steps': self._get_next_steps(final_qualification),
            'assessment_date': timezone.now(),
        }

    def _check_geographic_eligibility(self):
        """Check if household is in program target area"""
        village = getattr(self.household, 'village', None)
        if village and hasattr(village, 'is_program_area'):
            return getattr(village, 'is_program_area', False)
        return True  # Default to true if not specified

    def _check_program_capacity(self):
        """Check if there's capacity in local program"""
        # This would check against active programs and enrollment caps
        return True  # Simplified for now

    def _check_previous_participation(self):
        """Check if household has participated in similar programs"""
        # Check for previous program participation
        return True  # Simplified - would check program history

    def _check_consent_commitment(self):
        """Check household consent and commitment to participate"""
        # This would involve consent forms and commitment assessments
        return getattr(self.household, 'consent_given', False)

    def _make_final_decision(self, eligibility_result, qualification_checks):
        """Make final qualification decision"""
        # Must be eligible and pass all qualification checks
        is_eligible = eligibility_result['eligibility_level'] in ['highly_eligible', 'eligible']
        all_checks_pass = all(qualification_checks.values())

        if is_eligible and all_checks_pass:
            return {
                'qualified': True,
                'qualification_level': eligibility_result['eligibility_level'],
                'priority_score': eligibility_result['total_score'],
                'status': 'qualified',
            }
        elif is_eligible:
            return {
                'qualified': False,
                'qualification_level': 'conditional',
                'priority_score': eligibility_result['total_score'],
                'status': 'needs_review',
                'blocking_factors': [
                    check for check, passed in qualification_checks.items() if not passed
                ],
            }
        else:
            return {
                'qualified': False,
                'qualification_level': 'not_qualified',
                'priority_score': eligibility_result['total_score'],
                'status': 'not_qualified',
            }

    def _get_next_steps(self, final_qualification):
        """Get recommended next steps based on qualification result"""
        if final_qualification['qualified']:
            return [
                "Proceed with program enrollment",
                "Complete household registration",
                "Assign to mentor",
                "Schedule initial training sessions",
            ]
        elif final_qualification['status'] == 'needs_review':
            return [
                "Address blocking factors",
                "Complete additional assessments",
                "Obtain required documentation",
                "Resubmit for qualification review",
            ]
        else:
            return [
                "Refer to alternative programs",
                "Provide resource information",
                "Consider re-assessment in future",
            ]


# Utility functions for quick eligibility checks
def quick_eligibility_check(household):
    """Quick eligibility check for screening purposes"""
    scorer = EligibilityScorer(household)
    result = scorer.calculate_comprehensive_score()
    return result['eligibility_level'] in ['highly_eligible', 'eligible']


def batch_eligibility_assessment(households):
    """Assess eligibility for multiple households"""
    results = []
    for household in households:
        scorer = EligibilityScorer(household)
        result = scorer.calculate_comprehensive_score()
        results.append({
            'household_id': household.id,
            'household_name': household.name,
            'total_score': result['total_score'],
            'eligibility_level': result['eligibility_level'],
            'eligible': result['eligibility_level'] in ['highly_eligible', 'eligible'],
        })

    # Sort by score (highest first)
    results.sort(key=lambda x: x['total_score'], reverse=True)
    return results