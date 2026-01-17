# Meduroam Role & Permission Model

## User Roles

### 1. Patient
**Description**: Individual seeking clinical guidance

**Permissions**:
- Submit symptom descriptions
- View own consultation history
- Respond to medical student communications
- Request escalation to physician
- Accept/reject care recommendations
- Access own SOAP notes

**Cannot**:
- View other patients' data
- Access AI reasoning details
- Modify clinical assessments

**24/7 Access**: Yes (self-service symptom submission)

---

### 2. Medical Student
**Description**: Primary reviewer of AI outputs (mandatory human gate)

**Permissions**:
- View assigned consults and full AI reasoning
- Validate or modify AI assessments
- Select provider types and urgency levels
- Communicate with patients (plain language)
- Escalate to supervising physician
- Access structured decision rubrics

**Cannot**:
- Sign as physician of record
- Override supervising physician decisions
- Access consults not assigned to them
- Bypass structured reasoning requirements

**Supervision**: Required for all clinical decisions

**24/7 Coverage**: Rotating shifts with resident backup

**Training Requirements**:
- Clinical clerk (3rd/4th year medical student)
- Completed CDS platform training
- Regular case review with supervisors

---

### 3. Resident
**Description**: Supervising physician for escalated cases

**Permissions**:
- View all escalated consults
- Access AI reasoning and student reviews
- Approve, modify, or override student decisions
- Sign as physician of record
- Provide teaching feedback to students
- Finalize SOAP notes

**Cannot**:
- Bypass audit logging
- Delegate physician signature

**Responsibility**: Final clinical authority on escalated cases

**24/7 Availability**: On-call rotation

**Licensure**: Full medical license in province of practice

---

### 4. Attending Physician
**Description**: Senior physician oversight (quality assurance + complex cases)

**Permissions**:
- All resident permissions
- View any consult (for QA)
- System-wide quality metrics
- Approve/supervise residents
- Medical-legal final authority

**Cannot**:
- Modify completed/signed records (must add addendum)

**Role**: Quality oversight, complex case consultation, medical-legal authority

**Availability**: Designated attending on-call 24/7

---

### 5. Admin
**Description**: System administration and compliance

**Permissions**:
- View audit logs
- User management (create/disable accounts)
- System configuration
- Generate compliance reports
- No clinical decision authority

**Cannot**:
- Modify clinical records
- Make medical decisions
- Override physician authority

**Purpose**: System operation, compliance monitoring, user support

---

## Permission Matrix

| Action | Patient | Med Student | Resident | Attending | Admin |
|--------|---------|-------------|----------|-----------|-------|
| Submit symptoms | ✓ | - | - | - | - |
| View AI reasoning | - | ✓ | ✓ | ✓ | - |
| Validate assessment | - | ✓ | ✓ | ✓ | - |
| Modify SOAP | - | ✓ | ✓ | ✓ | - |
| Communicate with patient | - | ✓ | ✓ | ✓ | - |
| Escalate to physician | ✓ | ✓ | - | - | - |
| Sign as physician | - | - | ✓ | ✓ | - |
| Override decisions | - | - | ✓ | ✓ | - |
| View all consults | - | - | - | ✓ | ✓* |
| Access audit logs | - | - | - | ✓ | ✓ |
| Manage users | - | - | - | - | ✓ |

*Admin view is for operational purposes only, not clinical

---

## Workflow State Transitions

### Who Can Move Workflow to Each State:

```
INITIAL → AI_PROCESSING
  ↳ Patient (by submitting symptoms)

AI_PROCESSING → STUDENT_REVIEW
  ↳ System (automatic when AI completes)

STUDENT_REVIEW → PATIENT_COMMUNICATION
  ↳ Medical Student (approval without escalation)

STUDENT_REVIEW → RESIDENT_ESCALATION
  ↳ Medical Student (escalation decision)

PATIENT_COMMUNICATION → PATIENT_ACCEPTED
  ↳ Patient (acceptance)

PATIENT_COMMUNICATION → PATIENT_QUESTIONS
  ↳ Patient (follow-up questions)

PATIENT_COMMUNICATION → RESIDENT_ESCALATION
  ↳ Patient (escalation request)

PATIENT_QUESTIONS → PATIENT_COMMUNICATION
  ↳ Medical Student (after answering questions)

RESIDENT_ESCALATION → FINAL_APPROVED
  ↳ Resident/Attending (final decision)

PATIENT_ACCEPTED → FINAL_APPROVED
  ↳ System (automatic)

FINAL_APPROVED → CARE_ROUTING
  ↳ System (automatic)

CARE_ROUTING → COMPLETE
  ↳ System (automatic)
```

---

## Safety & Escalation Rules

### Mandatory Escalation Triggers:
1. **Student Uncertainty**: Confidence <70% or unsure of diagnosis
2. **Diagnosis Severity**: Cancer, serious cardiac, neurological conditions
3. **Urgency Change**: Student disagrees with AI urgency level
4. **ED Consideration**: Any case being routed to ED
5. **Patient Request**: Patient asks for physician review
6. **Complex Comorbidities**: Multiple serious conditions
7. **Controlled Substances**: Requires prescription beyond student scope
8. **Medical-Legal Concerns**: Potential liability issues
9. **Unusual Presentation**: Rare diagnosis or atypical symptoms
10. **First 100 Student Cases**: Training period oversight

### Emergency Override:
- Any user can trigger immediate 911 pathway
- Bypasses normal workflow for life-threatening situations
- Attending physician automatically notified
- Audit log captures emergency override event

---

## Data Access Controls

### Patient Health Information (PHI):
- **Strict need-to-know basis**
- Audit log for ALL access (PHIPA requirement)
- Time-limited session tokens
- Encryption in transit and at rest
- Geographic restrictions (Canadian data only)

### Student Access:
- Only assigned consults
- Cannot view cases not assigned
- Access logged and time-limited
- Supervisor can view student's cases

### Physician Access:
- Residents: Escalated cases + teaching oversight
- Attendings: System-wide for QA purposes
- All access is logged

### Admin Access:
- No clinical data access without explicit authorization
- Audit logs accessible for compliance
- System configuration only
- Cannot impersonate clinical users

---

## 24/7 Coverage Model

### Medical Students:
- **8-hour rotating shifts**: 7am-3pm, 3pm-11pm, 11pm-7am
- **Queue management**: First-come-first-served with urgency prioritization
- **Target response time**: <15 minutes for review initiation
- **Backup**: Resident can pick up queue if student unavailable

### Residents:
- **12-hour on-call shifts**: Day (7am-7pm), Night (7pm-7am)
- **Escalation response time**:
  - EMERGENCY: <1 hour
  - URGENT: <4 hours
  - ROUTINE: <24 hours
- **Backup**: Attending physician always available

### Attending Physicians:
- **24-hour on-call rotation** across attending group
- **Cross-coverage agreements** for unavailability
- **Emergency contact**: Direct phone line for critical cases
- **Response time**: <30 minutes for critical escalations

---

## Training & Competency Requirements

### Medical Students:
- Year 3 or 4 medical student
- Completed clinical clerkships
- Platform training (4 hours) including:
  - CDS system overview
  - Structured reasoning requirements
  - Escalation criteria
  - Patient communication
  - Safety protocols
- Observed cases (first 20 cases supervised)
- Quarterly competency review

### Residents/Attendings:
- Active medical license in province
- Malpractice insurance current
- Platform orientation (2 hours)
- Agreement to supervision responsibilities
- Annual recredentialing

---

## Physician-of-Record Rules

### Signature Required:
✓ All URGENT and EMERGENCY cases  
✓ All escalated cases  
✓ Cases with medicolegal implications  
✓ First 100 student cases (training)

### Signature Not Required (Async Oversight):
✗ ROUTINE cases approved by trained student  
✗ Low-risk assessments  
→ Physician reviews in batch (daily)

### Legal Responsibility:
- Signing physician = physician of record
- Assumes medical-legal responsibility
- Must have reviewed case personally
- Cannot delegate signature authority
- Signature is legally binding

---

## Accountability & Chain of Command

```
Patient
  ↓
Medical Student (Primary reviewer)
  ↓
Resident (Escalations + supervision)
  ↓
Attending Physician (Complex cases + QA)
  ↓
Medical Director (System oversight)
```

**Each level**:
- Has specific scope of authority
- Cannot be bypassed
- Is accountable for decisions made
- Has escalation path available
- Actions are fully audited

---

## Conclusion

This role-based model ensures:
- ✅ Multi-layer safety validation
- ✅ Appropriate supervision of trainees
- ✅ Clear accountability structure
- ✅ Patient protection and escalation rights
- ✅ Regulatory compliance (CPSO, provincial colleges)
- ✅ 24/7 coverage with appropriate backup
- ✅ Complete audit trail for liability protection
