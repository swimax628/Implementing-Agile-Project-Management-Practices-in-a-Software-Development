from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
from fastapi.templating import Jinja2Templates
import requests
import os
import logging
from dotenv import load_dotenv
import re

app = FastAPI()

# Load environment variables
load_dotenv(dotenv_path="storekey.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OpenAI API key is missing. Please set the OPENAI_API_KEY environment variable.")

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Define Pydantic models
class ProjectData(BaseModel):
    description: str

class RiskAnalysisData(BaseModel):
    descriptions: List[str]
    human_risks: List[List[str]]

# Helper function to call OpenAI API
def call_openai_api(prompt: str, system_prompt: Optional[str] = None):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": "gpt-3.5-turbo",  # You can change this to "gpt-4" if you have access and prefer
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0,  # Set temperature to 0 for deterministic output
    }
    response = requests.post(OPENAI_API_URL, headers=headers, json=data)
    logging.debug(f"Response Status Code: {response.status_code}")
    logging.debug(f"Response Text: {response.text}")

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error calling OpenAI API")

    return response.json()['choices'][0]['message']['content'].strip()

# Helper function to parse response
def parse_response(response: str, agile_label: str = "Agile:", waterfall_label: str = "Waterfall:"):
    lines = response.split('\n')
    agile_values, waterfall_values = [], []
    current_section = None

    for line in lines:
        line = line.strip()
        if line == '':
            continue  # Skip empty lines

        if line.startswith(agile_label):
            current_section = "Agile"
            continue
        elif line.startswith(waterfall_label):
            current_section = "Waterfall"
            continue

        if current_section == "Agile":
            value = extract_number(line)
            if value is not None:
                agile_values.append(value)
            else:
                logging.warning(f"No numeric value found in line '{line}' for Agile.")
        elif current_section == "Waterfall":
            value = extract_number(line)
            if value is not None:
                waterfall_values.append(value)
            else:
                logging.warning(f"No numeric value found in line '{line}' for Waterfall.")

    return agile_values, waterfall_values

def extract_number(text: str):
    match = re.search(r'[-+]?\d*\.\d+|\d+', text)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None

# Routes
@app.post("/identify_risks/")
async def identify_risks(project: ProjectData):
    try:
        prompt = f"Identify potential risks in the following project description:\n\n{project.description}\n\nRisks:"
        risks = call_openai_api(prompt)
        prompt_assessment = f"Assess the likelihood and impact of the following risks:\n\n{risks}\n\nAssessment:"
        assessment = call_openai_api(prompt_assessment)
        return {"risks": risks.split('\n'), "assessment": assessment}
    except Exception as e:
        logging.error(f"Error in /identify_risks/: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while identifying risks.")

@app.post("/mitigate_risks/")
async def mitigate_risks(project: ProjectData):
    try:
        prompt = f"Provide risk mitigation strategies for the following project description in the context of Agile project management:\n\n{project.description}\n\nMitigation Strategies:"
        mitigation = call_openai_api(prompt)
        return {"mitigation": mitigation}
    except Exception as e:
        logging.error(f"Error in /mitigate_risks/: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating mitigation strategies.")

@app.post("/clean_description/")
async def clean_description(project: ProjectData):
    try:
        prompt = f"Clean the following project description to improve clarity and conciseness:\n\n{project.description}\n\nCleaned Description:"
        cleaned_description = call_openai_api(prompt)
        return {"cleaned_description": cleaned_description}
    except Exception as e:
        logging.error(f"Error in /clean_description/: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while cleaning the description.")

@app.post("/analyze_risks/")
async def analyze_risks(data: RiskAnalysisData):
    try:
        # Ensure both lists have the same length
        if len(data.descriptions) != len(data.human_risks):
            raise ValueError("Mismatch between number of descriptions and number of risk lists.")

        results = []
        for desc, risks in zip(data.descriptions, data.human_risks):
            predicted_risks = call_openai_api(f"Identify potential risks in the following project description:\n\n{desc}\n\nRisks:")
            results.append({
                "description": desc,
                "human_risks": risks,
                "predicted_risks": predicted_risks.split('\n')
            })

        return {"results": results}
    except ValueError as ve:
        logging.error(f"ValueError in /analyze_risks/: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logging.error(f"Error in /analyze_risks/: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while analyzing risks.")

@app.post("/generate_productivity/")
async def generate_productivity(project: ProjectData):
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
        content = call_openai_api(prompt, system_prompt=system_prompt)
        agile_productivity, waterfall_productivity = parse_response(content)
        return {
            "agile_productivity": agile_productivity,
            "waterfall_productivity": waterfall_productivity
        }
    except Exception as e:
        logging.error(f"Error in /generate_productivity/: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating productivity values.")

@app.post("/generate_performance/")
async def generate_performance(project: ProjectData):
    prompt = f"""
Read the following project description and determine 5 float performance values for Agile and 5 float performance values for Waterfall which indicate their performance at 5 different time points during the development duration of the given project.

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
        content = call_openai_api(prompt, system_prompt=system_prompt)
        agile_performance, waterfall_performance = parse_response(content)
        return {
            "agile_performance": agile_performance,
            "waterfall_performance": waterfall_performance
        }
    except Exception as e:
        logging.error(f"Error in /generate_performance/: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating performance values.")

@app.post("/generate_mitigation/")
async def generate_mitigation(project: ProjectData):
    prompt = f"""
Read the following project description and determine 5 float risk mitigation values for Agile and 5 float risk mitigation values for Waterfall which indicate their ability to mitigate risks at 5 different time points during the development duration of the given project.

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
        content = call_openai_api(prompt, system_prompt=system_prompt)
        agile_mitigation, waterfall_mitigation = parse_response(content)
        return {
            "agile_mitigation": agile_mitigation,
            "waterfall_mitigation": waterfall_mitigation
        }
    except Exception as e:
        logging.error(f"Error in /generate_mitigation/: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating mitigation values.")

# HTML response routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/design_page", response_class=HTMLResponse)
async def design_page(request: Request, description: Optional[str] = None):
    return templates.TemplateResponse("design.html", {"request": request, "stage": "", "content": "", "cleaned_description": description or ""})

@app.post("/generate_design/")
async def generate_design(project: ProjectData):
    try:
        prompt = f"Generate a detailed plan of the design stage for the given project description if we implement Agile project management and compare it with the Waterfall model:\n\n{project.description}\n\nDesign:"
        content = call_openai_api(prompt)
        return {"design_content": content}
    except Exception as e:
        logging.error(f"Error in /generate_design/: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating the design.")

@app.get("/prototyping", response_class=HTMLResponse)
async def prototyping(request: Request, description: str = Query(...)):
    prompt = f"Generate a detailed plan for the prototyping stage of an Agile project for the given project description and compare it with prototyping in the Waterfall model, if any.\n\n{description}\n\nPrototyping:"
    content = call_openai_api(prompt)
    return templates.TemplateResponse("prototyping.html", {"request": request, "stage": "Prototyping", "content": content, "cleaned_description": description})

@app.get("/customer_evaluation", response_class=HTMLResponse)
async def customer_evaluation(request: Request, description: str = Query(...)):
    prompt = f"Generate a detailed plan for the customer evaluation stage of an Agile project for the given project description and compare it with the evaluation phase in the Waterfall model, if any.\n\n{description}\n\nCustomer Evaluation:"
    content = call_openai_api(prompt)
    return templates.TemplateResponse("customer_evaluation.html", {"request": request, "stage": "Customer Evaluation", "content": content, "cleaned_description": description})

@app.get("/review_and_update", response_class=HTMLResponse)
async def review_and_update(request: Request, description: str = Query(...)):
    prompt = f"Generate a detailed plan for the review and update stage of an Agile project for the given project description and compare it with the update stage in the Waterfall model, if any.\n\n{description}\n\nReview and Update:"
    content = call_openai_api(prompt)
    return templates.TemplateResponse("review_and_update.html", {"request": request, "stage": "Review and Update", "content": content, "cleaned_description": description})

@app.get("/development", response_class=HTMLResponse)
async def development(request: Request, description: str = Query(...)):
    prompt = f"Generate a detailed plan for the development stage of an Agile project for the given project description and compare it with development in the Waterfall model.\n\n{description}\n\nDevelopment:"
    content = call_openai_api(prompt)
    return templates.TemplateResponse("development.html", {"request": request, "stage": "Development", "content": content, "cleaned_description": description})

@app.get("/testing", response_class=HTMLResponse)
async def testing(request: Request, description: str = Query(...)):
    prompt = f"Generate a detailed plan for the testing stage of an Agile project for the given project description and compare it with testing in the Waterfall model.\n\n{description}\n\nTesting:"
    content = call_openai_api(prompt)
    return templates.TemplateResponse("testing.html", {"request": request, "stage": "Testing", "content": content, "cleaned_description": description})

@app.get("/maintenance", response_class=HTMLResponse)
async def maintenance(request: Request, description: str = Query(...)):
    prompt = f"Generate a detailed plan for the maintenance stage of an Agile project for the given project description and compare it with maintenance in the Waterfall model.\n\n{description}\n\nMaintenance:"
    content = call_openai_api(prompt)
    return templates.TemplateResponse("maintenance.html", {"request": request, "stage": "Maintenance", "content": content, "cleaned_description": description})

@app.get("/recommendation")
async def recommendation(description: Optional[str] = None):
    if description:
        prompt = f"Based on the following project description, recommend whether Agile or Waterfall is more suitable:\n\n{description}"
        recommendation_content = call_openai_api(prompt)
    else:
        recommendation_content = "No description provided."

    return JSONResponse(content={"recommendation": recommendation_content})

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
