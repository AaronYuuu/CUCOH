"""
Audit Logging and Compliance Framework
Comprehensive logging for legal protection and regulatory compliance
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import json


class AuditEventType(str, Enum):
    """Types of auditable events"""
    # User actions
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    
    # Patient interactions
    PATIENT_CONSULT_INITIATED = "PATIENT_CONSULT_INITIATED"
    PATIENT_RESPONSE_SUBMITTED = "PATIENT_RESPONSE_SUBMITTED"
    PATIENT_DATA_ACCESSED = "PATIENT_DATA_ACCESSED"
    PATIENT_ESCALATION_REQUEST = "PATIENT_ESCALATION_REQUEST"
    
    # AI actions
    AI_SOAP_GENERATED = "AI_SOAP_GENERATED"
    AI_REASONING_CREATED = "AI_REASONING_CREATED"
    
    # Medical student actions
    STUDENT_REVIEW_STARTED = "STUDENT_REVIEW_STARTED"
    STUDENT_REVIEW_COMPLETED = "STUDENT_REVIEW_COMPLETED"
    STUDENT_MODIFIED_ASSESSMENT = "STUDENT_MODIFIED_ASSESSMENT"
    STUDENT_ESCALATED = "STUDENT_ESCALATED"
    STUDENT_COMMUNICATION_SENT = "STUDENT_COMMUNICATION_SENT"
    
    # Physician actions
    PHYSICIAN_REVIEW_STARTED = "PHYSICIAN_REVIEW_STARTED"
    PHYSICIAN_REVIEW_COMPLETED = "PHYSICIAN_REVIEW_COMPLETED"
    PHYSICIAN_OVERRIDE = "PHYSICIAN_OVERRIDE"
    PHYSICIAN_SIGNATURE = "PHYSICIAN_SIGNATURE"
    
    # Workflow transitions
    STATE_TRANSITION = "STATE_TRANSITION"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
    
    # Care routing
    CARE_PLAN_GENERATED = "CARE_PLAN_GENERATED"
    REFERRAL_CREATED = "REFERRAL_CREATED"
    
    # Security events
    UNAUTHORIZED_ACCESS_ATTEMPT = "UNAUTHORIZED_ACCESS_ATTEMPT"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    
    # System events
    SYSTEM_ERROR = "SYSTEM_ERROR"
    DATA_EXPORT = "DATA_EXPORT"


class AuditSeverity(str, Enum):
    """Severity levels for audit events"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditEntry:
    """Single audit log entry"""
    
    def __init__(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        user_id: Optional[str],
        user_role: Optional[str],
        consult_id: Optional[str],
        patient_id: Optional[str],
        action: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        self.audit_id = f"audit_{datetime.now().timestamp()}"
        self.timestamp = datetime.now()
        self.event_type = event_type
        self.severity = severity
        self.user_id = user_id
        self.user_role = user_role
        self.consult_id = consult_id
        self.patient_id = patient_id
        self.action = action
        self.details = details or {}
        self.ip_address = ip_address
        self.session_id = session_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "audit_id": self.audit_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "severity": self.severity,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "consult_id": self.consult_id,
            "patient_id": self.patient_id,
            "action": self.action,
            "details": self.details,
            "ip_address": self.ip_address,
            "session_id": self.session_id
        }
    
    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps(self.to_dict(), indent=2)


class AuditLogger:
    """
    Centralized audit logging system
    All user actions and system events are logged for:
    - Legal protection
    - Regulatory compliance (PHIPA, provincial laws)
    - Quality assurance
    - Security monitoring
    """
    
    def __init__(self, storage_backend=None):
        """
        Args:
            storage_backend: Backend storage (database, file system, cloud)
                            Default: In-memory list (for MVP)
        """
        self.storage = storage_backend or InMemoryAuditStorage()
    
    def log(self, entry: AuditEntry) -> None:
        """Write audit entry to storage"""
        self.storage.write(entry)
        
        # For critical events, also trigger real-time alerts
        if entry.severity == AuditSeverity.CRITICAL:
            self._trigger_alert(entry)
    
    def log_patient_access(
        self,
        user_id: str,
        user_role: str,
        patient_id: str,
        consult_id: Optional[str],
        action: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Log patient data access (PHIPA requirement)"""
        entry = AuditEntry(
            event_type=AuditEventType.PATIENT_DATA_ACCESSED,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            user_role=user_role,
            consult_id=consult_id,
            patient_id=patient_id,
            action=action,
            details={"access_type": "patient_data_view"},
            ip_address=ip_address
        )
        self.log(entry)
    
    def log_clinical_decision(
        self,
        user_id: str,
        user_role: str,
        consult_id: str,
        patient_id: str,
        decision_type: str,
        decision_details: Dict[str, Any]
    ) -> None:
        """Log clinical decision (liability protection)"""
        entry = AuditEntry(
            event_type=AuditEventType.STUDENT_REVIEW_COMPLETED
                      if "STUDENT" in user_role
                      else AuditEventType.PHYSICIAN_REVIEW_COMPLETED,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            user_role=user_role,
            consult_id=consult_id,
            patient_id=patient_id,
            action=f"Clinical decision: {decision_type}",
            details=decision_details
        )
        self.log(entry)
    
    def log_physician_signature(
        self,
        physician_id: str,
        license_number: str,
        consult_id: str,
        patient_id: str,
        signature_type: str
    ) -> None:
        """Log physician signature (medical-legal requirement)"""
        entry = AuditEntry(
            event_type=AuditEventType.PHYSICIAN_SIGNATURE,
            severity=AuditSeverity.INFO,
            user_id=physician_id,
            user_role="PHYSICIAN",
            consult_id=consult_id,
            patient_id=patient_id,
            action=f"Physician signature: {signature_type}",
            details={
                "license_number": license_number,
                "signature_timestamp": datetime.now().isoformat()
            }
        )
        self.log(entry)
    
    def log_unauthorized_access(
        self,
        user_id: str,
        user_role: str,
        attempted_action: str,
        reason: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Log unauthorized access attempts (security)"""
        entry = AuditEntry(
            event_type=AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
            severity=AuditSeverity.WARNING,
            user_id=user_id,
            user_role=user_role,
            consult_id=None,
            patient_id=None,
            action=f"Unauthorized attempt: {attempted_action}",
            details={"reason": reason},
            ip_address=ip_address
        )
        self.log(entry)
    
    def log_ai_generation(
        self,
        consult_id: str,
        patient_id: str,
        ai_model: str,
        output_type: str,
        confidence: Optional[float] = None
    ) -> None:
        """Log AI-generated content (transparency requirement)"""
        entry = AuditEntry(
            event_type=AuditEventType.AI_SOAP_GENERATED,
            severity=AuditSeverity.INFO,
            user_id="system",
            user_role="AI",
            consult_id=consult_id,
            patient_id=patient_id,
            action=f"AI generated: {output_type}",
            details={
                "ai_model": ai_model,
                "output_type": output_type,
                "confidence": confidence
            }
        )
        self.log(entry)
    
    def get_consult_audit_trail(self, consult_id: str) -> List[AuditEntry]:
        """Retrieve complete audit trail for a consult"""
        return self.storage.get_by_consult(consult_id)
    
    def get_patient_access_log(self, patient_id: str) -> List[AuditEntry]:
        """Get all access to patient data (PHIPA requirement)"""
        return self.storage.get_by_patient(patient_id)
    
    def _trigger_alert(self, entry: AuditEntry) -> None:
        """Trigger real-time alert for critical events"""
        # In production: send to security team, page on-call, etc.
        print(f"🚨 CRITICAL ALERT: {entry.action}")


class InMemoryAuditStorage:
    """
    Simple in-memory storage for MVP
    Production should use:
    - PostgreSQL with audit-specific schema
    - Immutable append-only log
    - Regular backups to secure storage
    - Encryption at rest
    """
    
    def __init__(self):
        self.entries: List[AuditEntry] = []
    
    def write(self, entry: AuditEntry) -> None:
        """Append entry to log"""
        self.entries.append(entry)
    
    def get_by_consult(self, consult_id: str) -> List[AuditEntry]:
        """Get all entries for a consult"""
        return [e for e in self.entries if e.consult_id == consult_id]
    
    def get_by_patient(self, patient_id: str) -> List[AuditEntry]:
        """Get all entries for a patient"""
        return [e for e in self.entries if e.patient_id == patient_id]
    
    def get_all(self) -> List[AuditEntry]:
        """Get all entries (admin only)"""
        return self.entries


# ==================== COMPLIANCE FRAMEWORK ====================

class ComplianceChecker:
    """
    Ensure system meets regulatory requirements
    """
    
    @staticmethod
    def get_canadian_compliance_requirements() -> Dict[str, List[str]]:
        """
        Canadian healthcare compliance requirements
        """
        return {
            "PHIPA_Ontario": [
                "Patient consent for data collection",
                "Audit logs for all patient data access",
                "Data encryption in transit and at rest",
                "Right to access personal health information",
                "Breach notification procedures",
                "Data retention policies"
            ],
            "PIPEDA_Federal": [
                "Accountability for personal information",
                "Identifying purposes for data collection",
                "Obtaining consent",
                "Limiting collection, use, disclosure",
                "Accuracy of information",
                "Safeguards for protection",
                "Openness about policies",
                "Individual access to information",
                "Complaint procedures"
            ],
            "Medical_Regulation": [
                "Physician oversight required",
                "Clear CDS (non-diagnostic) labeling",
                "Informed consent from patients",
                "Documentation standards",
                "Physician-of-record concept",
                "Continuity of care provisions"
            ],
            "Liability_Protection": [
                "Clear attribution of AI vs human decisions",
                "Comprehensive audit trail",
                "Physician signature for final decisions",
                "Patient consent at each stage",
                "Escalation path always available",
                "Emergency override procedures"
            ]
        }
    
    @staticmethod
    def get_liability_containment_strategies() -> Dict[str, str]:
        """
        Strategies to limit liability exposure
        """
        return {
            "Clear_CDS_Framing": "System is labeled as Clinical Decision Support, not diagnostic tool. All outputs require human validation.",
            
            "Physician_Oversight": "All clinical decisions have physician oversight. Medical students operate under supervision.",
            
            "Comprehensive_Audit_Trail": "Every action is logged with timestamp, user, and reasoning. Provides evidence of due diligence.",
            
            "Patient_Consent": "Patients provide informed consent and can escalate at any time. Autonomy preserved.",
            
            "Multi-Layer_Review": "AI → Medical Student → (Optional) Physician creates multiple validation checkpoints.",
            
            "Clear_Attribution": "Final SOAP note clearly labels AI contribution vs human decisions. Responsibility is transparent.",
            
            "Emergency_Protocols": "Direct 911/ED pathway for emergencies. System does not delay critical care.",
            
            "Scope_Limitations": "System explicitly states what it can and cannot do. Sets appropriate expectations.",
            
            "Professional_Insurance": "Platform and providers maintain appropriate malpractice insurance.",
            
            "Terms_of_Service": "Clear user agreement outlining system capabilities, limitations, and user responsibilities."
        }
    
    @staticmethod
    def validate_consult_compliance(
        workflow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if a consult meets compliance requirements
        
        Returns validation results with pass/fail for each requirement
        """
        results = {
            "compliant": True,
            "checks": {},
            "issues": []
        }
        
        # Check 1: Patient consent obtained
        if not workflow_data.get("patient_consent"):
            results["compliant"] = False
            results["issues"].append("Missing patient consent")
        results["checks"]["patient_consent"] = bool(workflow_data.get("patient_consent"))
        
        # Check 2: AI output validated by human
        if not workflow_data.get("student_review_id"):
            results["compliant"] = False
            results["issues"].append("Missing human validation of AI output")
        results["checks"]["human_validation"] = bool(workflow_data.get("student_review_id"))
        
        # Check 3: Physician signature for high-urgency cases
        if workflow_data.get("urgency") in ["URGENT", "EMERGENCY"]:
            if not workflow_data.get("physician_signature"):
                results["compliant"] = False
                results["issues"].append("High-urgency case missing physician signature")
        results["checks"]["physician_signature"] = self._check_physician_signature(workflow_data)
        
        # Check 4: Clear attribution in final record
        if workflow_data.get("final_record"):
            has_attribution = all([
                "ai_contribution" in workflow_data["final_record"],
                "student_contribution" in workflow_data["final_record"]
            ])
            results["checks"]["attribution"] = has_attribution
            if not has_attribution:
                results["compliant"] = False
                results["issues"].append("Missing clear attribution in final record")
        
        # Check 5: Audit trail exists
        results["checks"]["audit_trail"] = bool(workflow_data.get("audit_entries"))
        if not workflow_data.get("audit_entries"):
            results["compliant"] = False
            results["issues"].append("Missing audit trail")
        
        return results
    
    @staticmethod
    def _check_physician_signature(workflow_data: Dict[str, Any]) -> bool:
        """Check if physician signature is present when required"""
        urgency = workflow_data.get("urgency")
        if urgency in ["URGENT", "EMERGENCY"]:
            return bool(workflow_data.get("physician_signature"))
        return True  # Not required for routine


# ==================== DATA RETENTION ====================

class DataRetentionPolicy:
    """
    Data retention requirements for Canadian healthcare
    """
    
    @staticmethod
    def get_retention_periods() -> Dict[str, str]:
        """
        Retention periods by data type
        Based on provincial regulations (Ontario as reference)
        """
        return {
            "clinical_records": "10 years from last patient contact (Ontario)",
            "audit_logs": "7 years minimum",
            "patient_communications": "10 years",
            "ai_outputs": "Same as clinical records (part of medical record)",
            "consent_forms": "10 years",
            "anonymized_data": "No limit (for research/quality improvement)"
        }
    
    @staticmethod
    def get_deletion_procedures() -> List[str]:
        """Procedures for secure data deletion"""
        return [
            "Patient right to request deletion (with exceptions for medical records)",
            "Secure overwrite methods for electronic data",
            "Maintain deletion audit log",
            "Retention of minimal data for legal/regulatory purposes",
            "Annual review of retention compliance"
        ]
