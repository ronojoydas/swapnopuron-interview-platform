
from fastapi import FastAPI

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
