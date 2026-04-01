from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import time
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.startup import startup_checks, log_startup_info
from app.api.routes import auth, projects, repos, deploy, payments
from app.db.client import supabase_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Run startup checks and warnings
    startup_checks()
    log_startup_info()
    
    # Test database connection
    try:
        # Simple connection test
        result = await supabase_client.select_records('users', {}, columns='count(*)')
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Xenitide - Student All-in-One Development Platform API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} - "
            f"Time: {process_time:.4f}s - "
            f"URL: {request.url}"
        )
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Error: {str(e)} - "
            f"Time: {process_time:.4f}s - "
            f"URL: {request.url}"
        )
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)} - URL: {request.url}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "type": "internal_error",
                "request_id": str(id(request))
            }
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    try:
        # Test database connection
        db_status = "healthy"
        try:
            await supabase_client.select_records('users', {}, columns='count(*)')
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "timestamp": time.time(),
            "database": db_status,
            "services": {
                "supabase": "connected" if db_status == "healthy" else "disconnected",
                "xendit": "connected" if settings.XENDIT_SECRET_KEY else "not_configured"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "Documentation not available in production",
        "health": "/health"
    }


# API routes
app.include_router(
    auth.router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(
    projects.router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(
    repos.router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(
    deploy.router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(
    payments.router,
    prefix=settings.API_V1_PREFIX,
)


# Static files (if needed)
# app.mount("/static", StaticFiles(directory="static"), name="static")


# Custom 404 handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "message": "Resource not found",
                "type": "not_found",
                "path": str(request.url.path)
            }
        }
    )


# Custom validation error handler
@app.exception_handler(422)
async def validation_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "message": "Validation error",
                "type": "validation_error",
                "details": exc.detail
            }
        }
    )


# Development-only endpoints
if settings.DEBUG:
    @app.get("/debug/info")
    async def debug_info():
        """
        Debug information endpoint (development only)
        """
        return {
            "settings": {
                "app_name": settings.APP_NAME,
                "debug": settings.DEBUG,
                "supabase_url": settings.SUPABASE_URL,
                "xendit_configured": bool(settings.XENDIT_SECRET_KEY),
                "cors_origins": settings.BACKEND_CORS_ORIGINS
            },
            "environment": "development"
        }
    
    @app.post("/debug/test-db")
    async def test_database():
        """
        Test database connection (development only)
        """
        try:
            # Test various tables
            tables = ['users', 'projects', 'repositories', 'deployments', 'payment_links']
            results = {}
            
            for table in tables:
                try:
                    result = await supabase_client.select_records(table, {}, columns='count(*)')
                    results[table] = {
                        "status": "ok",
                        "count": len(result.data) if result.data else 0
                    }
                except Exception as e:
                    results[table] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            return {
                "database": "connected",
                "tables": results
            }
        except Exception as e:
            return {
                "database": "error",
                "error": str(e)
            }


# Production startup checks
if not settings.DEBUG:
    @app.on_event("startup")
    async def production_startup_checks():
        """
        Production startup checks
        """
        required_env_vars = [
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "JWT_SECRET_KEY"
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not getattr(settings, var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            raise RuntimeError(f"Missing required environment variables: {missing_vars}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
