# utils.py

import re
import requests
import logging
from typing import Optional, Tuple
from config import OPENAI_API_KEY, OPENAI_API_URL
from database import promise_df, query_promise_dataset, query_tawos_dataset
from tenacity import retry, stop_after_attempt, wait_fixed
import numpy as np
from scipy import stats
# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Helper function to parse the project description
def parse_project_description(description: str):
    # Initialize metrics with default values
    estimated_loc = None
    complexity_level = None
    methodology = None
    wmc = None
    cbo = None

    # Regular expressions to extract metrics
    estimated_loc_match = re.search(r'Estimated LOC(?: is|=)?\s*(\d+)', description, re.IGNORECASE)
    if estimated_loc_match:
        estimated_loc = int(estimated_loc_match.group(1))
    else:
        logger.warning("Estimated LOC is missing in the project description.")

    complexity_level_match = re.search(r'(?:with a )?(low|medium|high) complexity level', description, re.IGNORECASE)
    if complexity_level_match:
        complexity_level = complexity_level_match.group(1).capitalize()
    else:
        logger.warning("Complexity level is missing in the project description.")

    methodology_match = re.search(r'(Agile|Waterfall) methodology', description, re.IGNORECASE)
    if methodology_match:
        methodology = methodology_match.group(1)
    else:
        logger.warning("Methodology is missing in the project description.")

    wmc_match = re.search(r'WMC(?: is|=)?\s*(\d+)', description, re.IGNORECASE)
    if wmc_match:
        wmc = int(wmc_match.group(1))
    else:
        logger.warning("WMC is missing in the project description.")

    cbo_match = re.search(r'CBO(?: is|=)?\s*(\d+)', description, re.IGNORECASE)
    if cbo_match:
        cbo = int(cbo_match.group(1))
    else:
        logger.warning("CBO is missing in the project description.")

    # Assign methodology based on thresholds if not specified
    if methodology is None and wmc is not None and estimated_loc is not None:
        complexity_threshold = 15  # WMC threshold
        size_threshold = 1000      # LOC threshold
        if wmc > complexity_threshold or estimated_loc > size_threshold:
            methodology = 'Waterfall'
        else:
            methodology = 'Agile'
        logger.info(f"Assigned methodology based on thresholds: {methodology}")

    # Default values if metrics are missing
    metrics = {
        'estimated_loc': estimated_loc if estimated_loc is not None else 15000,
        'complexity_level': complexity_level if complexity_level is not None else "High",
        'methodology': methodology if methodology is not None else "Agile",
        'wmc': wmc if wmc is not None else 25,
        'cbo': cbo if cbo is not None else 15
    }

    # Log metrics with defaults applied
    for key, value in metrics.items():
        if value == 15000 and key == 'estimated_loc':
            logger.info("Default Estimated LOC used (15000).")
        elif value == "High" and key == 'complexity_level':
            logger.info("Default Complexity Level used (High).")
        elif value == "Agile" and key == 'methodology':
            logger.info("Default Methodology used (Agile).")
        elif value == 25 and key == 'wmc':
            logger.info("Default WMC used (25).")
        elif value == 15 and key == 'cbo':
            logger.info("Default CBO used (15).")

    return metrics

# Helper function to call OpenAI API
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
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
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0,
    }
    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=data)
        response.raise_for_status()
        logger.debug(f"Response Status Code: {response.status_code}")
        logger.debug(f"Response Text: {response.text}")
        result = response.json()
        if 'choices' not in result or not result['choices']:
            logger.error("No choices returned from OpenAI API.")
            raise Exception("Invalid response from OpenAI API.")
        return result['choices'][0]['message']['content'].strip()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling OpenAI API: {e}")
        raise Exception("Error calling OpenAI API") from e

# Function to extract numeric value from text
def extract_number(text: str):
    match = re.search(r'[-+]?\d*\.\d+|\d+', text)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None

# Function to parse OpenAI response for numerical values
def parse_response(response: str, agile_label: str = "Agile:", waterfall_label: str = "Waterfall:") -> Tuple[list, list]:
    lines = response.strip().split('\n')
    agile_values, waterfall_values = [], []
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
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
                logger.warning(f"No numeric value found in line '{line}' for Agile.")
        elif current_section == "Waterfall":
            value = extract_number(line)
            if value is not None:
                waterfall_values.append(value)
            else:
                logger.warning(f"No numeric value found in line '{line}' for Waterfall.")

    return agile_values, waterfall_values

# Function to estimate defect rate
def estimate_defect_rate(metrics, historical_data):
    """
    Estimate defect rate based on metrics and historical data.
    Parameters:
        metrics (dict): Dictionary containing project metrics like 'estimated_loc'.
        historical_data (dict): Dictionary containing historical data like 'average_defect_density'.
    Returns:
        float: Estimated defect rate, or None if required data is missing.
    """
    try:
        avg_defect_density = historical_data.get('average_defect_density')
        estimated_loc = metrics.get('estimated_loc')

        if avg_defect_density is None or estimated_loc is None:
            logger.warning("Required data for defect rate calculation is missing.")
            return None

        return (avg_defect_density * estimated_loc) / 1000
    except Exception as e:
        logger.error(f"Error calculating defect rate: {e}")
        return None

# Function to calculate risk score
def calculate_risk_score(metrics, historical_data):
    """
    Calculate the risk score based on metrics and weighted historical data.
    Parameters:
        metrics (dict): Dictionary containing project metrics.
        historical_data (dict): Dictionary containing historical data.
    Returns:
        float: Calculated risk score.
    """
    try:
        risk_score = 0
        weights = {
            'average_defect_density': 0.4,
            'average_resolution_time': 0.3,
            'average_complexity': 0.3
        }

        for key, weight in weights.items():
            value = historical_data.get(key)
            risk_score += value * weight if value is not None else 0
            if value is None:
                logger.warning(f"Missing historical data for {key}")

        return risk_score
    except Exception as e:
        logger.error(f"Error calculating risk score: {e}")
        return None

# Function to suggest methodology
def suggest_methodology(metrics):
    """
    Suggest a methodology (Agile or Waterfall) based on defect density comparisons.
    Parameters:
        metrics (dict): Dictionary containing project metrics.
    Returns:
        tuple: Recommended methodology, Agile data, and Waterfall data.
    """
    try:
        metrics_agile = {**metrics, 'methodology': 'Agile'}
        agile_data = {**query_promise_dataset(metrics_agile), **query_tawos_dataset(metrics_agile)}

        metrics_waterfall = {**metrics, 'methodology': 'Waterfall'}
        waterfall_data = {**query_promise_dataset(metrics_waterfall), **query_tawos_dataset(metrics_waterfall)}

        agile_defect_density = agile_data.get('average_defect_density', float('inf'))
        waterfall_defect_density = waterfall_data.get('average_defect_density', float('inf'))

        recommended_methodology = 'Agile' if agile_defect_density < waterfall_defect_density else 'Waterfall'
        return recommended_methodology, agile_data, waterfall_data
    except Exception as e:
        logger.error(f"Error suggesting methodology: {e}")
        return None, {}, {}

# Function to calculate estimation accuracy
def calculate_estimation_accuracy(metrics):
    """
    Calculate the accuracy of LOC estimation against historical data.
    Parameters:
        metrics (dict): Dictionary containing project metrics like 'complexity_level' and 'estimated_loc'.
    Returns:
        float: Estimation accuracy percentage, or None if required data is missing.
    """
    try:
        complexity_level = metrics.get('complexity_level', '').capitalize()
        estimated_loc = metrics.get('estimated_loc')

        if not complexity_level or estimated_loc is None:
            logger.warning("Complexity level or Estimated LOC is missing.")
            return None

        filtered_df = promise_df[promise_df['complexity_level'] == complexity_level]
        if filtered_df.empty:
            logger.warning("No matching records in PROMISE dataset for estimation accuracy.")
            return None

        average_actual_loc = filtered_df['loc'].mean()
        return (1 - abs(estimated_loc - average_actual_loc) / average_actual_loc) * 100 if average_actual_loc else None
    except Exception as e:
        logger.error(f"Error calculating estimation accuracy: {e}")
        return None

# Function to assess complexity manageability
def assess_complexity_manageability(metrics):
    """
    Assess whether project complexity metrics (WMC, CBO) are manageable.
    Parameters:
        metrics (dict): Dictionary containing project metrics like 'wmc' and 'cbo'.
    Returns:
        bool: True if complexity is manageable, False otherwise.
    """
    try:
        wmc = metrics.get('wmc')
        cbo = metrics.get('cbo')

        if wmc is None or cbo is None:
            logger.warning("WMC or CBO values are missing in project description.")
            return False

        wmc_threshold = 50
        cbo_threshold = 10

        return wmc <= wmc_threshold and cbo <= cbo_threshold
    except Exception as e:
        logger.error(f"Error assessing complexity manageability: {e}")
        return False

# Additional Statistical Analysis Functions
def calculate_correlations():
    """
    Calculate the correlation matrix for numeric data in the PROMISE dataset.
    Returns:
        DataFrame: Correlation matrix for numeric columns.
    """
    try:
        numeric_data = promise_df.select_dtypes(include=['number']).dropna()
        if numeric_data.empty:
            logger.error("No numeric data available for correlation matrix.")
            return None
        return numeric_data.corr()
    except Exception as e:
        logger.error(f"Error calculating correlation matrix: {e}")
        return None


def perform_t_test(data1, data2):
    """
    Perform an independent t-test on two datasets, with type conversion and error handling.
    Parameters:
        data1 (list or array-like): First dataset.
        data2 (list or array-like): Second dataset.
    Returns:
        dict: Dictionary containing t-statistic and p-value.
    """
    try:
        data1 = np.array(data1, dtype=float)
        data2 = np.array(data2, dtype=float)

        t_stat, p_val = stats.ttest_ind(data1, data2, equal_var=False)
        logger.info(f"T-test performed successfully: t-statistic={t_stat}, p-value={p_val}")
        return {"t_statistic": t_stat, "p_value": p_val}
    except Exception as e:
        logger.error(f"Error performing t-test: {str(e)}")
        return {"error": str(e)}



