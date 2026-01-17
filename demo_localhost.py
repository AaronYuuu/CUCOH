"""
Automated Demo of Meduroam MVP
Non-interactive demonstration with sample case
"""

import os
import sys
import json
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.data_models import (
    PatientData, PatientTranscript, UrgencyLevel, ProviderType,
    StudentReview, StudentDecision, SOAPNote, AIReasoning, AIConsultOutput
)
from workflows.workflow_engine import WorkflowEngine, WorkflowOrchestrator
from workflows.student_decision_logic import StudentDecisionRubric
from decision_engine.care_routing import CareRoutingEngine
from compliance.audit_logging import AuditLogger
from api.gemini_integration import GeminiSOAPGenerator

# Queen's University Kingston configuration
QUEENS_CONFIG = {
    "institution": "Queen's University Faculty of Health Sciences",
    "address": "18 Stuart Street, Kingston, ON K7L 3N6",
    "postal_code": "K7L 3N6"
}


def run_automated_demo():
    """Run complete automated demo with sample patient"""
    
    print("\n" + "="*80)
    print("MEDUROAM MVP - AUTOMATED DEMO")
    print("Queen's University Faculty of Health Sciences - Kingston, ON")
    print("="*80)
    print()
    
    # Initialize system components
    print("🔧 Initializing system components...")
    api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyB7vrnf3k5HB8GrwWn_GMtLbf49HXBjpv8')
    
    try:
        soap_generator = GeminiSOAPGenerator(api_key)
        workflow_engine = WorkflowEngine()
        orchestrator = WorkflowOrchestrator(workflow_engine)
        routing_engine = CareRoutingEngine()
        audit_logger = AuditLogger()
        print("✓ System initialized\n")
    except Exception as e:
        print(f"⚠️  Could not initialize Gemini: {e}")
        print("   Continuing with mock data for demo...\n")
        soap_generator = None
    
    # Sample patient case
    print("="*80)
    print("STEP 1: PATIENT INTAKE")
    print("="*80)
    
    patient = PatientData(
        patient_id="P_DEMO_001",
        age=22,
        sex="Female",
        province="Ontario",
        postal_code=QUEENS_CONFIG["postal_code"],
        has_family_doctor=False,
        phone="613-555-0123",
        email="student@queensu.ca"
    )
    
    transcript = PatientTranscript(
        transcript_id="T_DEMO_001",
        patient_id=patient.patient_id,
        chief_complaint="Sore throat and fever for 3 days",
        symptom_description="""I'm a Queen's student and I've had a really bad sore throat 
        for the past 3 days. It hurts to swallow. I've also had a fever - I measured it this 
        morning and it was 38.5°C. I'm feeling pretty tired and achy. No cough, no runny nose. 
        I have white spots on my tonsils when I look in the mirror.""",
        duration="3 days",
        severity="Moderate (6/10)",
        associated_symptoms=["Fever (38.5°C)", "Fatigue", "Body aches", "White patches on tonsils"],
        medical_history=["No chronic conditions"],
        medications=["None"],
        allergies=["No known drug allergies"],
        timestamp=datetime.now()
    )
    
    print(f"✓ Patient: {patient.age}yo {patient.sex}, Queen's student")
    print(f"  Chief Complaint: {transcript.chief_complaint}")
    print(f"  Location: Kingston, ON ({patient.postal_code})")
    print()
    
    audit_logger.log_patient_access(
        user_id=patient.patient_id,
        user_role="PATIENT",
        patient_id=patient.patient_id,
        consult_id=None,
        action="Patient submitted consultation request"
    )
    
    # Create workflow
    workflow = workflow_engine.create_workflow(
        consult_id=f"C_DEMO_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        patient_id=patient.patient_id,
        transcript_id=transcript.transcript_id
    )
    
    # AI SOAP Generation
    print("="*80)
    print("STEP 2: AI SOAP NOTE GENERATION (Gemini)")
    print("="*80)
    
    if soap_generator:
        try:
            print("Generating SOAP note with Gemini AI...")
            ai_output = soap_generator.generate_soap_note(transcript, patient.age, patient.sex)
            print("✓ AI analysis complete\n")
        except Exception as e:
            print(f"⚠️  Gemini error: {e}")
            print("Using mock assessment...\n")
            ai_output = create_mock_soap(transcript, patient)
    else:
        print("Using mock assessment for demo...\n")
        ai_output = create_mock_soap(transcript, patient)
    
    print("AI ASSESSMENT:")
    print(f"  Subjective: {ai_output.soap_note.subjective[:100]}...")
    print(f"  Assessment: {ai_output.soap_note.assessment[:150]}...")
    print(f"  Urgency: {ai_output.preliminary_urgency.value}")
    print(f"  Confidence: {ai_output.reasoning.confidence_level:.0%}")
    print(f"  Differentials: {len(ai_output.reasoning.differential_diagnosis)} considered")
    print()
    
    audit_logger.log_ai_generation(
        consult_id=workflow.consult_id,
        patient_id=patient.patient_id,
        ai_model="gemini-1.5-pro",
        output_type="SOAP_NOTE",
        confidence=ai_output.reasoning.confidence_level
    )
    
    workflow = orchestrator.handle_ai_completion(workflow, ai_output.consult_id)
    
    # Medical Student Review
    print("="*80)
    print("STEP 3: MEDICAL STUDENT REVIEW")
    print("="*80)
    print("Medical student (Queen's Medicine Year 3) reviewing...")
    print()
    
    student_review = StudentReview(
        review_id="SR_DEMO_001",
        consult_id=workflow.consult_id,
        student_id="MS_QUEENS_001",
        student_name="Alex Chen (Queen's Medicine Class of 2027)",
        assessment_decision=StudentDecision.AGREE,
        validated_urgency=UrgencyLevel.URGENT,
        selected_providers=[ProviderType.URGENT_CARE, ProviderType.GP],
        clinical_reasoning_summary="""Classic presentation of pharyngitis with fever, exudative tonsils, 
        and absence of URI symptoms suggests bacterial (likely Strep) vs viral etiology. Centor score 
        supports bacterial infection. Patient needs throat swab and possible antibiotic treatment. As a 
        Queen's student without a family doctor, urgent care is most appropriate for timely access.""",
        key_differentials=[
            "Group A Strep pharyngitis (most likely)",
            "Viral pharyngitis (EBV, adenovirus)",
            "Peritonsillar abscess (less likely - no trismus or unilateral swelling reported)"
        ],
        red_flags_assessment="""No airway compromise, no drooling, can swallow liquids. No signs of 
        sepsis or spreading infection. Appropriate for urgent care setting with close follow-up.""",
        provider_selection_rationale="""Student lacks family doctor. Urgent care provides same-day/next-day 
        access with diagnostic capability (rapid strep test) and treatment. Kingston After Hours Clinic 
        is close to campus. Alternative: Student Wellness Services for Queen's students.""",
        requires_escalation=False,
        reviewed_at=datetime.now(),
        time_spent_minutes=8.5
    )
    
    # Validate review
    rubric = StudentDecisionRubric()
    errors = rubric.validate_student_review(student_review)
    
    if errors:
        print("⚠️  Validation issues:", errors)
    else:
        print("✓ Student review validation passed")
    
    print()
    print("STUDENT DECISION:")
    print(f"  Assessment: {student_review.assessment_decision.value}")
    print(f"  Urgency: {student_review.validated_urgency.value}")
    print(f"  Providers: {', '.join([p.value for p in student_review.selected_providers])}")
    print(f"  Escalation: {'Yes' if student_review.requires_escalation else 'No'}")
    print(f"  Time: {student_review.time_spent_minutes} minutes")
    print()
    
    audit_logger.log_clinical_decision(
        user_id=student_review.student_id,
        user_role="MEDICAL_STUDENT",
        consult_id=workflow.consult_id,
        patient_id=patient.patient_id,
        decision_type="STUDENT_REVIEW",
        decision_details={
            "decision": student_review.assessment_decision.value,
            "urgency": student_review.validated_urgency.value
        }
    )
    
    workflow = orchestrator.handle_student_approval(
        workflow, student_review.review_id, False, student_review.student_id
    )
    
    # Care Routing
    print("="*80)
    print("STEP 4: CARE NAVIGATION (Kingston Area)")
    print("="*80)
    print("Finding care options near Queen's University campus...")
    print()
    
    routing_plan = routing_engine.generate_routing_plan(
        consult_id=workflow.consult_id,
        patient=patient,
        urgency=student_review.validated_urgency,
        approved_providers=student_review.selected_providers,
        clinical_summary=ai_output.soap_note.assessment
    )
    
    print("✓ Care routing complete\n")
    print("RECOMMENDED CARE OPTIONS:")
    print()
    
    for i, option in enumerate(routing_plan.recommended_options[:3], 1):
        print(f"{i}. {option.facility_name}")
        print(f"   Type: {option.provider_type.value}")
        print(f"   Address: {option.address}")
        print(f"   Distance from Queen's: {option.distance_km} km")
        print(f"   Est. Wait: {option.estimated_wait_time or 'Call ahead'}")
        print(f"   Walk-in: {'Yes' if option.accepts_walk_ins else 'No - Appointment needed'}")
        if option.phone:
            print(f"   Phone: {option.phone}")
        print(f"   Priority Score: {option.priority_score:.0f}/100")
        print()
    
    # Patient Communication
    print("="*80)
    print("STEP 5: PATIENT COMMUNICATION")
    print("="*80)
    print()
    print("MESSAGE TO PATIENT:")
    print("-" * 80)
    print(f"""
Hi there,

Thank you for using Meduroam. Your symptoms have been reviewed by a medical 
student at Queen's Medicine under supervision.

WHAT'S GOING ON:
Based on your symptoms - sore throat with fever, white patches on your tonsils, 
and body aches - you likely have a bacterial throat infection (strep throat). 
This needs to be confirmed with a throat swab.

NEXT STEPS:
You should be seen today or tomorrow at an urgent care clinic. They will:
- Do a rapid strep test (takes 5-10 minutes)
- Prescribe antibiotics if test is positive
- Give you advice on symptom management

WHERE TO GO:
We recommend these options near Queen's campus:

1. Queen's Student Wellness Services (0.3 km away)
   - 146 Stuart Street
   - For Queen's students
   - Call: 613-533-2506

2. Kingston After Hours Clinic (1.8 km away)
   - 752 King Street West
   - Walk-in accepted
   - Call: 613-544-3310

WHEN TO SEEK EMERGENCY CARE:
Go to Kingston Health Sciences Centre Emergency if you develop:
- Difficulty breathing or swallowing
- Drooling or inability to handle secretions
- Severe neck swelling
- High fever that doesn't respond to medication

This assessment was reviewed by {student_review.student_name}.

Questions? Reply to this message or call any of the clinics above.

Take care!
Meduroam Clinical Team
    """)
    print("-" * 80)
    print()
    
    # Final Summary
    print("="*80)
    print("CONSULTATION COMPLETE")
    print("="*80)
    print()
    print(f"✓ Workflow State: {workflow.current_state.value}")
    print(f"✓ Audit Events: {len(audit_logger.storage.get_by_consult(workflow.consult_id))}")
    print(f"✓ Total Time: {(datetime.now() - workflow.created_at).seconds} seconds")
    print()
    
    # Save session data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"demo_consultation_{timestamp}.json"
    
    session_data = {
        "session_type": "automated_demo",
        "location": QUEENS_CONFIG,
        "timestamp": datetime.now().isoformat(),
        "patient": {
            "id": patient.patient_id,
            "age": patient.age,
            "sex": patient.sex,
            "chief_complaint": transcript.chief_complaint
        },
        "ai_assessment": {
            "urgency": ai_output.preliminary_urgency.value,
            "confidence": ai_output.reasoning.confidence_level,
            "differentials": ai_output.reasoning.differential_diagnosis
        },
        "student_review": {
            "name": student_review.student_name,
            "decision": student_review.assessment_decision.value,
            "urgency": student_review.validated_urgency.value,
            "time_minutes": student_review.time_spent_minutes
        },
        "care_options": [
            {
                "facility": opt.facility_name,
                "type": opt.provider_type.value,
                "distance_km": opt.distance_km,
                "phone": opt.phone
            }
            for opt in routing_plan.recommended_options[:3]
        ]
    }
    
    with open(filename, 'w') as f:
        json.dump(session_data, f, indent=2)
    
    print(f"💾 Session saved: {filename}")
    print()
    print("="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print()
    print("This demonstration showed:")
    print("  ✓ AI-powered SOAP note generation")
    print("  ✓ Medical student validation (mandatory human review)")
    print("  ✓ Geographic care routing (Kingston-specific facilities)")
    print("  ✓ Complete audit trail")
    print("  ✓ Patient-friendly communication")
    print()
    print("Ready for localhost deployment! 🚀")
    print()


def create_mock_soap(transcript, patient):
    """Create mock SOAP note if Gemini unavailable"""
    return AIConsultOutput(
        consult_id=f"C_DEMO_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        patient_id=transcript.patient_id,
        transcript_id=transcript.transcript_id,
        soap_note=SOAPNote(
            subjective=f"{patient.age}yo {patient.sex} presents with {transcript.chief_complaint}. "
                      f"{transcript.symptom_description}",
            objective="Patient-reported: Temperature 38.5°C, white exudate visible on tonsils per patient. "
                     "No physical examination performed (remote consultation).",
            assessment="DIFFERENTIAL DIAGNOSIS: 1) Group A Streptococcal pharyngitis (most likely given fever, "
                      "exudative tonsils, absence of cough), 2) Viral pharyngitis (EBV, adenovirus), "
                      "3) Peritonsillar abscess (lower probability without trismus). "
                      "CLINICAL IMPRESSION: Acute pharyngitis, likely bacterial. Requires throat culture/rapid strep test.",
            plan="URGENT evaluation recommended within 24 hours. Patient should present to urgent care or "
                "student health services for: 1) Throat swab (rapid strep/culture), 2) Clinical examination, "
                "3) Consider antibiotics if strep positive. Symptomatic management: rest, fluids, acetaminophen for fever/pain."
        ),
        reasoning=AIReasoning(
            differential_diagnosis=[
                "Group A Streptococcal pharyngitis (bacterial)",
                "Viral pharyngitis (EBV, adenovirus)",
                "Infectious mononucleosis",
                "Peritonsillar abscess"
            ],
            red_flags_assessed=[
                "Airway compromise: Negative (can swallow, no stridor)",
                "Signs of systemic infection: Fever present but patient stable",
                "Peritonsillar abscess signs: No trismus or unilateral swelling reported"
            ],
            clinical_reasoning="Patient presents with classic acute pharyngitis with fever and exudative tonsils. "
                             "High Centor score (fever, exudate, no cough, young age) suggests ~50% probability of "
                             "strep throat. Absence of upper respiratory symptoms makes viral less likely. "
                             "Requires confirmatory testing and likely antibiotic treatment.",
            confidence_level=0.80,
            supporting_evidence=[
                "Fever (38.5°C)",
                "Exudative tonsils",
                "Absence of cough/rhinorrhea",
                "Young age (college student)",
                "Acute onset (3 days)"
            ],
            ruled_out_conditions=[
                "Epiglottitis: No drooling, can swallow",
                "Diphtheria: Patient likely vaccinated, no pseudomembrane described"
            ]
        ),
        preliminary_urgency=UrgencyLevel.URGENT,
        suggested_providers=[ProviderType.URGENT_CARE, ProviderType.GP],
        generated_at=datetime.now(),
        ai_model_version="gemini-1.5-pro"
    )


if __name__ == "__main__":
    run_automated_demo()
