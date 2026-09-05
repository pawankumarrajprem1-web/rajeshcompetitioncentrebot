import os
import re
import sys
import subprocess
import shutil
import time
from docxtpl import RichText

def convert_to_pdf(input_file, output_pdf_path):
    """Windows aur Linux / Render Server dono par DOCX/PPTX ko PDF banata hai"""
    abs_input = os.path.abspath(input_file)
    abs_output = os.path.abspath(output_pdf_path)
    abs_outdir = os.path.dirname(abs_output)

    # ==========================================
    # 1. WINDOWS OS (Local VS Code Testing)
    # ==========================================
    if os.name == 'nt':
        # Step A: LibreOffice check
        libre_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            "soffice"
        ]
        for soffice_path in libre_paths:
            try:
                cmd = [soffice_path, "--headless", "--convert-to", "pdf", abs_input, "--outdir", abs_outdir]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                gen_pdf = os.path.splitext(abs_input)[0] + ".pdf"
                if os.path.exists(gen_pdf):
                    if os.path.exists(abs_output) and gen_pdf != abs_output:
                        os.remove(abs_output)
                    if gen_pdf != abs_output:
                        os.rename(gen_pdf, abs_output)
                    return
            except Exception:
                continue

        # Step B: PPTX ke liye PowerPoint COM Automation
        if input_file.lower().endswith(('.pptx', '.ppt')):
            try:
                import comtypes.client
                comtypes.CoInitialize()
                
                powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
                presentation = powerpoint.Presentations.Open(abs_input, WithWindow=False)
                presentation.SaveAs(abs_output, 32)
                presentation.Close()
                powerpoint.Quit()
                
                if os.path.exists(abs_output):
                    return
            except Exception as e:
                print(f"Windows PPT COM Error: {e}")
            finally:
                try: comtypes.CoUninitialize()
                except: pass

        # Step C: DOCX ke liye docx2pdf
        if input_file.lower().endswith(('.docx', '.doc')):
            try:
                from docx2pdf import convert
                convert(abs_input, abs_output)
                if os.path.exists(abs_output):
                    return
            except Exception as e:
                raise Exception(f"DOCX to PDF Error: {str(e)}")

        if not os.path.exists(abs_output):
            raise Exception("Windows पर PDF जनरेट नहीं हो सका। कृपया LibreOffice या MS PowerPoint/Word चेक करें।")

   # ==========================================
    # 2. LINUX / RENDER SERVER (Docker Environment)
    # ==========================================
    else:
        user_profile_dir = os.path.join(abs_outdir, "lo_profile")
        os.makedirs(user_profile_dir, exist_ok=True)
        
        export_filter = "pdf:impress_pdf_Export" if input_file.lower().endswith(('.pptx', '.ppt')) else "pdf:writer_pdf_Export"

        # 👇 PURANE 'cmd = [...]' KO HATA KAR IS NAYE BLOCK KO LAKAR CHIPKAIN 👇
        cmd = [
            "xvfb-run", "-a",
            "libreoffice",
            "--headless",
            "--invisible",
            "--nodefault",
            "--nofirststartwizard",
            "--norestore",
            f"-env:UserInstallation=file://{os.path.abspath(user_profile_dir)}",
            "--convert-to", export_filter,
            abs_input,
            "--outdir", abs_outdir
        ]
        
        env = os.environ.copy()
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
     
        
        if os.path.exists(user_profile_dir):
            shutil.rmtree(user_profile_dir, ignore_errors=True)

        gen_pdf = os.path.splitext(abs_input)[0] + ".pdf"
        if os.path.exists(gen_pdf) and gen_pdf != abs_output:
            if os.path.exists(abs_output):
                os.remove(abs_output)
            os.rename(gen_pdf, abs_output)

        if not os.path.exists(abs_output):
            raise Exception(f"Linux PDF Conversion Failed!\nSTDERR: {result.stderr}")

def parse_raw_text(raw_text):
    questions_list = []
    # Single questions ya multiple questions ko split karein
    q_blocks = re.split(r'\n(?=\s*\d+[\.\)\-])', '\n' + raw_text.strip())
    
    for block in q_blocks:
        if not block.strip(): 
            continue
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines: 
            continue
            
        q_text = re.sub(r'^\d+[\.\)\-]\s*', '', lines[0])
        full_text = "\n".join(lines[1:])
        
        # Flexibly capture options with standard formats (a), A., (A), A) etc.
        opt_a = re.search(r'(?:^|\n|\s*)(?:\([aA]\)|[aA][\.\)\-])\s*(.*?)(?=(?:\([bB]\)|[bB][\.\)\-])|$)', full_text, re.DOTALL)
        opt_b = re.search(r'(?:^|\n|\s*)(?:\([bB]\)|[bB][\.\)\-])\s*(.*?)(?=(?:\([cC]\)|[cC][\.\)\-])|$)', full_text, re.DOTALL)
        opt_c = re.search(r'(?:^|\n|\s*)(?:\([cC]\)|[cC][\.\)\-])\s*(.*?)(?=(?:\([dD]\)|[dD][\.\)\-])|$)', full_text, re.DOTALL)
        opt_d = re.search(r'(?:^|\n|\s*)(?:\([dD]\)|[dD][\.\)\-])\s*(.*?)(?=$)', full_text, re.DOTALL)
        
        # Fallback: Agar options multiline format me bina (a),(b) prefix ke hain
        if not (opt_a or opt_b or opt_c or opt_d) and len(lines) >= 5:
            questions_list.append({
                'text': q_text.strip(),
                'a': lines[1].strip(),
                'b': lines[2].strip(),
                'c': lines[3].strip(),
                'd': lines[4].strip()
            })
        else:
            questions_list.append({
                'text': q_text.strip(),
                'a': opt_a.group(1).strip() if opt_a else '',
                'b': opt_b.group(1).strip() if opt_b else '',
                'c': opt_c.group(1).strip() if opt_c else '',
                'd': opt_d.group(1).strip() if opt_d else ''
            })
            
    return questions_list

def format_docx_option(label, opt_text, show_answer=False):
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
