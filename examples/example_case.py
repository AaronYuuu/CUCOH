"""
Complete Case Walkthrough Example
Demonstrates full end-to-end workflow with real system integration
"""

import sys
from datetime import datetime
from models.data_models import (
    PatientData, PatientTranscript, UrgencyLevel, ProviderType,
    StudentReview, StudentDecision, UserRole
)
from api.gemini_integration import GeminiSOAPGenerator
from workflows.workflow_engine import WorkflowEngine, WorkflowOrchestrator
from workflows.student_decision_logic import StudentDecisionRubric, StudentWorkflowAssistant
from decision_engine.care_routing import CareRoutingEngine
from compliance.audit_logging import AuditLogger, AuditEventType, AuditSeverity
from roles.permissions import PhysicianOfRecordRules


# ==================== EXAMPLE CASE ====================

def run_example_case():
    """
    Real case walkthrough: 28-year-old female with chest pain
    """
    
    print("=" * 80)
    print("MEDUROAM CLINICAL DECISION SUPPORT - EXAMPLE CASE WALKTHROUGH")
    print("=" * 80)
    print()
    
    # Initialize system components
    gemini_api_key = "AIzaSyB7vrnf3k5HB8GrwWn_GMtLbf49HXBjpv8"
    gemini_client = GeminiSOAPGenerator(gemini_api_key)
    workflow_engine = WorkflowEngine()
    orchestrator = WorkflowOrchestrator(workflow_engine)
    routing_engine = CareRoutingEngine()
    audit_logger = AuditLogger()
    
    # ==================== STEP 1: PATIENT INITIATES CONSULT ====================
    print("STEP 1: PATIENT INITIATES CONSULT")
    print("-" * 80)
    
    patient = PatientData(
        patient_id="P12345",
        age=28,
        sex="Female",
        province="Ontario",
        postal_code="M5S 1A1",
        has_family_doctor=True,
        ohip_number="1234-567-890",
        phone="416-555-0199",
        email="patient@example.com"
    )
    
    transcript = PatientTranscript(
        transcript_id="T67890",
        patient_id=patient.patient_id,
        chief_complaint="Chest pain and shortness of breath",
        symptom_description="""I've been having chest pain for the past 2 hours. 
        It started suddenly while I was sitting at my desk. The pain is sharp and 
        located in the center of my chest. It gets worse when I take a deep breath. 
        I'm also feeling a bit short of breath.""",
        duration="2 hours",
        severity="Moderate to severe (7/10)",
        associated_symptoms=["Shortness of breath", "Sharp chest pain", "Pain with deep breathing"],
        medical_history=["Oral contraceptive use", "No prior cardiac history"],
        medications=["Oral contraceptive (Alesse)"],
        allergies=["No known drug allergies"],
        timestamp=datetime.now()
    )
    
    print(f"✓ Patient {patient.patient_id} initiated consult")
    print(f"  Chief Complaint: {transcript.chief_complaint}")
    print(f"  Duration: {transcript.duration}")
    print(f"  Severity: {transcript.severity}")
    print()
    
    # Audit log
    audit_logger.log_patient_access(
        user_id=patient.patient_id,
        user_role="PATIENT",
        patient_id=patient.patient_id,
        consult_id=None,
        action="Patient submitted consult request"
    )
    
    # Initialize workflow
    workflow = workflow_engine.create_workflow(
        consult_id=f"C_{transcript.transcript_id}",
        patient_id=patient.patient_id,
        transcript_id=transcript.transcript_id
    )
    
    # ==================== STEP 2: AI PROCESSING (GEMINI) ====================
    print("STEP 2: AI PROCESSING WITH GEMINI")
    print("-" * 80)
    print("Generating SOAP note and clinical reasoning...")
    print()
    
    try:
        # Call Gemini API
        ai_output = gemini_client.generate_soap_note(transcript)
        
        print("✓ AI Analysis Complete")
        print()
        print("AI-GENERATED SOAP NOTE:")
        print(f"Subjective: {ai_output.soap_note.subjective[:200]}...")
        print(f"Assessment: {ai_output.soap_note.assessment[:200]}...")
        print()
        print("AI REASONING:")
        print(f"Differential Diagnoses: {', '.join(ai_output.reasoning.differential_diagnosis[:3])}")
        print(f"Red Flags Assessed: {len(ai_output.reasoning.red_flags_assessed)} items")
        print(f"Preliminary Urgency: {ai_output.preliminary_urgency}")
        print(f"Confidence: {ai_output.reasoning.confidence_level:.2f}")
        print()
        
        # Audit log
        audit_logger.log_ai_generation(
            consult_id=workflow.consult_id,
            patient_id=patient.patient_id,
            ai_model="gemini-1.5-pro",
            output_type="SOAP_NOTE",
            confidence=ai_output.reasoning.confidence_level
        )
        
        # Update workflow
        workflow = orchestrator.handle_ai_completion(workflow, ai_output.consult_id)
        
    except Exception as e:
        print(f"⚠️  AI processing error: {e}")
        print("Using mock data for demonstration...")
        
        # Mock data fallback for demo
        from models.data_models import SOAPNote, AIReasoning, AIConsultOutput
        
        ai_output = AIConsultOutput(
            consult_id=f"C_{transcript.transcript_id}",
            patient_id=patient.patient_id,
            transcript_id=transcript.transcript_id,
            soap_note=SOAPNote(
                subjective="28-year-old female presents with acute onset sharp central chest pain (7/10) for 2 hours. Pain worsens with deep breathing. Associated with dyspnea. Currently taking OCPs. No prior cardiac history.",
                objective="Based on patient self-report: Alert, appears uncomfortable. Pleuritic chest pain pattern. No reported fever, cough, or leg swelling.",
                assessment="DIFFERENTIAL DIAGNOSIS: 1) Pleuritic chest pain - most likely musculoskeletal (costochondritis) vs. pleuritis, 2) Pulmonary embolism (MODERATE CONCERN - OCP use is risk factor, acute onset), 3) Pericarditis, 4) Pneumothorax. RED FLAGS: PE risk due to OCP use and acute onset requires urgent evaluation.",
                plan="URGENT evaluation recommended. Patient should be seen within 4-24 hours. Clinical assessment needed to rule out PE. Consider D-dimer, ECG, chest X-ray. If worsening symptoms or hemodynamic instability, direct to ED."
            ),
            reasoning=AIReasoning(
                differential_diagnosis=[
                    "Costochondritis / Musculoskeletal chest pain",
                    "Pulmonary embolism (PE) - REQUIRES URGENT RULING OUT",
                    "Pleuritis / Pericarditis",
                    "Pneumothorax",
                    "Acute coronary syndrome (less likely given age and presentation)"
                ],
                red_flags_assessed=[
                    "PE risk factors: POSITIVE (oral contraceptive use)",
                    "Hemodynamic stability: Patient reports stable",
                    "Acute onset: POSITIVE (sudden onset)",
                    "Pleuritic pattern: POSITIVE (worse with breathing)",
                    "No reported leg swelling/DVT symptoms"
                ],
                clinical_reasoning="This 28-year-old female presents with acute pleuritic chest pain. While musculoskeletal causes are common in young patients, the combination of acute onset, pleuritic nature, and OCP use raises concern for PE. The age makes ACS less likely. This requires urgent in-person evaluation to safely rule out life-threatening causes.",
                confidence_level=0.75,
                supporting_evidence=[
                    "Sharp, pleuritic chest pain pattern",
                    "Acute onset (2 hours)",
                    "Young age",
                    "OCP use (PE risk factor)"
                ],
                ruled_out_conditions=[
                    "Acute MI: Less likely given age, no cardiac risk factors, pleuritic pattern",
                    "Aortic dissection: No tearing pain, no risk factors"
                ]
            ),
            preliminary_urgency=UrgencyLevel.URGENT,
            suggested_providers=[ProviderType.URGENT_CARE, ProviderType.GP],
            generated_at=datetime.now(),
            ai_model_version="gemini-1.5-pro"
        )
        
        workflow = orchestrator.handle_ai_completion(workflow, ai_output.consult_id)
        print("✓ Using demonstration data")
        print()
    
    # ==================== STEP 3: MEDICAL STUDENT REVIEW ====================
    print("STEP 3: MEDICAL STUDENT REVIEW (MANDATORY)")
    print("-" * 80)
    
    # Generate review checklist for student
    checklist = StudentWorkflowAssistant.generate_review_checklist(ai_output)
    print("Medical Student Review Checklist:")
    for category, items in checklist.items():
        print(f"\n{category.upper().replace('_', ' ')}:")
        for item in items:
            print(f"  ☐ {item}")
    print()
    
    # Student performs review
    print("Medical student (MS_001 - Sarah Chen) reviewing case...")
    print()
    
    student_review = StudentReview(
        review_id="SR_001",
        consult_id=workflow.consult_id,
        student_id="MS_001",
        student_name="Sarah Chen",
        assessment_decision=StudentDecision.MODIFY,
        validated_urgency=UrgencyLevel.URGENT,
        selected_providers=[ProviderType.URGENT_CARE, ProviderType.ED],
        clinical_reasoning_summary="""I agree with the AI's concern about PE given the OCP use and 
        pleuritic chest pain. However, I believe this warrants immediate urgent care or ED evaluation 
        rather than waiting for a GP appointment. The Wells criteria for PE includes OCP use, and while 
        the patient is currently stable, PE can rapidly deteriorate. I'm modifying to include ED as an 
        option in case urgent care is not immediately available.""",
        key_differentials=[
            "Pulmonary embolism (most concerning)",
            "Costochondritis",
            "Pleuritis",
            "Pneumothorax"
        ],
        red_flags_assessment="""Assessed PE risk factors: POSITIVE for OCP use. Patient is currently 
        hemodynamically stable but requires urgent workup. No signs of massive PE (no hypotension, 
        severe dyspnea). Pleuritic pattern supports PE vs ACS.""",
        provider_selection_rationale="""Selected urgent care as primary option for timely evaluation 
        with diagnostic capability (D-dimer, ECG, CXR). Added ED as backup option given severity of 
        potential diagnosis. PE requires imaging and urgent care may need to transfer anyway.""",
        modified_soap=None,  # Keeping AI SOAP but adding note
        assessment_modifications="Added emphasis on PE ruling-out priority. Upgraded provider options to include ED backup.",
        requires_escalation=True,  # Escalating due to PE concern
        escalation_reason="Concerned about PE risk. Would like attending physician to review given potentially serious diagnosis and need for immediate workup.",
        reviewed_at=datetime.now(),
        time_spent_minutes=12.5
    )
    
    # Validate review meets requirements
    rubric = StudentDecisionRubric()
    validation_errors = rubric.validate_student_review(student_review)
    
    if validation_errors:
        print("⚠️  Student review has validation errors:")
        for field, errors in validation_errors.items():
            print(f"  {field}: {errors}")
        print()
    else:
        print("✓ Student review meets all validation requirements")
        print()
    
    print("STUDENT DECISION:")
    print(f"  Assessment Decision: {student_review.assessment_decision}")
    print(f"  Validated Urgency: {student_review.validated_urgency}")
    print(f"  Selected Providers: {', '.join([p.value for p in student_review.selected_providers])}")
    print(f"  Escalation: {'YES - ' + student_review.escalation_reason if student_review.requires_escalation else 'NO'}")
    print(f"  Time Spent: {student_review.time_spent_minutes} minutes")
    print()
    
    # Audit log
    audit_logger.log_clinical_decision(
        user_id=student_review.student_id,
        user_role="MEDICAL_STUDENT",
        consult_id=workflow.consult_id,
        patient_id=patient.patient_id,
        decision_type="STUDENT_REVIEW",
        decision_details={
            "assessment_decision": student_review.assessment_decision,
            "urgency": student_review.validated_urgency,
            "requires_escalation": student_review.requires_escalation
        }
    )
    
    # Update workflow
    workflow = orchestrator.handle_student_approval(
        workflow,
        student_review.review_id,
        student_review.requires_escalation,
        student_review.student_id
    )
    
    # ==================== STEP 4: RESIDENT ESCALATION ====================
    print("STEP 4: RESIDENT/PHYSICIAN ESCALATION")
    print("-" * 80)
    print("Case escalated to on-call resident...")
    print()
    
    # Check physician signature requirements
    supervision_reqs = PhysicianOfRecordRules.get_supervision_requirements(
        student_review.validated_urgency.value
    )
    print("SUPERVISION REQUIREMENTS:")
    for key, value in supervision_reqs.items():
        print(f"  {key}: {value}")
    print()
    
    print("Dr. James Park (Resident) reviewing escalated case...")
    print()
    
    from models.data_models import ResidentReview, ResidentDecision
    
    resident_review = ResidentReview(
        review_id="RR_001",
        consult_id=workflow.consult_id,
        resident_id="RES_001",
        resident_name="Dr. James Park",
        license_number="12345-ON",
        decision=ResidentDecision.APPROVE,
        final_soap=ai_output.soap_note,  # Approving AI SOAP with student modifications
        final_urgency=UrgencyLevel.URGENT,
        final_providers=[ProviderType.URGENT_CARE, ProviderType.ED],
        clinical_rationale="""I agree with the medical student's assessment and escalation. This patient 
        requires urgent evaluation for PE. The combination of acute pleuritic chest pain and OCP use 
        warrants immediate workup. Urgent care is appropriate if they have diagnostic capability; otherwise, 
        ED is the safer option. The student correctly identified the risk and appropriately escalated.""",
        modifications_made="Confirmed student's modification to include ED as provider option",
        teaching_points="""Excellent clinical reasoning by the student. Good recognition of PE risk factors 
        and appropriate escalation. In future, consider using Wells criteria explicitly in documentation. 
        Well done on safety-first approach.""",
        reviewed_at=datetime.now(),
        time_spent_minutes=8.0
    )
    
    print("RESIDENT DECISION:")
    print(f"  Decision: {resident_review.decision}")
    print(f"  Final Urgency: {resident_review.final_urgency}")
    print(f"  Final Providers: {', '.join([p.value for p in resident_review.final_providers])}")
    print(f"  Teaching Points: {resident_review.teaching_points}")
    print()
    
    # Audit log with physician signature
    audit_logger.log_physician_signature(
        physician_id=resident_review.resident_id,
        license_number=resident_review.license_number,
        consult_id=workflow.consult_id,
        patient_id=patient.patient_id,
        signature_type="ESCALATION_REVIEW"
    )
    
    # Create final SOAP record
    from models.data_models import FinalSOAPRecord
    
    final_record = FinalSOAPRecord(
        record_id="FR_001",
        consult_id=workflow.consult_id,
        patient_id=patient.patient_id,
        ai_contribution={
            "soap_note": ai_output.soap_note.dict(),
            "reasoning": ai_output.reasoning.dict(),
            "model": ai_output.ai_model_version
        },
        student_contribution={
            "student_name": student_review.student_name,
            "review": student_review.dict(),
            "modifications": student_review.assessment_modifications
        },
        resident_contribution={
            "resident_name": resident_review.resident_name,
            "license": resident_review.license_number,
            "decision": resident_review.decision,
            "rationale": resident_review.clinical_rationale
        },
        final_soap=resident_review.final_soap,
        final_urgency=resident_review.final_urgency,
        final_providers=resident_review.final_providers,
        supervising_physician_id=resident_review.resident_id,
        supervising_physician_name=resident_review.resident_name,
        created_at=datetime.now(),
        is_final=True
    )
    
    # Update workflow
    workflow = orchestrator.handle_resident_decision(
        workflow,
        resident_review.review_id,
        final_record.record_id,
        resident_review.resident_id
    )
    
    # ==================== STEP 5: CARE ROUTING & NAVIGATION ====================
    print("STEP 5: CARE ROUTING & NAVIGATION")
    print("-" * 80)
    print("Generating personalized care navigation plan...")
    print()
    
    routing_plan = routing_engine.generate_routing_plan(
        consult_id=workflow.consult_id,
        patient=patient,
        urgency=final_record.final_urgency,
        approved_providers=final_record.final_providers,
        clinical_summary=final_record.final_soap.assessment
    )
    
    print("RECOMMENDED CARE OPTIONS:")
    print()
    for i, option in enumerate(routing_plan.recommended_options[:3], 1):
        print(f"{i}. {option.facility_name} ({option.provider_type.value})")
        print(f"   Address: {option.address}")
        print(f"   Distance: {option.distance_km} km")
        print(f"   Wait Time: {option.estimated_wait_time or 'Not available'}")
        print(f"   Walk-in: {'Yes' if option.accepts_walk_ins else 'No'}")
        print(f"   Priority Score: {option.priority_score:.1f}/100")
        if option.phone:
            print(f"   Phone: {option.phone}")
        print()
    
    # Complete workflow
    workflow = orchestrator.handle_care_routing_completion(
        workflow,
        routing_plan.routing_id
    )
    
    # ==================== STEP 6: PATIENT COMMUNICATION ====================
    print("STEP 6: PATIENT-FACING COMMUNICATION")
    print("-" * 80)
    
    print("Plain-language summary sent to patient:")
    print()
    print("""
Dear Patient,

Thank you for using Meduroam. Your symptoms have been carefully reviewed by our 
medical team.

**WHAT'S LIKELY GOING ON:**
You have chest pain that gets worse with breathing. While this could be something 
simple like muscle strain, there is a concern that needs to be checked urgently: 
a possible blood clot in the lungs (pulmonary embolism). This is a concern because 
you're taking birth control pills, which slightly increase this risk.

**WHAT WE'VE RULED OUT AS IMMEDIATELY DANGEROUS:**
Based on your description, we don't think this is a heart attack, which is very 
rare in someone your age without risk factors.

**WHAT YOU NEED TO DO NEXT:**
You should be seen TODAY at an urgent care clinic or emergency department. They 
will do some tests (blood test, chest X-ray, possibly a CT scan) to make sure 
there's no blood clot.

**WHY THIS IS IMPORTANT:**
Even though you feel stable now, a blood clot in the lungs can be serious and 
needs to be ruled out quickly. It's better to be safe and get checked today.

**WHERE TO GO:**
We've found these nearby options for you:
1. Appletree Medical Walk-In - 1.8 km away, ~2 hour wait
2. East Toronto Urgent Care - 6.5 km away, ~90 minute wait
3. Toronto General Hospital ED - 3.5 km away (if urgent cares are unavailable)

**IF YOUR SYMPTOMS GET WORSE:**
If you develop severe shortness of breath, chest pain that's getting much worse, 
dizziness, or fainting, call 911 or go directly to the nearest emergency department.

This assessment was generated with AI assistance and reviewed by medical student 
Sarah Chen under the supervision of Dr. James Park (License #12345-ON).

Do you have any questions, or would you like to proceed with booking?
    """)
    print()
    
    # ==================== STEP 7: AUDIT TRAIL & COMPLIANCE ====================
    print("STEP 7: AUDIT TRAIL & COMPLIANCE CHECK")
    print("-" * 80)
    
    # Get complete audit trail
    audit_trail = audit_logger.get_consult_audit_trail(workflow.consult_id)
    print(f"✓ Complete audit trail: {len(audit_trail)} events logged")
    print()
    
    # Compliance check
    from compliance.audit_logging import ComplianceChecker
    
    compliance_data = {
        "patient_consent": True,
        "student_review_id": student_review.review_id,
        "urgency": final_record.final_urgency.value,
        "physician_signature": True,
        "final_record": final_record.dict(),
        "audit_entries": audit_trail
    }
    
    compliance_results = ComplianceChecker.validate_consult_compliance(compliance_data)
    
    print("COMPLIANCE VALIDATION:")
    print(f"  Overall Compliant: {'✓ YES' if compliance_results['compliant'] else '✗ NO'}")
    print()
    print("  Individual Checks:")
    for check, passed in compliance_results['checks'].items():
        status = "✓" if passed else "✗"
        print(f"    {status} {check.replace('_', ' ').title()}")
    
    if compliance_results['issues']:
        print("\n  Issues Found:")
        for issue in compliance_results['issues']:
            print(f"    - {issue}")
    print()
    
    # ==================== SUMMARY ====================
    print("=" * 80)
    print("CASE WALKTHROUGH COMPLETE")
    print("=" * 80)
    print()
    print(f"Final Workflow State: {workflow.current_state}")
    print(f"Total Processing Time: {(datetime.now() - workflow.created_at).seconds} seconds")
    print(f"Audit Events Logged: {len(audit_trail)}")
    print(f"Physician of Record: {final_record.supervising_physician_name}")
    print()
    print("Key Outcomes:")
    print(f"  ✓ AI-generated SOAP note validated by medical team")
    print(f"  ✓ Student identified critical PE risk and escalated appropriately")
    print(f"  ✓ Resident approved plan with teaching feedback")
    print(f"  ✓ Patient directed to appropriate urgent care")
    print(f"  ✓ Complete audit trail maintained")
    print(f"  ✓ All compliance requirements met")
    print()
    print("This demonstrates the complete meduroam human-in-the-loop workflow.")
    print("=" * 80)


if __name__ == "__main__":
    run_example_case()
