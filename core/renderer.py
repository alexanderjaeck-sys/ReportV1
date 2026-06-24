from typing import List

from core.data_models import ManufacturingDocModel, ProcedureNode


class ProductionHTMLRenderer:
    @staticmethod
    def render(model: ManufacturingDocModel, image_html_snippet: str = "") -> str:
        procedure_html = ProductionHTMLRenderer._build_procedure_html(model.procedure_tree)
        prereqs_html = "".join([f"<li>📢 <strong>[ ]</strong> {item.text}</li>" for item in model.prerequisites])
        outputs_html = "".join([f"<li>📦 <strong>[ ]</strong> {item.text}</li>" for item in model.required_outputs])
        criteria_html = "".join([f"<li>✅ <strong>[ ]</strong> {item.text}</li>" for item in model.acceptance_criteria])

        trouble_html = ""
        for entry in model.troubleshooting:
            trouble_html += (
                f'<tr><td style="color:#b91c1c; font-weight:bold; border:1px solid #000; padding:6px;">'
                f"{entry.problem}</td><td style=\"border:1px solid #000; padding:6px;\">"
                f"{entry.possible_cause}</td><td style=\"border:1px solid #000; padding:6px; font-weight:bold; color:#1e3a8a;\">"
                f"{entry.corrective_action}</td></tr>"
            )

        history_html = ""
        for entry in model.revision_history:
            history_html += (
                f'<tr><td style="border:1px solid #000; padding:5px; text-align:center;">'
                f"{entry.revision}</td><td style=\"border:1px solid #000; padding:5px; text-align:center;\">"
                f"{entry.change_date}</td><td style=\"border:1px solid #000; padding:5px;\">"
                f"{entry.description}</td><td style=\"border:1px solid #000; padding:5px; text-align:center;\">"
                f"{entry.author}</td><td style=\"border:1px solid #000; padding:5px; text-align:center;\">"
                f"{entry.reviewer}</td><td style=\"border:1px solid #000; padding:5px; text-align:center;\">"
                f"{entry.approver}</td></tr>"
            )

        itar_header = ""
        if model.safety_compliance.itar_controlled:
            itar_header = (
                '<div style="border:2px dashed #b91c1c; background-color:#fef2f2; padding:10px; margin-bottom:20px; text-align:center;">'
                '<span style="color:#b91c1c; font-weight:bold; font-size:11pt;">⚠️ EXPORT CONTROLLED REGULATORY WARNING NOTICE ⚠️</span>'
                '<br/><span style="color:#7f1d1d; font-size:8.5pt;">RESTRICTED BY THE ARMS EXPORT CONTROL ACT (TITLE 22, U.S.C., SEC 2751). '
                'EXPORT WITHOUT AUTHORIZATION IS STRICTLY PROHIBITED.</span></div>'
            )

        return f"""
        <!DOCTYPE html><html><head><meta charset="utf-8">
        <style>
            @page {{ size: letter; margin: 0.5in; @bottom-right {{ content: "Page " counter(page) " of " counter(pages); font-family: sans-serif; font-size: 8pt; }} }}
            body {{ font-family: Helvetica, Arial, sans-serif; color: #000000; line-height: 1.4; font-size: 10pt; }}
            .section-header {{ background-color: #1e3a8a; color: #ffffff; font-size: 11pt; font-weight: bold; padding: 4px 8px; margin-top: 20px; margin-bottom: 8px; text-transform: uppercase; }}
            .meta-table, .grid-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
            .meta-table td {{ border: 1px solid #000000; padding: 6px; font-size: 9pt; vertical-align: top; }}
            .meta-label {{ font-weight: bold; background-color: #f1f5f9; width: 18%; }}
            .grid-table th {{ border: 1px solid #000; padding: 6px; background-color: #f1f5f9; text-align: left; }}
            .grid-table td {{ border: 1px solid #000; padding: 6px; }}
            ul, ol {{ margin-top: 4px; margin-bottom: 10px; padding-left: 20px; }}
            li {{ margin-bottom: 4px; }}
        </style></head><body>
            {itar_header}
            <table class="meta-table">
                <tr><td class="meta-label">WI Number:</td><td><strong>{model.control.wi_number}</strong></td><td class="meta-label">Document Ref:</td><td>{model.control.doc_number}</td></tr>
                <tr><td class="meta-label">Revision Level:</td><td><strong>{model.control.revision_level}</strong></td><td class="meta-label">Control Status:</td><td style="font-weight:bold;color:green;">{model.control.approval_status}</td></tr>
                <tr><td class="meta-label">Author:</td><td>{model.control.author}</td><td class="meta-label">Reviewer:</td><td>{model.control.reviewer}</td></tr>
                <tr><td class="meta-label">Approver:</td><td>{model.control.approver}</td><td class="meta-label">Verification Date:</td><td>{model.control.date_approved}</td></tr>
            </table>
            <div class="section-header">Current Revision Summary</div><div style="font-style:italic; margin-bottom:10px;">{model.current_rev_summary}</div>
            <div class="section-header">1.0 Scope & Purpose</div><div>{model.purpose}</div>
            <div class="section-header">2.0 Operational Responsibilities</div><ul>{"".join([f"<li>{r}</li>" for r in model.responsibilities])}</ul>
            <div class="section-header">3.0 Required Tooling, Software & Materials</div><ul>{"".join([f"<li>🔧 {i}</li>" for i in model.equipment_materials])}</ul>
            <div class="section-header">4.0 Operational Gate Prerequisites</div><ul style="list-style-type:none; padding-left:5px;">{prereqs_html}</ul>
            <div class="section-header">5.0 Detailed Process Execution Sequence</div>{procedure_html}
            <div class="section-header">6.0 Required Traceability Outputs</div><ul style="list-style-type:none; padding-left:5px;">{outputs_html}</ul>
            <div class="section-header">7.0 Quality Acceptance Criteria</div><ul style="list-style-type:none; padding-left:5px;">{criteria_html}</ul>
            <div class="section-header">8.0 Troubleshooting Protocol</div><table class="grid-table"><tr><th>Detected Anomaly</th><th>Potential Root Cause</th><th>Mandatory Corrective Action</th></tr>{trouble_html}</table>
            {image_html_snippet}
            <div class="section-header">9.0 Document Control Configuration History</div><table class="grid-table" style="font-size:8.5pt;"><tr><th>Rev</th><th>Date</th><th>Change Description</th><th>Author</th><th>Reviewer</th><th>Approver</th></tr>{history_html}</table>
        </body></html>
        """

    @staticmethod
    def _build_procedure_html(nodes: List[ProcedureNode]) -> str:
        if not nodes:
            return ""
        level_map = {1: "1", 2: "a", 3: "i", 4: "1"}
        tag = f'ol type="{level_map.get(nodes[0].level, "1")}"'
        if nodes[0].level == 4:
            tag = 'ol style="list-style-type: decimal;"'

        html = f"<{tag}>"
        for node in nodes:
            html += f"<li>{node.content}"
            if node.children:
                html += ProductionHTMLRenderer._build_procedure_html(node.children)
            html += "</li>"
        html += f"</{tag.split()[0]}>"
        return html
