import os
import re
import subprocess
import shutil
from docxtpl import RichText

def convert_to_pdf(input_file, output_dir="."):
    """Linux / Render Server (Enhanced Error Logging & Explicit Path)"""
    abs_input = os.path.abspath(input_file)
    abs_outdir = os.path.abspath(output_dir)
    out_name = os.path.basename(input_file).rsplit('.', 1)[0] + '.pdf'
    abs_output = os.path.join(abs_outdir, out_name)

    if os.name == 'nt':  # Windows
        libre_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            "soffice"
        ]
        for soffice_path in libre_paths:
            try:
                cmd = [soffice_path, "--headless", "--convert-to", "pdf", abs_input, "--outdir", abs_outdir]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if os.path.exists(abs_output):
                    return
            except Exception:
                continue

        if input_file.endswith('.docx'):
            try:
                from docx2pdf import convert
                convert(abs_input, abs_output)
                return
            except Exception as e:
                raise Exception(f"DOCX to PDF Error: {str(e)}")

        raise Exception("Windows पर PDF जनरेट नहीं हो सका।")

    else:  # Linux / Render Server
        user_profile_dir = os.path.join(abs_outdir, "lo_profile")
        os.makedirs(user_profile_dir, exist_ok=True)
        
        # xvfb-run को कमांड के आगे जोड़ा गया है
        cmd = [
            "xvfb-run",
            "--auto-servernum",
            "libreoffice",
            "--headless",
            "--invisible",
            "--nodefault",
            "--nofirststartwizard",
            "--norestore",
            f"-env:UserInstallation=file://{os.path.abspath(user_profile_dir)}",
            "--convert-to", "pdf",
            abs_input,
            "--outdir", abs_outdir
        ]
        
        env = os.environ.copy()
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if not os.path.exists(abs_output):
            stdout_msg = result.stdout.strip() if result.stdout else "None"
            stderr_msg = result.stderr.strip() if result.stderr else "None"
            raise Exception(f"PDF Conversion Failed!\nSTDOUT: {stdout_msg}\nSTDERR: {stderr_msg}")
        
        # 4. यदि PDF जनरेट नहीं हुआ तो Logs निकालें
        if not os.path.exists(abs_output):
            stdout_msg = result.stdout.strip() if result.stdout else "None"
            stderr_msg = result.stderr.strip() if result.stderr else "None"
            exit_code = result.returncode
            
            raise Exception(
                f"PDF Conversion Failed!\n"
                f"▪ Exit Code: {exit_code}\n"
                f"▪ Input File Exists: {os.path.exists(abs_input)}\n"
                f"▪ STDOUT: {stdout_msg}\n"
                f"▪ STDERR: {stderr_msg}"
            )

def parse_raw_text(raw_text):
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
