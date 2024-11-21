# routers/risk_analysis.py

from fastapi import APIRouter, HTTPException
from models import ProjectData
from utils import parse_project_description, call_openai_api, estimate_defect_rate, calculate_risk_score
from database import query_promise_dataset, query_tawos_dataset
import logging

router = APIRouter()

@router.post("/identify_risks/")
async def identify_risks(project: ProjectData):
    try:
        parsed_metrics = parse_project_description(project.description)
        promise_data = query_promise_dataset(parsed_metrics)
        tawos_data = query_tawos_dataset(parsed_metrics)
        defect_rate = estimate_defect_rate(parsed_metrics, promise_data)
        risk_score = calculate_risk_score(parsed_metrics, {**promise_data, **tawos_data})

        prompt = f"""
Based on the project description and the following metrics:
Estimated LOC: {parsed_metrics['estimated_loc']}
Complexity Level: {parsed_metrics['complexity_level']}
Methodology: {parsed_metrics['methodology']}
Historical Average Defect Density: {promise_data['average_defect_density']}
Estimated Defect Rate: {defect_rate}
Risk Score: {risk_score}

Provide a risk assessment report that highlights potential challenges and recommendations.
"""
        assessment = call_openai_api(prompt)
        return {
            "defect_rate": defect_rate,
            "risk_score": risk_score,
            "assessment": assessment
        }
    except Exception as e:
        logging.error(f"Error in /identify_risks/: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while identifying risks.")
