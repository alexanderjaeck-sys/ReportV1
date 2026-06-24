from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class DocControl(BaseModel):
    wi_number: str = Field(..., description="Unique Work Instruction Identifier")
    doc_number: str = Field(..., description="Internal Document Identification Number")
    revision_level: str = Field(..., description="Current configuration revision level")
    author: str
    reviewer: str
    approver: str
    date_created: date
    date_revised: date
    date_approved: date
    approval_status: str = Field(
        default="DRAFT",
        description="DRAFT, REVIEWED, or APPROVED",
    )


class RevHistoryEntry(BaseModel):
    revision: str
    change_date: date
    description: str
    author: str
    reviewer: str
    approver: str


class SectionItem(BaseModel):
    text: str
    is_checked: bool = False


class ProcedureNode(BaseModel):
    level: int = 1
    index_label: str
    content: str
    children: List["ProcedureNode"] = Field(default_factory=list)


class TroubleshootingEntry(BaseModel):
    problem: str
    possible_cause: str
    corrective_action: str


class SafetyCompliance(BaseModel):
    itar_controlled: bool = True
    ppe_requirements: List[str] = Field(default_factory=list)
    handling_requirements: List[str] = Field(default_factory=list)
    esd_sensitive: bool = False
    environmental_notes: Optional[str] = None


class ManufacturingDocModel(BaseModel):
    control: DocControl
    current_rev_summary: str
    purpose: str
    responsibilities: List[str]
    equipment_materials: List[str]
    prerequisites: List[SectionItem]
    procedure_tree: List[ProcedureNode]
    required_outputs: List[SectionItem]
    acceptance_criteria: List[SectionItem]
    troubleshooting: List[TroubleshootingEntry]
    safety_compliance: SafetyCompliance
    revision_history: List[RevHistoryEntry]
