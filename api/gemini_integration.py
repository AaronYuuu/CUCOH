"""
Gemini AI Integration
Handles communication with Google's Gemini API for SOAP note generation
"""

import os
from datetime import datetime
from typing import Dict, Any
import google.generativeai as genai
from models.data_models import (
    AIConsultOutput, SOAPNote, AIReasoning, 
    PatientTranscript, UrgencyLevel, ProviderType
)


class GeminiSOAPGenerator:
    """
    Integrates with Gemini API to generate SOAP notes and clinical reasoning
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google AI API key
        """
        genai.configure(api_key=api_key)
        # Use gemini-2.0-flash model (faster, available model)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def generate_soap_note(
        self, 
        transcript: PatientTranscript,
        patient_age: int = None,
        patient_sex: str = None
    ) -> AIConsultOutput:
        """
        Generate complete SOAP note with reasoning from patient transcript
        
        Args:
            transcript: Patient symptom description and history
            patient_age: Patient age (optional)
            patient_sex: Patient sex (optional)
            
        Returns:
            Complete AI consultation output with SOAP note and reasoning
        """
        
        # Construct prompt for Gemini
        prompt = self._build_soap_prompt(transcript, patient_age, patient_sex)
        
        # Call Gemini API
        response = self.model.generate_content(prompt)
        
        # Parse response
        parsed_output = self._parse_gemini_response(response.text)
        
        # Create structured output
        consult_output = AIConsultOutput(
            consult_id=f"consult_{transcript.transcript_id}",
            patient_id=transcript.patient_id,
            transcript_id=transcript.transcript_id,
            soap_note=parsed_output["soap_note"],
            reasoning=parsed_output["reasoning"],
            preliminary_urgency=parsed_output["urgency"],
            suggested_providers=parsed_output["providers"],
            generated_at=datetime.now(),
            ai_model_version="gemini-2.0-flash-exp"
        )
        
        return consult_output
    
    def _build_soap_prompt(self, transcript: PatientTranscript, patient_age: int = None, patient_sex: str = None) -> str:
        """Build comprehensive prompt for Gemini"""
        
        age_str = str(patient_age) if patient_age else "Unknown"
        sex_str = patient_sex if patient_sex else "Unknown"
        
        prompt = f"""You are a clinical decision support AI assisting in primary care triage and assessment. 
Your role is to analyze patient symptoms and generate a structured clinical assessment that will be reviewed by a medical student and supervising physician.

**CRITICAL INSTRUCTIONS:**
- This is a CLINICAL DECISION SUPPORT tool, NOT a diagnostic system
- Your output will be REVIEWED and VALIDATED by licensed healthcare providers
- Be thorough in considering differential diagnoses
- Prioritize patient safety - when in doubt, recommend higher acuity
- Use clear, professional medical language
- Provide evidence-based reasoning

**PATIENT INFORMATION:**
Age: {age_str}
Sex: {sex_str}

**CHIEF COMPLAINT:**
{transcript.chief_complaint}

**SYMPTOM DESCRIPTION:**
{transcript.symptom_description}

**DURATION:** {transcript.duration}
**SEVERITY:** {transcript.severity}

**ASSOCIATED SYMPTOMS:**
{', '.join(transcript.associated_symptoms) if transcript.associated_symptoms else 'None reported'}

**MEDICAL HISTORY:**
{', '.join(transcript.medical_history) if transcript.medical_history else 'None reported'}

**CURRENT MEDICATIONS:**
{', '.join(transcript.medications) if transcript.medications else 'None reported'}

**ALLERGIES:**
{', '.join(transcript.allergies) if transcript.allergies else 'None reported'}

---

Please provide your assessment in the following structured format:

## SOAP NOTE

### SUBJECTIVE:
[Patient's description of symptoms in clinical terms]

### OBJECTIVE:
[Observable/measurable findings based on patient report. Note: No physical exam was performed - this is based on patient self-report only]

### ASSESSMENT:
[Your clinical impression including most likely diagnosis and important differentials]

### PLAN:
[Recommended next steps, provider type, timeframe, and any immediate actions]

---

## CLINICAL REASONING

### DIFFERENTIAL DIAGNOSIS:
[List 3-5 possible diagnoses in order of likelihood]
- [Diagnosis 1]: [Brief rationale]
- [Diagnosis 2]: [Brief rationale]
- etc.

### RED FLAGS ASSESSED:
[List dangerous symptoms you specifically evaluated for and ruled in/out]
- [Red flag 1]: [Your assessment]
- [Red flag 2]: [Your assessment]
- etc.

### CLINICAL REASONING:
[2-3 paragraphs explaining your thought process, key decision points, and evidence considered]

### RULED OUT CONDITIONS:
[List serious conditions you considered but ruled out with brief reasoning]
- [Condition 1]: [Why ruled out]
- [Condition 2]: [Why ruled out]

### SUPPORTING EVIDENCE:
[Key clinical features that support your assessment]
- [Evidence 1]
- [Evidence 2]
- etc.

### CONFIDENCE LEVEL:
[Provide a confidence score from 0.0 to 1.0, where 1.0 is very confident]

---

## URGENCY CLASSIFICATION

**URGENCY LEVEL:** [Choose ONE: ROUTINE, URGENT, or EMERGENCY]

**RATIONALE:** [Explain why you chose this urgency level]

---

## RECOMMENDED PROVIDER TYPES

**PRIMARY RECOMMENDATION:** [Choose from: GP, NP, RN, PSW, SPECIALIST, URGENT_CARE, ED]

**ALTERNATIVE OPTIONS:** [List 1-2 alternative appropriate provider types]

**RATIONALE:** [Explain why these provider types are appropriate]

---

**IMPORTANT DISCLAIMERS:**
- This assessment is based on limited information and requires validation by a healthcare provider
- If this is a life-threatening emergency, call 911 immediately
- Patient should seek in-person medical evaluation for comprehensive assessment
"""
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini's response into structured data
        
        Note: This is a simplified parser. Production version should be more robust
        with better error handling and validation.
        """
        
        # Initialize default structure
        result = {
            "soap_note": SOAPNote(
                subjective="",
                objective="",
                assessment="",
                plan=""
            ),
            "reasoning": AIReasoning(
                differential_diagnosis=[],
                red_flags_assessed=[],
                clinical_reasoning="",
                confidence_level=0.7,
                supporting_evidence=[],
                ruled_out_conditions=[]
            ),
            "urgency": UrgencyLevel.ROUTINE,
            "providers": [ProviderType.GP]
        }
        
        # Simple parsing (in production, use more sophisticated NLP or structured output)
        lines = response_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Section headers
            if 'SUBJECTIVE:' in line:
                current_section = 'subjective'
                continue
            elif 'OBJECTIVE:' in line:
                current_section = 'objective'
                continue
            elif 'ASSESSMENT:' in line:
                current_section = 'assessment'
                continue
            elif 'PLAN:' in line:
                current_section = 'plan'
                continue
            elif 'DIFFERENTIAL DIAGNOSIS:' in line:
                current_section = 'differential'
                continue
            elif 'RED FLAGS ASSESSED:' in line:
                current_section = 'red_flags'
                continue
            elif 'CLINICAL REASONING:' in line:
                current_section = 'clinical_reasoning'
                continue
            elif 'RULED OUT CONDITIONS:' in line:
                current_section = 'ruled_out'
                continue
            elif 'SUPPORTING EVIDENCE:' in line:
                current_section = 'supporting'
                continue
            elif 'CONFIDENCE LEVEL:' in line:
                current_section = 'confidence'
                continue
            elif 'URGENCY LEVEL:' in line:
                current_section = 'urgency'
                # Try to extract urgency from this line
                if 'EMERGENCY' in line.upper():
                    result['urgency'] = UrgencyLevel.EMERGENCY
                elif 'URGENT' in line.upper():
                    result['urgency'] = UrgencyLevel.URGENT
                else:
                    result['urgency'] = UrgencyLevel.ROUTINE
                continue
            elif 'PRIMARY RECOMMENDATION:' in line:
                current_section = 'providers'
                # Extract provider from line
                if 'ED' in line.upper():
                    result['providers'] = [ProviderType.ED]
                elif 'URGENT_CARE' in line or 'URGENT CARE' in line:
                    result['providers'] = [ProviderType.URGENT_CARE]
                elif 'SPECIALIST' in line.upper():
                    result['providers'] = [ProviderType.SPECIALIST]
                elif 'NP' in line or 'NURSE PRACTITIONER' in line:
                    result['providers'] = [ProviderType.NP]
                else:
                    result['providers'] = [ProviderType.GP]
                continue
            
            # Append content to current section
            if current_section and line and not line.startswith('#'):
                if current_section == 'subjective':
                    result['soap_note'].subjective += line + " "
                elif current_section == 'objective':
                    result['soap_note'].objective += line + " "
                elif current_section == 'assessment':
                    result['soap_note'].assessment += line + " "
                elif current_section == 'plan':
                    result['soap_note'].plan += line + " "
                elif current_section == 'clinical_reasoning':
                    result['reasoning'].clinical_reasoning += line + " "
                elif current_section == 'differential' and line.startswith('-'):
                    result['reasoning'].differential_diagnosis.append(line[1:].strip())
                elif current_section == 'red_flags' and line.startswith('-'):
                    result['reasoning'].red_flags_assessed.append(line[1:].strip())
                elif current_section == 'ruled_out' and line.startswith('-'):
                    result['reasoning'].ruled_out_conditions.append(line[1:].strip())
                elif current_section == 'supporting' and line.startswith('-'):
                    result['reasoning'].supporting_evidence.append(line[1:].strip())
                elif current_section == 'confidence':
                    try:
                        # Extract numeric confidence
                        import re
                        match = re.search(r'(\d+\.?\d*)', line)
                        if match:
                            conf = float(match.group(1))
                            if conf > 1.0:
                                conf = conf / 100  # Convert percentage
                            result['reasoning'].confidence_level = conf
                    except:
                        pass
        
        return result


def get_gemini_client(api_key: str = None) -> GeminiSOAPGenerator:
    """
    Factory function to get Gemini client
    
    Args:
        api_key: Optional API key. If not provided, reads from environment
    """
    if api_key is None:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
    
    return GeminiSOAPGenerator(api_key)
