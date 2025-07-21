from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from models.schemas import PaymentRequest, PaymentResponse
from models.database import create_tables, get_db
from api.payments import router as payments_router
from api.auth import router as auth_router
from api.webhooks import router as webhooks_router
from api.health import router as health_router
from utils.rate_limiter import limiter, rate_limit_middleware
from utils.monitoring import monitoring_middleware, health_checker, get_metrics
from slowapi.errors import RateLimitExceeded
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("payment_gateway")

# Create FastAPI app
app = FastAPI(
    title="All1ZED Payment Gateway",
    description="Handles mobile money payments through Konik SOAP gateway with authentication, webhooks, and analytics",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_middleware)

# Add monitoring middleware
app.middleware("http")(monitoring_middleware)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting All1ZED Payment Gateway...")
    create_tables()
    logger.info("✅ Database tables created")

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    db = next(get_db())
    
    health_status = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "2.0.0",
        "checks": {
            "database": health_checker.check_database_connection(db),
            "external_services": health_checker.check_external_services(),
            "system": health_checker.get_system_health()
        }
    }
    
    # Check if any service is unhealthy
    for check_name, check_result in health_status["checks"].items():
        if check_result.get("status") == "unhealthy":
            health_status["status"] = "unhealthy"
            break
    
    return health_status

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics()

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "All1ZED Payment Gateway API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }

# Legacy endpoints for backward compatibility
@app.post("/payments/initiate", response_model=PaymentResponse, deprecated=True)
def legacy_initiate_payment(request: PaymentRequest):
    """Legacy payment endpoint (deprecated)"""
    logger.warning("⚠️ Using deprecated legacy endpoint")
    raise HTTPException(
        status_code=400, 
        detail="This endpoint is deprecated. Please use /api/v1/payments/initiate with API key authentication."
    )

@app.get("/payments/query/{payment_reference}", deprecated=True)
def legacy_query_status(payment_reference: str):
    """Legacy query endpoint (deprecated)"""
    logger.warning("⚠️ Using deprecated legacy endpoint")
    raise HTTPException(
        status_code=400, 
        detail="This endpoint is deprecated. Please use /api/v1/payments/query/{payment_reference} with API key authentication."
    )

@app.get("/payments/balance", deprecated=True)
def legacy_get_balance():
    """Legacy balance endpoint (deprecated)"""
    logger.warning("⚠️ Using deprecated legacy endpoint")
    raise HTTPException(
        status_code=400, 
        detail="This endpoint is deprecated. Please use /api/v1/payments/balance with API key authentication."
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)