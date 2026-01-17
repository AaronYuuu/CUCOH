"""
Role-Based Permission System
Defines access control and authorization rules
"""

from enum import Enum
from typing import List, Set
from models.data_models import UserRole, WorkflowState


class Permission(str, Enum):
    """System permissions"""
    # Patient permissions
    VIEW_OWN_CONSULT = "VIEW_OWN_CONSULT"
    SUBMIT_SYMPTOMS = "SUBMIT_SYMPTOMS"
    RESPOND_TO_COMMUNICATION = "RESPOND_TO_COMMUNICATION"
    REQUEST_ESCALATION = "REQUEST_ESCALATION"
    VIEW_OWN_SOAP = "VIEW_OWN_SOAP"
    
    # Medical student permissions
    VIEW_ASSIGNED_CONSULTS = "VIEW_ASSIGNED_CONSULTS"
    VIEW_AI_REASONING = "VIEW_AI_REASONING"
    VALIDATE_ASSESSMENT = "VALIDATE_ASSESSMENT"
    MODIFY_SOAP = "MODIFY_SOAP"
    COMMUNICATE_WITH_PATIENT = "COMMUNICATE_WITH_PATIENT"
    ESCALATE_TO_RESIDENT = "ESCALATE_TO_RESIDENT"
    
    # Resident/Physician permissions
    VIEW_ALL_ESCALATIONS = "VIEW_ALL_ESCALATIONS"
    VIEW_STUDENT_REASONING = "VIEW_STUDENT_REASONING"
    OVERRIDE_ASSESSMENT = "OVERRIDE_ASSESSMENT"
    FINALIZE_SOAP = "FINALIZE_SOAP"
    SIGN_AS_PHYSICIAN_OF_RECORD = "SIGN_AS_PHYSICIAN_OF_RECORD"
    PROVIDE_TEACHING_FEEDBACK = "PROVIDE_TEACHING_FEEDBACK"
    
    # Admin permissions
    VIEW_ALL_CONSULTS = "VIEW_ALL_CONSULTS"
    VIEW_AUDIT_LOGS = "VIEW_AUDIT_LOGS"
    MANAGE_USERS = "MANAGE_USERS"
    SYSTEM_CONFIGURATION = "SYSTEM_CONFIGURATION"


# Permission mapping by role
ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.PATIENT: {
        Permission.VIEW_OWN_CONSULT,
        Permission.SUBMIT_SYMPTOMS,
        Permission.RESPOND_TO_COMMUNICATION,
        Permission.REQUEST_ESCALATION,
        Permission.VIEW_OWN_SOAP,
    },
    
    UserRole.MEDICAL_STUDENT: {
        Permission.VIEW_ASSIGNED_CONSULTS,
        Permission.VIEW_AI_REASONING,
        Permission.VALIDATE_ASSESSMENT,
        Permission.MODIFY_SOAP,
        Permission.COMMUNICATE_WITH_PATIENT,
        Permission.ESCALATE_TO_RESIDENT,
    },
    
    UserRole.RESIDENT: {
        Permission.VIEW_ALL_ESCALATIONS,
        Permission.VIEW_STUDENT_REASONING,
        Permission.OVERRIDE_ASSESSMENT,
        Permission.FINALIZE_SOAP,
        Permission.SIGN_AS_PHYSICIAN_OF_RECORD,
        Permission.PROVIDE_TEACHING_FEEDBACK,
        Permission.VIEW_AI_REASONING,
        Permission.VIEW_ASSIGNED_CONSULTS,
    },
    
    UserRole.ATTENDING_PHYSICIAN: {
        Permission.VIEW_ALL_ESCALATIONS,
        Permission.VIEW_STUDENT_REASONING,
        Permission.OVERRIDE_ASSESSMENT,
        Permission.FINALIZE_SOAP,
        Permission.SIGN_AS_PHYSICIAN_OF_RECORD,
        Permission.PROVIDE_TEACHING_FEEDBACK,
        Permission.VIEW_AI_REASONING,
        Permission.VIEW_ASSIGNED_CONSULTS,
        Permission.VIEW_ALL_CONSULTS,
    },
    
    UserRole.ADMIN: {
        Permission.VIEW_ALL_CONSULTS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.MANAGE_USERS,
        Permission.SYSTEM_CONFIGURATION,
    }
}


# State-based access control: who can move workflow to which states
STATE_TRANSITION_PERMISSIONS: dict[WorkflowState, dict[UserRole, List[WorkflowState]]] = {
    WorkflowState.INITIAL: {
        UserRole.PATIENT: [WorkflowState.AI_PROCESSING],
    },
    
    WorkflowState.AI_PROCESSING: {
        # Automatic transition - no human permission required
    },
    
    WorkflowState.STUDENT_REVIEW: {
        UserRole.MEDICAL_STUDENT: [
            WorkflowState.PATIENT_COMMUNICATION,
            WorkflowState.RESIDENT_ESCALATION
        ],
    },
    
    WorkflowState.PATIENT_COMMUNICATION: {
        UserRole.PATIENT: [
            WorkflowState.PATIENT_ACCEPTED,
            WorkflowState.PATIENT_QUESTIONS,
            WorkflowState.RESIDENT_ESCALATION
        ],
    },
    
    WorkflowState.PATIENT_QUESTIONS: {
        UserRole.MEDICAL_STUDENT: [
            WorkflowState.PATIENT_COMMUNICATION,
            WorkflowState.RESIDENT_ESCALATION
        ],
    },
    
    WorkflowState.PATIENT_ACCEPTED: {
        # Automatic transition to FINAL_APPROVED
    },
    
    WorkflowState.RESIDENT_ESCALATION: {
        UserRole.RESIDENT: [WorkflowState.FINAL_APPROVED],
        UserRole.ATTENDING_PHYSICIAN: [WorkflowState.FINAL_APPROVED],
    },
    
    WorkflowState.FINAL_APPROVED: {
        # Automatic transition to CARE_ROUTING
    },
    
    WorkflowState.CARE_ROUTING: {
        # Automatic transition to COMPLETE
    },
    
    WorkflowState.COMPLETE: {
        # Terminal state
    }
}


class PermissionChecker:
    """Authorization utility class"""
    
    @staticmethod
    def has_permission(user_role: UserRole, permission: Permission) -> bool:
        """Check if a role has a specific permission"""
        return permission in ROLE_PERMISSIONS.get(user_role, set())
    
    @staticmethod
    def can_transition_state(
        user_role: UserRole, 
        from_state: WorkflowState, 
        to_state: WorkflowState
    ) -> bool:
        """Check if user can transition workflow from one state to another"""
        allowed_transitions = STATE_TRANSITION_PERMISSIONS.get(from_state, {})
        role_transitions = allowed_transitions.get(user_role, [])
        return to_state in role_transitions
    
    @staticmethod
    def get_allowed_transitions(
        user_role: UserRole, 
        current_state: WorkflowState
    ) -> List[WorkflowState]:
        """Get list of states user can transition to from current state"""
        allowed_transitions = STATE_TRANSITION_PERMISSIONS.get(current_state, {})
        return allowed_transitions.get(user_role, [])


# ==================== PHYSICIAN-OF-RECORD LOGIC ====================

class PhysicianOfRecordRules:
    """
    Canadian medical-legal framework for physician responsibility
    """
    
    @staticmethod
    def requires_physician_signature(urgency: str, is_escalated: bool) -> bool:
        """Determine if consult requires supervising physician signature"""
        # All escalated cases MUST have physician signature
        if is_escalated:
            return True
        
        # Emergency urgency ALWAYS requires physician signature
        if urgency == "EMERGENCY":
            return True
        
        # Urgent cases should have physician review (24/7 coverage)
        if urgency == "URGENT":
            return True
        
        # Routine cases: student can proceed with async oversight
        return False
    
    @staticmethod
    def get_supervision_requirements(urgency: str) -> dict:
        """Get supervision requirements based on urgency"""
        requirements = {
            "ROUTINE": {
                "physician_signature_required": False,
                "review_timeframe": "async",
                "student_can_proceed": True,
                "physician_notification": "batch_summary"
            },
            "URGENT": {
                "physician_signature_required": True,
                "review_timeframe": "< 4 hours",
                "student_can_proceed": False,
                "physician_notification": "immediate"
            },
            "EMERGENCY": {
                "physician_signature_required": True,
                "review_timeframe": "< 1 hour",
                "student_can_proceed": False,
                "physician_notification": "immediate",
                "additional_requirement": "Direct physician contact recommended"
            }
        }
        return requirements.get(urgency, requirements["URGENT"])


# ==================== 24/7 COVERAGE CONSIDERATIONS ====================

class CoverageModel:
    """
    24/7 availability framework
    """
    
    @staticmethod
    def get_on_call_requirements() -> dict:
        """Define on-call coverage requirements"""
        return {
            "medical_students": {
                "shifts": "8-hour rotating shifts",
                "coverage": "24/7",
                "backup": "Resident on-call can pick up queue"
            },
            "residents": {
                "shifts": "12-hour on-call shifts",
                "coverage": "24/7",
                "backup": "Attending physician escalation path"
            },
            "attending_physicians": {
                "shifts": "24-hour on-call rotation",
                "coverage": "24/7",
                "backup": "Cross-coverage agreement with partner physicians"
            }
        }
    
    @staticmethod
    def get_escalation_path_by_time() -> dict:
        """Define escalation based on time of day"""
        return {
            "business_hours": {
                "hours": "8am-6pm weekdays",
                "student_to": "Assigned resident",
                "resident_to": "Supervising attending"
            },
            "after_hours": {
                "hours": "6pm-8am weekdays, weekends",
                "student_to": "On-call resident",
                "resident_to": "On-call attending"
            },
            "emergency_override": {
                "description": "Any life-threatening situation",
                "action": "Direct 911 / ED referral, notify on-call attending immediately"
            }
        }
