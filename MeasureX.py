import os
from google import genai

def pdf_to_pure_latex(pdf_path, output_tex_path):
    print("Initializing Gemini Client...")
    client = genai.Client()
    
    print(f"Uploading '{pdf_path}' to the Gemini File API...")
    uploaded_file = client.files.upload(file=pdf_path)
    
    prompt = (
        "You are an expert LaTeX typesetter. Carefully read the attached PDF document. "
        "Convert its entire layout, text, tables, headers, and mathematical equations into "
        "a fully compilable, clean, and beautifully structured LaTeX (.tex) document. "
        "Do NOT wrap your response in markdown code blocks (like ```latex). Start directly "
        "with \\documentclass and end with \\end{document}."
    )
    
    print("Processing document layout and generating LaTeX code...")
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[uploaded_file, prompt]
    )
    
    with open(output_tex_path, "w", encoding="utf-8") as f:
        f.write(response.text)
        
    print(f"\nSuccess! Your editable LaTeX code has been saved to: {output_tex_path}")

if __name__ == "__main__":
    pdf_input = "academic_paper.pdf"
    tex_output = "document_content.tex"
    
    if os.path.exists(pdf_input):
        pdf_to_pure_latex(pdf_input, tex_output)
    else:
        print(f"Error: '{pdf_input}' not found. Please place the PDF in this directory.")