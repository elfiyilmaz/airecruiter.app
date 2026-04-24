import PyPDF2
import docx


def extract_text(file):
    """
    FR2: PDF veya DOCX formatındaki CV'lerden metin ayıklar.
    """
    text = ""
    # PDF İşleme
    if file.name.endswith('.pdf'):
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()

    # DOCX İşleme
    elif file.name.endswith('.docx'):
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text

    return text.strip()