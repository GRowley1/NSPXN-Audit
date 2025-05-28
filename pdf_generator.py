from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "NSPXN Auto Estimate Review", ln=True, align='C')
        self.ln(10)

def create_pdf(text, upload_dir):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)
    output_path = os.path.join(upload_dir, "ReviewReport.pdf")
    pdf.output(output_path)
    return output_path