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

# --- BRANDED PRINT-SPECIFIC CSS/HTML TEMPLATE ---
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
        color: #414042;
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
        color: #E31E24;
        font-size: 16pt;
        font-weight: bold;
    }}
    .meta-table {{
        width: 100%;
        margin-bottom: 20px;
        border-collapse: collapse;
    }}
    .meta-table td {{
        padding: 10px 12px;
        font-size: 9.5pt;
        background-color: #ffffff;
        border: 1px solid #939598;
    }}
    .meta-label {{
        color: #414042;
        background-color: #f2f2f2;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 8pt;
        letter-spacing: 0.5px;
        width: 18%;
    }}
    .section-container {{
        margin-top: 18px;
        margin-bottom: 5px;
    }}
    .section-title {{
        color: #000000; /* Section header titles set to black */
        font-size: 11pt;
        font-weight: bold;
        border-bottom: 2px solid #E31E24; /* Bar remains AIS Red */
        padding-bottom: 3px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .content-block {{
        margin-bottom: 10px;
        color: #414042;
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
        background-color: #414042;
        color: #ffffff;
        font-weight: bold;
        text-align: left;
        padding: 8px 12px;
        font-size: 9pt;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: 1px solid #414042;
    }}
    table.matrix-table td {{
        border: 1px solid #939598;
        padding: 9px 12px;
        font-size: 9.5pt;
        vertical-align: top;
        color: #414042;
    }}
    table.matrix-table tr:nth-child(even) td {{
        background-color: #f9f9f9;
    }}
    .table-key {{
        font-weight: bold;
        color: #E31E24;
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
        border: 1px solid #939598;
        margin-bottom: 4px;
    }}
    .image-grid-caption {{
        font-size: 8.5pt;
        color: #939598;
        font-weight: bold;
    }}
    .footer-container {{
        text-align: right;
        font-size: 8pt;
        color: #939598;
        margin-top: 20px;
    }}
</style>
</head>
<body>
    <table class="header-layout">
        <tr>
            <td>{html_logo_tag}</td>
            <td class="pdf-app-title">PQI Work Instruction</td>
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
            <td class="meta-value" style="width: 45%;"><strong>{doc_date}</strong></td>
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
        AIS Quality Assurance | Page <pdf:pagenumber />
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
    table_based_categories = ["5. Procedure: VCMM/CMM Inspection", "7. Procedure: Data Reporting"]
    
    for header, value in fields.items():
        val_clean = value.strip()
        
        if header == "8. Visuals / Screenshots":
            if not val_clean and not images_list: continue
            html_output.append('<div class="section-container"><div class="section-title">Visuals / Screenshots</div>')
            if val_clean: html_output.append(f'<div class="content-block">{format_text_block(val_clean)}</div>')
            if images_list:
                html_output.append('<table class="image-grid">')
                for i in range(0, len(images_list), 2):
                    html_output.append('<tr>')
                    for j in range(2):
                        if i + j < len(images_list):
                            img = images_list[i+j]
                            img.seek(0)
                            b64 = base64.b64encode(img.read()).decode()
                            html_output.append(f'<td><img class="embedded-img" src="data:{img.type};base64,{b64}"><div class="image-grid-caption">Figure {i+j+1}: {img.name}</div></td>')
                        else: html_output.append('<td></td>')
                    html_output.append('</tr>')
                html_output.append('</table>')
            html_output.append('</div>')
            continue

        if not val_clean: continue
        clean_title = re.sub(r'^\d+\.\s*', '', header).replace(":", "")
        html_output.append(f'<div class="section-container"><div class="section-title">{clean_title}</div>')
        
        if header in table_based_categories:
            html_output.append('<table class="matrix-table"><tr><th>Element / Tab Mapping</th><th>Instruction / Action Block</th></tr>')
            for block in val_clean.split('\n'):
                if not block.strip(): continue
                if ":" in block:
                    parts = block.split(":", 1)
                    key, val = parts[0].strip(), parts[1].strip()
                else: key, val = "Action Step", block.strip()
                key = re.sub(r'^[\-\*]\s*', '', key)
                html_output.append(f'<tr><td class="table-key">{key}</td><td>{val if val else " "}</td></tr>')
            html_output.append('</table>')
        else:
            html_output.append(f'<div class="content-block">{format_text_block(val_clean)}</div>')
        html_output.append('</div>')
    return "".join(html_output)

# --- STREAMLIT UI DESIGN ---
st.set_page_config(page_title="AIS | PQI Work Instruction Generator", layout="centered")

# Injection of AIS Red and Grey Brand Colors into the App UI
st.markdown(f"""
    <style>
        .stApp {{ background-color: #ffffff; }}
        h1 {{ color: #E31E24 !important; font-weight: 800 !important; }}
        h4, h5 {{ color: #414042 !important; font-weight: 700 !important; }}
        .stButton>button {{
            background-color: #E31E24 !important;
            color: white !important;
            border-radius: 5px !important;
            border: none !important;
            font-weight: bold !important;
        }}
        .stButton>button:hover {{ background-color: #414042 !important; color: white !important; }}
        .stDivider {{ border-bottom-color: #939598 !important; }}
        div[data-baseweb="textarea"] textarea {{ border: 1px solid #939598 !important; }}
    </style>
""", unsafe_allow_html=True)

# Logo and Header
if logo_b64:
    st.image(LOGO_PATH, width=280)
st.title("PQI Work Instruction Generator")
st.text("Advanced Inspection Services | Quality Control Management")
st.divider()

# Metadata Section
st.markdown("#### 📓 Document Metadata")
input_doc_title = st.text_input("Document Title:", placeholder="e.g., Sandia-3A1488-01")
col_l, col_m, col_r = st.columns(3)
with col_l: input_template_num = st.text_input("Template #:", placeholder="e.g., TMP-002")
with col_m: input_date = st.date_input("Date:", date.today())
with col_r: input_author = st.text_input("Author:", placeholder="Initials/Name")
input_purpose = st.text_area("Scope/Purpose:", placeholder="Describe the document scope...", height=70)

st.divider()

# Instructions Sections
st.markdown("#### 📋 Framework Categories")
fields = {}
fields["1. WI Template Number"] = st.text_area("1. WI Template Number:", height=65)
fields["2. Purpose"] = st.text_area("2. Purpose:", height=65)
fields["3. Responsibilities"] = st.text_area("3. Responsibilities:", value="a. Users:\nb. Management:", height=80)
fields["4. Required Tools"] = st.text_area("4. Required Tools:", height=80)
fields["5. Procedure: VCMM/CMM Inspection"] = st.text_area("5. Procedure: VCMM/CMM (Key: Value):", value="Ticket #:\nPart #:\nSerial #:", height=100)
fields["6. Procedure: Visual Inspection"] = st.text_area("6. Procedure: Visual Inspection:", height=100)
fields["7. Procedure: Data Reporting"] = st.text_area("7. Procedure: Data Reporting (Key: Value):", value="Controls Tab:\nCustomer:\nNotes:", height=180)

st.markdown("---")
st.markdown("##### 🖼️ Section 8: Visuals & Attachments")
fields["8. Visuals / Screenshots"] = st.text_area("Narrative for Section 8:", height=70)
uploaded_images = st.file_uploader("Upload Figures (JPG/PNG):", accept_multiple_files=True, type=["jpg", "png", "jpeg"])
st.markdown("---")

fields["9. Safety / Precautions"] = st.text_area("9. Safety:", height=80)
fields["10. Troubleshooting"] = st.text_area("10. Notes/Troubleshooting:", height=80)
fields["11. Compliance"] = st.text_area("11. Compliance:", height=80)

st.divider()
_, col_btn = st.columns([2, 1])
with col_btn:
    compile_button = st.button("🚀 COMPILE TO PDF", use_container_width=True)

if compile_button:
    with st.spinner("Compiling AIS Branded Report..."):
        dynamic_content = generate_pdf_content(fields, uploaded_images)
        logo_tag = f'<img class="pdf-logo" src="data:image/png;base64,{logo_b64}">' if logo_b64 else ''
        
        final_html = HTML_TEMPLATE.format(
            html_logo_tag=logo_tag,
            doc_title=input_doc_title if input_doc_title.strip() else " ",
            template_num=input_template_num if input_template_num.strip() else " ",
            doc_date=input_date.strftime("%m/%d/%Y"),
            doc_author=input_author.strip() if input_author.strip() else "AIS Team",
            purpose=input_purpose if input_purpose.strip() else " ",
            dynamic_content=dynamic_content
        )
        
        pdf_buffer = BytesIO()
        pisa.CreatePDF(final_html, dest=pdf_buffer)
        st.success("AIS Branded Report Ready!")
        st.download_button("📥 DOWNLOAD PDF", data=pdf_buffer.getvalue(), file_name="AIS_Work_Instruction.pdf", mime="application/pdf", use_container_width=True)