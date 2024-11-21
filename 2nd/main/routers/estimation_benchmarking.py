# routers/estimation_benchmarking.py

from fastapi import APIRouter, HTTPException
from models import ProjectData
from utils import parse_project_description, calculate_estimation_accuracy, assess_complexity_manageability
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/benchmark_estimation/")
async def benchmark_estimation(project: ProjectData):
    try:
        parsed_metrics = parse_project_description(project.description)
        estimation_accuracy = calculate_estimation_accuracy(parsed_metrics)
        complexity_manageable = assess_complexity_manageability(parsed_metrics)

        response = {
            "estimation_accuracy": estimation_accuracy,
            "complexity_manageable": complexity_manageable
        }

        # Handle cases where data is missing
        messages = []
        if estimation_accuracy is None:
            messages.append("Estimation accuracy could not be calculated due to missing data.")
        if complexity_manageable is None:
            messages.append("Complexity manageability could not be assessed due to missing WMC or CBO values.")
        if messages:
            response["message"] = " ".join(messages)

        return response
    except Exception as e:
        logger.error(f"Error in /benchmark_estimation/: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while benchmarking estimation.")
