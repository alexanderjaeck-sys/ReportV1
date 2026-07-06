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
#
# Streamlit file_uploader widgets cannot be pre-populated from a loaded
# draft, so any image data that needs to survive a save/load round trip is
# converted to base64 and stashed in st.session_state.loaded_images. When
# building the PDF, a freshly uploaded file always wins; if nothing new was
# uploaded, we fall back to whatever was restored from the draft.
# ---------------------------------------------------------------------------

def resolve_image(uploaded_file, loaded_entry=None):
    """Return {'b64','type','name'} dict, preferring a freshly uploaded file
    over a previously loaded/saved one. Returns None if neither exists."""
    if uploaded_file is not None:
        uploaded_file.seek(0)
        b64 = base64.b64encode(uploaded_file.read()).decode()
        return {"b64": b64, "type": uploaded_file.type, "name": uploaded_file.name}
    if loaded_entry:
        return loaded_entry
    return None


def resolve_steps(steps, prefix):
    """Resolve images for a list of {'text','image'} step dicts and persist
    them into st.session_state.loaded_images so they survive later reruns
    and can be included in a saved draft."""
    resolved = []
    for i, s in enumerate(steps):
        step_key = f"{prefix}_{i + 1}"
        img = resolve_image(s["image"], st.session_state.loaded_images.get(step_key))
        if img:
            st.session_state.loaded_images[step_key] = img
        resolved.append({"text": s["text"], "image": img})
    return resolved


def img_html_block(resolved):
    if not resolved:
        return ""
    tag = f'<img class="step-img" src="data:{resolved["type"]};base64,{resolved["b64"]}">'
    return f'<div class="step-img-container"><br/>{tag}</div>'


def generate_pdf_content(fields, resolved_images_7, steps_4, steps_5, steps_6):
    html_output = []

    # Process regular string inputs (1, 2, 3)
    for h_key in ["1. WI Template Number", "2. Responsibilities", "3. Required Tools"]:
        if h_key in fields and fields[h_key].strip():
            clean_title = re.sub(r'^\d+\.\s*', '', h_key).replace(":", "")
            html_output.append(f'<div class="section-container"><div class="section-title">{clean_title}</div>')
            html_output.append(f'<div class="content-block">{format_text_block(fields[h_key])}</div></div>')

    def render_steps(title, steps):
        if not steps:
            return
        html_output.append(f'<div class="section-container"><div class="section-title">{title}</div>')
        html_output.append('<table class="matrix-table"><tr><th>Step #</th><th>Details</th></tr>')
        for idx, step_item in enumerate(steps):
            txt = step_item["text"].strip()
            img_html = img_html_block(step_item["image"])
            cell_text = txt if txt else "&nbsp;"
            html_output.append(f'<tr><td class="table-key">Step {idx + 1}</td><td>{cell_text}{img_html}</td></tr>')
        html_output.append('</table></div>')

    render_steps("Procedure: VCMM/CMM Inspection", steps_4)
    render_steps("Procedure: Visual Inspection", steps_5)
    render_steps("Procedure: Data Reporting", steps_6)

    # Process Section 7 Attachments Grid
    if "7. Visuals / Screenshots" in fields or resolved_images_7:
        val_clean = fields.get("7. Visuals / Screenshots", "").strip()
        html_output.append('<div class="section-container"><div class="section-title">Visuals / Screenshots</div>')
        if val_clean:
            html_output.append(f'<div class="content-block">{format_text_block(val_clean)}</div>')
        if resolved_images_7:
            html_output.append('<table class="image-grid">')
            for i in range(0, len(resolved_images_7), 2):
                html_output.append('<tr>')
                for j in range(2):
                    if i + j < len(resolved_images_7):
                        img = resolved_images_7[i + j]
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

    # Process Footer Sections (8, 9, 10)
    for h_key in ["8. Safety / Precautions", "9. Troubleshooting", "10. Compliance"]:
        if h_key in fields and fields[h_key].strip():
            clean_title = re.sub(r'^\d+\.\s*', '', h_key).replace(":", "")
            html_output.append(f'<div class="section-container"><div class="section-title">{clean_title}</div>')
            html_output.append(f'<div class="content-block">{format_text_block(fields[h_key])}</div></div>')

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
if "count_sec4" not in st.session_state: st.session_state.count_sec4 = 1
if "count_sec5" not in st.session_state: st.session_state.count_sec5 = 1
if "count_sec6" not in st.session_state: st.session_state.count_sec6 = 1
if "loaded_images" not in st.session_state: st.session_state.loaded_images = {}
if "applied_draft_id" not in st.session_state: st.session_state.applied_draft_id = None

# Defaults for text/date fields (only applied if not already restored from a draft)
_defaults = {
    "input_doc_title": "",
    "input_template_num": "",
    "input_date": date.today(),
    "input_author": "",
    "input_purpose": "",
    "field_1": "",
    "field_2": "a. Users:\nb. Management:",
    "field_3": "",
    "field_7_narrative": "",
    "field_8": "",
    "field_9": "",
    "field_10": "",
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# =====================================================================
# SAVE / LOAD PROGRESS
# =====================================================================
st.markdown("#### \U0001F4BE Save / Load Progress")
st.caption(
    "Load a previously saved `.json` draft to restore text fields and images. "
    "Uploading a new image for a step will always override a restored one."
)

col_load, col_reset = st.columns([3, 1])
with col_load:
    draft_file = st.file_uploader("Load a saved draft (.json):", type=["json"], key="draft_uploader")
with col_reset:
    st.write("")
    st.write("")
    if st.button("\U0001F5D1\uFE0F Start New", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
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
            st.session_state.count_sec4 = draft_data.get("count_sec4", 1)
            st.session_state.count_sec5 = draft_data.get("count_sec5", 1)
            st.session_state.count_sec6 = draft_data.get("count_sec6", 1)
            st.session_state.loaded_images = draft_data.get("images", {})
            st.session_state.applied_draft_id = _draft_id
            st.success("Draft loaded \u2014 restoring fields...")
            st.rerun()
        except Exception as e:
            st.error(f"Could not load draft: {e}")

st.divider()

# Metadata Section
st.markdown("#### \U0001F4D3 Document Metadata")
input_doc_title = st.text_input("Document Title:", key="input_doc_title", placeholder="e.g., Sandia-3A1488-01")
col_l, col_m, col_r = st.columns(3)
with col_l: input_template_num = st.text_input("Template #:", key="input_template_num", placeholder="e.g., TMP-002")
with col_m: input_date = st.date_input("Date:", key="input_date")
with col_r: input_author = st.text_input("Author:", key="input_author", placeholder="Initials/Name")
input_purpose = st.text_area("Scope/Purpose:", key="input_purpose", placeholder="Describe the document scope...", height=70)

st.divider()

st.markdown("#### \U0001F4CB Framework Categories")

fields = {}
st.markdown("#### 1. WI Template Number")
fields["1. WI Template Number"] = st.text_area("1. WI Template Number", key="field_1", height=65, label_visibility="collapsed")

st.markdown("#### 2. Responsibilities")
fields["2. Responsibilities"] = st.text_area("2. Responsibilities", key="field_2", height=80, label_visibility="collapsed")

st.markdown("#### 3. Required Tools")
fields["3. Required Tools"] = st.text_area("3. Required Tools", key="field_3", height=80, label_visibility="collapsed")

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
        if s_img is None and st.session_state.loaded_images.get(f"s4_{step_num}"):
            st.caption("\U0001F4CE Using saved image from loaded draft")
    steps_4.append({"text": s_txt, "image": s_img})

col_add4, col_del4, _ = st.columns([1, 1, 1])
with col_add4:
    if st.button("\u2795 Add Next Step", key="btn_add_4", use_container_width=True):
        st.session_state.count_sec4 += 1
        st.rerun()
with col_del4:
    if st.button("\u274C Delete Last Step", key="btn_del_4", use_container_width=True):
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
        if s_img is None and st.session_state.loaded_images.get(f"s5_{step_num}"):
            st.caption("\U0001F4CE Using saved image from loaded draft")
    steps_5.append({"text": s_txt, "image": s_img})

col_add5, col_del5, _ = st.columns([1, 1, 1])
with col_add5:
    if st.button("\u2795 Add Next Step", key="btn_add_5", use_container_width=True):
        st.session_state.count_sec5 += 1
        st.rerun()
with col_del5:
    if st.button("\u274C Delete Last Step", key="btn_del_5", use_container_width=True):
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
        if s_img is None and st.session_state.loaded_images.get(f"s6_{step_num}"):
            st.caption("\U0001F4CE Using saved image from loaded draft")
    steps_6.append({"text": s_txt, "image": s_img})

col_add6, col_del6, _ = st.columns([1, 1, 1])
with col_add6:
    if st.button("\u2795 Add Next Step", key="btn_add_6", use_container_width=True):
        st.session_state.count_sec6 += 1
        st.rerun()
with col_del6:
    if st.button("\u274C Delete Last Step", key="btn_del_6", use_container_width=True):
        if st.session_state.count_sec6 > 1:
            st.session_state.count_sec6 -= 1
            st.rerun()

st.divider()

st.markdown("#### 7. Visuals / Screenshots")
fields["7. Visuals / Screenshots"] = st.text_area("Narrative for Section 7:", key="field_7_narrative", height=70, label_visibility="collapsed")
uploaded_images = st.file_uploader("Upload Figures (JPG/PNG):", accept_multiple_files=True, type=["jpg", "png", "jpeg"])

image_captions = {}
if uploaded_images:
    st.markdown("###### \U0001F4DD Figure Description Captions")
    for idx, img in enumerate(uploaded_images):
        image_captions[img.name] = st.text_input(f"Description for figure ({img.name}):", key=f"cap_{idx}_{img.name}", placeholder="e.g., Highlighted alignment pin verification vector.")
elif st.session_state.loaded_images.get("section7"):
    st.caption(f"\U0001F4CE Using {len(st.session_state.loaded_images['section7'])} saved figure(s) from loaded draft")

st.divider()

st.markdown("#### 8. Safety / Precautions")
fields["8. Safety / Precautions"] = st.text_area("8. Safety / Precautions", key="field_8", height=80, label_visibility="collapsed")

st.markdown("#### 9. Notes / Troubleshooting")
fields["9. Troubleshooting"] = st.text_area("9. Notes / Troubleshooting", key="field_9", height=80, label_visibility="collapsed")

st.markdown("#### 10. Compliance")
fields["10. Compliance"] = st.text_area("10. Compliance", key="field_10", height=80, label_visibility="collapsed", on_change=clear_pdf_cache)

st.divider()

# --- RESOLVE IMAGES (fresh uploads win, otherwise fall back to loaded draft) ---
resolved_steps_4 = resolve_steps(steps_4, "s4")
resolved_steps_5 = resolve_steps(steps_5, "s5")
resolved_steps_6 = resolve_steps(steps_6, "s6")

if uploaded_images:
    resolved_images_7 = []
    for img in uploaded_images:
        img.seek(0)
        b64 = base64.b64encode(img.read()).decode()
        resolved_images_7.append({
            "name": img.name,
            "type": img.type,
            "b64": b64,
            "caption": image_captions.get(img.name, ""),
        })
    st.session_state.loaded_images["section7"] = resolved_images_7
else:
    resolved_images_7 = st.session_state.loaded_images.get("section7", [])


def build_draft_payload():
    values = {
        "input_doc_title": st.session_state.get("input_doc_title", ""),
        "input_template_num": st.session_state.get("input_template_num", ""),
        "input_date": st.session_state.get("input_date", date.today()).isoformat(),
        "input_author": st.session_state.get("input_author", ""),
        "input_purpose": st.session_state.get("input_purpose", ""),
        "field_1": st.session_state.get("field_1", ""),
        "field_2": st.session_state.get("field_2", ""),
        "field_3": st.session_state.get("field_3", ""),
        "field_7_narrative": st.session_state.get("field_7_narrative", ""),
        "field_8": st.session_state.get("field_8", ""),
        "field_9": st.session_state.get("field_9", ""),
        "field_10": st.session_state.get("field_10", ""),
    }
    for prefix, count in [("s4", st.session_state.count_sec4),
                          ("s5", st.session_state.count_sec5),
                          ("s6", st.session_state.count_sec6)]:
        for i in range(count):
            k = f"txt_{prefix}_{i + 1}"
            values[k] = st.session_state.get(k, "")

    return {
        "saved_at": datetime.now().isoformat(),
        "values": values,
        "count_sec4": st.session_state.count_sec4,
        "count_sec5": st.session_state.count_sec5,
        "count_sec6": st.session_state.count_sec6,
        "images": st.session_state.loaded_images,
    }


col_save, col_compile = st.columns(2)

with col_save:
    draft_json = json.dumps(build_draft_payload(), indent=2)
    safe_title = re.sub(r'[^A-Za-z0-9_\-]+', '_', input_doc_title.strip()) or "draft"
    st.download_button(
        "\U0001F4BE SAVE DRAFT (.json)",
        data=draft_json,
        file_name=f"WI_Draft_{safe_title}.json",
        mime="application/json",
        use_container_width=True,
    )

with col_compile:
    compile_button = st.button("\U0001F680 COMPILE TO PDF", use_container_width=True)

if compile_button:
    with st.spinner("Compiling AIS Branded Report..."):
        dynamic_content = generate_pdf_content(fields, resolved_images_7, resolved_steps_4, resolved_steps_5, resolved_steps_6)
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
        st.download_button("\U0001F4E5 DOWNLOAD PDF", data=pdf_buffer.getvalue(), file_name="AIS_Work_Instruction.pdf", mime="application/pdf", use_container_width=True)