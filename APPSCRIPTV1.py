import streamlit as st
import re
import base64
import os
import json
from xhtml2pdf import pisa
from io import BytesIO
from datetime import date, datetime

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
    .step-img-caption {{
        font-size: 8pt;
        color: #414042;
        font-style: italic;
        margin-top: 3px;
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


# ---------------------------------------------------------------------------
# IMAGE RESOLUTION HELPERS
# ---------------------------------------------------------------------------

def resolve_image(uploaded_file, loaded_entry=None):
    if uploaded_file is not None:
        uploaded_file.seek(0)
        b64 = base64.b64encode(uploaded_file.read()).decode()
        return {"b64": b64, "type": uploaded_file.type, "name": uploaded_file.name}
    if loaded_entry:
        return loaded_entry
    return None

def resolve_steps(steps, prefix):
    resolved = []
    for i, s in enumerate(steps):
        step_key = f"{prefix}_{i + 1}"
        img = resolve_image(s["image"], st.session_state.loaded_images.get(step_key))
        if img:
            st.session_state.loaded_images[step_key] = img
        resolved.append({"text": s["text"], "image": img, "caption": s.get("caption", "")})
    return resolved

def img_html_block(resolved, caption=""):
    if not resolved:
        return ""
    tag = f'<img class="step-img" src="data:{resolved["type"]};base64,{resolved["b64"]}">'
    cap_html = f'<div class="step-img-caption">{caption}</div>' if caption.strip() else ""
    return f'<div class="step-img-container"><br/>{tag}{cap_html}</div>'


def generate_pdf_content(fields, resolved_images_6, steps_2, steps_3, steps_4, steps_5, steps_7, steps_8):
    html_output = []

    # Section 1: Responsibilities (Split manually)
    users_val = fields.get("field_1_users", "").strip()
    mgmt_val = fields.get("field_1_mgmt", "").strip()
    if users_val or mgmt_val:
        html_output.append('<div class="section-container"><div class="section-title">Responsibilities</div>')
        if users_val:
            html_output.append(f'<div class="content-block"><strong>Users:</strong><br>{format_text_block(users_val)}</div>')
        if mgmt_val:
            html_output.append(f'<div class="content-block"><strong>Management:</strong><br>{format_text_block(mgmt_val)}</div>')
        html_output.append('</div>')

    def render_steps(title, steps, item_label="Step"):
        if not steps:
            return
        html_output.append(f'<div class="section-container"><div class="section-title">{title}</div>')
        html_output.append(f'<table class="matrix-table"><tr><th>{item_label} #</th><th>Details</th></tr>')
        for idx, step_item in enumerate(steps):
            txt = step_item["text"].strip()
            img_html = img_html_block(step_item["image"], step_item.get("caption", ""))
            cell_text = txt if txt else "&nbsp;"
            html_output.append(f'<tr><td class="table-key">{item_label} {idx + 1}</td><td>{cell_text}{img_html}</td></tr>')
        html_output.append('</table></div>')

    render_steps("Required Tools", steps_2, item_label="Tool")
    render_steps("Procedure: VCMM/CMM Inspection", steps_3)
    render_steps("Procedure: Visual Inspection", steps_4)
    render_steps("Procedure: Data Reporting", steps_5)

    # Section 6: Visuals / Screenshots Grid
    val_clean = fields.get("field_6_narrative", "").strip()
    if val_clean or resolved_images_6:
        html_output.append('<div class="section-container"><div class="section-title">Visuals / Screenshots</div>')
        if val_clean:
            html_output.append(f'<div class="content-block">{format_text_block(val_clean)}</div>')
        if resolved_images_6:
            html_output.append('<table class="image-grid">')
            for i in range(0, len(resolved_images_6), 2):
                html_output.append('<tr>')
                for j in range(2):
                    if i + j < len(resolved_images_6):
                        img = resolved_images_6[i + j]
                        custom_caption = (img.get("caption") or "").strip()
                        display_caption = f"Figure {i + j + 1}: {custom_caption}" if custom_caption else f"Figure {i + j + 1}: {img['name']}"
                        html_output.append(
                            f'<td><img class="embedded-img-frame" src="data:{img["type"]};base64,{img["b64"]}">'
                            f'<div class="image-grid-caption">{display_caption}</div></td>'
                        )
                    else:
                        html_output.append('<td></td>')
                html_output.append('</tr>')
            html_output.append('</table>')
        html_output.append('</div>')

    render_steps("Safety / Precautions", steps_7)
    render_steps("Notes / Troubleshooting", steps_8)

    # Section 9: Compliance
    if "field_9" in fields and fields["field_9"].strip():
        html_output.append('<div class="section-container"><div class="section-title">Compliance</div>')
        html_output.append(f'<div class="content-block">{format_text_block(fields["field_9"])}</div></div>')

    return "".join(html_output)


# ---------------------------------------------------------------------------
# STREAMLIT UI
# ---------------------------------------------------------------------------
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

# --- CORE SESSION STATE INITIALIZATION ---
if "count_sec2" not in st.session_state: st.session_state.count_sec2 = 1
if "count_sec3" not in st.session_state: st.session_state.count_sec3 = 1
if "count_sec4" not in st.session_state: st.session_state.count_sec4 = 1
if "count_sec5" not in st.session_state: st.session_state.count_sec5 = 1
if "count_sec7" not in st.session_state: st.session_state.count_sec7 = 1
if "count_sec8" not in st.session_state: st.session_state.count_sec8 = 1

if "loaded_images" not in st.session_state: st.session_state.loaded_images = {}
if "applied_draft_id" not in st.session_state: st.session_state.applied_draft_id = None

# Defaults
_defaults = {
    "input_doc_title": "",
    "input_template_num": "",
    "input_date": date.today(),
    "input_author": "",
    "input_purpose": "",
    "field_1_users": "",
    "field_1_mgmt": "",
    "field_6_narrative": "",
    "field_9": "",
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# =====================================================================
# SAVE / LOAD PROGRESS
# =====================================================================
st.markdown("#### 💾 Save / Load Progress")
st.caption("Load a previously saved `.json` draft to restore text fields and images.")

col_load, col_reset = st.columns([3, 1])
with col_load:
    draft_file = st.file_uploader("Load a saved draft (.json):", type=["json"], key="draft_uploader")
with col_reset:
    st.write("")
    st.write("")
if st.button("🗑️ Start New", use_container_width=True):
        # 1. Reset all step counters back to 1
        st.session_state.count_sec2 = 1
        st.session_state.count_sec3 = 1
        st.session_state.count_sec4 = 1
        st.session_state.count_sec5 = 1
        st.session_state.count_sec7 = 1
        st.session_state.count_sec8 = 1
        
        # 2. Clear stored images and draft memory
        st.session_state.loaded_images = {}
        st.session_state.applied_draft_id = None
        
        # 3. Explicitly overwrite ALL text inputs with empty strings to force the browser to clear
        for key in list(st.session_state.keys()):
            if key.startswith(("txt_", "cap_", "field_", "input_")):
                if key == "input_date":
                    st.session_state[key] = date.today()
                else:
                    st.session_state[key] = ""
                    
        # 4. Increment app_key to destroy file uploaders
        st.session_state.app_key = st.session_state.get("app_key", 0) + 1
        
        st.rerun()
if draft_file is not None:
    _draft_id = getattr(draft_file, "file_id", None) or f"{draft_file.name}_{draft_file.size}"
    if st.session_state.applied_draft_id != _draft_id:
        try:
            draft_data = json.loads(draft_file.read().decode("utf-8"))
            values = draft_data.get("values", {})
            if "input_date" in values:
                try:
                    values["input_date"] = datetime.strptime(values["input_date"], "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    values["input_date"] = date.today()
            for k, v in values.items():
                st.session_state[k] = v
            st.session_state.count_sec2 = draft_data.get("count_sec2", 1)
            st.session_state.count_sec3 = draft_data.get("count_sec3", 1)
            st.session_state.count_sec4 = draft_data.get("count_sec4", 1)
            st.session_state.count_sec5 = draft_data.get("count_sec5", 1)
            st.session_state.count_sec7 = draft_data.get("count_sec7", 1)
            st.session_state.count_sec8 = draft_data.get("count_sec8", 1)
            st.session_state.loaded_images = draft_data.get("images", {})
            st.session_state.applied_draft_id = _draft_id
            st.success("Draft loaded — restoring fields...")
            st.rerun()
        except Exception as e:
            st.error(f"Could not load draft: {e}")

st.divider()

# Metadata Section
st.markdown("#### 📓 Document Metadata")
input_doc_title = st.text_input("Document Title:", key="input_doc_title", placeholder="e.g., Sandia-3A1488-01")
col_l, col_m, col_r = st.columns(3)
with col_l: input_template_num = st.text_input("Template #:", key="input_template_num", placeholder="e.g., TMP-002")
with col_m: input_date = st.date_input("Date:", key="input_date")
with col_r: input_author = st.text_input("Author:", key="input_author", placeholder="Initials/Name")
input_purpose = st.text_area("Scope/Purpose:", key="input_purpose", placeholder="Describe the document scope...", height=70)

st.divider()

st.markdown("#### 📋 Framework Categories")

fields = {}

# --- SECTION 1: Responsibilities ---
st.markdown("#### 1. Responsibilities")
col_user, col_mgmt = st.columns(2)
with col_user:
    fields["field_1_users"] = st.text_area("Users:", key="field_1_users", height=80)
with col_mgmt:
    fields["field_1_mgmt"] = st.text_area("Management:", key="field_1_mgmt", height=80)
st.divider()


def build_dynamic_section(title, prefix, count_key, add_label, del_label, text_label="Details"):
    st.markdown(f"#### {title}")
    steps = []
    for i in range(st.session_state[count_key]):
        step_num = i + 1
        col_txt, col_img = st.columns([2, 1])
        with col_txt:
            s_txt = st.text_area(f"{text_label} {step_num}:", key=f"txt_{prefix}_{step_num}", height=120)
        with col_img:
            s_img = st.file_uploader(f"Image {step_num}:", type=["png", "jpg", "jpeg"], key=f"img_{prefix}_{step_num}")
            s_cap = st.text_input(f"Caption (optional):", key=f"cap_{prefix}_{step_num}")
            if s_img is None and st.session_state.loaded_images.get(f"{prefix}_{step_num}"):
                st.caption("📎 Using saved image from loaded draft")
        steps.append({"text": s_txt, "image": s_img, "caption": s_cap})

    col_add, col_del, _ = st.columns([1, 1, 1])
    with col_add:
        if st.button(f"➕ {add_label}", key=f"btn_add_{prefix}", use_container_width=True):
            st.session_state[count_key] += 1
            st.rerun()
    with col_del:
        if st.button(f"❌ {del_label}", key=f"btn_del_{prefix}", use_container_width=True):
            if st.session_state[count_key] > 1:
                st.session_state[count_key] -= 1
                st.rerun()
    st.divider()
    return steps


steps_2 = build_dynamic_section("2. Required Tools", "s2", "count_sec2", "Add Next Tool", "Delete Last Tool", "Tool")
steps_3 = build_dynamic_section("3. Procedure: VCMM/CMM Inspection", "s3", "count_sec3", "Add Next Step", "Delete Last Step", "Step")
steps_4 = build_dynamic_section("4. Procedure: Visual Inspection", "s4", "count_sec4", "Add Next Step", "Delete Last Step", "Step")
steps_5 = build_dynamic_section("5. Procedure: Data Reporting", "s5", "count_sec5", "Add Next Step", "Delete Last Step", "Step")

# --- SECTION 6: Visuals / Screenshots ---
st.markdown("#### 6. Visuals / Screenshots")
fields["field_6_narrative"] = st.text_area("Narrative for Section 6:", key="field_6_narrative", height=70, label_visibility="collapsed")
uploaded_images = st.file_uploader("Upload Figures (JPG/PNG):", accept_multiple_files=True, type=["jpg", "png", "jpeg"])

image_captions = {}
if uploaded_images:
    st.markdown("###### 📝 Figure Description Captions")
    for idx, img in enumerate(uploaded_images):
        image_captions[img.name] = st.text_input(f"Description for figure ({img.name}):", key=f"cap_grid_{idx}_{img.name}", placeholder="e.g., Highlighted alignment pin verification vector.")
elif st.session_state.loaded_images.get("section6"):
    st.caption(f"📎 Using {len(st.session_state.loaded_images['section6'])} saved figure(s) from loaded draft")
st.divider()


steps_7 = build_dynamic_section("7. Safety / Precautions", "s7", "count_sec7", "Add Next Item", "Delete Last Item", "Item")
steps_8 = build_dynamic_section("8. Notes / Troubleshooting", "s8", "count_sec8", "Add Next Item", "Delete Last Item", "Item")

# --- SECTION 9: Compliance ---
st.markdown("#### 9. Compliance")
fields["field_9"] = st.text_area("9. Compliance", key="field_9", height=80, label_visibility="collapsed") 
st.divider()


# --- RESOLVE IMAGES ---
resolved_steps_2 = resolve_steps(steps_2, "s2")
resolved_steps_3 = resolve_steps(steps_3, "s3")
resolved_steps_4 = resolve_steps(steps_4, "s4")
resolved_steps_5 = resolve_steps(steps_5, "s5")
resolved_steps_7 = resolve_steps(steps_7, "s7")
resolved_steps_8 = resolve_steps(steps_8, "s8")

if uploaded_images:
    resolved_images_6 = []
    for img in uploaded_images:
        img.seek(0)
        b64 = base64.b64encode(img.read()).decode()
        resolved_images_6.append({
            "name": img.name,
            "type": img.type,
            "b64": b64,
            "caption": image_captions.get(img.name, ""),
        })
    st.session_state.loaded_images["section6"] = resolved_images_6
else:
    resolved_images_6 = st.session_state.loaded_images.get("section6", [])


def build_draft_payload():
    values = {
        "input_doc_title": st.session_state.get("input_doc_title", ""),
        "input_template_num": st.session_state.get("input_template_num", ""),
        "input_date": st.session_state.get("input_date", date.today()).isoformat(),
        "input_author": st.session_state.get("input_author", ""),
        "input_purpose": st.session_state.get("input_purpose", ""),
        "field_1_users": st.session_state.get("field_1_users", ""),
        "field_1_mgmt": st.session_state.get("field_1_mgmt", ""),
        "field_6_narrative": st.session_state.get("field_6_narrative", ""),
        "field_9": st.session_state.get("field_9", ""),
    }
    # Dynamically pull all text and caption variables from active step arrays
    active_sections = [
        ("s2", st.session_state.count_sec2), ("s3", st.session_state.count_sec3),
        ("s4", st.session_state.count_sec4), ("s5", st.session_state.count_sec5),
        ("s7", st.session_state.count_sec7), ("s8", st.session_state.count_sec8)
    ]
    for prefix, count in active_sections:
        for i in range(count):
            values[f"txt_{prefix}_{i + 1}"] = st.session_state.get(f"txt_{prefix}_{i + 1}", "")
            values[f"cap_{prefix}_{i + 1}"] = st.session_state.get(f"cap_{prefix}_{i + 1}", "")

    return {
        "saved_at": datetime.now().isoformat(),
        "values": values,
        "count_sec2": st.session_state.count_sec2,
        "count_sec3": st.session_state.count_sec3,
        "count_sec4": st.session_state.count_sec4,
        "count_sec5": st.session_state.count_sec5,
        "count_sec7": st.session_state.count_sec7,
        "count_sec8": st.session_state.count_sec8,
        "images": st.session_state.loaded_images,
    }


col_save, col_compile = st.columns(2)

with col_save:
    draft_json = json.dumps(build_draft_payload(), indent=2)
    safe_title = re.sub(r'[^A-Za-z0-9_\-]+', '_', input_doc_title.strip()) or "draft"
    st.download_button(
        "💾 SAVE DRAFT (.json)",
        data=draft_json,
        file_name=f"WI_Draft_{safe_title}.json",
        mime="application/json",
        use_container_width=True,
    )

with col_compile:
    compile_button = st.button("🚀 COMPILE TO PDF", use_container_width=True)

if compile_button:
    with st.spinner("Compiling AIS Branded Report..."):
        dynamic_content = generate_pdf_content(
            fields, resolved_images_6, 
            resolved_steps_2, resolved_steps_3, resolved_steps_4, 
            resolved_steps_5, resolved_steps_7, resolved_steps_8
        )
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