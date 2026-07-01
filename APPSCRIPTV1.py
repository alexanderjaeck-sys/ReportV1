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
        line-height: 1.4;
        font-size: 10pt;
    }}
    .header-layout {{
        width: 100%;
        margin-bottom: 15px;
        border-collapse: collapse;
    }}
    .header-layout td {{
        vertical-align: middle;
        border: none;
    }}
    .logo-cell {{
        width: 250px;
    }}
    .title-cell {{
        text-align: right;
    }}
    .pdf-logo {{
        width: 170px;
        height: auto;
    }}
    .pdf-app-title {{
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
        padding: 8px 10px;
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
        width: 100px;
    }}
    .section-container {{
        margin-top: 15px;
        margin-bottom: 5px;
    }}
    .section-title {{
        color: #000000;
        font-size: 11pt;
        font-weight: bold;
        border-bottom: 2px solid #E31E24;
        padding-bottom: 2px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        -pdf-keep-with-next: true;
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
        padding: 6px 10px;
        font-size: 9pt;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: 1px solid #414042;
    }}
    table.matrix-table tr {{
        page-break-inside: avoid;
    }}
    table.matrix-table td {{
        border: 1px solid #939598;
        padding: 8px 10px;
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
        width: 80px;
    }}
    .step-img-container {{
        margin-top: 5px;
        text-align: left;
    }}
    .step-img {{
        width: 200px;
        height: auto;
        border: 1px solid #cbd5e1;
    }}
    .image-grid {{
        width: 100%;
        margin-top: 10px;
        border-collapse: collapse;
    }}
    .image-grid tr {{
        page-break-inside: avoid;
    }}
    .image-grid td {{
        width: 50%;
        padding: 5px;
        text-align: center;
        vertical-align: top;
    }}
    .embedded-img-frame {{
        width: 250px;
        height: 250px;
        object-fit: contain;
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        margin-bottom: 4px;
    }}
    .image-grid-caption {{
        font-size: 8.5pt;
        color: #414042;
        font-weight: bold;
        margin-top: 2px;
        line-height: 1.2;
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
            <td class="logo-cell">{html_logo_tag}</td>
            <td class="title-cell"><div class="pdf-app-title">PQI Work Instruction</div></td>
        </tr>
    </table>

    <table class="meta-table">
        <tr>
            <td class="meta-label">Doc Title</td>
            <td style="width: 280px;"><strong>{doc_title}</strong></td>
            <td class="meta-label">Template</td>
            <td>{template_num}</td>
        </tr>
        <tr>
            <td class="meta-label">Date</td>
            <td style="width: 280px;"><strong>{doc_date}</strong></td>
            <td class="meta-label">Author</td>
            <td>{doc_author}</td>
        </tr>
        <tr>
            <td class="meta-label">Purpose</td>
            <td colspan="3">{purpose}</td>
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

def generate_pdf_content(fields, images_list, image_captions, steps_4, steps_5, steps_6):
    html_output = []
    
    # Process regular string inputs (1, 2, 3)
    for h_key in ["1. WI Template Number", "2. Responsibilities", "3. Required Tools"]:
        if h_key in fields and fields[h_key].strip():
            clean_title = re.sub(r'^\d+\.\s*', '', h_key).replace(":", "")
            html_output.append(f'<div class="section-container"><div class="section-title">{clean_title}</div>')
            html_output.append(f'<div class="content-block">{format_text_block(fields[h_key])}</div></div>')
            
    # Process Section 4 Table
    if steps_4:
        html_output.append('<div class="section-container"><div class="section-title">Procedure: VCMM/CMM Inspection</div>')
        html_output.append('<table class="matrix-table"><tr><th>Step #</th><th>Details</th></tr>')
        for idx, step_item in enumerate(steps_4):
            txt = step_item["text"].strip()
            img = step_item["image"]
            img_html = ""
            if img is not None:
                img.seek(0)
                b64 = base64.b64encode(img.read()).decode()
                img_html = f'<div class="step-img-container"><br/><img class="step-img" src="data:{img.type};base64,{b64}"></div>'
            cell_text = txt if txt else "&nbsp;"
            html_output.append(f'<tr><td class="table-key">Step {idx+1}</td><td>{cell_text}{img_html}</td></tr>')
        html_output.append('</table></div>')
        
   # Process Section 5 Table
    if steps_5:
        html_output.append('<div class="section-container"><div class="section-title">Procedure: Visual Inspection</div>')
        html_output.append('<table class="matrix-table"><tr><th>Step #</th><th>Details</th></tr>')
        for idx, step_item in enumerate(steps_5):
            txt = step_item["text"].strip()
            img = step_item["image"]
            img_html = ""
            if img is not None:
                img.seek(0)
                b64 = base64.b64encode(img.read()).decode()
                img_html = f'<div class="step-img-container"><br/><img class="step-img" src="data:{img.type};base64,{b64}"></div>'
            cell_text = txt if txt else "&nbsp;"
            html_output.append(f'<tr><td class="table-key">Step {idx+1}</td><td>{cell_text}{img_html}</td></tr>')
        html_output.append('</table></div>')

    # Process Section 6 Table
    if steps_6:
        html_output.append('<div class="section-container"><div class="section-title">Procedure: Data Reporting</div>')
        html_output.append('<table class="matrix-table"><tr><th>Step #</th><th>Details</th></tr>')
        for idx, step_item in enumerate(steps_6):
            txt = step_item["text"].strip()
            img = step_item["image"]
            img_html = ""
            if img is not None:
                img.seek(0)
                b64 = base64.b64encode(img.read()).decode()
                img_html = f'<div class="step-img-container"><br/><img class="step-img" src="data:{img.type};base64,{b64}"></div>'
            cell_text = txt if txt else "&nbsp;"
            html_output.append(f'<tr><td class="table-key">Step {idx+1}</td><td>{cell_text}{img_html}</td></tr>')
        html_output.append('</table></div>')
        
    # Process Section 7 Attachments Grid
    if "7. Visuals / Screenshots" in fields or images_list:
        val_clean = fields.get("7. Visuals / Screenshots", "").strip()
        html_output.append('<div class="section-container"><div class="section-title">Visuals / Screenshots</div>')
        if val_clean: 
            html_output.append(f'<div class="content-block">{format_text_block(val_clean)}</div>')
        if images_list:
            html_output.append('<table class="image-grid">')
            for i in range(0, len(images_list), 2):
                html_output.append('<tr>')
                for j in range(2):
                    if i + j < len(images_list):
                        img = images_list[i+j]
                        img.seek(0)
                        b64 = base64.b64encode(img.read()).decode()
                        custom_caption = image_captions.get(img.name, "").strip()
                        display_caption = f"Figure {i+j+1}: {custom_caption}" if custom_caption else f"Figure {i+j+1}: {img.name}"
                        html_output.append(f'<td><img class="embedded-img-frame" src="data:{img.type};base64,{b64}"><div class="image-grid-caption">{display_caption}</div></td>')
                    else:
                        html_output.append('<td></td>')
                html_output.append('</tr>')
            html_output.append('</table>')
        html_output.append('</div>')
        
    # Process Footer Sections (8, 9, 10)
    for h_key in ["8. Safety / Precautions", "9. Troubleshooting", "10. Compliance"]:
        if h_key in fields and fields[h_key].strip():
            clean_title = re.sub(r'^\d+\.\s*', '', h_key).replace(":", "")
            html_output.append(f'<div class="section-container"><div class="section-title">{clean_title}</div>')
            html_output.append(f'<div class="content-block">{format_text_block(fields[h_key])}</div></div>')
            
    return "".join(html_output)

# --- STREAMLIT UI DESIGN ---
st.set_page_config(page_title="AIS | Work Instruction Generator", layout="centered")

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

if logo_b64:
    st.image(LOGO_PATH, width=280)
st.title("AIS Work Instruction Generator")
st.text("Advanced Inspection Services | Quality Control Management")
st.divider()

if "count_sec4" not in st.session_state: st.session_state.count_sec4 = 1
if "count_sec5" not in st.session_state: st.session_state.count_sec5 = 1
if "count_sec6" not in st.session_state: st.session_state.count_sec6 = 1

# Metadata Section
st.markdown("#### 📓 Document Metadata")
input_doc_title = st.text_input("Document Title:", placeholder="e.g., Sandia-3A1488-01")
col_l, col_m, col_r = st.columns(3)
with col_l: input_template_num = st.text_input("Template #:", placeholder="e.g., TMP-002")
with col_m: input_date = st.date_input("Date:", date.today())
with col_r: input_author = st.text_input("Author:", placeholder="Initials/Name")
input_purpose = st.text_area("Scope/Purpose:", placeholder="Describe the document scope...", height=70)

st.divider()

# UI UNIFORMITY FIX: Explicit Markdown headers mapped to collapsed textareas
st.markdown("#### 📋 Framework Categories")

fields = {}
st.markdown("#### 1. WI Template Number")
fields["1. WI Template Number"] = st.text_area("1. WI Template Number", height=65, label_visibility="collapsed")

st.markdown("#### 2. Responsibilities")
fields["2. Responsibilities"] = st.text_area("2. Responsibilities", value="a. Users:\nb. Management:", height=80, label_visibility="collapsed")

st.markdown("#### 3. Required Tools")
fields["3. Required Tools"] = st.text_area("3. Required Tools", height=80, label_visibility="collapsed")

st.divider()

# --- DYNAMIC SECTION 4 MANAGEMENT ---
st.markdown("#### 4. Procedure: VCMM/CMM Inspection")
steps_4 = []
for i in range(st.session_state.count_sec4):
    step_num = i + 1
    col_txt, col_img = st.columns([2, 1])
    with col_txt:
        s_txt = st.text_area(f"Step {step_num} Instruction Details:", key=f"txt_s4_{step_num}", height=65)
    with col_img:
        s_img = st.file_uploader(f"Step {step_num} Attachment Image:", type=["png", "jpg", "jpeg"], key=f"img_s4_{step_num}")
    steps_4.append({"text": s_txt, "image": s_img})

col_add4, col_del4, _ = st.columns([1, 1, 1])
with col_add4:
    if st.button("➕ Add Next Step", key="btn_add_4", use_container_width=True):
        st.session_state.count_sec4 += 1
        st.rerun()
with col_del4:
    if st.button("❌ Delete Last Step", key="btn_del_4", use_container_width=True):
        if st.session_state.count_sec4 > 1:
            st.session_state.count_sec4 -= 1
            st.rerun()

st.divider()

# --- DYNAMIC SECTION 5 MANAGEMENT ---
st.markdown("#### 5. Procedure: Visual Inspection")
steps_5 = []
for i in range(st.session_state.count_sec5):
    step_num = i + 1
    col_txt, col_img = st.columns([2, 1])
    with col_txt:
        s_txt = st.text_area(f"Step {step_num} Instruction Details:", key=f"txt_s5_{step_num}", height=65)
    with col_img:
        s_img = st.file_uploader(f"Step {step_num} Attachment Image:", type=["png", "jpg", "jpeg"], key=f"img_s5_{step_num}")
    steps_5.append({"text": s_txt, "image": s_img})

col_add5, col_del5, _ = st.columns([1, 1, 1])
with col_add5:
    if st.button("➕ Add Next Step", key="btn_add_5", use_container_width=True):
        st.session_state.count_sec5 += 1
        st.rerun()
with col_del5:
    if st.button("❌ Delete Last Step", key="btn_del_5", use_container_width=True):
        if st.session_state.count_sec5 > 1:
            st.session_state.count_sec5 -= 1
            st.rerun()

st.divider()

# --- DYNAMIC SECTION 6 MANAGEMENT ---
st.markdown("#### 6. Procedure: Data Reporting")
steps_6 = []
for i in range(st.session_state.count_sec6):
    step_num = i + 1
    col_txt, col_img = st.columns([2, 1])
    with col_txt:
        s_txt = st.text_area(f"Step {step_num} Instruction Details:", key=f"txt_s6_{step_num}", height=65)
    with col_img:
        s_img = st.file_uploader(f"Step {step_num} Attachment Image:", type=["png", "jpg", "jpeg"], key=f"img_s6_{step_num}")
    steps_6.append({"text": s_txt, "image": s_img})

col_add6, col_del6, _ = st.columns([1, 1, 1])
with col_add6:
    if st.button("➕ Add Next Step", key="btn_add_6", use_container_width=True):
        st.session_state.count_sec6 += 1
        st.rerun()
with col_del6:
    if st.button("❌ Delete Last Step", key="btn_del_6", use_container_width=True):
        if st.session_state.count_sec6 > 1:
            st.session_state.count_sec6 -= 1
            st.rerun()

st.divider()

st.markdown("#### 7. Visuals / Screenshots")
fields["7. Visuals / Screenshots"] = st.text_area("Narrative for Section 7:", height=70, label_visibility="collapsed")
uploaded_images = st.file_uploader("Upload Figures (JPG/PNG):", accept_multiple_files=True, type=["jpg", "png", "jpeg"])

image_captions = {}
if uploaded_images:
    st.markdown("###### 📝 Figure Description Captions")
    for idx, img in enumerate(uploaded_images):
        image_captions[img.name] = st.text_input(f"Description for figure ({img.name}):", key=f"cap_{idx}_{img.name}", placeholder="e.g., Highlighted alignment pin verification vector.")

st.divider()

st.markdown("#### 8. Safety / Precautions")
fields["8. Safety / Precautions"] = st.text_area("8. Safety / Precautions", height=80, label_visibility="collapsed")

st.markdown("#### 9. Notes / Troubleshooting")
fields["9. Troubleshooting"] = st.text_area("9. Notes / Troubleshooting", height=80, label_visibility="collapsed")

st.markdown("#### 10. Compliance")
fields["10. Compliance"] = st.text_area("10. Compliance", height=80, label_visibility="collapsed")

st.divider()
_, col_btn = st.columns([2, 1])
with col_btn:
    compile_button = st.button("🚀 COMPILE TO PDF", use_container_width=True)

if compile_button:
    with st.spinner("Compiling AIS Branded Report..."):
        dynamic_content = generate_pdf_content(fields, uploaded_images, image_captions, steps_4, steps_5, steps_6)
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
        pisa_status = pisa.CreatePDF(final_html, dest=pdf_buffer)
        st.success("AIS Branded Report Ready!")
        st.download_button("📥 DOWNLOAD PDF", data=pdf_buffer.getvalue(), file_name="AIS_Work_Instruction.pdf", mime="application/pdf", use_container_width=True)