# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 09:51:37 2023

@author: AdetoroBayo

To prepare the exe file:
    pyinstaller  PDFMetaViewer.spec


removed from spec:
    datas=[('C:\\Users\\AdetoroBayo\\PycharmProjects\\PDFMetaViewer\\pdf.ico', '.')],
"""

import tkinter as tk
from tkinter import filedialog
from tkinter import font as tkFont
import fitz
from datetime import datetime
from dateparser import parse
from pprint import pformat, pprint
from os import linesep, remove

DATE_FORMAT = '%Y%m%d%H%M%S'


def extract_date(date_string):
    try:
        return datetime.strptime(date_string[2:16], DATE_FORMAT)
    except ValueError:
        return parse(date_string[2:16])


def extract_metadata(file_path):
    doc = fitz.open(file_path)
    pages = doc.page_count
    text = chr(12).join([page.get_text() for page in doc])
    version = doc.version_count
    metadata = doc.metadata
    ocgs = doc.get_ocgs()
    return pages, version, metadata, ocgs, text


def analyze_layers(ocgs):
    return f"\nNumber of Layers: {len(ocgs)}\n" + pformat(ocgs, width=40)


def split_and_save_valid_pdfs(file_path):
    try:
        with open(file_path, 'rb') as original_file:
            pdf_content = original_file.read()

        eof_marker = b'%%EOF'
        eof_positions = [pos for pos in find_all(pdf_content, eof_marker)]

        if not eof_positions:
            print(f"No '%%EOF' marker found in the PDF file '{file_path}'.")
            return

        valid_pdfs = []
        ver = 0

        for i, eof_position in enumerate(eof_positions):
            start_position = 0
            ver += 1
            end_position = eof_position + len(eof_marker)

            output_file_path = f"{file_path[:-4]}_original.pdf"
            with open(output_file_path, 'wb') as output_file:
                output_file.write(pdf_content[start_position:end_position])

            # Validate the generated PDF file
            if is_valid_pdf(output_file_path):
                valid_pdfs.append(output_file_path)
                print(f"The generated PDF file '{output_file_path}' is valid.")
                break
            else:
                print(f"The generated PDF file '{output_file_path}' is not valid and will not be saved.")
                # Remove the invalid file
                remove(output_file_path)

        print(f"{len(eof_positions)} versions in total were discovered.")
        print(f"Valid PDF saved: {valid_pdfs}")

    except Exception as e:
        print(f"Error: {e}")


def is_valid_pdf(file_path):
    try:
        with fitz.open(file_path) as pdf_doc:
            if pdf_doc.page_count > 0:
                return True
            else:
                print(f"The PDF document '{file_path}' is empty.")
                return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1:
            return
        yield start
        start += len(sub)


def open_pdf():
    flag = 'Unlikely'
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])

    if file_path:
        pages, version, metadata, ocgs, text = extract_metadata(file_path)
        formatted_metadata = pformat(metadata, width=40)
        formatted_layers = analyze_layers(ocgs)

        if len(ocgs) > 0:
            full_metadata = formatted_metadata + linesep + formatted_layers
        else:
            full_metadata = formatted_metadata

        # pprint(metadata)

        created_date = extract_date(metadata.get("creationDate", "N/A"))
        modified_date = extract_date(metadata.get("modDate", "N/A"))
        producer_data = metadata.get("producer", "N/A")

        pages_count_label.config(text=f"Pages Count: {pages}")
        doc_version_label.config(text=f"Document Version: {version}")
        doc_layers_label.config(text=f'Number of Layers: {len(ocgs)}')

        doc_version_label.config(fg="black")  # Set to the default text color
        doc_layers_label.config(fg="black")  # Set to the default text color
        created_date_label.config(fg="black")
        modified_date_label.config(fg="black")
        modified_doc_label.config(fg="black")
        scanned_label.config(fg="black")

        if created_date != modified_date or created_date is None:
            created_date_label.config(fg="orange")
            modified_date_label.config(fg="orange")
            flag = 'Review with an Underwriter before proceeding'
            modified_doc_label.config(fg="red")
        if version > 1:
            doc_version_label.config(text=f"Document Version: {version}. (Original file generated)")
            doc_version_label.config(fg="red")  # Set the text color to red
            flag = 'Very Likely'
            modified_doc_label.config(fg="red")
            split_and_save_valid_pdfs(file_path)
        if any(keyword in producer_data for keyword in ["Printer", "Corel", "Distiller", "Acrobat", "Print To PDF",
                                                        "Microsoft"]):
            flag = 'Very Likely'
            modified_doc_label.config(fg="red")
        if len(ocgs) > 0:
            doc_layers_label.config(fg="red")  # Set the text color to red
            flag = 'Extremely Likely'
            modified_doc_label.config(fg="red")

        if len(text) <= 10:
            scanned_label.config(fg="red")
            scanned_label.config(text=f"Scanned Document: True")
        else:
            scanned_label.config(text=f"Scanned Document: False")

        if version > 1 or len(ocgs) > 0:
            # doc_version_label.config(fg="red")  # Set the text color to red

            # Create a font with bold style
            bold_font = tkFont.nametofont("TkDefaultFont")
            bold_font.configure(weight="bold")
            doc_version_label.config(font=bold_font)  # Set the font to bold
            doc_layers_label.config(font=bold_font)  # Set the font to bold
        else:
            # doc_version_label.config(fg="black")  # Set to the default text color
            normal_font = tkFont.nametofont("TkDefaultFont")
            normal_font.configure(weight="normal")
            doc_version_label.config(font=normal_font)  # Set the font to bold
            doc_layers_label.config(font=normal_font)  # Set the font to bold

        created_date_label.config(text=f"Created Date: {created_date}")
        modified_date_label.config(text=f"Modified Date: {modified_date}")
        modified_doc_label.config(text=f"Possibility of Fraud: {flag}")
        metadata_text.delete(1.0, tk.END)
        metadata_text.insert(tk.END, full_metadata)


root = tk.Tk()
root.title("PDF Metadata Viewer")
root.geometry("600x400")  # Set the width and height of the window

# # Set the path to your ICO or GIF file
# icon_path = "C:\\Users\\AdetoroBayo\\PycharmProjects\\PDFMetaViewer\\pdf.ico"  # Replace with the path to your icon file
#
# # Set the icon for the main window
# root.iconbitmap(icon_path)

open_button = tk.Button(root, text="Open PDF", command=open_pdf)
open_button.pack(pady=10)

pages_count_label = tk.Label(root, text="Pages Count: ")
pages_count_label.pack()

doc_version_label = tk.Label(root, text="Document Version: ")
doc_version_label.pack()

doc_layers_label = tk.Label(root, text="Number of Layers in file: ")
doc_layers_label.pack()

created_date_label = tk.Label(root, text="Created Date: ")
created_date_label.pack()

modified_date_label = tk.Label(root, text="Modified Date: ")
modified_date_label.pack()

scanned_label = tk.Label(root, text="Scanned Document: ")
scanned_label.pack()

modified_doc_label = tk.Label(root, text="Possibility of Fraud: ")
modified_doc_label.pack()

metadata_text = tk.Text(root, wrap=tk.WORD, width=50, height=15)
metadata_text.pack()

root.mainloop()
