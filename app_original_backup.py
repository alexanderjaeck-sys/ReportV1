import streamlit as st
import re
import base64
from xhtml2pdf import pisa
from io import BytesIO

# --- EXPANDED EXECUTIVE PRINT-SPECIFIC CSS/HTML TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: letter;
        margin: 0.6in 0.6in 0.8in 0.6in;
    }}
    body {{
        font-family: Helvetica, Arial, sans-serif;
        color: #334155;
        line-height: 1.6;
        font-size: 10pt;
    }}
    
    /* Compliance Alert Header */
    .warning-box {{
        border-left: 4px solid #dc2626;
        background-color: #fef2f2;
        padding: 14px 18px;
        margin-bottom: 25px;
    }}
    .warning-title {{
        color: #b91c1c;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 9pt;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }}
    .warning-text {{
        color: #7f1d1d;
        font-size: 8.5pt;
    }}
    
    /* Executive Metadata Grid */
    .meta-table {{
        width: 100%;
        margin-bottom: 35px;
        border-collapse: collapse;
    }}
    .meta-table td {{
        padding: 12px 14px;
        font-size: 9.5pt;
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
    }}
    .meta-label {{
        color: #64748b;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 8pt;
        letter-spacing: 0.3px;
        width: 20%;
    }}
    .meta-value {{
        color: #1e293b;
    }}
    
    /* Section Headers */
    .section-title {{
        color: #1e3a8a;
        font-size: 11pt;
        font-weight: bold;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 4px;
        margin-top: 25px;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    /* Content Elements & Nested Lists */
    .content-block {{
        margin-bottom: 12px;
        color: #475569;
        padding-left: 2px;
    }}
    ol, ul {{
        margin-top: 5px;
        margin-bottom: 15px;
        padding-left: 22px;
    }}
    ol ol {{
        margin-top: 3px;
        margin-bottom: 5px;
        padding-left: 20px;
        list-style-type: lower-alpha;
    }}
    li {{
        margin-bottom: 6px;
        color: #334155;
    }}
    
    /* Interactive Matrix & History Tables */
    table.matrix-table {{
        width: 100%;
        margin-top: 15px;
        margin-bottom: 20px;
        border-collapse: collapse;
    }}
    table.matrix-table th {{
        background-color: #1e3a8a;
        color: #ffffff;
        font-weight: bold;
        text-align: left;
        padding: 10px 14px;
        font-size: 9pt;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: 1px solid #1e3a8a;
    }}
    table.matrix-table td {{
        border: 1px solid #e2e8f0;
        padding: 12px 14px;
        font-size: 9pt;
        vertical-align: top;
        color: #334155;
    }}
    table.matrix-table tr:nth-child(even) td {{
        background-color: #f8fafc;
    }}
    .table-key {{
        font-weight: bold;
        color: #0f172a;
    }}
    
    /* Image Grid Engineering */
    .image-grid {{
        width: 100%;
        margin-top: 20px;
        margin-bottom: 20px;
    }}
    .image-grid td {{
        width: 50%;
        padding: 10px;
        text-align: center;
        vertical-align: top;
    }}
    .embedded-img {{
        width: 260px;
        height: auto;
        border: 1px solid #cbd5e1;
        margin-bottom: 6px;
    }}
    .image-caption {{
        font-size: 8.5pt;
        color: #64748b;
        font-weight: bold;
    }}
    
    .footer-container {{
        text-align: right;
        font-size: 8pt;
        color: #94a3b8;
        margin-top: 30px;
    }}
</style>
</head>
<body>

    <div class="warning-box">
        <div class="warning-title">⚠️ DRAFT: NOT PUBLISHED UNTIL RED NOTES COMPLETED</div>
        <div class="warning-text">🔒 <strong>ITAR REGULATED:</strong> Do not store, share, or screenshot this instruction outside of authorized platforms.</div>
    </div>

    <table class="meta-table">
        <tr>
            <td class="meta-label">Doc Title</td>
            <td class="meta-value" style="width: 45%;"><strong>{doc_title}</strong></td>
            <td class="meta-label">Template</td>
            <td class="meta-value">{template_num}</td>
        </tr>
        <tr>
            <td class="meta-label">Purpose</td>
            <td class="meta-value" colspan="3">{purpose}</td>
        </tr>
    </table>

    {dynamic_content}

    {image_content}

    <div class="footer-container">
        Document Page <pdf:pagenumber />
    </div>

</body>
</html>
"""

# --- STRING/ARRAY AUTOMATION PARSER ---
def parse_raw_dump(raw_text):
    clean_lines = []
    for line in raw_text.split('\n'):
        line_fixed = line.strip()
        if line_fixed:
            clean_lines.append(line_fixed)
            
    doc_title = "WI_010_Sandia-3A1488Headers_Rev1.0"
    template_num = "TMP_002 Rev. 1.1" 
    purpose = "To provide step-by-step instructions to run customer specific part, 3A1488-01 Headers. This ensures consistency, compliance with Sandia-specific protocols, and efficient workflow execution."
    
    html_output = []
    current_section = None  # None, "ordered", "unordered", "sub_ordered"
    in_table = False
    
    in_rev_history = False
    rev_rows = []
    
    known_headers = [
        "Responsibilities", "Required Tools / Software / Materials", 
        "Procedure: VCMM Inspection", "Procedure: Visual Inspection", 
        "Procedure: Data Reporting", "Safety / Precautions", 
        "Troubleshooting / Notes", "Compliance"
    ]
    
    for line in clean_lines:
        if any(x in line.lower() for x in ["purpose", "wi template number", "draft:", "the following table:"]):
            continue

        # Detect Revision History section
        if "revision history" in line.lower() or "rev,date,changes" in line.lower():
            in_rev_history = True
            if in_table:
                html_output.append("</table>")
                in_table = False
            if current_section == "sub_ordered":
                html_output.append("</ol></li >")
                current_section = "ordered"
            if current_section == "ordered":
                html_output.append("</ol>")
            elif current_section == "unordered":
                html_output.append("</ul>")
            current_section = "rev_mode"
            continue
            
        if in_rev_history:
            parts = line.split(',')
            if len(parts) >= 4 and parts[0].strip() and parts[1].strip():
                rev = parts[0].strip()
                date = parts[1].strip()
                changes = parts[2].strip()
                author = parts[3].strip()
                rev_rows.append(f"<tr><td>{rev}</td><td>{date}</td><td>{changes}</td><td>{author}</td></tr>")
            continue

        # Section Headings
        if line.endswith(':') or any(line.startswith(prefix) for prefix in known_headers):
            if in_table:
                html_output.append("</table>")
                in_table = False
            if current_section == "sub_ordered":
                html_output.append("</ol></li>")
                current_section = "ordered"
            if current_section == "ordered":
                html_output.append("</ol>")
            elif current_section == "unordered":
                html_output.append("</ul>")
                
            clean_header = line.replace(":", "").strip()
            html_output.append(f'<div class="section-title">{clean_header}</div>')
            current_section = "section_started"
            continue
            
        # Field mappings
        if "tab:" in line.lower() or "list:" in line.lower() or line.startswith("Report-V") or line.startswith("Notes:") or line.startswith("Cert_Uncert") or line.startswith("Equip List") or line.startswith("Comments Pg") or line.startswith("Customer:") or line.startswith("Part data:") or line.startswith("Additional Data:") or line.startswith("Primary Inspector:") or line.startswith("Report Pictures:"):
            delimiter = ":" if ":" in line else " "
            parts = line.split(delimiter, 1)
            key = parts[0].strip()
            val = parts[1].strip() if len(parts) > 1 else ""
            
            if not val or val.lower() == "no necessary input" or val.lower() == "leave the rest untouched.":
                continue
                
            if current_section == "sub_ordered":
                html_output.append("</ol></li>")
                current_section = "ordered"
            if current_section == "ordered":
                html_output.append("</ol>")
                current_section = None
            elif current_section == "unordered":
                html_output.append("</ul>")
                current_section = None
                
            if not in_table:
                html_output.append('<table class="matrix-table"><tr><th style="width:35%;">Element / Tab Mapping</th><th>Instruction / Action Block</th></tr>')
                in_table = True
            
            html_output.append(f'<tr><td class="table-key">{key}</td><td>{val}</td></tr>')
            continue

        if in_table:
            html_output.append("</table>")
            in_table = False

        # --- RE-ENGINEERED SMART MULTI-LEVEL LIST PARSER ---
        is_primary_step = line[0].isdigit() or (len(line) > 1 and line[1] == '.')
        is_sub_step = re.match(r'^[a-z]\s*[\.\)]', line) or (current_section in ["ordered", "sub_ordered"] and not is_primary_step and (line.startswith("Work Ticket") or line.startswith("Part Number") or line.startswith("Serial Number") or line.startswith("In G:")) )

        if is_sub_step:
            # If we are on a secondary sub-list item but haven't initialized the tree block yet
            if current_section == "ordered":
                html_output.append('<ol>')
                current_section = "sub_ordered"
            elif current_section == "section_started":
                # Fallback safeguard
                html_output.append('<ol><ol>')
                current_section = "sub_ordered"
                
            clean_li = re.sub(r'^[a-z]\s*[\.\)]\s*', '', line)
            html_output.append(f'<li>{clean_li}</li>')
            
        elif is_primary_step:
            # Close sub-list block smoothly if stepping back up to top level
            if current_section == "sub_ordered":
                html_output.append('</ol></li>')
                current_section = "ordered"
            if current_section != "ordered":
                html_output.append('<ol>')
                current_section = "ordered"
                
            clean_li = re.sub(r'^\d+\s*[a-zA-Z]?\.?\s*', '', line)
            html_output.append(f'<li>{clean_li}') # Keep <li> open to allow sub-list elements to nest inside clean trees
            
        else:
            # Standard unstructured lines
            if current_section == "sub_ordered":
                html_output.append('</ol></li>')
                current_section = "ordered"
            if current_section == "ordered":
                html_output.append('</ol>')
                current_section = None
            if current_section != "unordered" and current_section == "section_started":
                html_output.append('<ul>')
                current_section = "unordered"
                
            if current_section == "unordered":
                html_output.append(f'<li>{line}</li>')
            else:
                html_output.append(f'<div class="content-block">{line}</div>')
                
    if in_table: html_output.append("</table>")
    if current_section == "sub_ordered": html_output.append("</ol></li></ol>")
    elif current_section == "ordered": html_output.append("</ol>")
    elif current_section == "unordered": html_output.append("</ul>")
    
    if rev_rows:
        html_output.append('<div class="section-title">Revision Control History</div>')
        html_output.append('<table class="matrix-table">')
        html_output.append('<tr><th>Rev</th><th>Date</th><th>Changes Logged</th><th>Author</th></tr>')
        html_output.append("".join(rev_rows))
        html_output.append('</table>')
    
    return {
        "doc_title": doc_title,
        "template_num": template_num,
        "purpose": purpose,
        "dynamic_content": "".join(html_output)
    }

# --- STREAMLIT CONTROL PANEL ---
st.set_page_config(page_title="Secure Document Compiler", layout="centered")
st.title("🛡️ ITAR Secure Document Compiler")

DEFAULT_TEMPLATE = """Procedure: VCMM Inspection
1. Clean work surfaces and machine with approved alcohol and Kimtech wipes.
2. Gather all necessary equipment: job specific document folder, gloves, probe, fixture, and parts.
3. Check ODOO and document folder to see if the managers left any notes on version changes for the program or Smart Profile.
4. If no notes are left, continue to step d.
5. If there is a note, follow and talk with the manager if you need clarification.
    a. Verify previous drawing revision level.
    b. Review supervisor signature sign-off.
6. Run the program, follow instruction prompts.
    a. Work Ticket Number (303XXXX-XXX)
    b. Part Number (3A1488_01_Rev_K)
    c. Serial Number

Controls Tab:
Customer: 
Part data: 
Additional Data: 
Primary Inspector: 
Notes: 

Revision History
Rev,Date,Changes,Author
1.0,6/5/2025,Initial document generation.,Alyssa Barstad"""

raw_input = st.text_area(
    "Configure specification strings here:", 
    value=DEFAULT_TEMPLATE,
    height=360
)

st.subheader("📸 Attachment Injection (Optional)")
uploaded_images = st.file_uploader(
    "Upload setup figures or tracking charts (JPG/PNG):", 
    accept_multiple_files=True, 
    type=["jpg", "png", "jpeg"]
)

if st.button("Compile to PDF"):
    if raw_input.strip():
        with st.spinner("Processing template elements..."):
            content_data = parse_raw_dump(raw_input)
            
            img_html = []
            if uploaded_images:
                img_html.append('<div class="section-title">Visual Layout Reference Attachments</div>')
                img_html.append('<table class="image-grid">')
                
                for i in range(0, len(uploaded_images), 2):
                    img_html.append('<tr>')
                    img1 = uploaded_images[i]
                    b64_1 = base64.b64encode(img1.read()).decode()
                    img_html.append(f'<td><img class="embedded-img" src="data:{img1.type};base64,{b64_1}"><div class="image-caption">Figure {i+1}: {img1.name}</div></td>')
                    
                    if i + 1 < len(uploaded_images):
                        img2 = uploaded_images[i+1]
                        img2.seek(0)
                        b64_2 = base64.b64encode(img2.read()).decode()
                        img_html.append(f'<td><img class="embedded-img" src="data:{img2.type};base64,{b64_2}"><div class="image-caption">Figure {i+2}: {img2.name}</div></td>')
                    else:
                        img_html.append('<td></td>')
                    img_html.append('</tr>')
                img_html.append('</table>')
            
            final_html = HTML_TEMPLATE.format(
                doc_title=content_data["doc_title"],
                template_num=content_data["template_num"],
                purpose=content_data["purpose"],
                dynamic_content=content_data["dynamic_content"],
                image_content="".join(img_html)
            )
            
            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(final_html, dest=pdf_buffer)
            
            if not pisa_status.err:
                st.success("Document successfully compiled locally!")
                st.download_button(
                    label="📥 Download Polish Production PDF",
                    data=pdf_buffer.getvalue(),
                    file_name="Compiled_Specification.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Error formatting PDF document.")