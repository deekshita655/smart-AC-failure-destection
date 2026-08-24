import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.core.database import Base, engine
from app.utils.responses import APIError, error_body, new_request_id
import app.models
from app.api.routes import (auth, users, devices, service_tickets, images, ocr, ai_analysis, embeddings, comparison,
    device_analytics, manufacturer_analytics, role_analytics, sensors, predictive, preventive_tickets, chatbot,
    powerbi, health, audit, ml)

app = FastAPI(title="Smart AC Failure Intelligence & Predictive Maintenance API", version="0.1.0",
    description="Backend for the Smart AC Failure Intelligence and Predictive Maintenance platform.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def on_startup(): Base.metadata.create_all(bind=engine)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4()); response = await call_next(request); response.headers["X-Request-ID"] = request.state.request_id; return response

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    from fastapi.responses import JSONResponse
    rid = getattr(request.state, "request_id", new_request_id()); return JSONResponse(status_code=exc.status_code, content=error_body(exc, rid))

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    from fastapi.responses import JSONResponse
    rid = getattr(request.state, "request_id", new_request_id())
    return JSONResponse(status_code=422, content={"success": False, "error": {"code": "VALIDATION_ERROR", "message": "Request validation failed.", "retryable": False, "details": exc.errors()}, "request_id": rid})

for router in [auth.router, users.router, devices.router, service_tickets.router, images.router, ocr.router, ai_analysis.router,
    embeddings.router, comparison.router, device_analytics.router, manufacturer_analytics.router, role_analytics.router,
    sensors.router, predictive.router, preventive_tickets.router, chatbot.router, powerbi.router, health.router, audit.router, ml.router]:
    app.include_router(router, prefix="/api/v1")
