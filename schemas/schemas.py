from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ---------------- AUTH ----------------

class DoctorCreate(BaseModel):
    username: str
    email: str
    password: str


class DoctorLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class DoctorMini(BaseModel):

    id: int
    username: str
    full_name: str
    department: str

    class Config:
        from_attributes = True


# ---------------- PATIENT ----------------

class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str


class PatientOut(BaseModel):
    id: int
    name: str
    age: int
    gender: str

    class Config:
        from_attributes = True


class HistoryPatientOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# ---------------- HISTORY ----------------

class HistoryOut(BaseModel):
    id: int
    image_url: str
    gradcam_url: str
    eye_side: str
    created_at: datetime

    disease: str
    confidence: float

    patient: HistoryPatientOut

    class Config:
        from_attributes = True


# ---------------- DOCTOR RESPONSE ----------------

class DoctorResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: str

    department: Optional[str]
    license_number: Optional[str]
    role: Optional[str]
    experience_years: Optional[int]
    rating: Optional[int]
    scans: Optional[str]

    history: List[HistoryOut] = []

    class Config:
        from_attributes = True


# ---------------- PROFILE RESPONSE ----------------

class DoctorProfile(BaseModel):
    username: str
    full_name: str
    email: str
    number_of_patients: int

    department: Optional[str]
    role: Optional[str]
    experience_years: Optional[int]
    scans: Optional[str]

    class Config:
        from_attributes = True


# ---------------- MESSAGE RESPONSE ----------------

class MessageResponse(BaseModel):
    message: str
