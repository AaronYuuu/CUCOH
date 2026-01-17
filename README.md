# MEDUROAM - Clinical Reasoning Assistant Platform

**Version:** 1.0.0  
**Status:** Development  
**Compliance Target:** HIPAA-ready, Clinical Audit Standards

## Overview

MEDUROAM is a physician-in-the-loop AI consultation platform designed to simulate high-quality GP/internal medicine consultations while maintaining strict safety boundaries. The system operates as a **clinical reasoning assistant**, not a licensed physician.

### Core Capabilities

- Adaptive clinical interview (chief complaint → HPI → ROS → history)
- Red-flag detection with automatic escalation
- Structured SOAP note generation (JSON format)
- Explicit concern tracking and verification
- Confidence-scored differential diagnoses

### Safety Architecture

- Hard stops for emergency conditions
- No definitive diagnoses or treatment plans
- No medication dosing (except OTC general guidance)
- Clear disclaimers without breaking immersion
- Designed for human clinician review

## Project Structure

```
meduroam/
├── core/
│   ├── system_prompt.md          # Gemini system prompt
│   ├── state_machine.py          # Consultation flow logic
│   └── red_flags.json            # Emergency taxonomy
├── schemas/
│   ├── soap_schema.json          # SOAP note structure
│   └── session_state.json        # Conversation state
├── examples/
│   ├── consultation_transcript.md  # Full consultation example
│   └── sample_soap_output.json    # Generated SOAP note
├── docs/
│   ├── implementation_guide.md    # Gemini API integration
│   ├── clinical_protocol.md      # Medical logic documentation
│   └── audit_checklist.md        # Compliance validation
└── tests/
    └── red_flag_scenarios.md      # Safety test cases
```

## Regulatory Considerations

- **Not a medical device** under current design (decision support, not diagnosis)
- Assumes human clinician review before action
- All outputs timestamped and auditable
- Red-flag triggers logged for quality assurance

## Next Steps

1. Deploy system prompt to Gemini API Studio
2. Implement state machine in backend
3. Connect to secure HIPAA-compliant storage
4. Integrate with human review workflow
5. Clinical validation testing

---
**Disclaimer:** This system is a clinical reasoning tool. All outputs require validation by licensed healthcare professionals before clinical action.
