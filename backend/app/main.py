import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    auth,
    opportunities,
    candidates,
    applications,
    interviews,
    feedback,
)

app = FastAPI(
    title="Swapnopuron Recruitment & Interview Platform",
    description="Recruitment and interview management API for Swapnopuron",
    version="0.1.0",
)

# Allow local development and configured production frontend origins.
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

configured_origins = os.getenv("FRONTEND_ORIGINS", "")
frontend_origins = [
    origin.strip().rstrip("/")
    for origin in configured_origins.split(",")
    if origin.strip()
]

allowed_origins = list(dict.fromkeys(default_origins + frontend_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers.
app.include_router(auth.router)
app.include_router(opportunities.router)
app.include_router(candidates.router)
app.include_router(applications.router)
app.include_router(interviews.router)
app.include_router(feedback.router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Swapnopuron Recruitment Platform",
    }
