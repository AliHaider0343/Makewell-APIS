import base64
import imghdr
import PyPDF2
import tempfile
import os
import requests
import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_file):
    pdf_file=download_file(pdf_file)
    # Open the provided PDF file
    pdf_document = fitz.open(pdf_file)
    text = ""
    # Iterate through each page of the PDF
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        page_text = page.get_text()
        text += page_text
    pdf_document.close()

    return text

def download_file(url):
    # Function to download file from URL
    response = requests.get(url)
    if response.status_code == 200:
        temp_dir = tempfile.mkdtemp()
        file_name = url.split('/')[-1]  # Extract file name from URL
        file_path = os.path.join(temp_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(response.content)
        return file_path
    else:
        raise ValueError(f"Failed to download file from URL: {url}")



def encode_image(image_path):
    image_path=download_file(image_path)
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def save_file_to_temp(file, filename: str):
    # Save the file to a temporary directory and return the path
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, filename)
    with open(file_path, "wb") as f:
        for chunk in iter(lambda: file.read(4096), b""):
            f.write(chunk)
    return file_path

def is_image_or_pdf(file) -> str:
    # Check if file is an image or PDF
    image_formats = ["jpeg", "png", "gif", "bmp"]
    image_type = imghdr.what(file.file)
    if image_type in image_formats:
        return "image"

    file.seek(0)  # Reset file pointer for PyPDF2
    try:

        if ".pdf" in file.filename:
            return "pdf"
    except:
        pass

    return None