"""
Podcast Analysis Application v2 - Main FastAPI Application
"""
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from app.core.database import create_tables
from app.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    print("Creating database tables...")
    create_tables()
    print("Database tables created successfully")
    yield
    # Shutdown: cleanup if needed
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Podcast Analysis Application v2",
    description="Personal podcast analysis and knowledge management system",
    version="2.0.0",
    lifespan=lifespan
)

# Mount static files
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include API routes
app.include_router(api_router, prefix="/api")


# Frontend routes
@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Landing page"""
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse) 
async def dashboard(request: Request):
    """User dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/knowledge-base", response_class=HTMLResponse)
async def knowledge_base(request: Request):
    """Knowledge base page"""
    return templates.TemplateResponse("knowledge_base.html", {"request": request})


@app.get("/podcasts", response_class=HTMLResponse)
async def browse_podcasts(request: Request):
    """Browse and subscribe to podcasts"""
    return templates.TemplateResponse("podcasts.html", {"request": request})


@app.get("/subscriptions", response_class=HTMLResponse)
async def manage_subscriptions(request: Request):
    """Manage podcast subscriptions"""
    return templates.TemplateResponse("subscriptions.html", {"request": request})


@app.get("/analysis/{report_id}", response_class=HTMLResponse)
async def view_analysis(request: Request, report_id: int):
    """View specific analysis report"""
    return templates.TemplateResponse("analysis.html", {
        "request": request, 
        "report_id": report_id
    })


@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    """User settings page"""
    return templates.TemplateResponse("settings.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Podcast Analysis Application v2...")
    print("📡 Server will be available at: http://localhost:8080")
    print("📡 Also try: http://127.0.0.1:8080")
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)