import os

import requests
from werkzeug.http import parse_options_header

URL = "http://localhost:8000/fill-pdf/"
FILE = "1623_102_lab_rotation_formular_20170512.pdf"

with open(FILE, "rb") as f:
    file_content = f.read()

files = {"file": (os.path.basename(FILE), file_content)}
response = requests.post(URL, files=files, json={"Mat. No.": "123"})
print(response.status_code)
if response.status_code == 200:
    if response.headers.get("Content-Type") == "application/pdf" and (
        content_disposition := response.headers.get("content-disposition")
    ):
        _, cd = parse_options_header(content_disposition)
        print(f"PDF downloaded, saving to {cd['filename']}")
        with open(cd["filename"], "wb+") as f:
            f.write(response.content)
    else:
        print(response.text)
else:
    print(response.reason)
    if content := response.content:
        print(content.decode())
