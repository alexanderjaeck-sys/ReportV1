import re
from datetime import date, datetime
from typing import Any, Dict, List

from core.data_models import ProcedureNode, SectionItem, TroubleshootingEntry


class ManufacturingWIParser:
    def __init__(self):
        self.regex_p1 = re.compile(r"^(\d+)\.\s*(.*)$")
        self.regex_p2 = re.compile(r"^([a-z])\.\s*(.*)$")
        self.regex_p3 = re.compile(r"^([ivxlcdm]+)\.\s*(.*)$")
        self.regex_p4 = re.compile(r"^\((\d+)\)\s*(.*)$")

    def parse(self, raw_text: str) -> Dict[str, Any]:
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        payload: Dict[str, Any] = {
            "responsibilities": [],
            "equipment_materials": [],
            "prerequisites": [],
            "procedure_tree": [],
            "required_outputs": [],
            "acceptance_criteria": [],
            "troubleshooting": [],
            "revision_history": [],
        }

        current_section = None
        trouble_step: Dict[str, str] = {}
        active_procedure_stack: List[ProcedureNode] = []

        for line in lines:
            if line.startswith("---") or line.startswith("==="):
                continue

            lower_line = line.lower()
            if "document control" in lower_line:
                current_section = "control"
                continue
            if "current revision summary" in lower_line:
                current_section = "rev_sum"
                payload["current_rev_summary"] = ""
                continue
            if "purpose" in lower_line and "metadata" not in lower_line:
                current_section = "purpose"
                payload["purpose"] = ""
                continue
            if "responsibilities" in lower_line:
                current_section = "responsibilities"
                continue
            if "required equipment" in lower_line or "materials" in lower_line:
                current_section = "equipment"
                continue
            if "prerequisites" in lower_line:
                current_section = "prerequisites"
                continue
            if "procedure" in lower_line and "vcmm" not in lower_line:
                current_section = "procedure"
                continue
            if "required outputs" in lower_line:
                current_section = "outputs"
                continue
            if "acceptance criteria" in lower_line:
                current_section = "acceptance"
                continue
            if "troubleshooting" in lower_line:
                current_section = "trouble"
                continue
            if "safety" in lower_line or "compliance" in lower_line:
                current_section = "safety"
                self._init_safety(payload)
                continue
            if "revision history" in lower_line:
                current_section = "history"
                continue

            if current_section == "control" and ":" in line:
                self._parse_control_kv(line, payload)
            elif current_section == "rev_sum":
                payload["current_rev_summary"] += line + " "
            elif current_section == "purpose":
                payload["purpose"] += line + " "
            elif current_section == "responsibilities":
                payload["responsibilities"].append(line)
            elif current_section == "equipment":
                payload["equipment_materials"].append(line)
            elif current_section == "prerequisites":
                payload["prerequisites"].append(SectionItem(text=line))
            elif current_section == "outputs":
                payload["required_outputs"].append(SectionItem(text=line))
            elif current_section == "acceptance":
                payload["acceptance_criteria"].append(SectionItem(text=line))
            elif current_section == "trouble":
                self._parse_troubleshooting(line, trouble_step, payload)
            elif current_section == "safety":
                self._parse_safety_compliance(line, payload)
            elif current_section == "history":
                self._parse_history_row(line, payload)
            elif current_section == "procedure":
                self._parse_procedure_line(line, active_procedure_stack, payload)

        payload["current_rev_summary"] = payload.get("current_rev_summary", "").strip()
        payload["purpose"] = payload.get("purpose", "").strip()
        return payload

    def _parse_control_kv(self, line: str, payload: Dict[str, Any]):
        if "control" not in payload:
            payload["control"] = {}
        k, v = map(str.strip, line.split(":", 1))
        key_map = {
            "wi number": "wi_number",
            "document number": "doc_number",
            "revision level": "revision_level",
            "author": "author",
            "reviewer": "reviewer",
            "approver": "approver",
            "date created": "date_created",
            "date revised": "date_revised",
            "date approved": "date_approved",
            "approval status": "approval_status",
        }
        mapped_key = key_map.get(k.lower())
        if mapped_key:
            if "date" in mapped_key:
                try:
                    payload["control"][mapped_key] = datetime.strptime(v, "%Y-%m-%d").date()
                except ValueError:
                    payload["control"][mapped_key] = date.today()
            else:
                payload["control"][mapped_key] = v

    def _parse_procedure_line(self, line: str, stack: List[ProcedureNode], payload: Dict[str, Any]):
        m1 = self.regex_p1.match(line)
        m2 = self.regex_p2.match(line)
        m3 = self.regex_p3.match(line)
        m4 = self.regex_p4.match(line)

        if m1:
            node = ProcedureNode(level=1, index_label=m1.group(1), content=m1.group(2))
        elif m2:
            node = ProcedureNode(level=2, index_label=m2.group(1), content=m2.group(2))
        elif m3:
            node = ProcedureNode(level=3, index_label=m3.group(1), content=m3.group(2))
        elif m4:
            node = ProcedureNode(level=4, index_label=m4.group(1), content=m4.group(2))
        else:
            return

        if node.level == 1:
            payload["procedure_tree"].append(node)
            stack.clear()
            stack.append(node)
        else:
            while stack and stack[-1].level >= node.level:
                stack.pop()
            if stack:
                stack[-1].children.append(node)
                stack.append(node)
            else:
                payload["procedure_tree"].append(node)
                stack.append(node)

    def _parse_troubleshooting(self, line: str, step: Dict[str, str], payload: Dict[str, Any]):
        if ":" in line:
            k, v = map(str.strip, line.split(":", 1))
            if k.lower() == "problem":
                if step:
                    payload["troubleshooting"].append(TroubleshootingEntry(**step))
                step.clear()
                step["problem"] = v
            elif k.lower() == "possible cause":
                step["possible_cause"] = v
            elif k.lower() == "corrective action":
                step["corrective_action"] = v
                payload["troubleshooting"].append(TroubleshootingEntry(**step))
                step.clear()

    def _init_safety(self, payload: Dict[str, Any]):
        if "safety_compliance" not in payload:
            payload["safety_compliance"] = {
                "itar_controlled": True,
                "ppe_requirements": [],
                "handling_requirements": [],
                "esd_sensitive": False,
                "environmental_notes": None,
            }

    def _parse_safety_compliance(self, line: str, payload: Dict[str, Any]):
        sc = payload["safety_compliance"]
        if ":" in line:
            k, v = map(str.strip, line.split(":", 1))
            kl = k.lower()
            if "itar" in kl:
                sc["itar_controlled"] = "true" in v.lower() or "yes" in v.lower()
            elif "esd" in kl:
                sc["esd_sensitive"] = "true" in v.lower() or "yes" in v.lower()
            elif "ppe" in kl:
                sc["ppe_requirements"] = [x.strip() for x in v.split(",") if x.strip()]
            elif "handling" in kl:
                sc["handling_requirements"] = [x.strip() for x in v.split(",") if x.strip()]
            elif "environmental" in kl:
                sc["environmental_notes"] = v

    def _parse_history_row(self, line: str, payload: Dict[str, Any]):
        if line.lower().startswith("rev,date"):
            return
        parts = line.split(",")
        if len(parts) >= 4:
            try:
                ch_date = datetime.strptime(parts[1].strip(), "%Y-%m-%d").date()
            except ValueError:
                ch_date = date.today()
            from core.data_models import RevHistoryEntry

            payload["revision_history"].append(
                RevHistoryEntry(
                    revision=parts[0].strip(),
                    change_date=ch_date,
                    description=parts[2].strip(),
                    author=parts[3].strip(),
                    reviewer=parts[4].strip() if len(parts) > 4 else "N/A",
                    approver=parts[5].strip() if len(parts) > 5 else "N/A",
                )
            )
