# main.py

"""
Main application entry point. Sets up the FastAPI app and includes routers.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import (
    risk_analysis,
    methodology_recommendation,
    estimation_benchmarking,
    other_routes
)
import logging

# Initialize FastAPI app
app = FastAPI(
    title="Project Management Application",
    description="An application for analyzing project data and providing recommendations.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(risk_analysis.router)
app.include_router(methodology_recommendation.router)
app.include_router(estimation_benchmarking.router)
app.include_router(other_routes.router)

# Configure logging
logger = logging.getLogger(__name__)
