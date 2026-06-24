from typing import List, Tuple

from core.data_models import ManufacturingDocModel


class QualitySystemValidator:
    @staticmethod
    def validate_compliance(model: ManufacturingDocModel) -> Tuple[bool, List[str]]:
        logs = []
        if model.control.approval_status.upper() != "APPROVED":
            logs.append("⚠️ WARNING: Configuration Status is not marked as production-ready 'APPROVED'.")
        if not model.control.wi_number or model.control.wi_number.upper() == "PENDING":
            logs.append("❌ ERROR: Missing unique Work Instruction Identification number.")
        if model.control.date_approved < model.control.date_created:
            logs.append("❌ ERROR: Anomaly detected: Approval Date cannot precede Creation Date.")
        if len(model.purpose) < 20:
            logs.append("❌ ERROR: Purpose section is too brief for aerospace compliance baselines.")
        if not model.procedure_tree:
            logs.append("❌ ERROR: Process block is completely empty.")
        if model.safety_compliance.itar_controlled:
            logs.append("🔒 ITAR TRACKING ENGAGED: Automated export-control safety block will be injected.")

        is_valid = not any("❌ ERROR:" in x for x in logs)
        return is_valid, logs
