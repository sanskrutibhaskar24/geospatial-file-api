from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path
import uuid
import shutil

from app.services import process_geospatial_file

app = FastAPI(
    title="Geospatial File Measurement API",
    version="1.0.0"
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

files_db = {}


@app.get("/")
def root():
    return {"message": "Geospatial File Measurement API is running"}


@app.post("/api/files/")
async def upload_file(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(400, "No file provided.")

    if not (
        file.filename.lower().endswith(".kml")
        or file.filename.lower().endswith(".zip")
    ):
        raise HTTPException(400, "Only .kml and .zip files are supported.")

    file_id = str(uuid.uuid4())
    extension = Path(file.filename).suffix.lower()
    saved_path = UPLOAD_DIR / f"{file_id}{extension}"

    with saved_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = process_geospatial_file(saved_path)
    except Exception as e:
        raise HTTPException(400, f"File processing failed: {str(e)}")

    response = {
        "id": file_id,
        "filename": file.filename,
        "status": "COMPLETED",
        **result
    }

    files_db[file_id] = response

    return response


@app.get("/api/files/{file_id}/")
def get_file(file_id: str):

    if file_id not in files_db:
        raise HTTPException(404, "File not found.")

    return files_db[file_id]


@app.get("/api/files/{file_id}/measurements/")
def get_measurements(file_id: str):

    if file_id not in files_db:
        raise HTTPException(404, "File not found.")

    data = files_db[file_id]

    return {
        "id": file_id,
        "filename": data["filename"],
        "measurements": [
            {
                "feature_id": feature["feature_id"],
                "geometry_type": feature["geometry_type"],
                "measurement": feature["measurement"]
            }
            for feature in data["features"]
        ]
    }