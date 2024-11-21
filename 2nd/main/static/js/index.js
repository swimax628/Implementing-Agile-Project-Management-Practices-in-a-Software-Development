// static/js/index.js

// Global variables
let cleanedDescription = '';

// Function to escape HTML to prevent XSS
function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

// Function to check if the cleaned description is available
function checkCleanedDescription() {
    if (!cleanedDescription || cleanedDescription.trim() === "") {
        cleanedDescription = sessionStorage.getItem('cleanedDescription');
        if (!cleanedDescription || cleanedDescription.trim() === "") {
            alert('Cleaned description is not available. Please analyse the project first.');
            return false;
        }
    }
    return true;
}

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Event listener for 'Submit Description' button on index.html
    const submitDescriptionButton = document.getElementById('submitDescriptionButton');
    if (submitDescriptionButton) {
        submitDescriptionButton.addEventListener('click', submitDescription);
    }

    // Event listener for 'Generate Charts' button
    const generateChartsButton = document.getElementById('generateChartsButton');
    if (generateChartsButton) {
        generateChartsButton.addEventListener('click', generateChartsHandler);
    }

    // Event listener for 'View Analyses' button
    const viewAnalysesButton = document.getElementById('viewAnalysesButton');
    if (viewAnalysesButton) {
        viewAnalysesButton.addEventListener('click', function() {
            window.location.href = '/all_analysis';
        });
    }

    // Event listener for 'Clean Description' button on clean_description.html
    const cleanDescriptionButton = document.getElementById('cleanDescriptionButton');
    if (cleanDescriptionButton) {
        cleanDescriptionButton.addEventListener('click', cleanDescriptionHandler);
    }

    // Event listener for 'Comprehensive Analysis' button
    const comprehensiveAnalysisButton = document.getElementById('comprehensiveAnalysisButton');
    if (comprehensiveAnalysisButton) {
        comprehensiveAnalysisButton.addEventListener('click', function() {
            if (checkCleanedDescription()) {
                window.location.href = '/comprehensive_analysis?description=' + encodeURIComponent(cleanedDescription);
            } else {
                alert('Please analyze the project first.');
            }
        });
    }

    // Attach event listeners for stage-specific pages
    attachStageEventListeners();

    // Update navbar links with cleaned description
    updateNavbarLinks();

    // Attach event listener for 'Test Prototype' button
    attachTestPrototypeListener();

    // Additional page-specific initialization
    initializePage();

    // If on all_analysis.html, fetch all analyses
    if (window.location.pathname === '/all_analysis') {
        fetchAllAnalyses();
    }
});


// Function to submit the project description and initiate analyses
async function submitDescription() {
    const descriptionInput = document.getElementById('description');
    const description = descriptionInput.value.trim();

    if (!description) {
        alert('Please enter a project description.');
        return;
    }

    try {
        // Clean the description
        cleanedDescription = await cleanDescription(description);

        // Display the cleaned description
        displayCleanedDescription(cleanedDescription);

        // Store the cleaned description in sessionStorage
        sessionStorage.setItem('cleanedDescription', cleanedDescription);

        // Perform analyses
        await identifyRisks(cleanedDescription);
        await getMethodologyRecommendation(cleanedDescription);
        await benchmarkEstimation(cleanedDescription);

        // Show the buttons to generate charts and view analyses
        document.getElementById('generateChartsButton').style.display = 'inline-block';
        document.getElementById('viewAnalysesButton').style.display = 'inline-block';
        document.getElementById('comprehensiveAnalysisButton').style.display = 'inline-block';

    } catch (error) {
        console.error("Error processing description:", error);
        alert("Failed to process the project description. Please check your API or network connection.");
    }
}

// Function to clean the project description using the backend API
async function cleanDescription(description) {
    const response = await fetch('/clean_description/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: description })
    });

    if (!response.ok) throw new Error("Network response was not ok");

    const data = await response.json();
    return data.cleaned_description;
}

// Function to handle cleaning the description on clean_description.html
async function cleanDescriptionHandler() {
    const descriptionInput = document.getElementById('projectDescription');
    const description = descriptionInput.value.trim();

    if (!description) {
        alert('Please enter a project description.');
        return;
    }

    try {
        // Clean the description
        cleanedDescription = await cleanDescription(description);

        // Display the cleaned description
        const cleanedDescriptionElement = document.getElementById('cleanedDescription');
        cleanedDescriptionElement.innerText = cleanedDescription;
        document.getElementById('cleanedDescriptionSection').style.display = 'block';

        // Update the 'Proceed to Analysis' link
        const proceedLink = document.getElementById('proceedToAnalysisLink');
        proceedLink.href = '/all_analysis?description=' + encodeURIComponent(cleanedDescription);

        // Store the cleaned description in sessionStorage
        sessionStorage.setItem('cleanedDescription', cleanedDescription);

    } catch (error) {
        console.error('Error cleaning description:', error);
        alert('Failed to clean description. Please check your API or network connection.');
    }
}

// Function to display the cleaned description on the page
function displayCleanedDescription(cleanedDescription) {
    const cleanedResultElement = document.getElementById('cleaned-result');
    cleanedResultElement.innerHTML = '';
    const strongElement = document.createElement('strong');
    strongElement.textContent = 'Cleaned Description:';
    cleanedResultElement.appendChild(strongElement);
    cleanedResultElement.appendChild(document.createElement('br'));
    const descriptionTextNode = document.createTextNode(cleanedDescription);
    cleanedResultElement.appendChild(descriptionTextNode);
}

// Function to identify risks using the backend API
async function identifyRisks(description) {
    try {
        const response = await fetch('/identify_risks/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: description })
        });

        if (!response.ok) throw new Error("Network response was not ok");

        const data = await response.json();

        const assessmentContent = data.assessment || "No risk assessment available.";
        document.getElementById('riskAssessmentContent').innerText = assessmentContent;
        document.getElementById('riskAssessmentSection').style.display = 'block';

    } catch (error) {
        console.error("Error fetching risk assessment:", error);
        alert("Failed to fetch risk assessment. Please check your API or network connection.");
    }
}

// Function to get methodology recommendation using the backend API
async function getMethodologyRecommendation(description) {
    try {
        const response = await fetch('/recommend_methodology/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: description })
        });

        if (!response.ok) throw new Error("Network response was not ok");

        const data = await response.json();

        const recommendationContent = data.recommendation_details || "No recommendation available.";
        document.getElementById('methodologyContent').innerText = recommendationContent;
        document.getElementById('methodologySection').style.display = 'block';

    } catch (error) {
        console.error("Error fetching methodology recommendation:", error);
        alert("Failed to fetch methodology recommendation. Please check your API or network connection.");
    }
}

// Function to benchmark estimation using the backend API
async function benchmarkEstimation(description) {
    try {
        const response = await fetch('/benchmark_estimation/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: description })
        });

        if (!response.ok) throw new Error("Network response was not ok");

        const data = await response.json();

        let estimationContent = '';
        if (data.estimation_accuracy !== null) {
            estimationContent += `Estimation Accuracy: ${data.estimation_accuracy.toFixed(2)}%\n`;
        } else {
            estimationContent += `Estimation accuracy could not be calculated.\n`;
        }
        if (data.complexity_manageable !== null) {
            estimationContent += `Complexity Manageability: ${data.complexity_manageable ? 'Manageable' : 'Not Manageable'}\n`;
        } else {
            estimationContent += `Complexity manageability could not be assessed.\n`;
        }
        if (data.message) {
            estimationContent += `\n${data.message}`;
        }

        document.getElementById('estimationContent').innerText = estimationContent;
        document.getElementById('estimationSection').style.display = 'block';

    } catch (error) {
        console.error("Error fetching estimation benchmarking:", error);
        alert("Failed to fetch estimation benchmarking. Please check your API or network connection.");
    }
}

// Function to handle generating charts
// Function to handle generating charts with added null and data validation
async function generateChartsHandler() {
    if (!checkCleanedDescription()) return;

    try {
        const response = await fetch('/generate_productivity/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: cleanedDescription })
        });

        if (!response.ok) throw new Error("Network response was not ok");

        const data = await response.json();

        // Check for null, undefined, and data type validation in the API response
        const agileData = data.agile_productivity;
        const waterfallData = data.waterfall_productivity;

        if (
            !Array.isArray(agileData) || agileData.length !== 5 || agileData.some(value => typeof value !== 'number' || isNaN(value)) ||
            !Array.isArray(waterfallData) || waterfallData.length !== 5 || waterfallData.some(value => typeof value !== 'number' || isNaN(value))
        ) {
            throw new Error("Invalid data format or non-numeric/missing values received from the server.");
        }

        // Generate charts
        generateCharts(agileData, waterfallData);
        document.getElementById('chartsSection').style.display = 'flex';

    } catch (error) {
        console.error("Error fetching or validating productivity data:", error);
        alert("Failed to fetch or validate productivity data. Please check your API or network connection.");
    }
}


// Function to generate productivity charts using Chart.js
function generateCharts(agileValues, waterfallValues) {
    // Labels for the charts
    const labels = agileValues.map((_, index) => `Point ${index + 1}`);

    // Agile Productivity Chart Data
    const agileChartData = {
        labels: labels,
        datasets: [{
            label: 'Agile Productivity',
            data: agileValues,
            backgroundColor: 'rgba(75, 192, 192, 0.6)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 2
        }]
    };

    // Waterfall Productivity Chart Data
    const waterfallChartData = {
        labels: labels,
        datasets: [{
            label: 'Waterfall Productivity',
            data: waterfallValues,
            backgroundColor: 'rgba(255, 99, 132, 0.6)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 2
        }]
    };

    // Configuration for Agile Chart
    const configAgile = {
        type: 'bar',
        data: agileChartData,
        options: getChartOptions()
    };

    // Configuration for Waterfall Chart
    const configWaterfall = {
        type: 'bar',
        data: waterfallChartData,
        options: getChartOptions()
    };

    // Destroy existing charts if they exist
    if (window.agileChartInstance) {
        window.agileChartInstance.destroy();
    }
    if (window.waterfallChartInstance) {
        window.waterfallChartInstance.destroy();
    }

    // Render Agile Chart
    const agileCtx = document.getElementById('agileChart').getContext('2d');
    window.agileChartInstance = new Chart(agileCtx, configAgile);

    // Render Waterfall Chart
    const waterfallCtx = document.getElementById('waterfallChart').getContext('2d');
    window.waterfallChartInstance = new Chart(waterfallCtx, configWaterfall);
}

// Helper function to get common chart options
function getChartOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Productivity'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Time Points'
                }
            }
        },
        plugins: {
            legend: {
                display: true,
                position: 'top'
            }
        }
    };
}

// Function to attach event listeners for stage-specific pages
function attachStageEventListeners() {
    // Map of stage IDs to their corresponding generate functions
    const stageFunctions = {
        'generateDesignButton': generateDesign,
        'generatePrototypingButton': generatePrototyping,
        'generateCustomerEvaluationButton': generateCustomerEvaluationPlan,
        'generateReviewUpdateButton': generateReviewUpdatePlan,
        'generateDevelopmentButton': generateDevelopmentPlan,
        'generateTestingButton': generateTesting,
        'generateMaintenanceButton': generateMaintenancePlan
    };

    for (const [buttonId, func] of Object.entries(stageFunctions)) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.addEventListener('click', func);
        }
    }
}

// Function to update navbar links with the cleaned description
function updateNavbarLinks() {
    const navLinks = document.querySelectorAll('#nav-links a');
    if (navLinks.length > 0) {
        let description = sessionStorage.getItem('cleanedDescription') || '';
        if (description) {
            const encodedDescription = encodeURIComponent(description);
            navLinks.forEach(function(link) {
                const href = link.getAttribute('href').split('?')[0];
                link.setAttribute('href', `${href}?description=${encodedDescription}`);
            });
        }
    }
}

// Function to initialize page-specific content
function initializePage() {
    // For identified_risks.html
    const identifiedRisksContent = document.getElementById('identifiedRisksContent');
    if (identifiedRisksContent && !identifiedRisksContent.innerText.trim()) {
        fetchRiskContent('/identify_risks/', 'assessment', 'identifiedRisksContent');
    }

    // For risk_assessment.html
    const riskAssessmentContent = document.getElementById('riskAssessmentContent');
    if (riskAssessmentContent && !riskAssessmentContent.innerText.trim()) {
        fetchRiskContent('/generate_risk_assessment/', 'assessment', 'riskAssessmentContent');
    }

    // For risk_mitigation.html
    const riskMitigationContent = document.getElementById('riskMitigationContent');
    if (riskMitigationContent && !riskMitigationContent.innerText.trim()) {
        fetchRiskContent('/generate_risk_mitigation/', 'mitigation_strategies', 'riskMitigationContent');
    }
}

// General function to fetch risk content
async function fetchRiskContent(endpoint, dataKey, contentElementId) {
    if (!checkCleanedDescription()) return;

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: cleanedDescription })
        });

        if (!response.ok) throw new Error('Network response was not ok');

        const data = await response.json();
        document.getElementById(contentElementId).innerText = data[dataKey];

    } catch (error) {
        console.error(`Error fetching content from ${endpoint}:`, error);
        alert('Failed to fetch content. Please check your API or network connection.');
    }
}

// Function to generate Design content
async function generateDesign() {
    await generateStageContent('design', 'design_content');
}

// Function to generate Prototyping content
async function generatePrototyping() {
    await generateStageContent('prototyping', 'prototyping_content');
}

// Function to generate Customer Evaluation Plan
async function generateCustomerEvaluationPlan() {
    await generateStageContent('customer_evaluation', 'customer_evaluation_content');
}

// Function to generate Review and Update Plan
async function generateReviewUpdatePlan() {
    await generateStageContent('review_and_update', 'review_update_content');
}

// Function to generate Development Plan
async function generateDevelopmentPlan() {
    await generateStageContent('development', 'development_content');
}

// Function to generate Testing Plan
async function generateTesting() {
    await generateStageContent('testing', 'testing_content');
}

// Function to generate Maintenance Plan
async function generateMaintenancePlan() {
    await generateStageContent('maintenance', 'maintenance_content');
}

// General function to generate content for a stage
async function generateStageContent(stage, contentElementId) {
    if (!checkCleanedDescription()) return;

    try {
        const response = await fetch(`/generate_${stage}/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: cleanedDescription })
        });

        if (!response.ok) throw new Error(`Network response was not ok`);

        const data = await response.json();
        document.getElementById(contentElementId).innerText = data[`${stage}_content`];

    } catch (error) {
        console.error(`Error fetching ${stage} content:`, error);
        alert(`Failed to generate ${stage} plan. Please check your API or network connection.`);
    }
}

// Function to attach event listener for 'Test Prototype' button
function attachTestPrototypeListener() {
    const testButton = document.getElementById('testButton');
    if (testButton) {
        testButton.addEventListener('click', testPrototype);
    }
}

// Function to handle prototype testing
async function testPrototype() {
    const testDescriptionInput = document.getElementById('test_description');
    const testDescription = testDescriptionInput.value.trim();

    // Retrieve cleanedDescription from sessionStorage
    let cleanedDescription = sessionStorage.getItem('cleanedDescription');

    if (!testDescription) {
        alert('Please enter a test description.');
        return;
    }

    if (!cleanedDescription || cleanedDescription.trim() === "") {
        alert('Cleaned description is not available. Please return to the main page and analyze the project first.');
        return;
    }

    try {
        // Disable the test button to prevent multiple submissions
        const testButton = document.getElementById('testButton');
        testButton.disabled = true;

        const response = await fetch('/test_prototype/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                description: cleanedDescription,
                test_description: testDescription
            })
        });

        if (!response.ok) throw new Error('Network response was not ok');

        const data = await response.json();
        document.getElementById('test_results').innerText = data.test_results;
        document.getElementById('testResultSection').style.display = 'block';
        testButton.disabled = false;
    } catch (error) {
        console.error('Error during prototype testing:', error);
        alert('Failed to test prototype. Please check your API or network connection.');
        document.getElementById('testButton').disabled = false;
    }
}

// Function to fetch and display all analyses on all_analysis.html
async function fetchAllAnalyses() {
    if (!checkCleanedDescription()) return;

    try {
        // Fetch Defect Density Analysis
        await fetchAnalysis('/analysis/promise/defect_density', 'defectDensityAnalysis', 'Defect Density Analysis');
        
        // Fetch Effort and Resolution Time Comparison
        await fetchAnalysis('/analysis/tawos/effort_resolution_comparison', 'effortResolutionTimeComparison', 'Effort and Resolution Time Analysis');
        
        // Fetch T-Tests Analysis
        await fetchAnalysis('/analysis/promise/t_tests', 'tTestsAnalysis', 'T-Tests Analysis');
        
    } catch (error) {
        console.error('Error fetching analyses:', error);
        alert('Failed to fetch analyses. Please check your API or network connection.');
    }
}

// Helper function to fetch each analysis
async function fetchAnalysis(endpoint, elementId, analysisName) {
    try {
        const response = await fetch(endpoint, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
            const content = await response.text();
            document.getElementById(elementId).innerHTML = content;
        } else {
            document.getElementById(elementId).innerHTML = `<p>Failed to load ${analysisName}.</p>`;
        }
    } catch (error) {
        console.error(`Error fetching ${analysisName}:`, error);
        document.getElementById(elementId).innerHTML = `<p>Failed to load ${analysisName} due to a network error.</p>`;
    }
}

// Function to check if the analysis is ready and display the button
function checkAnalysisComplete() {
    // Add logic to determine if the analysis is complete
    return true; // Placeholder return
}

// Modify existing functions or add new ones to update the display of the button based on the completion of the analysis

