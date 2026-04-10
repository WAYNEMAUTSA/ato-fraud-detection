"""
ATO Shield v2 - FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from store.database import engine, Base
import api.websocket as websocket
from api.routes import transactions, cases, decisions
from dashboard.routes import router as dashboard_router

# Create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ATO Shield v2",
    description="Fraud Analyst Workstation API",
    version="2.0.0"
)

# Mount static files for dashboard
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

# Include API routers
app.include_router(transactions.router, prefix="/api/v1", tags=["transactions"])
app.include_router(cases.router, prefix="/api/v1", tags=["cases"])
app.include_router(decisions.router, prefix="/api/v1", tags=["decisions"])

# Include dashboard routes
app.include_router(dashboard_router)

# WebSocket manager
app.include_router(websocket.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root redirect to dashboard"""
    return {"message": "ATO Shield v2 API - Visit /dashboard to access the workstation"}
