"""
BigRalph API - Raffle/Giveaway Platform Backend

Main application entry point with versioned API routing and static file serving.
"""
# Trigger reload: fixed bcrypt version
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import Base, engine
from .routers import raffles, comments, tickets, auth, wallet

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BigRalph API",
    description="Backend API for the BigRalph raffle and giveaway platform",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers under /api/v1 prefix
API_V1_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(wallet.router, prefix=API_V1_PREFIX)
app.include_router(raffles.router, prefix=API_V1_PREFIX)
app.include_router(tickets.router, prefix=API_V1_PREFIX)
app.include_router(comments.router, prefix=API_V1_PREFIX)

# Path to frontend files (one directory above backend)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "")


@app.get("/api/v1")
def api_info():
    """API version information."""
    return {
        "version": "1.0.0",
        "endpoints": {
            "raffles": "/api/v1/raffles",
            "tickets": "/api/v1/raffles/{raffle_id}/tickets",
            "comments": "/api/v1/raffles/{raffle_id}/comments"
        }
    }


@app.get("/")
def serve_homepage():
    """Serve the homepage."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/index.html")
def serve_index():
    """Serve index.html explicitly."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/item.html")
def serve_item():
    """Serve the item detail page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "item.html"))


@app.get("/about.html")
def serve_about():
    """Serve the about page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "about.html"))


# Serve all frontend files (html, css, js) from the root directory
# This must be the last route to avoid overriding API endpoints
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
