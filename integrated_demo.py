"""
Integrated Meduroam MVP with Human-in-the-Loop Workflow
Combines AI consultation with medical student review and care navigation
"""

import os
import sys
import json
from datetime import datetime
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import google.generativeai as genai
from dotenv import load_dotenv

# Import our human-in-the-loop components
from models.data_models import (
    PatientData, PatientTranscript, UrgencyLevel, ProviderType,
    StudentReview, StudentDecision, UserRole, SOAPNote, AIReasoning,
    AIConsultOutput
)
from workflows.workflow_engine import WorkflowEngine, WorkflowOrchestrator
from workflows.student_decision_logic import StudentDecisionRubric, StudentWorkflowAssistant
from decision_engine.care_routing import CareRoutingEngine
from compliance.audit_logging import AuditLogger
from api.gemini_integration import GeminiSOAPGenerator

# Load environment variables
load_dotenv()

# Configuration - Queen's University Kingston location
QUEENS_LOCATION = {
    "institution": "Queen's University Faculty of Health Sciences",
    "address": "18 Stuart Street, Kingston, ON K7L 3N6",
    "postal_code": "K7L 3N6",
    "latitude": 44.2312,
    "longitude": -76.4860,
    "default_patient_postal": "K7L 3N6",  # Near campus
    "province": "Ontario"
}


class IntegratedMeduroamConsultation:
    """
    Complete consultation flow:
    1. Patient interaction (conversational AI)
    2. SOAP generation (Gemini)
    3. Medical student review (simulated)
    4. Care routing (geographic)
    5. Audit logging
    """
    
    def __init__(self, api_key=None):
        # Get API key
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY required")
        
        # Initialize Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        self.soap_generator = GeminiSOAPGenerator(self.api_key)
        
        # Initialize workflow components
        self.workflow_engine = WorkflowEngine()
        self.orchestrator = WorkflowOrchestrator(self.workflow_engine)
        self.routing_engine = CareRoutingEngine()
        self.audit_logger = AuditLogger()
        
        # Session data
        self.session_id = str(uuid4())
        self.chat_history = []
        
    def run_consultation(self):
        """Run complete end-to-end consultation"""
        print("\n" + "="*80)
        print("MEDUROAM - Clinical Decision Support Platform")
        print("Queen's University Faculty of Health Sciences - Kingston, ON")
        print("="*80)
        print("\n⚠️  DISCLAIMER: This is a Clinical Decision Support tool.")
        print("All outputs will be reviewed by medical students and physicians.")
        print("="*80 + "\n")
        
        try:
            # Step 1: Patient interaction
            patient, transcript = self._patient_interview()
            
            # Step 2: Generate SOAP note
            ai_output = self._generate_ai_soap(transcript)
            
            # Step 3: Student review (simulated for demo)
            student_review = self._student_review_demo(ai_output, patient)
            
            # Step 4: Care routing for Kingston area
            routing_plan = self._generate_care_routing(patient, ai_output, student_review)
            
            # Step 5: Display final summary
            self._display_final_summary(patient, ai_output, student_review, routing_plan)
            
            # Save session data
            self._save_session_data(patient, transcript, ai_output, student_review, routing_plan)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Consultation interrupted by user.")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def _patient_interview(self):
        """Interactive patient interview"""
        print("STEP 1: PATIENT INTERVIEW")
        print("-" * 80)
        print("\nPlease provide patient information:\n")
        
        # Collect patient data
        age = input("Patient age: ").strip() or "28"
        sex = input("Patient sex (M/F/Other): ").strip() or "Female"
        has_gp = input("Has family doctor? (y/n): ").strip().lower() == 'y'
        
        # Create patient data with Queen's location
        patient = PatientData(
            patient_id=f"P_{self.session_id[:8]}",
            age=int(age),
            sex=sex,
            province=QUEENS_LOCATION["province"],
            postal_code=QUEENS_LOCATION["default_patient_postal"],
            has_family_doctor=has_gp,
            ohip_number=None,
            phone=None,
            email=None
        )
        
        print(f"\n✓ Patient {patient.patient_id} registered")
        print(f"  Location: Kingston, ON ({patient.postal_code})")
        print()
        
        # Log patient creation
        self.audit_logger.log_patient_access(
            user_id=patient.patient_id,
            user_role="PATIENT",
            patient_id=patient.patient_id,
            consult_id=None,
            action="Patient initiated consultation"
        )
        
        # Conversational symptom collection
        print("\nNow let's discuss your symptoms...")
        print("(The AI will ask you questions. Type 'done' when ready to generate assessment)\n")
        
        # Start chat with medical interview prompt
        chat = self.model.start_chat(history=[])
        
        initial_prompt = """You are a medical AI conducting a patient interview. 
        
Your goal is to gather:
- Chief complaint
- History of present illness (OPQRST)
- Associated symptoms
- Duration and severity
- Medical history
- Current medications
- Allergies

Be conversational and empathetic. Ask one question at a time. 
When you have enough information, say "INTERVIEW_COMPLETE".

Start by asking about the chief complaint."""
        
        response = chat.send_message(initial_prompt)
        print(f"🏥 MEDUROAM: {response.text}\n")
        
        symptoms = []
        user_responses = []
        
        while True:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'done':
                break
            
            user_responses.append(user_input)
            symptoms.append(user_input)
            
            response = chat.send_message(user_input)
            print(f"\n🏥 MEDUROAM: {response.text}\n")
            
            if "INTERVIEW_COMPLETE" in response.text:
                break
        
        # Create transcript from conversation
        full_description = " ".join(user_responses)
        
        # Extract structured data (simplified)
        chief_complaint = user_responses[0] if user_responses else "General symptoms"
        
        transcript = PatientTranscript(
            transcript_id=f"T_{self.session_id[:8]}",
            patient_id=patient.patient_id,
            chief_complaint=chief_complaint[:200],
            symptom_description=full_description,
            duration="As described",
            severity="As described",
            associated_symptoms=[],
            medical_history=[],
            medications=[],
            allergies=[],
            timestamp=datetime.now()
        )
        
        print("\n✓ Patient interview complete")
        print()
        
        return patient, transcript
    
    def _generate_ai_soap(self, transcript):
        """Generate SOAP note using Gemini"""
        print("STEP 2: AI SOAP NOTE GENERATION")
        print("-" * 80)
        print("Analyzing symptoms with Gemini AI...\n")
        
        try:
            ai_output = self.soap_generator.generate_soap_note(transcript)
            
            print("✓ AI Analysis Complete\n")
            print("SOAP NOTE PREVIEW:")
            print(f"  Assessment: {ai_output.soap_note.assessment[:150]}...")
            print(f"  Urgency: {ai_output.preliminary_urgency.value}")
            print(f"  Confidence: {ai_output.reasoning.confidence_level:.0%}")
            print()
            
            # Log AI generation
            self.audit_logger.log_ai_generation(
                consult_id=ai_output.consult_id,
                patient_id=transcript.patient_id,
                ai_model="gemini-1.5-pro",
                output_type="SOAP_NOTE",
                confidence=ai_output.reasoning.confidence_level
            )
            
            return ai_output
            
        except Exception as e:
            print(f"⚠️  Error generating SOAP note: {e}")
            print("Using simplified assessment for demo...\n")
            
            # Fallback simple SOAP
            return AIConsultOutput(
                consult_id=f"C_{transcript.transcript_id}",
                patient_id=transcript.patient_id,
                transcript_id=transcript.transcript_id,
                soap_note=SOAPNote(
                    subjective=transcript.symptom_description,
                    objective="Patient-reported symptoms, no physical exam performed",
                    assessment="Requires clinical evaluation based on reported symptoms",
                    plan="Recommend in-person assessment by healthcare provider"
                ),
                reasoning=AIReasoning(
                    differential_diagnosis=["Requires clinical assessment"],
                    red_flags_assessed=["To be evaluated in person"],
                    clinical_reasoning="Patient-reported symptoms require in-person evaluation for accurate assessment",
                    confidence_level=0.5,
                    supporting_evidence=[],
                    ruled_out_conditions=[]
                ),
                preliminary_urgency=UrgencyLevel.ROUTINE,
                suggested_providers=[ProviderType.GP],
                generated_at=datetime.now(),
                ai_model_version="gemini-1.5-pro"
            )
    
    def _student_review_demo(self, ai_output, patient):
        """Simulated medical student review"""
        print("STEP 3: MEDICAL STUDENT REVIEW (Simulated)")
        print("-" * 80)
        print("Medical student reviewing AI assessment...\n")
        
        # Simulate student review
        student_review = StudentReview(
            review_id=f"SR_{self.session_id[:8]}",
            consult_id=ai_output.consult_id,
            student_id="MS_DEMO",
            student_name="Demo Medical Student (Queen's Medicine)",
            assessment_decision=StudentDecision.AGREE,
            validated_urgency=ai_output.preliminary_urgency,
            selected_providers=ai_output.suggested_providers,
            clinical_reasoning_summary="Reviewed AI assessment and agree with preliminary analysis. Differential diagnosis is appropriate for the clinical presentation. Patient should follow recommended care pathway.",
            key_differentials=ai_output.reasoning.differential_diagnosis[:3],
            red_flags_assessment="No immediate red flags identified based on patient report. Appropriate for routine follow-up.",
            provider_selection_rationale=f"Selected {ai_output.suggested_providers[0].value} as appropriate provider based on urgency level and clinical needs.",
            requires_escalation=False,
            reviewed_at=datetime.now(),
            time_spent_minutes=5.0
        )
        
        print("✓ Student Review Complete")
        print(f"  Decision: {student_review.assessment_decision.value}")
        print(f"  Urgency: {student_review.validated_urgency.value}")
        print(f"  Providers: {', '.join([p.value for p in student_review.selected_providers])}")
        print()
        
        # Log student review
        self.audit_logger.log_clinical_decision(
            user_id=student_review.student_id,
            user_role="MEDICAL_STUDENT",
            consult_id=ai_output.consult_id,
            patient_id=patient.patient_id,
            decision_type="STUDENT_REVIEW",
            decision_details={
                "assessment_decision": student_review.assessment_decision.value,
                "urgency": student_review.validated_urgency.value
            }
        )
        
        return student_review
    
    def _generate_care_routing(self, patient, ai_output, student_review):
        """Generate care routing plan for Kingston area"""
        print("STEP 4: CARE ROUTING (Kingston Area)")
        print("-" * 80)
        print("Finding care options near Queen's University...\n")
        
        routing_plan = self.routing_engine.generate_routing_plan(
            consult_id=ai_output.consult_id,
            patient=patient,
            urgency=student_review.validated_urgency,
            approved_providers=student_review.selected_providers,
            clinical_summary=ai_output.soap_note.assessment
        )
        
        print("✓ Care Navigation Complete\n")
        
        return routing_plan
    
    def _display_final_summary(self, patient, ai_output, student_review, routing_plan):
        """Display final consultation summary"""
        print("="*80)
        print("CONSULTATION SUMMARY")
        print("="*80)
        print()
        
        print(f"📋 PATIENT: {patient.patient_id}")
        print(f"   Age: {patient.age} | Sex: {patient.sex}")
        print(f"   Location: Kingston, ON ({patient.postal_code})")
        print()
        
        print(f"🔍 CLINICAL ASSESSMENT:")
        print(f"   Urgency: {student_review.validated_urgency.value}")
        print(f"   AI Confidence: {ai_output.reasoning.confidence_level:.0%}")
        print()
        
        print(f"🏥 RECOMMENDED CARE OPTIONS (Kingston Area):")
        for i, option in enumerate(routing_plan.recommended_options[:3], 1):
            print(f"\n   {i}. {option.facility_name}")
            print(f"      Type: {option.provider_type.value}")
            print(f"      Address: {option.address}")
            print(f"      Distance: {option.distance_km} km from Queen's")
            print(f"      Wait Time: {option.estimated_wait_time or 'Call for availability'}")
            if option.phone:
                print(f"      Phone: {option.phone}")
            print(f"      Priority Score: {option.priority_score:.0f}/100")
        
        print("\n" + "="*80)
        print("✓ Consultation Complete - All data saved and logged")
        print("="*80)
        print()
    
    def _save_session_data(self, patient, transcript, ai_output, student_review, routing_plan):
        """Save complete session data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"meduroam_consult_{timestamp}.json"
        
        session_data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "location": QUEENS_LOCATION,
            "patient": {
                "patient_id": patient.patient_id,
                "age": patient.age,
                "sex": patient.sex,
                "postal_code": patient.postal_code
            },
            "transcript": {
                "chief_complaint": transcript.chief_complaint,
                "description": transcript.symptom_description
            },
            "ai_assessment": {
                "soap_note": ai_output.soap_note.dict(),
                "reasoning": ai_output.reasoning.dict(),
                "urgency": ai_output.preliminary_urgency.value,
                "confidence": ai_output.reasoning.confidence_level
            },
            "student_review": {
                "student_name": student_review.student_name,
                "decision": student_review.assessment_decision.value,
                "validated_urgency": student_review.validated_urgency.value,
                "providers": [p.value for p in student_review.selected_providers]
            },
            "care_routing": {
                "options": [
                    {
                        "facility": opt.facility_name,
                        "type": opt.provider_type.value,
                        "address": opt.address,
                        "distance_km": opt.distance_km,
                        "wait_time": opt.estimated_wait_time,
                        "phone": opt.phone,
                        "priority_score": opt.priority_score
                    }
                    for opt in routing_plan.recommended_options[:5]
                ]
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        print(f"💾 Session data saved to: {filename}\n")


def main():
    """Main entry point"""
    print("\n🚀 Starting Integrated Meduroam MVP...")
    print("   Location: Queen's University, Kingston, ON\n")
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        api_key = "AIzaSyB7vrnf3k5HB8GrwWn_GMtLbf49HXBjpv8"
        print(f"ℹ️  Using provided API key")
    
    try:
        # Create consultation session
        consultation = IntegratedMeduroamConsultation(api_key=api_key)
        
        # Run complete workflow
        consultation.run_consultation()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
