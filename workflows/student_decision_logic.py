"""
Medical Student Decision Support
Rubrics, guidelines, and validation logic
"""

from typing import Dict, List, Optional
from models.data_models import (
    StudentDecision, UrgencyLevel, ProviderType,
    StudentReview, AIConsultOutput, SOAPNote
)


class StudentDecisionRubric:
    """
    Decision-making framework for medical students
    Ensures structured clinical reasoning
    """
    
    @staticmethod
    def get_assessment_guidelines() -> Dict[str, List[str]]:
        """Guidelines for validating AI assessment"""
        return {
            "AGREE": [
                "AI differential diagnosis is comprehensive",
                "No critical diagnoses were missed",
                "Red flags were appropriately assessed",
                "Urgency level matches clinical picture",
                "Reasoning is sound and evidence-based"
            ],
            "MODIFY": [
                "Core assessment is correct but incomplete",
                "Need to add/remove differential diagnoses",
                "Urgency level needs adjustment",
                "Plan needs refinement but direction is right",
                "Minor clinical reasoning gaps to address"
            ],
            "DISAGREE": [
                "Missed critical diagnosis",
                "Inappropriate urgency classification",
                "Dangerous oversight or error",
                "Reasoning is flawed or unsupported",
                "Plan could cause patient harm"
            ]
        }
    
    @staticmethod
    def get_urgency_criteria() -> Dict[str, Dict[str, any]]:
        """Clinical criteria for urgency classification"""
        return {
            "EMERGENCY": {
                "definition": "Life or limb threatening, requires immediate ED evaluation",
                "examples": [
                    "Chest pain concerning for MI/PE",
                    "Acute stroke symptoms",
                    "Severe shortness of breath",
                    "Severe trauma or bleeding",
                    "Altered mental status",
                    "Severe abdominal pain with peritoneal signs"
                ],
                "timeframe": "Immediate (call 911 or go to ED now)",
                "red_flags": [
                    "Hemodynamic instability",
                    "Airway compromise",
                    "Acute neurological deficit",
                    "Uncontrolled bleeding"
                ]
            },
            "URGENT": {
                "definition": "Needs medical attention soon, could worsen if delayed",
                "examples": [
                    "Suspected UTI with fever",
                    "Worsening cellulitis",
                    "Moderate pain or discomfort",
                    "Persistent vomiting/diarrhea",
                    "Medication side effects"
                ],
                "timeframe": "24-48 hours",
                "considerations": [
                    "Could progress if untreated",
                    "Significant impact on function",
                    "Requires timely intervention"
                ]
            },
            "ROUTINE": {
                "definition": "Can be addressed in routine care setting",
                "examples": [
                    "Chronic disease management",
                    "Preventive care needs",
                    "Minor skin issues",
                    "Mild stable symptoms",
                    "Follow-up care"
                ],
                "timeframe": "Days to weeks",
                "considerations": [
                    "Stable condition",
                    "No immediate risk",
                    "Can wait for appropriate provider"
                ]
            }
        }
    
    @staticmethod
    def get_provider_selection_guide() -> Dict[str, Dict[str, any]]:
        """Guide for selecting appropriate provider types"""
        return {
            "GP": {
                "description": "Family physician / General practitioner",
                "appropriate_for": [
                    "Chronic disease management",
                    "Complex medical history",
                    "Requires continuity of care",
                    "Multiple comorbidities",
                    "Needs comprehensive assessment"
                ],
                "limitations": [
                    "May have long wait times",
                    "Requires established patient relationship (often)",
                    "Not always available for acute issues"
                ],
                "canadian_context": "Primary gatekeeper in Canadian system"
            },
            "NP": {
                "description": "Nurse practitioner",
                "appropriate_for": [
                    "Minor acute illnesses",
                    "Routine chronic disease management",
                    "Prescriptions and referrals",
                    "Patient education"
                ],
                "limitations": [
                    "Scope of practice varies by province",
                    "May need physician consultation for complex cases"
                ],
                "canadian_context": "Increasing role in primary care, good for access"
            },
            "RN": {
                "description": "Registered nurse",
                "appropriate_for": [
                    "Health education",
                    "Wound care",
                    "Chronic disease education",
                    "Triage and assessment"
                ],
                "limitations": [
                    "Cannot prescribe medications (most provinces)",
                    "Cannot make diagnoses"
                ],
                "canadian_context": "Often first point of contact in clinics"
            },
            "URGENT_CARE": {
                "description": "Walk-in urgent care clinic",
                "appropriate_for": [
                    "Minor injuries",
                    "Acute illnesses",
                    "After-hours needs",
                    "No family doctor available"
                ],
                "limitations": [
                    "No continuity of care",
                    "May have limited diagnostic capabilities",
                    "Can have long wait times"
                ],
                "canadian_context": "Good option for urgent but non-emergent issues"
            },
            "ED": {
                "description": "Emergency department",
                "appropriate_for": [
                    "Life-threatening emergencies",
                    "Severe acute conditions",
                    "When other options exhausted"
                ],
                "limitations": [
                    "Very long wait times for non-emergent issues",
                    "No continuity of care",
                    "Resource-intensive"
                ],
                "canadian_context": "Only for true emergencies - significant strain on system"
            },
            "SPECIALIST": {
                "description": "Medical specialist",
                "appropriate_for": [
                    "Complex or rare conditions",
                    "Failed treatment by primary care",
                    "Requires specialized expertise"
                ],
                "limitations": [
                    "Requires referral from GP/NP",
                    "Long wait times (months)",
                    "Geographic barriers"
                ],
                "canadian_context": "Gatekeeper system - must have referral"
            }
        }
    
    @staticmethod
    def get_escalation_triggers() -> List[str]:
        """When student MUST escalate to resident"""
        return [
            "Any disagreement with AI urgency classification",
            "Consideration of ED referral",
            "Unusual or rare diagnosis suspected",
            "Patient has multiple complex comorbidities",
            "Student uncertainty about clinical decision",
            "Patient requesting physician review",
            "Medicolegal concerns",
            "Diagnosis has significant consequences (e.g., cancer)",
            "Requires controlled substance prescription",
            "Student lacks confidence in assessment (>30% uncertainty)"
        ]
    
    @staticmethod
    def validate_student_review(review: StudentReview) -> Dict[str, List[str]]:
        """
        Validate that student review meets minimum standards
        Returns dict of validation errors (empty if valid)
        """
        errors = {}
        
        # Check reasoning length requirements
        if len(review.clinical_reasoning_summary) < 50:
            errors.setdefault("reasoning", []).append(
                "Clinical reasoning too brief - minimum 50 characters required"
            )
        
        if len(review.red_flags_assessment) < 30:
            errors.setdefault("reasoning", []).append(
                "Red flags assessment insufficient - minimum 30 characters required"
            )
        
        if len(review.provider_selection_rationale) < 30:
            errors.setdefault("reasoning", []).append(
                "Provider selection rationale insufficient - minimum 30 characters required"
            )
        
        # Check that differentials are provided
        if not review.key_differentials or len(review.key_differentials) < 2:
            errors.setdefault("differentials", []).append(
                "Must consider at least 2 differential diagnoses"
            )
        
        # Check provider selection
        if not review.selected_providers:
            errors.setdefault("providers", []).append(
                "Must select at least one provider type"
            )
        
        # If DISAGREE, must provide modifications
        if review.assessment_decision == StudentDecision.DISAGREE:
            if not review.modified_soap and not review.assessment_modifications:
                errors.setdefault("modifications", []).append(
                    "DISAGREE decision requires modified SOAP note or assessment modifications"
                )
        
        # If escalating, must provide reason
        if review.requires_escalation and not review.escalation_reason:
            errors.setdefault("escalation", []).append(
                "Escalation requires explanation"
            )
        
        # Validate urgency vs provider selection
        if review.validated_urgency == UrgencyLevel.EMERGENCY:
            if ProviderType.ED not in review.selected_providers:
                errors.setdefault("urgency_mismatch", []).append(
                    "EMERGENCY urgency should include ED as provider option"
                )
        
        return errors


class StudentWorkflowAssistant:
    """Helper functions for student workflow"""
    
    @staticmethod
    def generate_review_checklist(ai_output: AIConsultOutput) -> Dict[str, List[str]]:
        """Generate checklist for student to complete"""
        return {
            "clinical_review": [
                "Review patient transcript carefully",
                "Evaluate AI differential diagnosis",
                "Assess red flag identification",
                "Validate urgency classification",
                "Consider additional differentials"
            ],
            "decision_making": [
                "Choose assessment decision (AGREE/MODIFY/DISAGREE)",
                "Select appropriate provider type(s)",
                "Confirm urgency level",
                "Document clinical reasoning",
                "Decide if escalation needed"
            ],
            "documentation": [
                "Write clinical reasoning summary (50+ characters)",
                "List key differentials (minimum 2)",
                "Document red flags assessment (30+ characters)",
                "Explain provider selection (30+ characters)",
                "Modify SOAP if needed"
            ],
            "safety_checks": [
                "Red flags appropriately addressed?",
                "Urgency matches clinical severity?",
                "Provider type appropriate for condition?",
                "Patient safety considerations documented?",
                "Escalation appropriate?"
            ]
        }
    
    @staticmethod
    def generate_teaching_prompts(ai_output: AIConsultOutput) -> List[str]:
        """Generate educational prompts for student learning"""
        prompts = [
            f"What are the most concerning differential diagnoses for this presentation?",
            f"What red flags would make you escalate urgency?",
            f"Why is {ai_output.preliminary_urgency} the appropriate urgency level?",
            f"What provider type is most appropriate and why?",
            f"What key questions would you ask on history?",
            f"What would you want to know from physical exam?",
            f"What follow-up instructions would you give the patient?"
        ]
        return prompts
    
    @staticmethod
    def suggest_modifications(
        ai_output: AIConsultOutput,
        student_concerns: List[str]
    ) -> Dict[str, str]:
        """Suggest specific modifications based on student concerns"""
        suggestions = {}
        
        concern_map = {
            "urgency": "Consider if patient needs to be seen sooner based on symptom severity",
            "differential": "Add additional diagnoses to differential list that AI may have missed",
            "red_flags": "Document additional red flags or dangerous symptoms that need monitoring",
            "provider": "Consider if a different provider type would be more appropriate",
            "plan": "Modify treatment plan to better address patient's specific situation"
        }
        
        for concern in student_concerns:
            if concern.lower() in concern_map:
                suggestions[concern] = concern_map[concern.lower()]
        
        return suggestions
