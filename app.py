"""
Meduroam Web Application
Flask-based web interface for localhost deployment
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from uuid import uuid4

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.data_models import (
    PatientData, PatientTranscript, UrgencyLevel, ProviderType,
    StudentReview, StudentDecision, SOAPNote, AIReasoning, AIConsultOutput
)
from workflows.workflow_engine import WorkflowEngine, WorkflowOrchestrator
from decision_engine.care_routing import CareRoutingEngine
from compliance.audit_logging import AuditLogger
from api.gemini_integration import GeminiSOAPGenerator

app = Flask(__name__)
app.secret_key = 'meduroam-secret-key-change-in-production'

# Global components
API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyB7vrnf3k5HB8GrwWn_GMtLbf49HXBjpv8')
workflow_engine = WorkflowEngine()
orchestrator = WorkflowOrchestrator(workflow_engine)
routing_engine = CareRoutingEngine()
audit_logger = AuditLogger()

try:
    soap_generator = GeminiSOAPGenerator(API_KEY)
except:
    soap_generator = None

# Queen's University configuration
QUEENS_CONFIG = {
    "postal_code": "K7L 3N6",
    "institution": "Queen's University"
}


@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')


@app.route('/start-consult', methods=['POST'])
def start_consult():
    """Initialize a new consultation"""
    data = request.json
    
    # Create patient
    patient_id = f"P_{str(uuid4())[:8]}"
    patient = PatientData(
        patient_id=patient_id,
        age=int(data.get('age', 25)),
        sex=data.get('sex', 'Unknown'),
        province="Ontario",
        postal_code=QUEENS_CONFIG['postal_code'],
        has_family_doctor=data.get('has_gp', False),
        phone=data.get('phone'),
        email=data.get('email')
    )
    
    # Store in session
    session['patient_id'] = patient_id
    session['patient_data'] = patient.dict()
    
    return jsonify({
        'success': True,
        'patient_id': patient_id,
        'message': 'Patient registered. Please describe your symptoms.'
    })


@app.route('/submit-symptoms', methods=['POST'])
def submit_symptoms():
    """Submit patient symptoms"""
    data = request.json
    patient_data = session.get('patient_data')
    
    if not patient_data:
        return jsonify({'success': False, 'error': 'No patient session found'}), 400
    
    # Create transcript
    transcript_id = f"T_{str(uuid4())[:8]}"
    transcript = PatientTranscript(
        transcript_id=transcript_id,
        patient_id=patient_data['patient_id'],
        chief_complaint=data.get('chief_complaint', ''),
        symptom_description=data.get('description', ''),
        duration=data.get('duration', 'Not specified'),
        severity=data.get('severity', 'Not specified'),
        associated_symptoms=data.get('associated_symptoms', []),
        medical_history=data.get('medical_history', []),
        medications=data.get('medications', []),
        allergies=data.get('allergies', []),
        timestamp=datetime.now()
    )
    
    # Generate SOAP note
    try:
        patient = PatientData(**patient_data)
        if soap_generator:
            ai_output = soap_generator.generate_soap_note(
                transcript, 
                patient.age, 
                patient.sex
            )
        else:
            ai_output = create_mock_soap(transcript, patient)
    except Exception as e:
        print(f"AI Error: {e}")
        patient = PatientData(**patient_data)
        ai_output = create_mock_soap(transcript, patient)
    
    # Create workflow
    consult_id = f"C_{transcript_id}"
    workflow = workflow_engine.create_workflow(
        consult_id=consult_id,
        patient_id=patient_data['patient_id'],
        transcript_id=transcript_id
    )
    
    # Log AI generation
    audit_logger.log_ai_generation(
        consult_id=consult_id,
        patient_id=patient_data['patient_id'],
        ai_model="gemini-1.5-pro",
        output_type="SOAP_NOTE",
        confidence=ai_output.reasoning.confidence_level
    )
    
    # Simulate student review
    student_review = create_student_review(ai_output, patient_data['patient_id'])
    
    # Generate care routing
    patient = PatientData(**patient_data)
    routing_plan = routing_engine.generate_routing_plan(
        consult_id=consult_id,
        patient=patient,
        urgency=student_review.validated_urgency,
        approved_providers=student_review.selected_providers,
        clinical_summary=ai_output.soap_note.assessment
    )
    
    # Store results in session
    session['consult_id'] = consult_id
    session['results'] = {
        'ai_assessment': {
            'subjective': ai_output.soap_note.subjective,
            'assessment': ai_output.soap_note.assessment,
            'plan': ai_output.soap_note.plan,
            'urgency': ai_output.preliminary_urgency.value,
            'confidence': ai_output.reasoning.confidence_level,
            'differentials': ai_output.reasoning.differential_diagnosis
        },
        'student_review': {
            'name': student_review.student_name,
            'decision': student_review.assessment_decision.value,
            'urgency': student_review.validated_urgency.value,
            'reasoning': student_review.clinical_reasoning_summary
        },
        'care_options': [
            {
                'facility': opt.facility_name,
                'type': opt.provider_type.value,
                'address': opt.address,
                'distance_km': opt.distance_km,
                'wait_time': opt.estimated_wait_time,
                'phone': opt.phone,
                'walk_in': opt.accepts_walk_ins,
                'priority_score': opt.priority_score
            }
            for opt in routing_plan.recommended_options[:5]
        ]
    }
    
    return jsonify({
        'success': True,
        'consult_id': consult_id,
        'results': session['results']
    })


@app.route('/results')
def results():
    """Display results page"""
    results_data = session.get('results')
    if not results_data:
        return "No consultation data found. Please start a new consultation.", 404
    
    return render_template('results.html', results=results_data)


def create_mock_soap(transcript, patient):
    """Create mock SOAP for demo"""
    return AIConsultOutput(
        consult_id=f"C_{transcript.transcript_id}",
        patient_id=transcript.patient_id,
        transcript_id=transcript.transcript_id,
        soap_note=SOAPNote(
            subjective=f"{patient.age}yo {patient.sex} presenting with {transcript.chief_complaint}. {transcript.symptom_description}",
            objective="Patient-reported symptoms. No physical examination performed (telemedicine consultation).",
            assessment="Based on patient-reported symptoms, requires clinical evaluation for accurate assessment and diagnosis.",
            plan="Recommend in-person evaluation by appropriate healthcare provider for complete assessment and management plan."
        ),
        reasoning=AIReasoning(
            differential_diagnosis=["Requires clinical assessment"],
            red_flags_assessed=["To be evaluated in person"],
            clinical_reasoning="Patient symptoms require in-person clinical evaluation for accurate diagnosis and treatment planning.",
            confidence_level=0.6,
            supporting_evidence=[],
            ruled_out_conditions=[]
        ),
        preliminary_urgency=UrgencyLevel.ROUTINE,
        suggested_providers=[ProviderType.GP],
        generated_at=datetime.now(),
        ai_model_version="gemini-1.5-pro"
    )


def create_student_review(ai_output, patient_id):
    """Create simulated student review"""
    return StudentReview(
        review_id=f"SR_{str(uuid4())[:8]}",
        consult_id=ai_output.consult_id,
        student_id="MS_DEMO",
        student_name="Medical Student (Queen's Medicine)",
        assessment_decision=StudentDecision.AGREE,
        validated_urgency=ai_output.preliminary_urgency,
        selected_providers=ai_output.suggested_providers,
        clinical_reasoning_summary="Reviewed AI assessment. Clinical presentation is consistent with preliminary analysis. Appropriate care pathway recommended.",
        key_differentials=ai_output.reasoning.differential_diagnosis[:3],
        red_flags_assessment="No immediate red flags requiring emergency evaluation based on reported symptoms.",
        provider_selection_rationale=f"Recommended {ai_output.suggested_providers[0].value} based on clinical urgency and patient needs.",
        requires_escalation=False,
        reviewed_at=datetime.now(),
        time_spent_minutes=5.0
    )


if __name__ == '__main__':
    print("\n" + "="*80)
    print("MEDUROAM - Starting Web Server")
    print("="*80)
    print("\n🌐 Open your browser and go to: http://localhost:5001")
    print("\n📍 Location: Queen's University, Kingston, ON")
    print("\n⚠️  Press Ctrl+C to stop the server\n")
    print("="*80 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
