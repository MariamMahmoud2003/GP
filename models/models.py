from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship

from database.database import Base

import datetime


# ---------------- DOCTOR ----------------

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    department = Column(String)
    license_number = Column(String)
    role = Column(String)
    experience_years = Column(Integer)
    rating = Column(Integer, default=0)  #
    scans = Column(String, nullable=True)
    history = relationship("History", back_populates="doctor")


# ---------------- HISTORY ----------------

class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String)
    gradcam_url = Column(String, nullable=True)
    created_at = Column(
        DateTime,
        default=datetime.datetime.utcnow
    )

    eye_side = Column(String)

    disease = Column(String)
    confidence = Column(Float)
    percentage = Column(Integer)

    # doctor relation
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    doctor = relationship("Doctor", back_populates="history")

    # patient relation
    patient_id = Column(Integer, ForeignKey("patients.id"))
    patient = relationship("Patient", back_populates="history")


# ---------------- PATIENT ----------------

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    age = Column(Integer)
    gender = Column(String)

    history = relationship("History", back_populates="patient")
