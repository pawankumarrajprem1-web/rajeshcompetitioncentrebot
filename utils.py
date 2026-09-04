import os
import re
import subprocess
from docxtpl import RichText

def convert_to_pdf(input_file, output_dir="."):
    """Windows और Linux/Render के लिए कनवर्टर"""
    abs_input = os.path.abspath(input_file)
    out_name = os.path.basename(input_file).rsplit('.', 1)[0] + '.pdf'
    abs_output = os.path.abspath(os.path.join(output_dir, out_name))

    if os.name == 'nt':  # Windows PC
        libre_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            "soffice"
        ]
        for soffice_path in libre_paths:
            try:
                cmd = [soffice_path, "--headless", "--convert-to", "pdf", abs_input, "--outdir", output_dir]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if os.path.exists(abs_output):
                    return
            except Exception:
                continue

        if input_file.endswith('.pptx') or input_file.endswith('.ppt'):
            try:
                import win32com.client
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                except Exception:
                    pass
                
                powerpoint = win32com.client.Dispatch("PowerPoint.Application")
                deck = powerpoint.Presentations.Open(abs_input, WithWindow=False)
                deck.SaveAs(abs_output, 32)
                deck.Close()
                return
            except Exception:
                raise Exception("Windows पर PPT को PDF बनाने के लिए MS PowerPoint का होना आवश्यक है!")

        if input_file.endswith('.docx'):
            try:
                from docx2pdf import convert
                convert(abs_input, abs_output)
                return
            except Exception as e:
                raise Exception(f"DOCX to PDF Error: {str(e)}")

        raise Exception("PDF कनवर्टर फ़ाइल जनरेट करने में असमर्थ रहा।")
    else:  # Linux / Render Server (Clean CLI Fix)
        cmd = [
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            abs_input,
            "--outdir", output_dir
        ]
        
        env = os.environ.copy()
        env["SAL_USE_VCLPLUGIN"] = "gen"
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode != 0 or not os.path.exists(abs_output):
            raise Exception(f"LibreOffice Error: {result.stderr or result.stdout}")

def parse_raw_text(raw_text):
    """प्रश्न और विकल्पों को अलग-अलग पार्स करता है"""
    questions_list = []
    q_blocks = re.split(r'\n(?=\s*\d+[\.\)\-])', '\n' + raw_text.strip())
    
    for block in q_blocks:
        if not block.strip(): 
            continue
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines: 
            continue
            
        q_text = re.sub(r'^\d+[\.\)\-]\s*', '', lines[0])
        full_text = "\n".join(lines[1:])
        
        opt_a = re.search(r'(?:^|\n|\s*)(?:\(a\)|a[\.\)\-])\s*(.*?)(?=(?:\(b\)|b[\.\)\-])|$)', full_text, re.DOTALL | re.IGNORECASE)
        opt_b = re.search(r'(?:^|\n|\s*)(?:\(b\)|b[\.\)\-])\s*(.*?)(?=(?:\(c\)|c[\.\)\-])|$)', full_text, re.DOTALL | re.IGNORECASE)
        opt_c = re.search(r'(?:^|\n|\s*)(?:\(c\)|c[\.\)\-])\s*(.*?)(?=(?:\(d\)|d[\.\)\-])|$)', full_text, re.DOTALL | re.IGNORECASE)
        opt_d = re.search(r'(?:^|\n|\s*)(?:\(d\)|d[\.\)\-])\s*(.*?)(?=$)', full_text, re.DOTALL | re.IGNORECASE)
        
        questions_list.append({
            'text': q_text.strip(),
            'a': opt_a.group(1).strip() if opt_a else '',
            'b': opt_b.group(1).strip() if opt_b else '',
            'c': opt_c.group(1).strip() if opt_c else '',
            'd': opt_d.group(1).strip() if opt_d else ''
        })
    return questions_list

def format_docx_option(label, opt_text, show_answer=False):
    """DOCX फ़ाइल में सही उत्तर को Bold करने का फ़ंक्शन"""
    if not opt_text: 
        return ""
    rt = RichText()
    is_answer = "✅" in opt_text or "*" in opt_text
    cleaned = opt_text.replace("✅", "").replace("*", "").strip()
    
    if show_answer and is_answer:
        rt.add(f"{label} {cleaned}", bold=True)
    else:
        rt.add(f"{label} {cleaned}", bold=False)
    return rt
