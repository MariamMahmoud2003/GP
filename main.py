import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from controllers.doctor_controller import (
    router as doctor_router
)

from controllers.upload import (
    router as upload_router
)

from controllers.generate_report import (
    router as history_router
)

from models.models import Base
from database.database import engine


Base.metadata.create_all(bind=engine)

app = FastAPI()

os.makedirs("uploads", exist_ok=True)

# ---------------- ROUTERS ----------------

app.include_router(doctor_router)

app.include_router(upload_router)

app.include_router(history_router)


# ---------------- STATIC FILES ----------------

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)

app.mount(
    "/uploads",
    StaticFiles(directory="reports"),
    name="reports"
)
