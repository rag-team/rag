import os
from fastapi import FastAPI, UploadFile, File, Response

app = FastAPI()

@app.post("/upload-file/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Ensure the directory for storing files exists, if not create it
        os.makedirs("uploads", exist_ok=True)

        # Save the uploaded file to the "uploads" directory with the original name
        with open(os.path.join("uploads", file.filename), "wb") as buffer:
            buffer.write(await file.read())

        return Response(content=f"File {file.filename} uploaded successfully", status_code=200)
    except Exception as e:
        return Response(content=f"Failed to upload file: {e}", status_code=500)
