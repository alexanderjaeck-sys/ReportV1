import streamlit as st
import re
import base64
import os
from xhtml2pdf import pisa
from io import BytesIO
from datetime import date

# Helper Function to convert local image to a base64 string safely
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

# Fetch local logo asset
LOGO_PATH = "AIS Logo.png"
logo_b64 = get_base64_image(LOGO_PATH)

# --- FIXED PRINT-SPECIFIC CSS/HTML TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: letter;
        margin: 0.5in 0.5in 0.6in 0.5in;
    }}
    body {{
        font-family: Helvetica, Arial, sans-serif;
        color: #1e293b;
        line-height: 1.5;
        font-size: 10pt;
    }}
    .header-layout {{
        width: 100%;
        margin-bottom: 15px;
    }}
    .header-layout td {{
        vertical-align: middle;
        border: none;
    }}
    .pdf-logo {{
        width: 180px;
        height: auto;
    }}
    .pdf-app-title {{
        text-align: right;
        color: #1e3a8a;
        font-size: 16pt;
        font-weight: bold;
        font-family: Helvetica, Arial, sans-serif;
    }}
    .meta-table {{
        width: 100%;
        margin-bottom: 20px;
        border-collapse: collapse;
    }}
    .meta-table td {{
        padding: 10px 12px;
        font-size: 9.5pt;
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
    }}
    .meta-label {{
        color: #475569;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 8pt;
        letter-spacing: 0.5px;
        width: 18%;
    }}
    .meta-value {{
        color: #0f172a;
    }}
    .section-container {{
        margin-top: 18px;
        margin-bottom: 5px;
    }}
    .section-title {{
        color: #1e3a8a;
        font-size: 11pt;
        font-weight: bold;
        border-bottom: 1.5px solid #3b82f6;
        padding-bottom: 3px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .content-block {{
        margin-bottom: 10px;
        color: #334155;
        font-size: 10pt;
        padding-left: 2px;
    }}
    .text-line {{
        margin-bottom: 4px;
    }}
    table.matrix-table {{
        width: 100%;
        margin-top: 5px;
        margin-bottom: 12px;
        border-collapse: collapse;
    }}
    table.matrix-table th {{
        background-color: #1e3a8a;
        color: #ffffff;
        font-weight: bold;
        text-align: left;
        padding: 8px 12px;
        font-size: 9pt;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: 1px solid #1e3a8a;
    }}
    table.matrix-table td {{
        border: 1px solid #cbd5e1;
        padding: 9px 12px;
        font-size: 9.5pt;
        vertical-align: top;
        color: #334155;
    }}
    table.matrix-table tr:nth-child(even) td {{
        background-color: #f8fafc;
    }}
    .table-key {{
        font-weight: bold;
        color: #0f172a;
        width: 30%;
    }}
    .image-grid {{
        width: 100%;
        margin-top: 10px;
    }}
    .image-grid td {{
        width: 50%;
        padding: 6px;
        text-align: center;
        vertical-align: top;
    }}
    .embedded-img {{
        width: 280px;
        height: auto;
        border: 1px solid #cbd5e1;
        margin-bottom: 4px;
    }}
    .image-grid-caption {{
        font-size: 8.5pt;
        color: #64748b;
        font-weight: bold;
    }}
    .footer-container {{
        text-align: right;
        font-size: 8pt;
        color: #94a3b8;
        margin-top: 20px;
    }}
</style>
</head>
<body>
    <table class="header-layout">
        <tr>
            <td>
                {html_logo_tag}
            </td>
            <td class="pdf-app-title">
                PQI Work Instruction Document
            </td>
        </tr>
    </table>

    <table class="meta-table">
        <tr>
            <td class="meta-label">Doc Title</td>
            <td class="meta-value" style="width: 45%;"><strong>{doc_title}</strong></td>
            <td class="meta-label">Template</td>
            <td class="meta-value">{template_num}</td>
        </tr>
        <tr>
            <td class="meta-label">Date</td>
            <td class="meta-value"><strong>{doc_date}</strong></td>
            <td class="meta-label">Author</td>
            <td class="meta-value">{doc_author}</td>
        </tr>
        <tr>
            <td class="meta-label">Purpose</td>
            <td class="meta-value" colspan="3">{purpose}</td>
        </tr>
    </table>
    
    {dynamic_content}

    <div class="footer-container">
        Page <pdf:pagenumber />
    </div>
</body>
</html>
"""

def format_text_block(text_value):
    lines = text_value.strip().split('\n')
    html_lines = []
    for line in lines:
        if line.strip():
            html_lines.append(f'<div class="text-line">{line}</div>')
        else:
            html_lines.append('<div style="height: 6px;"></div>')
    return "".join(html_lines)

def generate_pdf_content(fields, images_list):
    html_output = []
    table_based_categories = [
        "5. Procedure: VCMM/CMM Inspection", 
        "7. Procedure: Data Reporting"
    ]
    
    for header, value in fields.items():
        val_clean = value.strip()
        
        if header == "8. Visuals / Screenshots":
            if not val_clean and not images_list:
                continue
                
            html_output.append('<div class="section-container">')
            html_output.append('<div class="section-title">Visuals / Screenshots</div>')
            
            if val_clean:
                html_output.append(f'<div class="content-block">{format_text_block(val_clean)}</div>')
            
            if images_list:
                html_output.append('<table class="image-grid">')
                for i in range(0, len(images_list), 2):
                    html_output.append('<tr>')
                    img1 = images_list[i]
                    img1.seek(0)
                    b64_1 = base64.b64encode(img1.read()).decode()
                    html_output.append(f'<td><img class="embedded-img" src="data:{img1.type};base64,{b64_1}"><div class="image-grid-caption">Figure {i+1}: {img1.name}</div></td>')
                    
                    if i + 1 < len(images_list):
                        img2 = images_list[i+1]
                        img2.seek(0)
                        b64_2 = base64.b64encode(img2.read()).decode()
                        html_output.append(f'<td><img class="embedded-img" src="data:{img2.type};base64,{b64_2}"><div class="image-grid-caption">Figure {i+2}: {img2.name}</div></td>')
                    else:
                        html_output.append('<td></td>')
                    html_output.append('</tr>')
                html_output.append('</table>')
            html_output.append('</div>')
            continue

        if not val_clean:
            continue
            
        clean_title = re.sub(r'^\d+\.\s*', '', header).replace(":", "")
        html_output.append('<div class="section-container">')
        html_output.append(f'<div class="section-title">{clean_title}</div>')
        
        if header in table_based_categories:
            html_output.append('<table class="matrix-table">')
            html_output.append('<tr><th>Element / Tab Mapping</th><th>Instruction / Action Block</th></tr>')
            
            for block in val_clean.split('\n'):
                if not block.strip():
                    continue
                if ":" in block:
                    parts = block.split(":", 1)
                    key = parts[0].strip()
                    val = parts[1].strip()
                else:
                    key = "Action Step"
                    val = block.strip()
                
                key = re.sub(r'^[\-\*]\s*', '', key)
                html_output.append(f'<tr><td class="table-key">{key}</td><td>{val if val else " "}</td></tr>')
            html_output.append('</table>')
        else:
            html_output.append(f'<div class="content-block">{format_text_block(val_clean)}</div>')
            
        html_output.append('</div>')
            
    return "".join(html_output)

# --- MINIMAL NATIVE STREAMLIT UI DESIGN ---
st.set_page_config(page_title="PQI Work Instruction Generator", layout="centered")

# RENDER APP INTERFACE HEADER IMAGE ACCORDINGLY
if logo_b64:
    st.image(os.path.join(os.getcwd(), LOGO_PATH), width=240)

st.title("PQI Work Instruction Generator")
st.text("Advanced Inspection Services | Controlled Production Requirements")
st.divider()

st.markdown("#### 📓 Global Metadata Properties")
input_doc_title = st.text_input("Document Title:", placeholder="e.g., WI_010_Sandia-3A1488Headers_Rev1.0")

meta_col_left, meta_col_mid, meta_col_right = st.columns(3)
with meta_col_left:
    input_template_num = st.text_input("Template Number:", placeholder="e.g., TMP_002 Rev. 1.1")
with meta_col_mid:
    input_date = st.date_input("Tracking Date:", date.today())
with meta_col_right:
    input_author = st.text_input("Author:", placeholder="Enter your full name or initials...")

input_purpose = st.text_area(
    "Purpose Scope Description:",
    placeholder="Describe the operational purpose and scope execution rules of this document...",
    height=90
)

st.divider()

st.markdown("#### 📋 Instruction Framework Categories")
st.caption("Fields left completely blank will automatically hide themselves from generating inside the final PDF document structure.")

input_fields = {}
input_fields["1. WI Template Number"] = st.text_area("1. WI Template Number:", height=70)
input_fields["2. Purpose"] = st.text_area("2. Purpose:", height=90)
input_fields["3. Responsibilities"] = st.text_area("3. Responsibilities:", value="a. All Users:\nb. Quality Manager / Project Manager:", height=100)
input_fields["4. Required Tools / Software / Materials"] = st.text_area("4. Required Tools / Software / Materials:", height=100)
input_fields["5. Procedure: VCMM/CMM Inspection"] = st.text_area("5. Procedure: VCMM/CMM Inspection (Use 'Key: Value' layout for clean metric matrix printing):", value="Work Ticket Number:\nPart Number:\nSerial Number:", height=120)
input_fields["6. Procedure: Visual Inspection"] = st.text_area("6. Procedure: Visual Inspection:", height=110)
input_fields["7. Procedure: Data Reporting"] = st.text_area("7. Procedure: Data Reporting (Use 'Key: Value' layout for clean metric matrix printing):", value="Controls Tab:\nCustomer:\nPart data:\nAdditional Data:\nPrimary Inspector:\nNotes:\nCert_Uncert:\nComments Pg:\nEquip List:\nReport-V:\nReport Pictures:", height=260)

st.markdown("---")
st.markdown("##### 🖼️ Section 8 Configuration Hub")
input_fields["8. Visuals / Screenshots"] = st.text_area("8. Visuals / Screenshots Narrative Notes (Optional):", height=80)
uploaded_images = st.file_uploader(
    "Upload reference figures specifically for Section 8 (JPG/PNG):", 
    accept_multiple_files=True, 
    type=["jpg", "png", "jpeg"]
)
st.markdown("---")

input_fields["9. Safety / Precautions"] = st.text_area("9. Safety / Precautions:", height=100)
input_fields["10. Troubleshooting / Notes"] = st.text_area("10. Troubleshooting / Notes:", height=100)
input_fields["11. Compliance"] = st.text_area("11. Compliance:", height=100)

st.divider()

col_spacer, col_btn = st.columns([2, 1])
with col_btn:
    compile_button = st.button("Compile to PDF", type="primary", use_container_width=True)

if compile_button:
    if input_doc_title.strip() or any(f.strip() for f in input_fields.values()):
        author_stamp = input_author.strip() if input_author.strip() else "Not Specified"
        date_stamp = input_date.strftime("%m/%d/%Y")
        
        with st.spinner("Compiling..."):
            dynamic_pdf_content = generate_pdf_content(input_fields, uploaded_images)
            
            # Setup logo img HTML component cleanly
            html_logo_tag = f'<img class="pdf-logo" src="data:image/png;base64,{logo_b64}">' if logo_b64 else ''
            
            final_html = HTML_TEMPLATE.format(
                html_logo_tag=html_logo_tag,
                doc_title=input_doc_title if input_doc_title.strip() else " ",
                template_num=input_template_num if input_template_num.strip() else " ",
                doc_date=date_stamp,
                doc_author=author_stamp,
                purpose=input_purpose if input_purpose.strip() else " ",
                dynamic_content=dynamic_pdf_content
            )
            
            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(final_html, dest=pdf_buffer)
            
            if not pisa_status.err:
                st.success("Compilation complete.")
                st.download_button(
                    label="Download Production PDF",
                    data=pdf_buffer.getvalue(),
                    file_name="Compiled_Specification.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.error("Error formatting PDF.")