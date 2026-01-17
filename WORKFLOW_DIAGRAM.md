# Meduroam End-to-End Workflow

## Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PATIENT INITIATES CONSULT                          │
│                    (Symptom description via chat/form)                      │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI PROCESSING (Gemini)                              │
│  • Analyzes patient transcript                                              │
│  • Generates SOAP note (Subjective, Objective, Assessment, Plan)            │
│  • Creates reasoning trace (differential diagnosis, red flags)              │
│  • Assigns preliminary urgency level                                        │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              ★ MEDICAL STUDENT REVIEW (MANDATORY GATE) ★                    │
│                                                                              │
│  Receives:                                                                   │
│  ✓ Full patient transcript                                                  │
│  ✓ AI-generated SOAP note                                                   │
│  ✓ AI reasoning trace                                                       │
│                                                                              │
│  Student Must Complete:                                                      │
│  1. Validate/Modify Assessment                                               │
│     └─ Select from: AGREE | MODIFY | DISAGREE                               │
│  2. Select Next-Step Provider Type(s)                                        │
│     └─ Options: GP, NP, RN, PSW, Specialist, Urgent Care, ED               │
│  3. Assign/Confirm Urgency Level                                             │
│     └─ ROUTINE | URGENT | EMERGENCY                                         │
│  4. Structured Reasoning (REQUIRED)                                          │
│     ├─ Clinical reasoning summary                                            │
│     ├─ Key differentials considered                                          │
│     ├─ Red flags assessed                                                    │
│     └─ Rationale for provider selection                                      │
│                                                                              │
│  Decision:                                                                   │
│  ├─ [APPROVE] → Send to Patient                                             │
│  └─ [ESCALATE] → Send to Resident/Physician                                 │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                    ┌──────────────┴───────────────┐
                    │                              │
                    ▼                              ▼
    ┌───────────────────────────┐   ┌──────────────────────────────────────┐
    │   PATIENT COMMUNICATION   │   │  RESIDENT/PHYSICIAN ESCALATION       │
    │                           │   │                                      │
    │  Student sends:           │   │  Resident Receives:                  │
    │  • Plain-language summary │   │  • All patient data                  │
    │  • What's likely going on │   │  • AI SOAP + reasoning               │
    │  • What was ruled out     │   │  • Student review + reasoning        │
    │  • Next steps             │   │                                      │
    │  • Why this makes sense   │   │  Resident Actions:                   │
    │                           │   │  [APPROVE] [MODIFY] [OVERRIDE]      │
    │  Patient Options:         │   │                                      │
    │  ├─ [ACCEPT]              │   │  Decision = FINAL                    │
    │  ├─ [ASK QUESTIONS]       │   │                                      │
    │  └─ [ESCALATE]            │   └──────────────┬───────────────────────┘
    └───────────┬───────────────┘                  │
                │                                  │
                │  ◄────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FINAL SOAP NOTE GENERATION                              │
│                                                                              │
│  Merged note clearly labels:                                                 │
│  • AI Contribution (original SOAP + reasoning)                               │
│  • Medical Student Contribution (validation + modifications)                 │
│  • Resident Decision (if escalated)                                          │
│  • Final Assessment & Plan                                                   │
│                                                                              │
│  → This becomes patient's permanent record in app                            │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CARE NAVIGATION & ROUTING                                 │
│                                                                              │
│  Decision Engine considers:                                                  │
│  • Validated urgency level                                                   │
│  • Approved provider type(s)                                                 │
│  • Patient location                                                          │
│  • Government API data:                                                      │
│    ├─ Clinic availability                                                    │
│    ├─ Wait times                                                             │
│    └─ Geographic proximity                                                   │
│                                                                              │
│  Prioritization:                                                             │
│  1. Lowest appropriate acuity                                                │
│  2. Shortest wait time                                                       │
│  3. Gatekeeper rules (Canadian referral system)                              │
│                                                                              │
│  Output:                                                                     │
│  • Ranked list of care options                                               │
│  • Booking links / contact info                                              │
│  • Estimated wait times                                                      │
│  • Referral note (if specialist)                                             │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
                        ┌──────────────────┐
                        │  PATIENT BOOKS   │
                        │  APPOINTMENT     │
                        └──────────────────┘
```

## State Transitions

| State | Next Possible States | Triggered By |
|-------|---------------------|--------------|
| `INITIAL` | `AI_PROCESSING` | Patient submits consult |
| `AI_PROCESSING` | `STUDENT_REVIEW` | AI completes SOAP generation |
| `STUDENT_REVIEW` | `PATIENT_COMMUNICATION`, `RESIDENT_ESCALATION` | Student approves or escalates |
| `PATIENT_COMMUNICATION` | `PATIENT_ACCEPTED`, `PATIENT_QUESTIONS`, `RESIDENT_ESCALATION` | Patient response |
| `PATIENT_QUESTIONS` | `STUDENT_REVIEW`, `PATIENT_COMMUNICATION` | Follow-up clarification |
| `RESIDENT_ESCALATION` | `FINAL_APPROVED` | Resident makes decision |
| `PATIENT_ACCEPTED` | `FINAL_APPROVED` | Patient accepts plan |
| `FINAL_APPROVED` | `CARE_ROUTING` | SOAP note finalized |
| `CARE_ROUTING` | `COMPLETE` | Patient receives options |

## Timing Considerations

- **AI Processing**: < 30 seconds
- **Student Review**: Target < 15 minutes (24/7 coverage required)
- **Patient Response**: Async (push notification)
- **Resident Escalation**: Target < 1 hour (emergency), < 4 hours (urgent)

## Safety Checkpoints

1. ✅ **AI Output Validation** - All AI output reviewed by licensed trainee
2. ✅ **Structured Reasoning** - No "rubber stamp" approvals
3. ✅ **Escalation Path** - Always available to physician
4. ✅ **Patient Consent** - Patient can escalate at any point
5. ✅ **Audit Trail** - Every decision logged with attribution
