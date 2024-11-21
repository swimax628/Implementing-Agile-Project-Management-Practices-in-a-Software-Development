# routers/other_routes.py

from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from models import ProjectData
from utils import (
    parse_project_description,
    call_openai_api,
    estimate_defect_rate,
    calculate_risk_score,
    suggest_methodology,
    calculate_estimation_accuracy,
    assess_complexity_manageability,
    perform_t_test,
    calculate_correlations,
    parse_response  
)
from database import query_promise_dataset, query_tawos_dataset, promise_df, engine
import logging
import pandas as pd
import plotly.express as px
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import httpx
router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Setup logging
logger = logging.getLogger(__name__)

# Index Route
@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Renders the index page.
    """
    return templates.TemplateResponse("index.html", {"request": request})

# Clean Description Route
@router.post("/clean_description/")
async def clean_description(project: ProjectData):
    """
    Cleans and preprocesses the project description using the OpenAI API.
    """
    try:
        prompt = f"Clean and preprocess the following project description for analysis:\n\n{project.description}\n\nCleaned Description:"
        cleaned_description = call_openai_api(prompt)
        return {"cleaned_description": cleaned_description}
    except Exception as e:
        logger.error(f"Error in /clean_description/: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while cleaning the description.")

# Statistical Analysis Routes

@router.get("/analysis/promise/correlations", response_class=HTMLResponse)
async def promise_correlations(request: Request):
    """
    Displays the correlation matrix heatmap for the PROMISE dataset.
    """
    try:
        corr_matrix = calculate_correlations()
        fig = px.imshow(corr_matrix, text_auto=True, title="PROMISE Dataset Correlation Matrix")
        chart_html = fig.to_html(full_html=False)
        description = "This heatmap shows the correlations between different numerical metrics in the PROMISE dataset."
        return templates.TemplateResponse("correlations.html", {
            "request": request,
            "chart": chart_html,
            "description": description
        })
    except Exception as e:
        logger.error(f"Error generating correlation matrix: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating the correlation matrix.")

@router.get("/analysis/promise/t_tests", response_class=HTMLResponse)
async def promise_t_tests(request: Request):
    """
    Performs t-tests on the PROMISE dataset and displays the results.
    """
    try:
        t_test_results = perform_t_test()
        return templates.TemplateResponse("t_tests.html", {
            "request": request,
            "t_test_results": t_test_results
        })
    except Exception as e:
        logger.error(f"Error performing t-tests: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while performing t-tests.")

@router.get("/analysis/tawos/resolution_time", response_class=HTMLResponse)
async def tawos_resolution_time_comparison(request: Request):
    """
    Displays a bar chart comparing average resolution times between Agile and Waterfall methodologies in the TAWOS dataset.
    """
    try:
        # Pass relevant data to infer methodology
        project_data = {
            "sprint_count": 2,  # You can dynamically assign this based on the project data
            "project_duration": 12  # Project duration in months
        }
        
        tawos_data = query_tawos_dataset(project_data)
        avg_resolution_time = tawos_data.get("average_resolution_time", None)

        if avg_resolution_time is None:
            raise HTTPException(status_code=500, detail="Unable to calculate resolution time.")

        # Render results (assuming you have an HTML template to display this)
        return templates.TemplateResponse("tawos_resolution_time.html", {
            "request": request,
            "avg_resolution_time": avg_resolution_time
        })
    except Exception as e:
        logger.error(f"Error generating resolution time comparison: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating the resolution time comparison.")

# Generate Productivity Route
@router.post("/generate_productivity/")
async def generate_productivity(project: ProjectData):
    """
    Generates productivity values for Agile and Waterfall methodologies using the OpenAI API.
    """
    prompt = f"""
    Read the following project description and determine 5 float productivity values for Agile and 5 float productivity values for Waterfall at 5 different time points during the development duration of the given project.

    Important: You must **only** output the numerical values without any numbering, bullet points, explanations, or additional text. Do not include any introductory or concluding remarks.

    Format the response exactly as follows:

    Agile:
    value1
    value2
    value3
    value4
    value5

    Waterfall:
    value1
    value2
    value3
    value4
    value5
    """
    system_prompt = "You are an assistant that strictly outputs numerical values as instructed, without any additional text."
    try:
        # Log the prompt sent to the API
        logger.info("Sending prompt to OpenAI API")

        content = call_openai_api(prompt, system_prompt=system_prompt)
        
        # Log the raw API response
        logger.info(f"API response content: {content}")

        agile_productivity, waterfall_productivity = parse_response(content)

        # Check and log the final values before returning
        if not (agile_productivity and waterfall_productivity):
            logger.error("Parsed values are empty or None")
            raise ValueError("Parsed values are empty or None")
        
        logger.info("Returning productivity data")
        return {
            "agile_productivity": agile_productivity,
            "waterfall_productivity": waterfall_productivity
        }

    except Exception as e:
        logger.error(f"Error in /generate_productivity/: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating productivity values.")


# Test Prototype
@router.get("/test_prototype", response_class=HTMLResponse)
async def test_prototype_page(request: Request, description: Optional[str] = Query(None)):
    """
    Renders the test prototype page.
    """
    description = description or ""
    return templates.TemplateResponse("test_prototype.html", {
        "request": request,
        "cleaned_description": description
    })


@router.post("/test_prototype/")
async def test_prototype(project: ProjectData):
    """
    Performs a test on the prototype based on the provided test description.
    """
    try:
        description = project.description
        test_description = project.test_description
        if not test_description:
            raise HTTPException(status_code=400, detail="Test description is required.")
        prompt = f"Based on the project description:\n\n{description}\n\nPerform a test with the following input:\n\n{test_description}\n\nTest Results:"
        test_results = call_openai_api(prompt)
        return {"test_results": test_results}
    except HTTPException as he:
        raise he  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error in /test_prototype/: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during prototype testing.")

# Risk Mitigation Route
@router.get("/risk_mitigation", response_class=HTMLResponse)
async def risk_mitigation_page(request: Request, description: Optional[str] = Query(None)):
    """
    Renders the risk mitigation page.
    """
    description = description or ""
    return templates.TemplateResponse("risk_mitigation.html", {
        "request": request,
        "cleaned_description": description,
        "mitigation_strategies": ""
    })

@router.post("/generate_risk_mitigation/")
async def generate_risk_mitigation(project: ProjectData):
    """
    Generates risk mitigation strategies using the OpenAI API.
    """
    try:
        prompt = f"Based on the following project description, provide risk mitigation strategies:\n\n{project.description}\n\nRisk Mitigation Strategies:"
        mitigation_strategies = call_openai_api(prompt)
        return {"mitigation_strategies": mitigation_strategies}
    except Exception as e:
        logger.error(f"Error in /generate_risk_mitigation/: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating risk mitigation strategies.")

# Project Stages Routes

stage_info = {
    "design": {
        "name": "Design",
        "template": "design.html"
    },
    "prototyping": {
        "name": "Prototyping",
        "template": "prototyping.html"
    },
    "customer_evaluation": {
        "name": "Customer Evaluation",
        "template": "customer_evaluation.html"
    },
    "review_and_update": {
        "name": "Review & Update",
        "template": "review_and_update.html"
    },
    "development": {
        "name": "Development",
        "template": "development.html"
    },
    "testing": {
        "name": "Testing",
        "template": "testing.html"
    },
    "maintenance": {
        "name": "Maintenance",
        "template": "maintenance.html"
    }
}

def create_stage_routes(stage_key, stage_details):
    @router.get(f"/{stage_key}", response_class=HTMLResponse)
    async def stage_page(request: Request, description: Optional[str] = Query(None)):
        """
        Renders the page for the specified project stage.
        """
        description = description or ""
        return templates.TemplateResponse(stage_details["template"], {
            "request": request,
            "stage": stage_details["name"],
            "content": "",
            "cleaned_description": description
        })

    @router.post(f"/generate_{stage_key}/")
    async def generate_stage_content(project: ProjectData):
        """
        Generates content for the specified project stage using the OpenAI API.
        """
        try:
            prompt = f"Generate a detailed plan for the {stage_details['name'].lower()} stage of an Agile project for the following project description and compare it with the same phase in the Waterfall model, if any.\n\n{project.description}\n\n{stage_details['name']} Plan:"
            content = call_openai_api(prompt)
            return {f"{stage_key}_content": content}
        except Exception as e:
            logger.error(f"Error in /generate_{stage_key}/: {e}")
            raise HTTPException(status_code=500, detail=f"An error occurred while generating the {stage_details['name'].lower()} plan.")

    # Add routes to the router
    router.add_api_route(f"/{stage_key}", stage_page, methods=["GET"], response_class=HTMLResponse)
    router.add_api_route(f"/generate_{stage_key}/", generate_stage_content, methods=["POST"])

# Create routes for each project stage
for stage_key, stage_details in stage_info.items():
    create_stage_routes(stage_key, stage_details)

# Identified Risks Route
@router.get("/identified_risks", response_class=HTMLResponse)
async def identified_risks_page(request: Request, description: Optional[str] = Query(None)):
    """
    Renders the identified risks page.
    """
    description = description or ""
    return templates.TemplateResponse("identified_risks.html", {
        "request": request,
        "cleaned_description": description,
        "assessment": ""
    })

# Risk Assessment Route
@router.get("/risk_assessment", response_class=HTMLResponse)
async def risk_assessment_page(request: Request, description: Optional[str] = Query(None)):
    """
    Renders the risk assessment page.
    """
    description = description or ""
    return templates.TemplateResponse("risk_assessment.html", {
        "request": request,
        "cleaned_description": description,
        "assessment": ""
    })

@router.post("/generate_risk_assessment/")
async def generate_risk_assessment(project: ProjectData):
    """
    Generates a risk assessment report using the OpenAI API.
    """
    try:
        parsed_metrics = parse_project_description(project.description)
        promise_data = query_promise_dataset(parsed_metrics)
        tawos_data = query_tawos_dataset(parsed_metrics)
        defect_rate = estimate_defect_rate(parsed_metrics, promise_data)
        risk_score = calculate_risk_score(parsed_metrics, {**promise_data, **tawos_data})

        prompt = f"""
Based on the project description and the following metrics:
Estimated LOC: {parsed_metrics.get('estimated_loc', 'N/A')}
Complexity Level: {parsed_metrics.get('complexity_level', 'N/A')}
Methodology: {parsed_metrics.get('methodology', 'N/A')}
Historical Average Defect Density: {promise_data.get('average_defect_density', 'N/A')}
Estimated Defect Rate: {defect_rate if defect_rate is not None else 'N/A'}
Risk Score: {risk_score if risk_score is not None else 'N/A'}

Provide a detailed risk assessment report that highlights potential challenges and recommendations.
"""
        assessment = call_openai_api(prompt)
        return {"assessment": assessment}
    except Exception as e:
        logger.error(f"Error in /generate_risk_assessment/: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating risk assessment.")

# Methodology Recommendation Route
@router.post("/recommend_methodology/")
async def recommend_methodology(project: ProjectData):
    """
    Recommends the optimal methodology (Agile or Waterfall) based on project metrics and historical data.
    """
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

# Benchmark Estimation Route
@router.post("/benchmark_estimation/")
async def benchmark_estimation(project: ProjectData):
    """
    Benchmarks the project estimation accuracy and assesses complexity manageability.
    """
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

# Additional Analysis Routes

@router.get("/analysis/promise/defect_density", response_class=HTMLResponse)
async def promise_defect_density_analysis(request: Request):
    """
    Displays analysis of defect density by methodology in the PROMISE dataset.
    """
    try:
        df = promise_df.copy()
        df = df.dropna(subset=['defect_density', 'assigned_methodology'])
        df_grouped = df.groupby('assigned_methodology')['defect_density'].mean().reset_index()
        fig = px.bar(df_grouped, x='assigned_methodology', y='defect_density', title='Average Defect Density by Methodology')
        chart_html = fig.to_html(full_html=False)
        description = "This chart illustrates the average defect density for projects using Agile and Waterfall methodologies based on the PROMISE dataset."
        return templates.TemplateResponse("defect_density_analysis.html", {
            "request": request,
            "chart": chart_html,
            "description": description
        })
    except Exception as e:
        logger.error(f"Error generating defect density analysis: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating the defect density analysis.")

@router.get("/analysis/tawos/effort_comparison", response_class=HTMLResponse)
async def tawos_effort_comparison(request: Request):
    """
    Displays a comparison of average effort minutes between methodologies in the TAWOS dataset.
    """
    try:
        query = text("""
        SELECT
            Project.methodology,
            AVG(Issue.Total_Effort_Minutes) as avg_effort_minutes
        FROM Project
        JOIN Issue ON Project.ID = Issue.Project_ID
        GROUP BY Project.methodology
        """)
        with engine.connect() as conn:
            df = pd.read_sql_query(query, conn)
        fig = px.bar(df, x='methodology', y='avg_effort_minutes', title='Average Effort Minutes by Methodology')
        chart_html = fig.to_html(full_html=False)
        description = "This chart compares the average effort in minutes for issues in projects using Agile and Waterfall methodologies in the TAWOS dataset."
        return templates.TemplateResponse("effort_comparison.html", {
            "request": request,
            "chart": chart_html,
            "description": description
        })
    except SQLAlchemyError as e:
        logger.error(f"Database error in /analysis/tawos/effort_comparison: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while accessing the database.")
    except Exception as e:
        logger.error(f"Error generating effort comparison: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating the effort comparison.")


###########################~~~~~~~~~~~~~~~~~~~~~~~~~~##############################

@router.get("/all_analysis", response_class=HTMLResponse)
async def all_analysis_page(request: Request):
    """
    Renders the all_analysis.html page as a static page.
    """
    return templates.TemplateResponse("all_analysis.html", {"request": request})



################################
@router.get("/comprehensive_analysis", response_class=HTMLResponse)
async def comprehensive_analysis(request: Request, description: str):
    """
    Generates a comprehensive analysis by combining the project description with insights
    from the PROMISE and TAWOS datasets, and returns a professional project management guide.
    """
    try:
        # The description is passed as a query parameter (e.g., /comprehensive_analysis?description=...)
        project_description = description  # Retrieved from the query string

        # Read PROMISE and TAWOS analysis summaries from text files
        with open("data/promise_O.txt", "r") as f:
            promise_analysis = f.read()
        with open("data/tawos_O.txt", "r") as f:
            tawos_analysis = f.read()

        # Define separate prompts for each section
        strategy_prompt = (
            f"Based on the following project description, recommend the most effective management strategy. "
            f"Consider Agile, Waterfall, or a hybrid approach and justify your recommendation.\n\n"
            f"Project Description:\n{project_description}"
        )

        recommendations_prompt = (
            f"Generate a high-level, professional step-by-step project management guide based on the following project description. "
            f"Structure the recommendations into major phases (e.g., Initiation, Planning, Design, Development, Testing, Deployment, Monitoring, and Closure), "
            f"and provide a concise summary of key actions and expected outcomes in each phase. Use a formal tone.\n\n"
            f"Project Description:\n{project_description}"
        )

        promise_insights_prompt = (
            f"Summarize the following PROMISE dataset insights as they relate to software quality, defect rates, and methodology "
            f"for the described project. Suggest how these insights might improve the project's outcomes.\n\n"
            f"PROMISE Dataset Insights:\n{promise_analysis}"
        )

        tawos_insights_prompt = (
            f"Summarize the following TAWOS dataset insights with respect to effort, resolution times, and productivity. "
            f"Provide suggestions on how these insights can optimize resource allocation and project timelines.\n\n"
            f"TAWOS Dataset Insights:\n{tawos_analysis}"
        )

        summarized_insights_prompt = (
            f"Based on the following PROMISE and TAWOS dataset insights, provide a combined summary. "
            f"Highlight key points that could influence project success and suggest how these insights together inform best practices "
            f"for project management.\n\nPROMISE Dataset Insights:\n{promise_analysis}\n\nTAWOS Dataset Insights:\n{tawos_analysis}"
        )
        final_conclusion_prompt = (
            f"Based on the insights from the PROMISE and TAWOS datasets, along with the project description, provide a final conclusion "
            f"that summarizes the key takeaways and offers a final recommendation for the project's success.\n\n"
            f"Project Description:\n{project_description}\n\n"
            f"PROMISE Dataset Insights:\n{promise_analysis}\n\nTAWOS Dataset Insights:\n{tawos_analysis}"
        )

        # Call OpenAI API for each section and log the responses for debugging
        management_strategy = call_openai_api(strategy_prompt) or "No management strategy generated."
        recommendations = call_openai_api(recommendations_prompt).split('\n') or ["No recommendations generated."]
        promise_insights = call_openai_api(promise_insights_prompt) or "No insights from PROMISE dataset."
        tawos_insights = call_openai_api(tawos_insights_prompt) or "No insights from TAWOS dataset."
        summarized_insights = call_openai_api(summarized_insights_prompt) or "No summarized insights."
        final_conclusion = call_openai_api(final_conclusion_prompt) or "No final conclusion generated."

        # Log the raw responses to verify their content
        logger.info(f"Management Strategy: {management_strategy}")
        logger.info(f"Recommendations: {recommendations}")
        logger.info(f"PROMISE Insights: {promise_insights}")
        logger.info(f"TAWOS Insights: {tawos_insights}")
        logger.info(f"Summarized Insights: {summarized_insights}")
        logger.info(f"Final Conclusion: {final_conclusion}")

        # Render the response in the template
        return templates.TemplateResponse("comprehensive_analysis.html", {
            "request": request,
            "description": project_description,
            "management_strategy": management_strategy,
            "recommendations": recommendations,
            "promise_insights": promise_insights,
            "tawos_insights": tawos_insights,
            "summarized_insights": summarized_insights,
            "final_conclusion": final_conclusion
        })

    except Exception as e:
        logger.error(f"Error in /comprehensive_analysis: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating the comprehensive analysis.")
