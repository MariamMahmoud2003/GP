from database.database import SessionLocal
from models.models import Doctor
from core.auth import hash_password

db = SessionLocal()

# create doctor manually
doctors = [
    Doctor(
        username="doc1",
        full_name="Doctor One",
        email="doc1@test.com",
        hashed_password=hash_password("123"),
        department="Cardiology",
        license_number="LIC-101",
        role="doctor",
        experience_years=5,
        rating=4
    ),
    Doctor(
        username="doc2",
        full_name="Doctor Two",
        email="doc2@test.com",
        hashed_password=hash_password("456"),
        department="Neurology",
        license_number="LIC-202",
        role="doctor",
        experience_years=8,
        rating=5
    )
]

db.add_all(doctors)
db.commit()
db.close()

print("Doctor added successfully")
