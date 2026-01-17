#!/usr/bin/env python3
"""
MEDUROAM - Clinical Reasoning Assistant MVP
A healthcare consultation platform using Gemini AI
"""

import os
import json
import sys
from datetime import datetime
from uuid import uuid4

try:
    import google.generativeai as genai
except ImportError:
    print("ERROR: google-generativeai not installed.")
    print("Run: pip install google-generativeai python-dotenv")
    sys.exit(1)

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("\n❌ ERROR: GEMINI_API_KEY not found in environment")
    print("Create a .env file with: GEMINI_API_KEY=your_key_here")
    print("Or set it now:")
    GEMINI_API_KEY = input("Paste your Gemini API key: ").strip()
    if not GEMINI_API_KEY:
        sys.exit(1)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# System Prompt
SYSTEM_PROMPT = """You are MEDUROAM, a clinical reasoning assistant conducting a medical consultation.

CRITICAL BOUNDARIES:
- You are NOT a licensed physician
- You do NOT provide definitive diagnoses
- You do NOT prescribe medications
- All outputs require validation by a healthcare professional

CONSULTATION PROTOCOL:
1. Start with open-ended chief complaint
2. History of Present Illness (OPQRST/OLDCARTS):
   - Onset, Location, Duration, Character
   - Aggravating/Alleviating factors
   - Radiation, Timing, Severity
3. Targeted Review of Systems (red-flag screening)
4. Past medical history, medications, allergies, social history
5. Concern verification - ask if anything was missed

RED FLAGS (immediate escalation):
- Chest pain + radiation/diaphoresis → "⚠️ CARDIAC EMERGENCY - Call 911"
- Sudden severe headache/neuro deficit → "⚠️ STROKE ALERT - Call 911"
- Severe breathing difficulty → "⚠️ BREATHING EMERGENCY - Call 911"
- Fever + altered mental status/stiff neck → "⚠️ INFECTION - Seek ER"
- Suicidal ideation → "⚠️ CRISIS - Call 988"

COMMUNICATION STYLE:
- Warm, professional, empathetic
- One question at a time
- Plain language (explain medical terms)
- Natural disclaimers: "for your doctor to evaluate..."

When consultation complete, say: "CONSULTATION_COMPLETE"

Then generate SOAP note in JSON format with:
- metadata (timestamp, session_id, red_flag_status)
- subjective (chief_complaint, hpi_narrative, hpi_bullets, ros, pmh, meds, allergies, social_hx)
- objective (vital_signs: patient-reported or null)
- assessment (differential_diagnosis with confidence levels and reasoning)
- plan (recommended_actions with urgency, safety_netting, disclaimer)
"""

RED_FLAG_KEYWORDS = [
    "chest pain", "crushing", "pressure", "radiating",
    "can't breathe", "difficulty breathing", "blue lips",
    "worst headache", "sudden weakness", "slurred speech", "face drooping",
    "stiff neck", "confused", "altered mental status",
    "suicidal", "kill myself", "end my life"
]


class MeduroamSession:
    def __init__(self):
        self.session_id = str(uuid4())
        self.start_time = datetime.now()
        self.messages = []
        self.red_flag_detected = False
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-pro',
            generation_config={
                'temperature': 0.7,
                'top_p': 0.95,
                'max_output_tokens': 2048,
            }
        )
        
        # Start conversation with system prompt
        self.chat = self.model.start_chat(history=[])
        
    def check_red_flags(self, text):
        """Quick keyword-based red flag detection"""
        text_lower = text.lower()
        for keyword in RED_FLAG_KEYWORDS:
            if keyword in text_lower:
                return True
        return False
    
    def conduct_consultation(self):
        """Main consultation loop"""
        print("\n" + "="*70)
        print("MEDUROAM - Clinical Reasoning Assistant")
        print("="*70)
        print("\nDISCLAIMER: This is an AI assistant, not a licensed physician.")
        print("All information requires validation by a healthcare professional.")
        print("\nType 'exit' to end consultation early.\n")
        print("="*70 + "\n")
        
        # Initial greeting
        greeting = self._send_to_ai(SYSTEM_PROMPT + "\n\nStart the consultation with your opening greeting.")
        print(f"🏥 MEDUROAM: {greeting}\n")
        
        consultation_active = True
        
        while consultation_active:
            # Get patient input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == 'exit':
                print("\n⚠️ Consultation ended by user.")
                return None
            
            # Check for red flags
            if self.check_red_flags(user_input):
                self.red_flag_detected = True
                
            # Send to AI
            response = self._send_to_ai(user_input)
            
            # Check if consultation complete
            if "CONSULTATION_COMPLETE" in response:
                print("\n🏥 MEDUROAM: Thank you for sharing all that information.")
                print("I'm now generating your structured clinical summary...\n")
                consultation_active = False
            else:
                print(f"\n🏥 MEDUROAM: {response}\n")
        
        # Generate SOAP note
        return self._generate_soap_note()
    
    def _send_to_ai(self, message):
        """Send message to Gemini and get response"""
        try:
            response = self.chat.send_message(message)
            return response.text
        except Exception as e:
            return f"Error communicating with AI: {str(e)}"
    
    def _generate_soap_note(self):
        """Request structured SOAP note from AI"""
        print("Generating SOAP note...")
        
        soap_request = """
Now generate a complete SOAP note in valid JSON format with this exact structure:

{
  "metadata": {
    "session_id": "UUID",
    "timestamp": "ISO 8601",
    "red_flag_status": true/false,
    "overall_confidence": "high/moderate/low"
  },
  "subjective": {
    "chief_complaint": "string",
    "hpi_narrative": "2-3 paragraph narrative",
    "hpi_bullets": ["Onset: ...", "Location: ...", etc],
    "review_of_systems": {"constitutional": "...", "cardiovascular": "...", etc},
    "past_medical_history": ["conditions"],
    "medications": ["meds"],
    "allergies": ["allergies"],
    "social_history": {"tobacco": "...", "alcohol": "...", "occupation": "..."},
    "patient_concerns": ["explicit concerns"]
  },
  "objective": {
    "vital_signs": {"note": "Patient-reported or not available", "temperature": null, etc},
    "physical_exam": "Not performed - remote consultation"
  },
  "assessment": {
    "clinical_summary": "synthesis of presentation",
    "differential_diagnosis": [
      {
        "condition": "name",
        "confidence": "high/moderate/low",
        "reasoning": "clinical logic",
        "supporting_findings": ["findings"]
      }
    ],
    "red_flags_identified": []
  },
  "plan": {
    "recommended_actions": [
      {
        "category": "diagnostic_testing/specialist_referral/primary_care_followup/emergency",
        "urgency": "immediate/urgent/routine",
        "description": "action",
        "rationale": "reason"
      }
    ],
    "safety_netting": "when to seek re-evaluation",
    "disclaimer": "AI-generated, requires physician validation"
  }
}

Generate ONLY the JSON, no other text.
"""
        
        try:
            soap_response = self._send_to_ai(soap_request)
            
            # Extract JSON from response (handle markdown code blocks)
            soap_text = soap_response.strip()
            if soap_text.startswith("```json"):
                soap_text = soap_text.split("```json")[1].split("```")[0].strip()
            elif soap_text.startswith("```"):
                soap_text = soap_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            soap_data = json.loads(soap_text)
            
            # Add session metadata
            soap_data["metadata"]["session_id"] = self.session_id
            soap_data["metadata"]["timestamp"] = self.start_time.isoformat()
            soap_data["metadata"]["red_flag_status"] = self.red_flag_detected
            
            return soap_data
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Error parsing SOAP note JSON: {e}")
            print(f"Raw response:\n{soap_response[:500]}...")
            return None
        except Exception as e:
            print(f"⚠️ Error generating SOAP note: {e}")
            return None


def save_soap_note(soap_data, filename=None):
    """Save SOAP note to file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"soap_note_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(soap_data, f, indent=2, ensure_ascii=False)
    
    return filename


def display_soap_summary(soap_data):
    """Display human-readable SOAP summary"""
    print("\n" + "="*70)
    print("SOAP NOTE SUMMARY")
    print("="*70)
    
    # Subjective
    print(f"\n📋 CHIEF COMPLAINT:")
    print(f"   {soap_data['subjective']['chief_complaint']}")
    
    # Assessment
    print(f"\n🔍 DIFFERENTIAL DIAGNOSES:")
    for idx, dx in enumerate(soap_data['assessment']['differential_diagnosis'], 1):
        print(f"   {idx}. {dx['condition']} (Confidence: {dx['confidence']})")
        print(f"      → {dx['reasoning'][:100]}...")
    
    # Plan
    print(f"\n📝 RECOMMENDED ACTIONS:")
    for action in soap_data['plan']['recommended_actions']:
        urgency_emoji = {"immediate": "🚨", "urgent": "⚡", "routine": "📅"}.get(action['urgency'], "•")
        print(f"   {urgency_emoji} [{action['urgency'].upper()}] {action['description']}")
    
    # Red flags
    if soap_data['metadata']['red_flag_status']:
        print(f"\n⚠️ RED FLAGS DETECTED:")
        for flag in soap_data['assessment'].get('red_flags_identified', []):
            print(f"   • {flag}")
    
    print("\n" + "="*70)
    print("⚠️ DISCLAIMER: AI-generated. Requires validation by licensed healthcare provider.")
    print("="*70 + "\n")


def main():
    """Main entry point"""
    print("\n🚀 Starting MEDUROAM Clinical Reasoning Assistant MVP...")
    
    # Create session
    session = MeduroamSession()
    
    try:
        # Run consultation
        soap_data = session.conduct_consultation()
        
        if soap_data:
            # Display summary
            display_soap_summary(soap_data)
            
            # Save to file
            filename = save_soap_note(soap_data)
            print(f"✅ Full SOAP note saved to: {filename}")
            
            # Ask if user wants to see full JSON
            show_full = input("\nView full SOAP note JSON? (y/n): ").strip().lower()
            if show_full == 'y':
                print("\n" + json.dumps(soap_data, indent=2))
        else:
            print("\n⚠️ Consultation ended without complete SOAP note.")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Consultation interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error during consultation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
