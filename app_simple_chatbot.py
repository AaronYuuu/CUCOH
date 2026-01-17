#!/usr/bin/env python3
"""
Simple Hardcoded Chatbot - No external dependencies
Port: 5004
"""

from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, timedelta
from uuid import uuid4

app = Flask(__name__)
app.secret_key = 'meduroam-simple-chatbot-2026'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# In-memory storage
consultations = {}


@app.route('/')
def index():
    """Render chatbot interface"""
    session.clear()
    return render_template('chatbot.html')


@app.route('/start-consult', methods=['POST'])
def start_consult():
    """Initialize consultation"""
    consult_id = str(uuid4())
    session['consult_id'] = consult_id
    session.permanent = True
    
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
    """Process symptoms and generate hardcoded response"""
    data = request.json
    consult_id = data.get('consult_id')
    
    if not consult_id or consult_id not in consultations:
        return jsonify({'error': 'Invalid consultation ID'}), 400
    
    # Extract data
    age = int(data['age'])
    sex = data['sex']
    has_gp = data['has_gp']
    chief_complaint = data['chief_complaint']
    symptoms = data['symptoms']
    duration = data['duration']
    severity = data['severity']
    additional = data.get('additional_info', 'None')
    
    # Determine urgency based on keywords
    urgency = determine_urgency(chief_complaint, symptoms, severity)
    
    # Generate hardcoded care options
    care_options = generate_care_options(urgency, has_gp)
    
    # Store results
    session['results'] = {
        'patient': {
            'age': age,
            'sex': sex,
            'has_gp': (has_gp == 'yes')
        },
        'chief_complaint': chief_complaint,
        'urgency': urgency,
        'confidence': 0.85,
        'soap': {
            'subjective': f"Patient reports {chief_complaint}. {symptoms} Duration: {duration}. Severity: {severity}. Additional: {additional}",
            'objective': "Virtual consultation - no physical examination performed.",
            'assessment': f"Patient presenting with {chief_complaint}. Based on symptom description, {get_assessment_text(urgency)}",
            'plan': get_plan_text(urgency)
        },
        'differential_diagnoses': get_differential_diagnoses(chief_complaint),
        'student_review': {
            'name': 'Medical Student (Demo)',
            'agrees': True,
            'notes': 'Assessment reviewed. Routing appears appropriate for urgency level.'
        },
        'care_options': care_options,
        'reasoning': {
            'key_findings': [chief_complaint, f"Duration: {duration}", f"Severity: {severity}"],
            'red_flags_identified': get_red_flags(chief_complaint, symptoms),
            'guideline_references': ['Canadian Triage and Acuity Scale (CTAS)'],
            'confidence_explanation': f'Assessment based on presenting symptoms and {urgency.lower()} acuity level.'
        }
    }
    
    return jsonify({'status': 'success'})


@app.route('/results')
def results():
    """Display results"""
    if 'results' not in session:
        return "No consultation found. Please start a new consultation.", 404
    
    return render_template('results.html', **session['results'])


def determine_urgency(complaint, symptoms, severity):
    """Determine urgency level from keywords"""
    complaint_lower = complaint.lower()
    symptoms_lower = symptoms.lower()
    
    # Emergency keywords
    emergency_keywords = [
        'chest pain', 'heart attack', 'stroke', 'seizure', 'unconscious',
        'severe bleeding', 'can\'t breathe', 'choking', 'suicide'
    ]
    
    # Urgent keywords
    urgent_keywords = [
        'severe pain', 'high fever', 'difficulty breathing', 'broken',
        'fracture', 'deep cut', 'head injury', 'very severe'
    ]
    
    # Check for emergency
    for keyword in emergency_keywords:
        if keyword in complaint_lower or keyword in symptoms_lower:
            return 'EMERGENCY'
    
    # Check for urgent
    if 'very severe' in severity.lower():
        return 'URGENT'
    
    for keyword in urgent_keywords:
        if keyword in complaint_lower or keyword in symptoms_lower:
            return 'URGENT'
    
    return 'ROUTINE'


def get_assessment_text(urgency):
    """Get assessment text based on urgency"""
    if urgency == 'EMERGENCY':
        return "this requires immediate emergency department evaluation."
    elif urgency == 'URGENT':
        return "this warrants prompt medical attention within 24 hours."
    else:
        return "routine medical evaluation is recommended."


def get_plan_text(urgency):
    """Get plan text based on urgency"""
    if urgency == 'EMERGENCY':
        return "IMMEDIATE REFERRAL: Go to emergency department now or call 911."
    elif urgency == 'URGENT':
        return "Seek medical attention within 24 hours. Urgent care or walk-in clinic recommended."
    else:
        return "Schedule appointment with primary care provider or walk-in clinic."


def get_differential_diagnoses(complaint):
    """Generate differential diagnoses"""
    diagnoses_map = {
        'chest pain': [
            {'diagnosis': 'Acute coronary syndrome', 'probability': 25},
            {'diagnosis': 'Musculoskeletal pain', 'probability': 40},
            {'diagnosis': 'Gastroesophageal reflux', 'probability': 20},
            {'diagnosis': 'Anxiety', 'probability': 15}
        ],
        'headache': [
            {'diagnosis': 'Tension headache', 'probability': 50},
            {'diagnosis': 'Migraine', 'probability': 30},
            {'diagnosis': 'Sinus infection', 'probability': 15},
            {'diagnosis': 'Other', 'probability': 5}
        ],
        'fever': [
            {'diagnosis': 'Viral infection', 'probability': 60},
            {'diagnosis': 'Bacterial infection', 'probability': 25},
            {'diagnosis': 'Inflammatory condition', 'probability': 10},
            {'diagnosis': 'Other', 'probability': 5}
        ],
        'shortness of breath': [
            {'diagnosis': 'Asthma exacerbation', 'probability': 30},
            {'diagnosis': 'Pneumonia', 'probability': 25},
            {'diagnosis': 'Heart failure', 'probability': 20},
            {'diagnosis': 'Anxiety', 'probability': 15},
            {'diagnosis': 'Other', 'probability': 10}
        ]
    }
    
    complaint_lower = complaint.lower()
    for key, diagnoses in diagnoses_map.items():
        if key in complaint_lower:
            return diagnoses
    
    # Default
    return [
        {'diagnosis': 'Requires clinical evaluation', 'probability': 70},
        {'diagnosis': 'Multiple possibilities', 'probability': 30}
    ]


def get_red_flags(complaint, symptoms):
    """Identify red flag symptoms"""
    red_flags = []
    text = (complaint + ' ' + symptoms).lower()
    
    if 'chest pain' in text:
        red_flags.append('Chest pain requires urgent evaluation')
    if 'difficulty breathing' in text or 'shortness of breath' in text:
        red_flags.append('Respiratory distress')
    if 'severe' in text:
        red_flags.append('Severe symptoms reported')
    
    return red_flags if red_flags else ['None identified']


def generate_care_options(urgency, has_gp):
    """Generate care options for Kingston area"""
    if urgency == 'EMERGENCY':
        return [
            {
                'facility_name': 'Kingston Health Sciences Centre - Emergency',
                'provider_type': 'ED',
                'address': '76 Stuart St, Kingston, ON K7L 2V7',
                'distance_km': 0.4,
                'wait_time': '2-4 hours',
                'phone': '(613) 548-3232',
                'score': 95
            },
            {
                'facility_name': 'Call 911',
                'provider_type': 'EMERGENCY',
                'address': 'Emergency Services',
                'distance_km': 0.0,
                'wait_time': 'Immediate',
                'phone': '911',
                'score': 100
            }
        ]
    elif urgency == 'URGENT':
        return [
            {
                'facility_name': 'Appletree Medical - Kingston Walk-In',
                'provider_type': 'URGENT_CARE',
                'address': '1471 John Counter Blvd, Kingston, ON K7M 8S8',
                'distance_km': 4.2,
                'wait_time': '1-2 hours',
                'phone': '(613) 634-1140',
                'score': 88
            },
            {
                'facility_name': 'Queen\'s Student Wellness Services - Same Day',
                'provider_type': 'NP',
                'address': '146 Stuart St, Kingston, ON K7L 3N6',
                'distance_km': 0.3,
                'wait_time': '2-4 hours',
                'phone': '(613) 533-2506',
                'score': 85
            },
            {
                'facility_name': 'Kingston Health Sciences Centre - Urgent Care',
                'provider_type': 'URGENT_CARE',
                'address': '76 Stuart St, Kingston, ON K7L 2V7',
                'distance_km': 0.4,
                'wait_time': '2-3 hours',
                'phone': '(613) 548-3232',
                'score': 82
            }
        ]
    else:  # ROUTINE
        return [
            {
                'facility_name': 'Queen\'s Student Wellness Services',
                'provider_type': 'GP',
                'address': '146 Stuart St, Kingston, ON K7L 3N6',
                'distance_km': 0.3,
                'wait_time': '1-3 days',
                'phone': '(613) 533-2506',
                'score': 92
            },
            {
                'facility_name': 'Appletree Medical - Kingston',
                'provider_type': 'GP',
                'address': '1471 John Counter Blvd, Kingston, ON K7M 8S8',
                'distance_km': 4.2,
                'wait_time': '1-2 days',
                'phone': '(613) 634-1140',
                'score': 85
            },
            {
                'facility_name': 'Kingston Community Health Centre',
                'provider_type': 'NP',
                'address': '263 Weller Ave, Kingston, ON K7K 3J4',
                'distance_km': 2.8,
                'wait_time': '2-4 days',
                'phone': '(613) 542-2949',
                'score': 78
            }
        ]


if __name__ == '__main__':
    print("\n" + "="*80)
    print("MEDUROAM SIMPLE CHATBOT - Starting Web Server")
    print("="*80)
    print("\n🌐 Open your browser: http://localhost:5004")
    print("\n📍 Location: Queen's University, Kingston, ON")
    print("\n⚠️  Press Ctrl+C to stop")
    print("\n" + "="*80 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5004,
        debug=True,
        use_reloader=False
    )
