"""
Meduroam Data Models
Core data structures for clinical decision support workflow
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ==================== ENUMS ====================

class WorkflowState(str, Enum):
    """Workflow state machine"""
    INITIAL = "INITIAL"
    AI_PROCESSING = "AI_PROCESSING"
    STUDENT_REVIEW = "STUDENT_REVIEW"
    PATIENT_COMMUNICATION = "PATIENT_COMMUNICATION"
    PATIENT_QUESTIONS = "PATIENT_QUESTIONS"
    PATIENT_ACCEPTED = "PATIENT_ACCEPTED"
    RESIDENT_ESCALATION = "RESIDENT_ESCALATION"
    FINAL_APPROVED = "FINAL_APPROVED"
    CARE_ROUTING = "CARE_ROUTING"
    COMPLETE = "COMPLETE"


class UrgencyLevel(str, Enum):
    """Clinical urgency classification"""
    ROUTINE = "ROUTINE"          # Can wait days/weeks
    URGENT = "URGENT"            # Should be seen within 24-48 hours
    EMERGENCY = "EMERGENCY"      # Requires immediate attention


class ProviderType(str, Enum):
    """Types of healthcare providers in Canadian system"""
    GP = "GP"                           # General Practitioner / Family Physician
    NP = "NP"                           # Nurse Practitioner
    RN = "RN"                           # Registered Nurse
    PSW = "PSW"                         # Personal Support Worker
    SPECIALIST = "SPECIALIST"           # Requires referral
    URGENT_CARE = "URGENT_CARE"         # Walk-in urgent care clinic
    ED = "ED"                           # Emergency Department


class StudentDecision(str, Enum):
    """Medical student assessment decision"""
    AGREE = "AGREE"              # Agrees with AI assessment
    MODIFY = "MODIFY"            # Accepts with modifications
    DISAGREE = "DISAGREE"        # Disagrees with AI assessment


class ResidentDecision(str, Enum):
    """Supervising physician final decision"""
    APPROVE = "APPROVE"          # Approves student/AI plan
    MODIFY = "MODIFY"            # Modifies the plan
    OVERRIDE = "OVERRIDE"        # Completely overrides


class UserRole(str, Enum):
    """System user roles"""
    PATIENT = "PATIENT"
    MEDICAL_STUDENT = "MEDICAL_STUDENT"
    RESIDENT = "RESIDENT"
    ATTENDING_PHYSICIAN = "ATTENDING_PHYSICIAN"
    ADMIN = "ADMIN"


# ==================== PATIENT DATA ====================

class PatientData(BaseModel):
    """Patient demographic and contact information"""
    patient_id: str
    age: int
    sex: str
    province: str
    postal_code: str
    has_family_doctor: bool
    ohip_number: Optional[str] = None  # Ontario Health Insurance
    phone: Optional[str] = None
    email: Optional[str] = None


class PatientTranscript(BaseModel):
    """Patient symptom description and interaction history"""
    transcript_id: str
    patient_id: str
    chief_complaint: str
    symptom_description: str
    duration: str
    severity: str
    associated_symptoms: List[str]
    medical_history: List[str]
    medications: List[str]
    allergies: List[str]
    timestamp: datetime


# ==================== AI GENERATED CONTENT ====================

class SOAPNote(BaseModel):
    """AI-generated SOAP note"""
    subjective: str          # Patient's description of symptoms
    objective: str           # Measurable/observable findings
    assessment: str          # Clinical impression/diagnosis
    plan: str               # Recommended next steps
    
    
class AIReasoning(BaseModel):
    """AI reasoning trace for transparency"""
    differential_diagnosis: List[str]     # Possible conditions considered
    red_flags_assessed: List[str]         # Dangerous symptoms ruled out
    clinical_reasoning: str               # Explanation of thought process
    confidence_level: float = Field(ge=0.0, le=1.0)
    supporting_evidence: List[str]
    ruled_out_conditions: List[str]


class AIConsultOutput(BaseModel):
    """Complete AI analysis output"""
    consult_id: str
    patient_id: str
    transcript_id: str
    soap_note: SOAPNote
    reasoning: AIReasoning
    preliminary_urgency: UrgencyLevel
    suggested_providers: List[ProviderType]
    generated_at: datetime
    ai_model_version: str


# ==================== MEDICAL STUDENT REVIEW ====================

class StudentReview(BaseModel):
    """Medical student validation and assessment"""
    review_id: str
    consult_id: str
    student_id: str
    student_name: str
    
    # Required structured decisions
    assessment_decision: StudentDecision
    validated_urgency: UrgencyLevel
    selected_providers: List[ProviderType]
    
    # Required structured reasoning (no free-text only!)
    clinical_reasoning_summary: str = Field(min_length=50)
    key_differentials: List[str]
    red_flags_assessment: str = Field(min_length=30)
    provider_selection_rationale: str = Field(min_length=30)
    
    # Optional modifications to AI SOAP
    modified_soap: Optional[SOAPNote] = None
    assessment_modifications: Optional[str] = None
    plan_modifications: Optional[str] = None
    
    # Escalation decision
    requires_escalation: bool
    escalation_reason: Optional[str] = None
    
    reviewed_at: datetime
    time_spent_minutes: float


# ==================== PATIENT COMMUNICATION ====================

class PatientCommunication(BaseModel):
    """Plain-language summary sent to patient"""
    communication_id: str
    consult_id: str
    
    # Plain-language sections
    likely_diagnosis: str
    ruled_out_dangerous: List[str]
    next_steps: str
    rationale: str
    
    # Urgency communication
    urgency_explanation: str
    timeframe: str
    
    sent_at: datetime
    sent_by_student_id: str


class PatientResponse(BaseModel):
    """Patient response to communication"""
    response_id: str
    communication_id: str
    patient_id: str
    
    action: str  # "ACCEPT" | "QUESTION" | "ESCALATE"
    questions: Optional[List[str]] = None
    escalation_concern: Optional[str] = None
    
    responded_at: datetime


# ==================== RESIDENT OVERSIGHT ====================

class ResidentReview(BaseModel):
    """Supervising physician escalation review"""
    review_id: str
    consult_id: str
    resident_id: str
    resident_name: str
    license_number: str
    
    # Decision
    decision: ResidentDecision
    
    # Final validated data
    final_soap: SOAPNote
    final_urgency: UrgencyLevel
    final_providers: List[ProviderType]
    
    # Resident reasoning
    clinical_rationale: str
    modifications_made: Optional[str] = None
    teaching_points: Optional[str] = None  # Feedback to student
    
    reviewed_at: datetime
    time_spent_minutes: float


# ==================== FINAL RECORD ====================

class FinalSOAPRecord(BaseModel):
    """Final patient-visible SOAP note with clear attribution"""
    record_id: str
    consult_id: str
    patient_id: str
    
    # Attribution sections
    ai_contribution: Dict[str, Any]
    student_contribution: Dict[str, Any]
    resident_contribution: Optional[Dict[str, Any]] = None
    
    # Final validated content
    final_soap: SOAPNote
    final_urgency: UrgencyLevel
    final_providers: List[ProviderType]
    
    # Physician of record
    supervising_physician_id: Optional[str] = None
    supervising_physician_name: Optional[str] = None
    
    created_at: datetime
    is_final: bool = True


# ==================== CARE ROUTING ====================

class CareOption(BaseModel):
    """Individual care routing option"""
    option_id: str
    provider_type: ProviderType
    facility_name: str
    address: str
    distance_km: float
    
    # Availability data
    estimated_wait_time: Optional[str] = None
    accepts_walk_ins: bool
    booking_url: Optional[str] = None
    phone: Optional[str] = None
    
    # Gatekeeper considerations
    requires_referral: bool
    referral_note_generated: bool = False
    
    # Ranking
    priority_score: float  # Higher = better match


class CareRoutingPlan(BaseModel):
    """Complete care navigation output"""
    routing_id: str
    consult_id: str
    patient_id: str
    
    recommended_options: List[CareOption]
    urgency_level: UrgencyLevel
    
    # Government data integration
    data_sources_used: List[str]
    data_freshness: datetime
    
    # Referral materials
    referral_note: Optional[str] = None
    patient_summary: str
    
    generated_at: datetime


# ==================== WORKFLOW TRACKING ====================

class ConsultWorkflow(BaseModel):
    """Master workflow tracker for entire consult"""
    consult_id: str
    patient_id: str
    
    # State management
    current_state: WorkflowState
    state_history: List[Dict[str, Any]]
    
    # References to all components
    transcript_id: str
    ai_output_id: Optional[str] = None
    student_review_id: Optional[str] = None
    patient_communication_id: Optional[str] = None
    patient_response_id: Optional[str] = None
    resident_review_id: Optional[str] = None
    final_record_id: Optional[str] = None
    routing_plan_id: Optional[str] = None
    
    # Timing
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    # Flags
    is_escalated: bool = False
    requires_immediate_attention: bool = False
