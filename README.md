Agile vs Waterfall Productivity Comparison Tool
<!-- Replace with your project's logo if available -->

Overview
The Agile vs Waterfall Productivity Comparison Tool is a web-based application designed to assist project managers and teams in evaluating and comparing the productivity, performance, and risk mitigation strategies of Agile and Waterfall methodologies. Leveraging the power of FastAPI for the backend and modern frontend technologies, this tool provides insightful, data-driven decisions to optimize project management practices.

Features
Project Description Cleaning: Enhance the clarity and conciseness of project descriptions.
Risk Identification & Assessment: Automatically identify potential risks and assess their likelihood and impact.
Risk Mitigation Strategies: Generate effective strategies to mitigate identified risks.
Productivity & Performance Metrics: Compare productivity and performance metrics between Agile and Waterfall methodologies.
Methodology Recommendations: Receive data-driven recommendations on whether Agile or Waterfall is more suitable for your project.
Interactive Charts: Visualize data through dynamic and responsive charts.
Responsive Design: User-friendly interface optimized for various devices.
Technologies Used
Backend:
FastAPI - High-performance web framework for building APIs with Python.
Uvicorn - ASGI server for running the FastAPI app.
Pydantic - Data validation and settings management using Python type annotations.
Requests - HTTP library for interacting with the OpenAI API.
Python Dotenv - Loads environment variables from a .env file.
Frontend:
HTML5 - Markup language for structuring web content.
CSS3 - Styling language for designing the appearance of web pages.
JavaScript - Programming language for creating interactive web elements.
Bootstrap 4.5.2 - CSS framework for responsive design.
Chart.js - JavaScript library for data visualization through charts.
External Services:
OpenAI API - Provides access to advanced language models for natural language processing tasks.
Installation
Prerequisites
Python 3.7+
Git
Steps
Clone the Repository:

bash
Copy code
git clone https://github.com/yourusername/agile-waterfall-comparison.git
cd agile-waterfall-comparison
Create a Virtual Environment:

bash
Copy code
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install Dependencies:

bash
Copy code
pip install -r requirements.txt
Set Up Environment Variables:

Create a .env file in the root directory.

bash
Copy code
touch .env
Add the following to the .env file:

env
Copy code
OPENAI_API_KEY=your_openai_api_key_here
Replace your_openai_api_key_here with your actual OpenAI API key.

Run the Application:

bash
Copy code
uvicorn main:app --reload
Access the Application:

Open your web browser and navigate to http://localhost:8000 to access the tool.

Usage
Submit Project Description:

Enter your project description in the provided form to clean and enhance its clarity.
Identify Risks:

Automatically identify potential risks associated with your project.
Mitigate Risks:

Generate strategies to mitigate the identified risks effectively.
Analyze Risks:

Perform a detailed analysis of the identified risks.
Generate Metrics:

Compare productivity and performance metrics between Agile and Waterfall methodologies using interactive charts.
Get Recommendations:

Receive data-driven recommendations on whether Agile or Waterfall is more suitable for your project based on the analyzed data.
Navigate Through Stages:

Use the navigation buttons to explore different stages of the project lifecycle, including Design, Prototyping, Customer Evaluation, Review and Update, Development, Testing, and Maintenance.


This project leverages modern web technologies and AI capabilities to provide valuable insights into project management methodologies.
