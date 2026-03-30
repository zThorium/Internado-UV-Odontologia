from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.limiter import limiter
from app.routers import auth, logbook, incidents, evaluations, dashboard
from app.routers import attendance
from app.routers import alerts

app = FastAPI(title="Internado Odontología UV API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Privacy policy:
# - /logbook/*   → student, coordinator only (tutor blocked)
# - /incidents/* → student, coordinator only (tutor blocked)
# - /evaluations/my-students, POST /evaluations → tutor only
# - /evaluations/students/{id} → student, tutor, coordinator
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(logbook.router, prefix="/logbook", tags=["logbook"])
app.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
app.include_router(evaluations.router, prefix="/evaluations", tags=["evaluations"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
