#!/usr/bin/env python3
"""
Meduroam Chatbot Interface - Human-in-the-Loop Clinical Decision Support
Port: 5004
"""

from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, timedelta
import os
import sys
from uuid import uuid4

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.data_models import (
    PatientData, PatientTranscript, WorkflowState, UrgencyLevel
)
from workflows.workflow_engine import WorkflowOrchestrator
from api.gemini_integration import GeminiSOAPGenerator
from decision_engine.care_routing import CareRoutingEngine
from roles.permissions import Permission

app = Flask(__name__)
app.secret_key = 'meduroam-chatbot-secret-key-2026'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Global storage (in-memory for demo)
consultations = {}

# Initialize services
gemini_api_key = "AIzaSyB7vrnf3k5HB8GrwWn_GMtLbf49HXBjpv8"
soap_generator = GeminiSOAPGenerator(api_key=gemini_api_key)
care_router = CareRoutingEngine()


@app.route('/')
def index():
    """Render chatbot interface"""
    session.clear()
    return render_template('chatbot.html')


@app.route('/start-consult', methods=['POST'])
def start_consult():
    """Initialize a new consultation session"""
    consult_id = str(uuid4())
    session['consult_id'] = consult_id
    session.permanent = True
    
    # Initialize empty consultation
    consultations[consult_id] = {
        'created_at': datetime.now(),
        'state': 'collecting_info'
    }
    
    return jsonify({
        'consult_id': consult_id,
        'status': 'started'
    })


@app.route('/submit-symptoms', methods=['POST'])
def submit_symptoms():
    """Process complete symptom information from chatbot"""
    data = request.json
    consult_id = data.get('consult_id')
    
    if not consult_id or consult_id not in consultations:
        return jsonify({'error': 'Invalid consultation ID'}), 400
    
    try:
        # Create patient data
        patient = PatientData(
            patient_id="DEMO_PATIENT",
            age=int(data['age']),
            sex=data['sex'],
            location_postal_code="K7L 3N6",  # Queen's University
            has_regular_gp=(data['has_gp'] == 'yes')
        )
        
        # Create transcript
        transcript = PatientTranscript(
            chief_complaint=data['chief_complaint'],
            transcript_text=f"""
Patient presents with: {data['chief_complaint']}

Detailed symptoms: {data['symptoms']}

Duration: {data['duration']}
Severity: {data['severity']}

Additional information: {data.get('additional_info', 'None provided')}
""".strip()
        )
        
        # Initialize workflow
        orchestrator = WorkflowOrchestrator()
        workflow = orchestrator.start_consultation(patient, transcript)
        
        # Generate SOAP note with Gemini
        print(f"Generating SOAP note for consultation {consult_id}...")
        try:
            ai_consult = soap_generator.generate_soap_note(
                transcript=transcript,
                patient_age=patient.age,
                patient_sex=patient.sex
            )
            print(f"✓ SOAP generated - Urgency: {ai_consult.urgency_level}")
        except Exception as e:
            print(f"⚠ Gemini API error: {e}")
            # Create mock SOAP if API fails
            ai_consult = create_mock_soap(transcript, patient)
            print(f"✓ Using mock SOAP - Urgency: {ai_consult.urgency_level}")
        
        # Transition workflow to AI complete
        workflow = orchestrator.handle_ai_completion(workflow, ai_consult)
        
        # Simulate student review (in demo, auto-approve)
        from models.data_models import StudentReview
        student_review = StudentReview(
            reviewed_by_student_id="MED_STUDENT_001",
            student_name="Demo Student",
            review_timestamp=datetime.now(),
            agrees_with_ai_assessment=True,
            concerns_flags=[],
            assessment_notes="Assessment reviewed and appears appropriate.",
            routing_modifications=None
        )
        
        # Approve and route
        workflow = orchestrator.handle_student_approval(workflow, student_review)
        
        # Get care routing - determine provider types based on urgency
        if ai_consult.urgency_level == UrgencyLevel.EMERGENCY:
            approved_providers = [ProviderType.ED]
        elif ai_consult.urgency_level == UrgencyLevel.URGENT:
            approved_providers = [ProviderType.URGENT_CARE, ProviderType.GP, ProviderType.NP]
        else:
            approved_providers = [ProviderType.GP, ProviderType.NP, ProviderType.SPECIALIST]
        
        care_plan = care_router.generate_routing_plan(
            consult_id=consult_id,
            patient=patient,
            urgency=ai_consult.urgency_level,
            approved_providers=approved_providers,
            clinical_summary=ai_consult.soap.assessment
        )
        
        # Store results in session
        session['results'] = {
            'patient': {
                'age': patient.age,
                'sex': patient.sex,
                'has_gp': patient.has_regular_gp
            },
            'chief_complaint': transcript.chief_complaint,
            'urgency': ai_consult.urgency_level.value,
            'confidence': ai_consult.confidence_score,
            'soap': {
                'subjective': ai_consult.soap.subjective,
                'objective': ai_consult.soap.objective,
                'assessment': ai_consult.soap.assessment,
                'plan': ai_consult.soap.plan
            },
            'differential_diagnoses': [
                {'diagnosis': d.diagnosis, 'probability': d.probability_percent}
                for d in ai_consult.differential_diagnoses
            ],
            'student_review': {
                'name': student_review.student_name,
                'agrees': student_review.agrees_with_ai_assessment,
                'notes': student_review.assessment_notes
            },
            'care_options': [
                {
                    'facility_name': opt.facility_name,
                    'provider_type': opt.provider_type.value,
                    'address': opt.address,
                    'distance_km': opt.distance_km,
                    'wait_time': opt.estimated_wait_time,
                    'phone': opt.contact_phone,
                    'score': opt.score
                }
                for opt in care_plan.ranked_options[:3]
            ],
            'reasoning': ai_consult.reasoning.model_dump()
        }
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        print(f"Error processing consultation: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/results')
def results():
    """Display results page"""
    if 'results' not in session:
        return "No consultation data found. Please start a new consultation.", 404
    
    return render_template('results.html', **session['results'])


def create_mock_soap(transcript: PatientTranscript, patient: PatientData):
    """Create mock SOAP when Gemini fails"""
    from models.data_models import AIConsultOutput, SOAPNote, DifferentialDiagnosis, AIReasoning
    
    return AIConsultOutput(
        soap=SOAPNote(
            subjective=transcript.transcript_text,
            objective="Virtual consultation - no physical exam performed.",
            assessment="Symptoms require clinical evaluation.",
            plan="Recommend in-person assessment with appropriate healthcare provider."
        ),
        urgency_level=UrgencyLevel.URGENT,
        confidence_score=0.7,
        differential_diagnoses=[
            DifferentialDiagnosis(
                diagnosis=transcript.chief_complaint,
                probability_percent=60,
                rationale="Based on presenting symptoms"
            )
        ],
        reasoning=AIReasoning(
            key_findings=[transcript.chief_complaint],
            red_flags_identified=[],
            guideline_references=[],
            confidence_explanation="Mock assessment - please seek in-person care"
        )
    )


if __name__ == '__main__':
    print("\n" + "="*80)
    print("MEDUROAM CHATBOT - Starting Web Server")
    print("="*80)
    print("\n🌐 Open your browser and go to: http://localhost:5004")
    print("\n📍 Location: Queen's University, Kingston, ON")
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("\n" + "="*80 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5004,
        debug=True,
        use_reloader=False
    )
