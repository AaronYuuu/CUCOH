"""
Workflow State Machine
Manages consult state transitions and validation
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from models.data_models import (
    ConsultWorkflow, WorkflowState, UserRole, UrgencyLevel
)
from roles.permissions import PermissionChecker


class WorkflowEngine:
    """Manages workflow state transitions and validation"""
    
    def __init__(self):
        self.permission_checker = PermissionChecker()
    
    def create_workflow(
        self, 
        consult_id: str, 
        patient_id: str, 
        transcript_id: str
    ) -> ConsultWorkflow:
        """Initialize a new consult workflow"""
        return ConsultWorkflow(
            consult_id=consult_id,
            patient_id=patient_id,
            transcript_id=transcript_id,
            current_state=WorkflowState.INITIAL,
            state_history=[{
                "state": WorkflowState.INITIAL,
                "timestamp": datetime.now().isoformat(),
                "triggered_by": "system"
            }],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def transition_state(
        self,
        workflow: ConsultWorkflow,
        new_state: WorkflowState,
        user_role: UserRole,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConsultWorkflow:
        """
        Transition workflow to new state with permission checking
        
        Raises:
            PermissionError: If user doesn't have permission for transition
            ValueError: If transition is invalid
        """
        # Check permission
        if not self.permission_checker.can_transition_state(
            user_role, workflow.current_state, new_state
        ):
            raise PermissionError(
                f"{user_role} cannot transition from {workflow.current_state} to {new_state}"
            )
        
        # Validate state transition logic
        self._validate_transition(workflow, new_state)
        
        # Update workflow
        workflow.current_state = new_state
        workflow.updated_at = datetime.now()
        
        # Record state history
        history_entry = {
            "state": new_state,
            "timestamp": datetime.now().isoformat(),
            "triggered_by": user_id,
            "user_role": user_role,
        }
        if metadata:
            history_entry["metadata"] = metadata
        
        workflow.state_history.append(history_entry)
        
        # Mark completion if terminal state
        if new_state == WorkflowState.COMPLETE:
            workflow.completed_at = datetime.now()
        
        return workflow
    
    def _validate_transition(
        self, 
        workflow: ConsultWorkflow, 
        new_state: WorkflowState
    ) -> None:
        """Validate that workflow has required data for transition"""
        
        validations = {
            WorkflowState.STUDENT_REVIEW: self._require_ai_output,
            WorkflowState.PATIENT_COMMUNICATION: self._require_student_review,
            WorkflowState.RESIDENT_ESCALATION: self._require_escalation_trigger,
            WorkflowState.FINAL_APPROVED: self._require_final_decision,
            WorkflowState.CARE_ROUTING: self._require_final_record,
        }
        
        validator = validations.get(new_state)
        if validator:
            validator(workflow)
    
    def _require_ai_output(self, workflow: ConsultWorkflow) -> None:
        if not workflow.ai_output_id:
            raise ValueError("AI output required before student review")
    
    def _require_student_review(self, workflow: ConsultWorkflow) -> None:
        if not workflow.student_review_id:
            raise ValueError("Student review required before patient communication")
    
    def _require_escalation_trigger(self, workflow: ConsultWorkflow) -> None:
        # Can be triggered by student or patient
        if not (workflow.student_review_id or workflow.patient_response_id):
            raise ValueError("Escalation requires student review or patient response")
    
    def _require_final_decision(self, workflow: ConsultWorkflow) -> None:
        # Must have either patient acceptance OR resident review
        if not (workflow.patient_response_id or workflow.resident_review_id):
            raise ValueError("Final approval requires patient acceptance or resident decision")
    
    def _require_final_record(self, workflow: ConsultWorkflow) -> None:
        if not workflow.final_record_id:
            raise ValueError("Final SOAP record required before care routing")
    
    def auto_transition(
        self,
        workflow: ConsultWorkflow,
        new_state: WorkflowState
    ) -> ConsultWorkflow:
        """
        Automatic state transition (no user permission required)
        Used for system-triggered transitions
        """
        self._validate_transition(workflow, new_state)
        
        workflow.current_state = new_state
        workflow.updated_at = datetime.now()
        
        workflow.state_history.append({
            "state": new_state,
            "timestamp": datetime.now().isoformat(),
            "triggered_by": "system_auto",
            "user_role": "system"
        })
        
        if new_state == WorkflowState.COMPLETE:
            workflow.completed_at = datetime.now()
        
        return workflow
    
    def get_next_actions(
        self, 
        workflow: ConsultWorkflow,
        user_role: UserRole
    ) -> List[Dict[str, Any]]:
        """Get available next actions for user based on current state"""
        allowed_states = self.permission_checker.get_allowed_transitions(
            user_role, workflow.current_state
        )
        
        actions = []
        for state in allowed_states:
            action = self._state_to_action(workflow.current_state, state, user_role)
            if action:
                actions.append(action)
        
        return actions
    
    def _state_to_action(
        self,
        current_state: WorkflowState,
        target_state: WorkflowState,
        user_role: UserRole
    ) -> Optional[Dict[str, Any]]:
        """Convert state transition to user-facing action"""
        
        action_map = {
            (WorkflowState.STUDENT_REVIEW, WorkflowState.PATIENT_COMMUNICATION): {
                "action": "approve_and_communicate",
                "label": "Approve and Send to Patient",
                "requires": ["student_review_complete"]
            },
            (WorkflowState.STUDENT_REVIEW, WorkflowState.RESIDENT_ESCALATION): {
                "action": "escalate_to_resident",
                "label": "Escalate to Supervising Physician",
                "requires": ["escalation_reason"]
            },
            (WorkflowState.PATIENT_COMMUNICATION, WorkflowState.PATIENT_ACCEPTED): {
                "action": "accept_plan",
                "label": "Accept Recommendation",
                "requires": []
            },
            (WorkflowState.PATIENT_COMMUNICATION, WorkflowState.PATIENT_QUESTIONS): {
                "action": "ask_questions",
                "label": "Ask Questions",
                "requires": ["question_text"]
            },
            (WorkflowState.PATIENT_COMMUNICATION, WorkflowState.RESIDENT_ESCALATION): {
                "action": "request_physician",
                "label": "Request Physician Review",
                "requires": ["concern_description"]
            },
            (WorkflowState.RESIDENT_ESCALATION, WorkflowState.FINAL_APPROVED): {
                "action": "finalize_decision",
                "label": "Finalize and Sign",
                "requires": ["resident_review_complete", "physician_signature"]
            },
        }
        
        return action_map.get((current_state, target_state))


class WorkflowOrchestrator:
    """High-level workflow orchestration"""
    
    def __init__(self, workflow_engine: WorkflowEngine):
        self.engine = workflow_engine
    
    def handle_ai_completion(
        self,
        workflow: ConsultWorkflow,
        ai_output_id: str
    ) -> ConsultWorkflow:
        """Handle AI processing completion"""
        workflow.ai_output_id = ai_output_id
        return self.engine.auto_transition(workflow, WorkflowState.STUDENT_REVIEW)
    
    def handle_student_approval(
        self,
        workflow: ConsultWorkflow,
        student_review_id: str,
        requires_escalation: bool,
        student_id: str
    ) -> ConsultWorkflow:
        """Handle student review completion"""
        workflow.student_review_id = student_review_id
        
        if requires_escalation:
            workflow.is_escalated = True
            return self.engine.transition_state(
                workflow,
                WorkflowState.RESIDENT_ESCALATION,
                UserRole.MEDICAL_STUDENT,
                student_id,
                {"reason": "student_escalation"}
            )
        else:
            return self.engine.transition_state(
                workflow,
                WorkflowState.PATIENT_COMMUNICATION,
                UserRole.MEDICAL_STUDENT,
                student_id
            )
    
    def handle_patient_response(
        self,
        workflow: ConsultWorkflow,
        response_id: str,
        action: str,
        patient_id: str
    ) -> ConsultWorkflow:
        """Handle patient response to communication"""
        workflow.patient_response_id = response_id
        
        if action == "ACCEPT":
            workflow = self.engine.transition_state(
                workflow,
                WorkflowState.PATIENT_ACCEPTED,
                UserRole.PATIENT,
                patient_id
            )
            # Auto-transition to final approved
            return self.engine.auto_transition(workflow, WorkflowState.FINAL_APPROVED)
        
        elif action == "QUESTION":
            return self.engine.transition_state(
                workflow,
                WorkflowState.PATIENT_QUESTIONS,
                UserRole.PATIENT,
                patient_id
            )
        
        elif action == "ESCALATE":
            workflow.is_escalated = True
            return self.engine.transition_state(
                workflow,
                WorkflowState.RESIDENT_ESCALATION,
                UserRole.PATIENT,
                patient_id,
                {"reason": "patient_request"}
            )
        
        raise ValueError(f"Invalid patient action: {action}")
    
    def handle_resident_decision(
        self,
        workflow: ConsultWorkflow,
        resident_review_id: str,
        final_record_id: str,
        resident_id: str
    ) -> ConsultWorkflow:
        """Handle resident final decision"""
        workflow.resident_review_id = resident_review_id
        workflow.final_record_id = final_record_id
        
        workflow = self.engine.transition_state(
            workflow,
            WorkflowState.FINAL_APPROVED,
            UserRole.RESIDENT,
            resident_id
        )
        
        # Auto-transition to care routing
        return self.engine.auto_transition(workflow, WorkflowState.CARE_ROUTING)
    
    def handle_care_routing_completion(
        self,
        workflow: ConsultWorkflow,
        routing_plan_id: str
    ) -> ConsultWorkflow:
        """Handle care routing completion"""
        workflow.routing_plan_id = routing_plan_id
        return self.engine.auto_transition(workflow, WorkflowState.COMPLETE)
