# methodology.py

def infer_methodology(project_data):
    """
    Infers the methodology based on project attributes.
    
    Parameters:
        project_data (dict): Dictionary containing project-related fields like `sprints`, `total_duration`, etc.
    
    Returns:
        str: Inferred methodology ('Agile' or 'Waterfall')
    """
    if 'sprint_count' in project_data and project_data['sprint_count'] > 1:
        return 'Agile'
    elif 'project_duration' in project_data and project_data['project_duration'] > 6:  # duration in months
        return 'Waterfall'
    else:
        # Default to Agile if no strong indication
        return 'Agile'
