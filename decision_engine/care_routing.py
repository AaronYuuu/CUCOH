"""
Care Navigation & Routing Decision Engine
Determines where patients should seek care based on clinical need,
availability, and Canadian healthcare system constraints
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
import math
from models.data_models import (
    UrgencyLevel, ProviderType, CareOption, CareRoutingPlan,
    PatientData
)


class CareRoutingEngine:
    """
    Decision engine for care navigation
    Prioritizes: 1) Appropriate acuity, 2) Wait times, 3) Gatekeeper rules
    """
    
    def __init__(self, government_api_client=None):
        """
        Args:
            government_api_client: Client for provincial health APIs
                                   (placeholder for real implementation)
        """
        self.gov_api = government_api_client or MockGovernmentAPI()
    
    def generate_routing_plan(
        self,
        consult_id: str,
        patient: PatientData,
        urgency: UrgencyLevel,
        approved_providers: List[ProviderType],
        clinical_summary: str
    ) -> CareRoutingPlan:
        """
        Generate complete care routing plan with ranked options
        """
        # Get all available care options
        available_options = self._get_available_options(
            patient, approved_providers, urgency
        )
        
        # Score and rank options
        ranked_options = self._rank_options(
            available_options, urgency, patient
        )
        
        # Generate referral materials if needed
        referral_note = None
        if ProviderType.SPECIALIST in approved_providers:
            referral_note = self._generate_referral_note(
                patient, clinical_summary
            )
        
        return CareRoutingPlan(
            routing_id=f"route_{consult_id}_{datetime.now().timestamp()}",
            consult_id=consult_id,
            patient_id=patient.patient_id,
            recommended_options=ranked_options[:5],  # Top 5 options
            urgency_level=urgency,
            data_sources_used=self.gov_api.get_data_sources(),
            data_freshness=datetime.now(),
            referral_note=referral_note,
            patient_summary=clinical_summary,
            generated_at=datetime.now()
        )
    
    def _get_available_options(
        self,
        patient: PatientData,
        approved_providers: List[ProviderType],
        urgency: UrgencyLevel
    ) -> List[CareOption]:
        """Fetch available care options from government APIs"""
        options = []
        
        for provider_type in approved_providers:
            # Query government API for facilities
            facilities = self.gov_api.get_facilities(
                provider_type=provider_type,
                postal_code=patient.postal_code,
                province=patient.province,
                urgency=urgency
            )
            
            for facility in facilities:
                option = CareOption(
                    option_id=f"opt_{facility['id']}",
                    provider_type=provider_type,
                    facility_name=facility['name'],
                    address=facility['address'],
                    distance_km=facility['distance_km'],
                    estimated_wait_time=facility.get('wait_time'),
                    accepts_walk_ins=facility.get('walk_in', False),
                    booking_url=facility.get('booking_url'),
                    phone=facility.get('phone'),
                    requires_referral=self._requires_referral(provider_type),
                    referral_note_generated=False,
                    priority_score=0.0  # Will be calculated
                )
                options.append(option)
        
        return options
    
    def _rank_options(
        self,
        options: List[CareOption],
        urgency: UrgencyLevel,
        patient: PatientData
    ) -> List[CareOption]:
        """
        Rank care options based on multiple factors
        
        Scoring algorithm:
        - Appropriate acuity (0-40 points)
        - Wait time (0-30 points)
        - Distance (0-20 points)
        - Gatekeeper rules (0-10 points)
        """
        scored_options = []
        
        for option in options:
            score = 0.0
            
            # 1. Appropriate acuity (highest priority)
            score += self._score_acuity(option.provider_type, urgency)
            
            # 2. Wait time
            score += self._score_wait_time(option.estimated_wait_time, urgency)
            
            # 3. Geographic proximity
            score += self._score_distance(option.distance_km)
            
            # 4. Gatekeeper rules and access
            score += self._score_access(option, patient)
            
            option.priority_score = score
            scored_options.append(option)
        
        # Sort by score (descending)
        return sorted(scored_options, key=lambda x: x.priority_score, reverse=True)
    
    def _score_acuity(self, provider_type: ProviderType, urgency: UrgencyLevel) -> float:
        """
        Score based on appropriateness of provider for urgency
        Returns 0-40 points
        """
        # Acuity matching matrix
        scoring = {
            UrgencyLevel.EMERGENCY: {
                ProviderType.ED: 40,
                ProviderType.URGENT_CARE: 20,
                ProviderType.GP: 0,
                ProviderType.NP: 0,
                ProviderType.RN: 0,
                ProviderType.SPECIALIST: 0,
            },
            UrgencyLevel.URGENT: {
                ProviderType.URGENT_CARE: 40,
                ProviderType.GP: 35,
                ProviderType.NP: 35,
                ProviderType.ED: 15,  # Penalize ED for non-emergency
                ProviderType.RN: 20,
                ProviderType.SPECIALIST: 25,
            },
            UrgencyLevel.ROUTINE: {
                ProviderType.GP: 40,
                ProviderType.NP: 38,
                ProviderType.SPECIALIST: 35,
                ProviderType.RN: 30,
                ProviderType.URGENT_CARE: 20,
                ProviderType.ED: 0,  # Strongly discourage ED for routine
            }
        }
        
        return scoring.get(urgency, {}).get(provider_type, 0)
    
    def _score_wait_time(self, wait_time: Optional[str], urgency: UrgencyLevel) -> float:
        """
        Score based on wait time appropriateness
        Returns 0-30 points
        """
        if not wait_time:
            return 15  # Neutral score if unknown
        
        # Parse wait time (e.g., "2 hours", "3 days", "2 weeks")
        wait_hours = self._parse_wait_time(wait_time)
        
        # Urgency-based thresholds
        thresholds = {
            UrgencyLevel.EMERGENCY: 2,      # < 2 hours ideal
            UrgencyLevel.URGENT: 48,        # < 48 hours ideal
            UrgencyLevel.ROUTINE: 336,      # < 2 weeks ideal
        }
        
        threshold = thresholds.get(urgency, 48)
        
        if wait_hours <= threshold * 0.5:
            return 30  # Excellent wait time
        elif wait_hours <= threshold:
            return 25  # Good wait time
        elif wait_hours <= threshold * 2:
            return 15  # Acceptable wait time
        else:
            return 5   # Long wait time
    
    def _score_distance(self, distance_km: float) -> float:
        """
        Score based on geographic proximity
        Returns 0-20 points
        """
        if distance_km <= 5:
            return 20
        elif distance_km <= 10:
            return 15
        elif distance_km <= 20:
            return 10
        elif distance_km <= 50:
            return 5
        else:
            return 2
    
    def _score_access(self, option: CareOption, patient: PatientData) -> float:
        """
        Score based on access considerations and gatekeeper rules
        Returns 0-10 points
        """
        score = 0.0
        
        # Walk-ins preferred for urgent needs
        if option.accepts_walk_ins:
            score += 5
        
        # Booking available
        if option.booking_url:
            score += 3
        
        # Patient has family doctor - prefer GP continuity
        if patient.has_family_doctor and option.provider_type == ProviderType.GP:
            score += 7
        
        # Penalize if requires referral and patient doesn't have GP
        if option.requires_referral and not patient.has_family_doctor:
            score -= 5
        
        return max(0, score)  # Don't go negative
    
    def _parse_wait_time(self, wait_time: str) -> float:
        """Parse wait time string to hours"""
        wait_time = wait_time.lower()
        
        # Handle ranges like "1-2 hours" - use midpoint
        if '-' in wait_time.split()[0]:
            try:
                low, high = wait_time.split()[0].split('-')
                avg = (float(low) + float(high)) / 2
                if "minute" in wait_time:
                    return avg / 60
                elif "hour" in wait_time:
                    return avg
                elif "day" in wait_time:
                    return avg * 24
                elif "week" in wait_time:
                    return avg * 24 * 7
            except:
                pass
        
        try:
            if "minute" in wait_time:
                return float(wait_time.split()[0]) / 60
            elif "hour" in wait_time:
                return float(wait_time.split()[0])
            elif "day" in wait_time:
                return float(wait_time.split()[0]) * 24
            elif "week" in wait_time:
                return float(wait_time.split()[0]) * 24 * 7
            elif "month" in wait_time:
                return float(wait_time.split()[0]) * 24 * 30
        except:
            pass
        
        return 999  # Unknown format, assume long
    
    def _requires_referral(self, provider_type: ProviderType) -> bool:
        """Check if provider type requires referral in Canadian system"""
        return provider_type in [ProviderType.SPECIALIST]
    
    def _generate_referral_note(
        self,
        patient: PatientData,
        clinical_summary: str
    ) -> str:
        """Generate referral letter for specialist"""
        return f"""REFERRAL REQUEST

Patient: {patient.patient_id}
Age: {patient.age} | Sex: {patient.sex}
Province: {patient.province}

REASON FOR REFERRAL:
{clinical_summary}

CLINICAL SUMMARY:
Patient requires specialist evaluation based on clinical decision support assessment.

This referral was generated through the Meduroam clinical decision support platform
and has been reviewed by a medical professional.

For questions, please contact referring provider through the Meduroam platform.
"""


class MockGovernmentAPI:
    """
    Mock implementation of government healthcare data APIs
    Replace with real provincial APIs in production
    """
    
    def get_facilities(
        self,
        provider_type: ProviderType,
        postal_code: str,
        province: str,
        urgency: UrgencyLevel
    ) -> List[Dict]:
        """
        Mock facility data
        Real implementation would call:
        - Ontario: Health Data Platform API
        - BC: HealthLink BC API
        - Alberta: AHS Wait Times API
        - etc.
        
        For MVP: Returns Kingston-area healthcare facilities
        """
        
        # Check if Kingston area (K7L postal code)
        is_kingston = postal_code.startswith("K7L")
        
        if is_kingston:
            # Kingston healthcare facilities (Queen's University area)
            facilities = {
                ProviderType.GP: [
                    {
                        "id": "gp_k001",
                        "name": "Queen's Family Health Team",
                        "address": "220 Bagot Street, Kingston, ON K7L 5E9",
                        "distance_km": 0.5,
                        "wait_time": "2-3 days",
                        "walk_in": False,
                        "booking_url": None,
                        "phone": "613-544-3400"
                    },
                    {
                        "id": "gp_k002",
                        "name": "Kingston Community Health Centre",
                        "address": "263 Weller Avenue, Kingston, ON K7K 7E8",
                        "distance_km": 2.1,
                        "wait_time": "1 week",
                        "walk_in": False,
                        "booking_url": None,
                        "phone": "613-542-2949"
                    },
                    {
                        "id": "gp_k003",
                        "name": "Princess Family Health Team",
                        "address": "752 King Street West, Kingston, ON K7L 1G5",
                        "distance_km": 1.8,
                        "wait_time": "3-5 days",
                        "walk_in": False,
                        "booking_url": None,
                        "phone": "613-544-3310"
                    }
                ],
                ProviderType.NP: [
                    {
                        "id": "np_k001",
                        "name": "Queen's University Student Wellness Services",
                        "address": "146 Stuart Street, Kingston, ON K7L 3N6",
                        "distance_km": 0.3,
                        "wait_time": "Same day - 2 days",
                        "walk_in": True,
                        "phone": "613-533-2506"
                    }
                ],
                ProviderType.URGENT_CARE: [
                    {
                        "id": "uc_k001",
                        "name": "Appletree Medical Group - Kingston",
                        "address": "1471 John Counter Boulevard, Kingston, ON K7M 8S8",
                        "distance_km": 4.2,
                        "wait_time": "1-2 hours",
                        "walk_in": True,
                        "phone": "613-384-2524"
                    },
                    {
                        "id": "uc_k002",
                        "name": "Kingston After Hours Clinic",
                        "address": "752 King Street West, Kingston, ON K7L 1G5",
                        "distance_km": 1.8,
                        "wait_time": "2-3 hours",
                        "walk_in": True,
                        "phone": "613-544-3310"
                    }
                ],
                ProviderType.ED: [
                    {
                        "id": "ed_k001",
                        "name": "Kingston Health Sciences Centre - Emergency",
                        "address": "76 Stuart Street, Kingston, ON K7L 2V7",
                        "distance_km": 0.4,
                        "wait_time": "Check online for current wait times",
                        "walk_in": True,
                        "phone": "613-548-3232",
                        "booking_url": "https://kingstonhsc.ca/patients-families-and-visitors/wait-times"
                    }
                ],
                ProviderType.SPECIALIST: [
                    {
                        "id": "spec_k001",
                        "name": "Hotel Dieu Hospital Specialty Clinics",
                        "address": "166 Brock Street, Kingston, ON K7L 5G2",
                        "distance_km": 0.8,
                        "wait_time": "4-8 weeks (referral required)",
                        "walk_in": False,
                        "booking_url": None,
                        "phone": "613-544-3310"
                    },
                    {
                        "id": "spec_k002",
                        "name": "Kingston Health Sciences Centre Specialists",
                        "address": "76 Stuart Street, Kingston, ON K7L 2V7",
                        "distance_km": 0.4,
                        "wait_time": "6-12 weeks (referral required)",
                        "walk_in": False,
                        "phone": "613-548-3232"
                    }
                ]
            }
        else:
            # Default Toronto-area facilities for non-Kingston postal codes
            facilities = {
                ProviderType.GP: [
                    {
                        "id": "gp_001",
                        "name": "University Family Health Team",
                        "address": "123 College St, Toronto, ON",
                        "distance_km": 2.5,
                        "wait_time": "3 days",
                        "walk_in": False,
                        "booking_url": "https://example.com/book",
                        "phone": "416-555-0100"
                    },
                    {
                        "id": "gp_002",
                        "name": "Downtown Medical Centre",
                        "address": "456 Queen St, Toronto, ON",
                        "distance_km": 4.1,
                        "wait_time": "1 week",
                        "walk_in": False,
                        "booking_url": "https://example.com/book2",
                        "phone": "416-555-0101"
                    }
                ],
                ProviderType.NP: [
                    {
                        "id": "np_001",
                        "name": "Nurse Practitioner Led Clinic",
                        "address": "789 Dundas St, Toronto, ON",
                        "distance_km": 3.2,
                        "wait_time": "24 hours",
                        "walk_in": True,
                        "phone": "416-555-0200"
                    }
                ],
                ProviderType.URGENT_CARE: [
                    {
                        "id": "uc_001",
                        "name": "Appletree Medical Walk-In",
                        "address": "321 Yonge St, Toronto, ON",
                        "distance_km": 1.8,
                        "wait_time": "2 hours",
                        "walk_in": True,
                        "phone": "416-555-0300"
                    },
                    {
                        "id": "uc_002",
                        "name": "East Toronto Urgent Care",
                        "address": "555 Pape Ave, Toronto, ON",
                        "distance_km": 6.5,
                        "wait_time": "90 minutes",
                        "walk_in": True,
                        "phone": "416-555-0301"
                    }
                ],
                ProviderType.ED: [
                    {
                        "id": "ed_001",
                        "name": "Toronto General Hospital ED",
                        "address": "200 Elizabeth St, Toronto, ON",
                        "distance_km": 3.5,
                        "wait_time": "4 hours",
                        "walk_in": True,
                        "phone": "416-340-3155"
                    }
                ],
                ProviderType.SPECIALIST: [
                    {
                        "id": "spec_001",
                        "name": "Specialty Medical Centre",
                        "address": "100 Medical Blvd, Toronto, ON",
                        "distance_km": 5.0,
                        "wait_time": "6 weeks",
                        "walk_in": False,
                        "booking_url": "https://example.com/specialist",
                        "phone": "416-555-0400"
                    }
                ]
            }
        
        return facilities.get(provider_type, [])
    
    def get_data_sources(self) -> List[str]:
        """Return list of data sources used"""
        return [
            "Mock Provincial Health Database",
            "Mock Wait Times API",
            "Mock Facility Registry"
        ]


class GatekeeperRules:
    """
    Canadian healthcare system gatekeeper rules
    """
    
    @staticmethod
    def can_access_specialist(
        patient: PatientData,
        has_referral: bool
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if patient can access specialist
        
        Returns:
            (can_access, reason_if_not)
        """
        if has_referral:
            return (True, None)
        
        if not patient.has_family_doctor:
            return (False, "Requires referral from GP or NP. Patient needs to establish care with family doctor first.")
        
        return (False, "Requires referral from primary care provider")
    
    @staticmethod
    def recommend_primary_care_first(
        patient: PatientData,
        urgency: UrgencyLevel
    ) -> bool:
        """
        Determine if patient should be directed to primary care first
        (Canadian gatekeeper model)
        """
        # Emergency - go straight to ED
        if urgency == UrgencyLevel.EMERGENCY:
            return False
        
        # If no family doctor and routine - should establish care
        if not patient.has_family_doctor and urgency == UrgencyLevel.ROUTINE:
            return True
        
        return False
