# Meduroam - Clinical Decision Support Platform MVP

## Overview
Meduroam is a Canadian clinical decision support (CDS) platform with human-in-the-loop validation and care navigation. This MVP implements a multi-tier review system with medical student primary review and physician oversight.

## Key Features
- ✅ AI-generated SOAP notes with reasoning traces
- ✅ Mandatory medical student review and validation
- ✅ Patient communication and consent workflow
- ✅ Physician escalation path
- ✅ Care navigation with government data integration
- ✅ Audit logging and compliance tracking
- ✅ Role-based access control

## Architecture

### Actors
1. **Patient** - Provides symptoms, receives recommendations
2. **AI (Gemini)** - Generates initial SOAP note and assessment
3. **Medical Student** - Primary reviewer (mandatory gate)
4. **Supervising Resident/Physician** - Final authority on escalated cases
5. **Government APIs** - Wait times, clinic availability

### Workflow States
```
INITIAL → AI_PROCESSING → STUDENT_REVIEW → PATIENT_REVIEW → 
[RESIDENT_ESCALATION] → FINAL_APPROVED → CARE_ROUTING
```

## Directory Structure
```
meduroam/
├── config/              # Configuration files
├── models/              # Data models and schemas
├── workflows/           # Workflow state management
├── roles/               # Role-based permissions
├── decision_engine/     # Care routing logic
├── compliance/          # Audit logs and legal framework
├── examples/            # Case walkthroughs
└── api/                 # API integration layer
```

## Legal Framework
**CRITICAL**: This system is a Clinical Decision Support tool, NOT a diagnostic system.
- Does not replace physician judgment
- All decisions require human validation
- Maintains clear attribution of AI vs human contributions
- Comprehensive audit trail for liability protection

## Getting Started
```bash
pip install -r requirements.txt
python examples/example_case.py
```

## Compliance Notes
- PHIPA (Ontario) / Provincial privacy laws compliant
- Maintains physician-of-record concept
- 24/7 availability considerations built-in
- Clear CDS (non-diagnostic) framing throughout
