"""
Jan Suraksha Backend - Main FastAPI Application
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time
from datetime import datetime
from pathlib import Path
from app.database import engine, Base
from app.routers import (
    auth_router,
    workers_router,
    companies_router,
    police_router,
    verification_router,
    admin_router
)

print("\n" + "="*80)
print("JAN SURAKSHA BACKEND STARTING")
print("="*80)
print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")

# Create database tables
print("[STARTUP] Creating database tables...")
Base.metadata.create_all(bind=engine)
print("[STARTUP] Database tables created successfully\n")

# Initialize FastAPI app
app = FastAPI(
    title="Jan Suraksha API",
    description="National Last-Mile Trust & Verification Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount static files for uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
print("[STARTUP] Mounted /uploads directory for static files")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # Add production origins here when deploying
    ],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    
    # Log incoming request
    print(f"\n{'='*80}")
    print(f"[REQUEST] {request.method} {request.url.path}")
    print(f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if request.query_params:
        print(f"[QUERY] {dict(request.query_params)}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log response
    print(f"[RESPONSE] Status: {response.status_code}")
    print(f"[DURATION] {process_time:.3f}s")
    print(f"{'='*80}\n")
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if app.debug else "An error occurred"
        }
    )


# Include routers
print("[STARTUP] Registering API routers...")
app.include_router(auth_router, prefix="/api")
print("  [OK] Auth router registered")
app.include_router(workers_router, prefix="/api")
print("  [OK] Workers router registered")
app.include_router(companies_router, prefix="/api")
print("  [OK] Companies router registered")
app.include_router(police_router, prefix="/api")
print("  [OK] Police router registered")
app.include_router(verification_router, prefix="/api")
print("  [OK] Verification router registered")
app.include_router(admin_router, prefix="/api")
print("  [OK] Admin router registered")
print("[STARTUP] All routers registered successfully\n")


# Health check endpoint
@app.get("/health")
async def health_check():
    print("[HEALTH] Health check request received")
    return {
        "status": "healthy",
        "service": "Jan Suraksha API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Jan Suraksha API",
        "docs": "/api/docs",
        "health": "/health"
    }


# User info endpoint (also accessible via /api/users/me)
@app.get("/api/users/me")
async def get_current_user_via_users_me(request: Request):
    """Alternative endpoint for getting current user"""
    from app.dependencies import get_current_user
    from app.database import get_db
    from fastapi import Depends
    
    # This will be handled by the auth router, but we add it here for clarity
    return {"message": "Use /api/auth/me endpoint"}


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*80)
    print("STARTING UVICORN SERVER")
    print("="*80)
    print("Host: 0.0.0.0")
    print("Port: 8000")
    print("Reload: Enabled")
    print("Docs: http://localhost:8000/api/docs")
    print("="*80 + "\n")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

