# routers/methodology_recommendation.py

from fastapi import APIRouter, HTTPException
from models import ProjectData
from utils import parse_project_description, call_openai_api, suggest_methodology
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/recommend_methodology/")
async def recommend_methodology(project: ProjectData):
    try:
        parsed_metrics = parse_project_description(project.description)
        recommendation, agile_data, waterfall_data = suggest_methodology(parsed_metrics)

        prompt = f"""
Based on the following project metrics and historical data:

Project Metrics:
Estimated LOC: {parsed_metrics.get('estimated_loc', 'N/A')}
Complexity Level: {parsed_metrics.get('complexity_level', 'N/A')}

Agile Metrics:
Average Defect Density: {agile_data.get('average_defect_density', 'N/A')}
Average Resolution Time: {agile_data.get('average_resolution_time', 'N/A')}

Waterfall Metrics:
Average Defect Density: {waterfall_data.get('average_defect_density', 'N/A')}
Average Resolution Time: {waterfall_data.get('average_resolution_time', 'N/A')}

Recommend the optimal methodology (Agile or Waterfall) for this project and justify your recommendation.
"""
        recommendation_content = call_openai_api(prompt)
        return {
            "recommended_methodology": recommendation,
            "recommendation_details": recommendation_content
        }
    except Exception as e:
        logger.error(f"Error in /recommend_methodology/: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while recommending methodology.")
