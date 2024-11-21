# database.py

import os
import pandas as pd
import glob
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config import TAWOS_DB_URI
from methodology import infer_methodology  # Import from methodology.py

# Configure logging
logger = logging.getLogger(__name__)

# Load PROMISE Dataset
def load_promise_dataset():
    # Path to PROMISE dataset CSV files
    promise_files = glob.glob(os.path.join('data/promise', '*.csv'))
    promise_dataframes = []
    all_columns = set()

    # Load and concatenate all CSV files
    for file in promise_files:
        try:
            logger.info(f"Loading {file}")
            df = pd.read_csv(file)
            # Collect all columns
            all_columns.update(df.columns)
            promise_dataframes.append(df)
        except Exception as e:
            logger.error(f"Error loading {file}: {e}")
            continue

    if not promise_dataframes:
        logger.error("No PROMISE dataset files were loaded successfully.")
        raise RuntimeError("Failed to load PROMISE dataset.")

    # Ensure all dataframes have the same columns
    for df in promise_dataframes:
        missing_columns = all_columns - set(df.columns)
        for col in missing_columns:
            df[col] = pd.NA  # Use pandas NA for missing values

    # Concatenate all dataframes
    combined_df = pd.concat(promise_dataframes, ignore_index=True)

    # Ensure necessary columns are present
    required_columns = {'bug', 'loc', 'amc', 'wmc', 'cbo', 'rfc', 'cam'}
    missing_required_columns = required_columns - set(combined_df.columns)
    if missing_required_columns:
        logger.error(f"Missing required columns in PROMISE dataset: {missing_required_columns}")
        raise RuntimeError(f"Missing required columns in PROMISE dataset: {missing_required_columns}")

    # Compute 'defect_density' as bug count divided by lines of code
    combined_df['defect_density'] = combined_df.apply(
        lambda row: row['bug'] / row['loc'] if pd.notna(row['bug']) and pd.notna(row['loc']) and row['loc'] > 0 else pd.NA, axis=1
    )

    # Use 'amc' (Average Method Complexity) as 'complexity'
    combined_df['complexity'] = combined_df['amc']

    # Remove rows with missing 'complexity' values
    combined_df = combined_df.dropna(subset=['complexity'])

    # Categorize 'complexity' into 'complexity_level'
    bins = [0, 5, 10, float('inf')]
    labels = ['Low', 'Medium', 'High']
    combined_df['complexity_level'] = pd.cut(combined_df['complexity'], bins=bins, labels=labels, right=False)

    # Assign methodologies based on thresholds if not already assigned
    complexity_threshold = 15  # WMC threshold
    size_threshold = 1000      # LOC threshold
    combined_df['assigned_methodology'] = combined_df.apply(
        lambda row: 'Waterfall' if (row['wmc'] > complexity_threshold or row['loc'] > size_threshold) else 'Agile',
        axis=1
    )

    return combined_df

# Load PROMISE dataset
try:
    promise_df = load_promise_dataset()
except Exception as e:
    logger.error(f"Error loading PROMISE dataset: {e}")
    promise_df = pd.DataFrame()  # Set to empty DataFrame if loading fails

# Create database engine for TAWOS dataset
engine = None
try:
    engine = create_engine(TAWOS_DB_URI)
    # Test the connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except SQLAlchemyError as e:
    logger.error(f"Error creating database engine: {e}")
    engine = None  # Set engine to None if connection fails

# Function to query PROMISE dataset
def query_promise_dataset(metrics):
    methodology = metrics.get('methodology')
    complexity_level = metrics.get('complexity_level')

    if not methodology or not complexity_level:
        logger.warning("Methodology or complexity level is missing in parsed metrics.")
        return {'average_defect_density': None, 'average_complexity': None}

    methodology = methodology.lower()
    complexity_level = complexity_level.capitalize()  # Since labels are 'Low', 'Medium', 'High'

    # Filter dataframe with case-insensitive matching
    filtered_df = promise_df[
        (promise_df['assigned_methodology'].str.lower() == methodology) &
        (promise_df['complexity_level'] == complexity_level)
    ]

    if filtered_df.empty:
        logger.warning("No matching records found in PROMISE dataset.")
        return {'average_defect_density': None, 'average_complexity': None}

    average_defect_density = filtered_df['defect_density'].mean()
    average_complexity = filtered_df['complexity'].mean()

    return {
        'average_defect_density': average_defect_density,
        'average_complexity': average_complexity
    }


def query_tawos_dataset(project_data):
    """
    Queries TAWOS dataset and includes methodology inference.
    
    Parameters:
        project_data (dict): Dictionary containing project-related fields.
    
    Returns:
        dict: Result data with metrics calculated based on inferred methodology.
    """
    methodology = project_data.get('methodology')
    if not methodology:
        methodology = infer_methodology(project_data)  # Infer methodology if not provided

    query = text("""
        SELECT
            AVG(TIMESTAMPDIFF(MINUTE, Issue.Creation_Date, Issue.Resolution_Date)) AS avg_resolution_time
        FROM Project
        JOIN Issue ON Project.ID = Issue.Project_ID
        WHERE LOWER(:methodology) = LOWER(:methodology_param)
    """)

    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"methodology_param": methodology}).fetchone()
            return {"average_resolution_time": result["avg_resolution_time"]}
    except SQLAlchemyError as e:
        logger.error(f"Database error in query_tawos_dataset: {e}")
        return {}