"""
ATO Shield v2 - FastAPI Application Entry Point
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from store.database import engine, Base
import api.websocket as websocket
from api.routes import transactions, cases, decisions
from dashboard.routes import router as dashboard_router
from simulator.routes import router as simulator_router

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state for ML engine health
ml_engine_healthy = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    global ml_engine_healthy
    
    # Startup: Create database tables and verify ML engine
    logger.info("🚀 Starting ATO Shield v2...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables verified")
    
    # Test ML engine availability
    try:
        from engine.scorer import get_scorer_singleton
        from engine.explainer import get_explainer_singleton
        
        scorer = get_scorer_singleton()
        explainer = get_explainer_singleton()
        ml_engine_healthy = True
        logger.info("✅ ML engine loaded successfully")
    except FileNotFoundError as e:
        ml_engine_healthy = False
        logger.warning(f"⚠️  ML engine not available: {str(e)}")
        logger.warning("⚠️  Transaction scoring will fail until models are trained")
    except Exception as e:
        ml_engine_healthy = False
        logger.error(f"❌ Error loading ML engine: {str(e)}")
    
    logger.info("✅ ATO Shield v2 ready")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down ATO Shield v2...")


app = FastAPI(
    title="ATO Shield v2",
    description="Fraud Analyst Workstation API",
    version="2.0.0",
    lifespan=lifespan
)

# Mount static files for dashboard
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

# Include API routers
app.include_router(transactions.router, prefix="/api/v1", tags=["transactions"])
app.include_router(cases.router, prefix="/api/v1", tags=["cases"])
app.include_router(decisions.router, prefix="/api/v1", tags=["decisions"])
from api.routes import dashboard_stats
app.include_router(dashboard_stats.router, prefix="/api/v1", tags=["dashboard"])

# Include dashboard routes
app.include_router(dashboard_router)

# Include simulator routes
app.include_router(simulator_router, prefix="/simulate", tags=["simulator"])

# WebSocket manager
app.include_router(websocket.router)


@app.get("/health")
async def health_check():
    """Health check endpoint with ML engine status"""
    return {
        "status": "ok" if ml_engine_healthy else "degraded",
        "ml_engine": "loaded" if ml_engine_healthy else "not_available",
        "database": "connected"
    }


@app.get("/")
async def root():
    """Root redirect to dashboard"""
    return {"message": "ATO Shield v2 API - Visit /dashboard to access the workstation"}
