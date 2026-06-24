import base64
from io import BytesIO

import streamlit as st
from xhtml2pdf import pisa

from core.data_models import ManufacturingDocModel
from core.parser import ManufacturingWIParser
from core.renderer import ProductionHTMLRenderer
from core.validators import QualitySystemValidator

st.set_page_config(page_title="Production WI Compiler", layout="wide")

PRODUCTION_DEFAULT_RAW_DUMP = """==================================================
DOCUMENT CONTROL METADATA
==================================================
WI Number: WI-010-SANDIA
Document Number: AIS-QA-WI-2026-010
Revision Level: 2.0
Author: Alyssa Barstad
Reviewer: Quality Engineering Dept
Approver: QA Director / Operations Lead
Date Created: 2025-06-05
Date Revised: 2026-06-23
Date Approved: 2026-06-23
Approval Status: APPROVED

CURRENT REVISION SUMMARY
Migrated specification blueprint schema mappings into production-grade multi-layer DFA model architecture. Expanded checklist controls to satisfy clean audit parameters.

PURPOSE
To provide clear, reproducible step-by-step instructions for running the customer-specific part, 3A1488-01 Headers. This ensures configuration consistency, compliance with Sandia National Laboratories protocols, and efficient workflow execution on calibrated metrology platforms.

RESPONSIBILITIES
All Operators: Responsible for ensuring all components are handled cleanly according to precision handling rules.
Metrology Technicians: Mandatory verification of equipment calibration logs prior to initiating part measurement execution loops.

REQUIRED EQUIPMENT / SOFTWARE / MATERIALS
OGP SmartScope VCMM (PQI-0422 Calibration Tracking Check Active)
SmartProfile Geometrical Processing Data Software Platform Suite
High-Purity 91% Isopropyl Alcohol Fluid Base Agent & Low-Lint Cleanroom Wipes
Calibrated Nitrogen-Purged Rotary Indexing Unit Fixture Block Assemblies
Nitrile Powder-Free Specimen Grounding Gloves

PREREQUISITES
Calibrated machine startup checklist loop confirmation executed.
Operator certified to Advanced Metrology Level II standard curriculum parameters.
ITAR Access clearance level authorization currently validated.

PROCEDURE
1. Clean work surfaces and machine tool staging deck with approved fluid agents.
2. Gather all process-essential component bags and verification routers.
3. Check internal tracking server logs for changes to the nominal CAD or alignment protocols.
4. Execute primary metrology software platform runtime initialization.
    a. Open master verification folder through target directory: G:\\Master_Programs\\3A1488_RevK
    b. Load specific inspection instruction sequence code file block.
5. Setup workspace mechanical layout infrastructure.
    a. Mount calibrated fixture base securely onto rotary table tracking slot.
    b. Align alignment block locator reference markers.
        i. Torque fastening bolts down uniformly to 12 in-lbs limit threshold.
        ii. Clean alignment surfaces with chemical agent fluid base.
            (1) Inspect interface point with micro-loupe for particulate matter contamination.
            (2) Verify alignment runout metrics using electronic drop indicator indicator.
6. Mount the physical specimen header block array.
    a. Confirm serialization coordinates correlate with layout records.
    b. Clamp internal pin interfaces down smoothly.

REQUIRED OUTPUTS
Smart Profile Functional Project Run Database File Logs
High-Density Point Cloud Point-Data Text Matrix Logs
QC-Calc Automated Production Interface Export Files
Geometric Dimensioning and Tolerancing (GD&T) Metrology Conformity Inspection Report

ACCEPTANCE CRITERIA
Point cloud verification matrices match file output parameters.
Statistical data packages transmitted to manufacturing server paths.
All metrics pass mechanical specification tolerances.

TROUBLESHOOTING
Problem: Point clouds not saving to target file servers
Possible Cause: Network drive security block or program export file path modification
Corrective Action: Verify write permissions for the target folder path and contact the designated automation program owner.

Problem: Calibration scan tracking error registry alert triggers
Possible Cause: Surface contamination or particle layer buildup on probe tip sphere
Corrective Action: Run probe cleaning cycle protocol and perform verification standard baseline test sequence.

SAFETY / COMPLIANCE
ITAR Regulatory Control: True
ESD Sensitive Component Protection: True
PPE Requirements: Safety Glasses, Grounding Nitrile Gloves, Anti-Static ESD Smock
Handling Requirements: Hold parts only by external non-functional tooling flange surfaces. Do not use metallic tweezers.
Environmental Notes: Ambient room temperature must be maintained at 20 deg C +/- 0.5 degrees limit constraint variations.

REVISION HISTORY
Rev,Date,Changes,Author,Reviewer,Approver
1.0,2025-06-05,Initial document generation.,Alyssa Barstad,QA Dept,Ops Mgr
2.0,2026-06-23,Dynamic tracking implemented.,Alexander Jaeck,QA Lead,Operations Dir
"""

st.title("🛡️ Aerospace Document Compiler (AS9100 / ITAR Compliance Mode)")

col1, col2 = st.columns([1, 1])
with col1:
    raw_input = st.text_area("Input Specification Payload Stream:", value=PRODUCTION_DEFAULT_RAW_DUMP, height=450)
    uploaded_images = st.file_uploader("Upload sequential figures (PNG/JPG):", accept_multiple_files=True, type=["png", "jpg", "jpeg"])

with col2:
    st.subheader("🔍 Compliance Scanner Output")
    if st.button("🚀 Process Stream & Run Compliance Scan", use_container_width=True):
        if raw_input.strip():
            try:
                parser = ManufacturingWIParser()
                document_model = ManufacturingDocModel(**parser.parse(raw_input))
                is_valid, validation_logs = QualitySystemValidator.validate_compliance(document_model)

                for log in validation_logs:
                    if "❌ ERROR:" in log:
                        st.error(log)
                    elif "⚠️ WARNING:" in log:
                        st.warning(log)
                    else:
                        st.info(log)

                if is_valid:
                    image_html_snippet = ""
                    if uploaded_images:
                        image_html_snippet += '<div class="section-header">10.0 Controlled Visual Reference Figures</div><table style="width:100%; border-collapse:collapse; margin-top:10px;">'
                        for i in range(0, len(uploaded_images), 2):
                            image_html_snippet += "<tr>"
                            img1 = uploaded_images[i]
                            b64_1 = base64.b64encode(img1.read()).decode()
                            image_html_snippet += f'<td style="width:50%; padding:10px; text-align:center; border:1px solid #cbd5e1;"><img src="data:{img1.type};base64,{b64_1}" style="width:220px; height:auto; border:1px solid #000;"/><br/><span style="font-size:8.5pt; font-weight:bold;">Figure {i+1}: {img1.name}</span></td>'

                            if i + 1 < len(uploaded_images):
                                img2 = uploaded_images[i + 1]
                                img2.seek(0)
                                b64_2 = base64.b64encode(img2.read()).decode()
                                image_html_snippet += f'<td style="width:50%; padding:10px; text-align:center; border:1px solid #cbd5e1;"><img src="data:{img2.type};base64,{b64_2}" style="width:220px; height:auto; border:1px solid #000;"/><br/><span style="font-size:8.5pt; font-weight:bold;">Figure {i+2}: {img2.name}</span></td>'
                            else:
                                image_html_snippet += '<td style="width:50%; border:1px solid #cbd5e1;"></td>'
                            image_html_snippet += "</tr>"
                        image_html_snippet += "</table>"

                    final_html = ProductionHTMLRenderer.render(document_model, image_html_snippet)
                    pdf_buffer = BytesIO()
                    pisa_status = pisa.CreatePDF(final_html, dest=pdf_buffer)

                    if not pisa_status.err:
                        st.balloons()
                        st.download_button(
                            label="📥 Export High-Contrast Production PDF",
                            data=pdf_buffer.getvalue(),
                            file_name=f"{document_model.control.wi_number}_REV{document_model.control.revision_level}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
            except Exception as ex:
                st.error(f"System Exception: {str(ex)}")
