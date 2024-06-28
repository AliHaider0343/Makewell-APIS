from fastapi.responses import JSONResponse
from typing import List,Optional, Dict
from CloudServices import upload_file
from FileUtils import encode_image, is_image_or_pdf, save_file_to_temp, extract_text_from_pdf
from OpenAIServices import extract_information_from_image, extract_data_and_schedule_appointment_followup
from fastapi import FastAPI, UploadFile, File, Query,HTTPException
from fastapi.middleware.cors import CORSMiddleware
import speech_recognition as sr
import tempfile
import os
from agent import generate_response
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
from sqlalchemy.sql import func

engine = create_engine('sqlite:///database.db')  # Replace with your database URL
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Define your table schema
class leads_and_followup_status(Base):
    __tablename__ = 'leads_and_followup_status'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))  # Using UUID as string
    hcf_id=Column(String)
    appointment_status = Column(String)
    status_message = Column(String)
    username = Column(String)
    email_address = Column(String)
    medical_procedures_name = Column(String)
    preferred_country = Column(String)
    preferred_city = Column(String)
    important_concerns = Column(String)
    preferred_date = Column(String)
    summary = Column(String)
    added_at = Column(DateTime, default=func.now())

Base.metadata.create_all(engine)

class ChatRequest(BaseModel):
    question: str
    chat_history: Optional[List[Dict[str, str]]] = None

class ScheduleRequest(BaseModel):
    hcf_id: str
    chat_history: str


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    result=generate_response(request.question,request.chat_history)
    response_message = "Message Returned successfully."
    return JSONResponse(content={"message": response_message, "answer": result})

@app.post("/upload_files/")
async def upload_files(files: List[UploadFile] = File(...)):
    images_public_url = []
    pdfs_public_url = []

    for file in files:
        file_type = is_image_or_pdf(file)
        file_name = file.filename
        if file_type == "image":
            file_path = save_file_to_temp(file.file, "image")
            images_public_url.append(upload_file(file_path, file_name))
        elif file_type == "pdf":
            file_path = save_file_to_temp(file.file, "pdf")
            pdfs_public_url.append(upload_file(file_path, file_name))
        else:
            raise HTTPException(status_code=400, detail=f"File {file.filename} is neither an image nor a PDF.")

    medical_records_context = ""
    if len(images_public_url) > 0 or len(pdfs_public_url) > 0:
        medical_records_context += "<Medical Records>\n"

        if len(images_public_url) > 0:
            for image in images_public_url:
                base64_image = encode_image(image)
                if base64_image:
                    medical_records_context += extract_information_from_image(base64_image)

        if len(pdfs_public_url) > 0:
            for pdf in pdfs_public_url:
                medical_records_context += extract_text_from_pdf(pdf)

        medical_records_context += "\n<Medical Records>\n"

    response_message = "Files uploaded and processed successfully."

    return JSONResponse(content={"message": response_message, "medical_history_text": medical_records_context})

@app.post("/speech-to-text/")
async def speech_to_text(file: UploadFile = File(...)):
    if file.content_type.startswith('audio'):
        recognizer = sr.Recognizer()
        audio_data = await file.read()

        # Create a temporary file to store the uploaded audio data
        with tempfile.NamedTemporaryFile(delete=False) as temp_audio_file:
            temp_audio_file.write(audio_data)
            temp_audio_file_path = temp_audio_file.name

        try:
            # Use the temporary file path to create the AudioFile object
            with sr.AudioFile(temp_audio_file_path) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio)
                return {"text": text}

        except sr.UnknownValueError:
            raise HTTPException(status_code=400, detail="Unable to recognize speech")

        except sr.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error from Google Speech Recognition service: {e}")

        finally:
            # Clean up: delete the temporary audio file after use
            if temp_audio_file_path:
                os.remove(temp_audio_file_path)

    else:
        raise HTTPException(status_code=400, detail="Only audio files are allowed.")

@app.post("/schedule-appointment/")
async def schedule_appointment(request:ScheduleRequest):
    return {"response":extract_data_and_schedule_appointment_followup(request.chat_history,request.hcf_id,session,leads_and_followup_status)}

@app.get("/leads_and_followup_status/")
async def read_leads_and_followup_status():
    entries = session.query(leads_and_followup_status).all()
    if entries:
        return {"status": "ok", "message": "All leads and followups data have been returned successfully.",
                "data": {"leads_and_followups_data": entries}}
    else:
        raise HTTPException(status_code=404, detail="No leads and followups data Found.")

@app.get("/leads_and_followup_status/{hcf_id}")
async def read_leads_by_hcf_id(hcf_id: str):
    entries = session.query(leads_and_followup_status).filter(leads_and_followup_status.hcf_id == hcf_id).all()
    if entries:
        return {"status": "ok", "message": "All leads and followups data have been returned successfully.",
                "data": {"leads_and_followups_data": entries}}
    else:
        raise HTTPException(status_code=404, detail="No leads and followups data Found.")