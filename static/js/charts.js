/**
 * Energy Anomaly Detection System
 * Charts visualization module
 */

// Chart.js global settings
if (typeof Chart !== 'undefined') {
    Chart.defaults.color = '#ecf0f1';
    Chart.defaults.font.family = "'Roboto', 'Segoe UI', sans-serif";
    Chart.defaults.elements.line.borderWidth = 3;
    Chart.defaults.elements.line.tension = 0.3;
    Chart.defaults.elements.point.radius = 3;
    Chart.defaults.elements.point.hoverRadius = 5;
    Chart.defaults.plugins.legend.labels.boxWidth = 15;
    Chart.defaults.plugins.legend.labels.padding = 15;
    Chart.defaults.plugins.tooltip.titleFont.size = 14;
    Chart.defaults.plugins.tooltip.bodyFont.size = 13;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.displayColors = true;
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(10, 10, 20, 0.8)';
    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false;
}

// Store chart instances for later reference
const chartInstances = {};

/**
 * Initialize charts on the page
 */
function initializeCharts() {
    // Initialize dashboard overview charts if on dashboard page
    if (document.getElementById('anomalies-by-hour-chart')) {
        initializeDashboardCharts();
    }
    
    // Initialize results charts if on results page
    if (document.getElementById('time-series-chart')) {
        initializeResultCharts();
    }
    
    // Initialize model insights charts if on model insights page
    if (document.getElementById('model-performance-chart')) {
        initializeModelInsightCharts();
    }
}

/**
 * Initialize dashboard overview charts
 */
function initializeDashboardCharts() {
    const overviewDataElement = document.getElementById('overview-data');
    
    if (!overviewDataElement) return;
    
    try {
        const overviewData = JSON.parse(overviewDataElement.textContent);
        
        // Anomalies by hour chart
        createBarChart(
            'anomalies-by-hour-chart',
            {
                labels: overviewData.anomalies_by_hour.labels.map(hour => `${hour}:00`),
                datasets: [{
                    label: 'Anomalies',
                    data: overviewData.anomalies_by_hour.values,
                    backgroundColor: 'rgba(231, 76, 60, 0.7)',
                    borderColor: 'rgba(231, 76, 60, 1)',
                    borderWidth: 2
                }]
            },
            {
                plugins: {
                    title: {
                        display: true,
                        text: 'Anomalies by Hour of Day',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: function(tooltipItems) {
                                return `Hour: ${tooltipItems[0].label}`;
                            },
                            label: function(context) {
                                return `Anomalies: ${context.raw}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Hour of Day',
                            font: {
                                size: 14
                            }
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Anomalies',
                            font: {
                                size: 14
                            }
                        },
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        );
        
        // Results by algorithm chart
        if (overviewData.results_by_algorithm && overviewData.results_by_algorithm.labels.length > 0) {
            createPieChart(
                'results-by-algorithm-chart',
                {
                    labels: overviewData.results_by_algorithm.labels.map(algo => {
                        return algo.charAt(0).toUpperCase() + algo.slice(1).replace('_', ' ');
                    }),
                    datasets: [{
                        data: overviewData.results_by_algorithm.values,
                        backgroundColor: [
                            'rgba(46, 204, 113, 0.7)',
                            'rgba(52, 152, 219, 0.7)',
                            'rgba(155, 89, 182, 0.7)'
                        ],
                        borderColor: [
                            'rgba(46, 204, 113, 1)',
                            'rgba(52, 152, 219, 1)',
                            'rgba(155, 89, 182, 1)'
                        ],
                        borderWidth: 2
                    }]
                },
                {
                    plugins: {
                        title: {
                            display: true,
                            text: 'Anomaly Detection by Algorithm',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.raw;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            );
        } else {
            document.getElementById('results-by-algorithm-chart').innerHTML = 
                '<div class="d-flex align-items-center justify-content-center h-100">' +
                '<p class="text-muted">No algorithm results available yet</p>' +
                '</div>';
        }
        
        // Datasets over time chart
        if (overviewData.datasets_over_time && overviewData.datasets_over_time.labels.length > 0) {
            createLineChart(
                'datasets-over-time-chart',
                {
                    labels: overviewData.datasets_over_time.labels,
                    datasets: [{
                        label: 'Datasets Uploaded',
                        data: overviewData.datasets_over_time.values,
                        backgroundColor: 'rgba(26, 188, 156, 0.2)',
                        borderColor: 'rgba(26, 188, 156, 1)',
                        borderWidth: 2,
                        fill: true
                    }]
                },
                {
                    plugins: {
                        title: {
                            display: true,
                            text: 'Dataset Uploads Over Time',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Date',
                                font: {
                                    size: 14
                                }
                            },
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Number of Datasets',
                                font: {
                                    size: 14
                                }
                            },
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            );
        } else {
            document.getElementById('datasets-over-time-chart').innerHTML = 
                '<div class="d-flex align-items-center justify-content-center h-100">' +
                '<p class="text-muted">No dataset history available yet</p>' +
                '</div>';
        }
        
        // Model performance chart
        if (overviewData.model_performance && overviewData.model_performance.algorithms.length > 0) {
            createRadarChart(
                'model-performance-dashboard-chart',
                {
                    labels: ['Precision', 'Recall', 'F1 Score'],
                    datasets: overviewData.model_performance.algorithms.map((algo, index) => {
                        const colors = [
                            'rgba(46, 204, 113, 0.7)',  // green
                            'rgba(52, 152, 219, 0.7)',  // blue
                            'rgba(155, 89, 182, 0.7)'   // purple
                        ];
                        
                        return {
                            label: algo.charAt(0).toUpperCase() + algo.slice(1).replace('_', ' '),
                            data: [
                                overviewData.model_performance.precision[index],
                                overviewData.model_performance.recall[index],
                                overviewData.model_performance.f1_score[index]
                            ],
                            backgroundColor: colors[index % colors.length].replace('0.7', '0.2'),
                            borderColor: colors[index % colors.length].replace('0.7', '1'),
                            borderWidth: 2,
                            pointBackgroundColor: colors[index % colors.length].replace('0.7', '1')
                        };
                    })
                },
                {
                    plugins: {
                        title: {
                            display: true,
                            text: 'Model Performance Comparison',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        }
                    },
                    scales: {
                        r: {
                            angleLines: {
                                color: 'rgba(255, 255, 255, 0.15)'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            pointLabels: {
                                font: {
                                    size: 14
                                }
                            },
                            suggestedMin: 0,
                            suggestedMax: 1
                        }
                    }
                }
            );
        } else {
            document.getElementById('model-performance-dashboard-chart').innerHTML = 
                '<div class="d-flex align-items-center justify-content-center h-100">' +
                '<p class="text-muted">No model performance data available yet</p>' +
                '</div>';
        }
        
    } catch (error) {
        console.error('Error initializing dashboard charts:', error);
    }
}

/**
 * Initialize charts for the results page
 */
function initializeResultCharts() {
    // Get the selected result ID
    const resultIdElement = document.getElementById('selected-result-id');
    
    if (!resultIdElement || !resultIdElement.value) return;
    
    const resultId = resultIdElement.value;
    
    // Fetch result data
    fetch(`/api/result/${resultId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Time series chart with anomalies
            createTimeSeriesChart(data);
            
            // Metric charts
            if (data.metrics) {
                createMetricsCharts(data.metrics);
            }
            
            // Anomalies by hour if available
            if (data.time_series && data.time_series.timestamps) {
                createAnomaliesDistributionChart(data);
            }
        })
        .catch(error => {
            console.error('Error fetching result data:', error);
            document.getElementById('time-series-chart').innerHTML = 
                `<div class="alert alert-danger">Error loading chart data: ${error.message}</div>`;
        });
}

/**
 * Create time series chart with anomalies highlighted
 * @param {Object} data - The API response data
 */
function createTimeSeriesChart(data) {
    const timestamps = data.time_series.timestamps;
    const values = data.time_series.values;
    const anomalies = data.time_series.anomalies;
    
    // Process data to separate normal and anomaly points
    const normalPoints = [];
    const anomalyPoints = [];
    
    for (let i = 0; i < timestamps.length; i++) {
        if (anomalies[i] === 1) {
            anomalyPoints.push({
                x: timestamps[i],
                y: values[i]
            });
            // Add null for normal points to maintain the line
            normalPoints.push({
                x: timestamps[i],
                y: null
            });
        } else {
            normalPoints.push({
                x: timestamps[i],
                y: values[i]
            });
            // Add null for anomaly points
            anomalyPoints.push({
                x: timestamps[i],
                y: null
            });
        }
    }
    
    // Create the chart
    createScatterLineChart(
        'time-series-chart',
        {
            datasets: [
                {
                    label: 'Energy Consumption',
                    data: normalPoints,
                    borderColor: 'rgba(26, 188, 156, 1)',
                    backgroundColor: 'rgba(26, 188, 156, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false,
                    spanGaps: true
                },
                {
                    label: 'Anomalies',
                    data: anomalyPoints,
                    borderColor: 'rgba(231, 76, 60, 1)',
                    backgroundColor: 'rgba(231, 76, 60, 0.7)',
                    borderWidth: 0,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    pointStyle: 'circle',
                    spanGaps: false
                }
            ]
        },
        {
            plugins: {
                title: {
                    display: true,
                    text: 'Energy Consumption Time Series with Anomalies',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                tooltip: {
                    callbacks: {
                        title: function(tooltipItems) {
                            return tooltipItems[0].raw.x;
                        },
                        label: function(context) {
                            if (context.datasetIndex === 0 && context.raw.y !== null) {
                                return `Energy Value: ${context.raw.y}`;
                            } else if (context.datasetIndex === 1 && context.raw.y !== null) {
                                return `Anomaly: ${context.raw.y}`;
                            }
                            return '';
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'MMM d'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Time',
                        font: {
                            size: 14
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Energy Consumption',
                        font: {
                            size: 14
                        }
                    }
                }
            }
        }
    );
}

/**
 * Create metrics charts for the result
 * @param {Object} metrics - The metrics data
 */
function createMetricsCharts(metrics) {
    // Create gauge chart for precision, recall, f1_score
    if (metrics.precision !== undefined && 
        metrics.recall !== undefined && 
        metrics.f1_score !== undefined) {
        
        createGaugeChart(
            'metrics-chart',
            {
                labels: ['Precision', 'Recall', 'F1 Score'],
                datasets: [{
                    data: [
                        metrics.precision, 
                        metrics.recall, 
                        metrics.f1_score
                    ],
                    backgroundColor: [
                        'rgba(46, 204, 113, 0.7)',
                        'rgba(52, 152, 219, 0.7)',
                        'rgba(155, 89, 182, 0.7)'
                    ],
                    borderColor: [
                        'rgba(46, 204, 113, 1)',
                        'rgba(52, 152, 219, 1)',
                        'rgba(155, 89, 182, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            {
                plugins: {
                    title: {
                        display: true,
                        text: 'Model Performance Metrics',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                return `${context.label}: ${(value * 100).toFixed(1)}%`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        ticks: {
                            callback: function(value) {
                                return (value * 100) + '%';
                            }
                        }
                    }
                }
            }
        );
    }
    
    // Create anomaly summary donut chart
    if (metrics.anomaly_count !== undefined && metrics.total_points !== undefined) {
        const normalCount = metrics.total_points - metrics.anomaly_count;
        createDoughnutChart(
            'anomaly-summary-chart',
            {
                labels: ['Normal Points', 'Anomalies'],
                datasets: [{
                    data: [normalCount, metrics.anomaly_count],
                    backgroundColor: [
                        'rgba(46, 204, 113, 0.7)',
                        'rgba(231, 76, 60, 0.7)'
                    ],
                    borderColor: [
                        'rgba(46, 204, 113, 1)',
                        'rgba(231, 76, 60, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            {
                plugins: {
                    title: {
                        display: true,
                        text: 'Anomaly Distribution',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        );
    }
}

/**
 * Create anomalies distribution chart by time features
 * @param {Object} data - The API response data
 */
function createAnomaliesDistributionChart(data) {
    if (!data.anomalies_by_hour) return;
    
    // Anomalies by hour
    createBarChart(
        'anomalies-distribution-chart',
        {
            labels: data.anomalies_by_hour.labels.map(hour => `${hour}:00`),
            datasets: [{
                label: 'Anomalies',
                data: data.anomalies_by_hour.values,
                backgroundColor: 'rgba(231, 76, 60, 0.7)',
                borderColor: 'rgba(231, 76, 60, 1)',
                borderWidth: 2
            }]
        },
        {
            plugins: {
                title: {
                    display: true,
                    text: 'Anomalies by Hour of Day',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Hour of Day',
                        font: {
                            size: 14
                        }
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Anomalies',
                        font: {
                            size: 14
                        }
                    },
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    );
}

/**
 * Initialize charts for the model insights page
 */
function initializeModelInsightCharts() {
    const modelPerformanceData = document.getElementById('model-performance-data');
    
    if (!modelPerformanceData) return;
    
    try {
        const performanceData = JSON.parse(modelPerformanceData.textContent);
        
        // Create comparison radar chart
        createRadarChart(
            'model-performance-chart',
            {
                labels: ['Precision', 'Recall', 'F1 Score', 'Efficiency', 'Interpretability'],
                datasets: performanceData.map((model, index) => {
                    const colors = [
                        'rgba(46, 204, 113, 0.7)',  // green
                        'rgba(52, 152, 219, 0.7)',  // blue
                        'rgba(155, 89, 182, 0.7)'   // purple
                    ];
                    
                    return {
                        label: model.name,
                        data: [
                            model.precision,
                            model.recall,
                            model.f1_score,
                            model.efficiency,
                            model.interpretability
                        ],
                        backgroundColor: colors[index % colors.length].replace('0.7', '0.2'),
                        borderColor: colors[index % colors.length].replace('0.7', '1'),
                        borderWidth: 2,
                        pointBackgroundColor: colors[index % colors.length].replace('0.7', '1')
                    };
                })
            },
            {
                plugins: {
                    title: {
                        display: true,
                        text: 'Model Performance Comparison',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    }
                },
                scales: {
                    r: {
                        angleLines: {
                            color: 'rgba(255, 255, 255, 0.15)'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        pointLabels: {
                            font: {
                                size: 14
                            }
                        },
                        suggestedMin: 0,
                        suggestedMax: 1
                    }
                }
            }
        );
        
        // Create anomaly detection comparison
        if (document.getElementById('anomaly-comparison-chart')) {
            createBarChart(
                'anomaly-comparison-chart',
                {
                    labels: performanceData.map(model => model.name),
                    datasets: [{
                        label: 'Anomalies Detected',
                        data: performanceData.map(model => model.anomalies_detected),
                        backgroundColor: getChartColors(performanceData.length),
                        borderColor: getChartColors(performanceData.length, 1),
                        borderWidth: 2
                    }]
                },
                {
                    plugins: {
                        title: {
                            display: true,
                            text: 'Anomalies Detected by Model',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Number of Anomalies',
                                font: {
                                    size: 14
                                }
                            },
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            );
        }
        
        // Create execution time comparison
        if (document.getElementById('execution-time-chart')) {
            createBarChart(
                'execution-time-chart',
                {
                    labels: performanceData.map(model => model.name),
                    datasets: [{
                        label: 'Execution Time (seconds)',
                        data: performanceData.map(model => model.execution_time),
                        backgroundColor: getChartColors(performanceData.length),
                        borderColor: getChartColors(performanceData.length, 1),
                        borderWidth: 2
                    }]
                },
                {
                    plugins: {
                        title: {
                            display: true,
                            text: 'Model Execution Time Comparison',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Execution Time (seconds)',
                                font: {
                                    size: 14
                                }
                            }
                        }
                    }
                }
            );
        }
        
    } catch (error) {
        console.error('Error initializing model insight charts:', error);
    }
}

/**
 * Create a line chart
 * @param {string} canvasId - The canvas element ID
 * @param {Object} data - The chart data
 * @param {Object} options - The chart options
 * @returns {Chart} - The Chart.js instance
 */
function createLineChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    
    if (!ctx) return null;
    
    // Destroy existing chart if it exists
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }
    
    // Create new chart
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'line',
        data: data,
        options: options
    });
    
    return chartInstances[canvasId];
}

/**
 * Create a bar chart
 * @param {string} canvasId - The canvas element ID
 * @param {Object} data - The chart data
 * @param {Object} options - The chart options
 * @returns {Chart} - The Chart.js instance
 */
function createBarChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    
    if (!ctx) return null;
    
    // Destroy existing chart if it exists
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }
    
    // Create new chart
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: options
    });
    
    return chartInstances[canvasId];
}

/**
 * Create a pie chart
 * @param {string} canvasId - The canvas element ID
 * @param {Object} data - The chart data
 * @param {Object} options - The chart options
 * @returns {Chart} - The Chart.js instance
 */
function createPieChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    
    if (!ctx) return null;
    
    // Destroy existing chart if it exists
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }
    
    // Create new chart
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'pie',
        data: data,
        options: options
    });
    
    return chartInstances[canvasId];
}

/**
 * Create a doughnut chart
 * @param {string} canvasId - The canvas element ID
 * @param {Object} data - The chart data
 * @param {Object} options - The chart options
 * @returns {Chart} - The Chart.js instance
 */
function createDoughnutChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    
    if (!ctx) return null;
    
    // Destroy existing chart if it exists
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }
    
    // Create new chart
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: options
    });
    
    return chartInstances[canvasId];
}

/**
 * Create a radar chart
 * @param {string} canvasId - The canvas element ID
 * @param {Object} data - The chart data
 * @param {Object} options - The chart options
 * @returns {Chart} - The Chart.js instance
 */
function createRadarChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    
    if (!ctx) return null;
    
    // Destroy existing chart if it exists
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }
    
    // Create new chart
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'radar',
        data: data,
        options: options
    });
    
    return chartInstances[canvasId];
}

/**
 * Create a scatter plot combined with line chart
 * @param {string} canvasId - The canvas element ID
 * @param {Object} data - The chart data
 * @param {Object} options - The chart options
 * @returns {Chart} - The Chart.js instance
 */
function createScatterLineChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    
    if (!ctx) return null;
    
    // Destroy existing chart if it exists
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }
    
    // Create new chart
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'line',
        data: data,
        options: options
    });
    
    return chartInstances[canvasId];
}

/**
 * Create a gauge chart (using horizontal bar chart)
 * @param {string} canvasId - The canvas element ID
 * @param {Object} data - The chart data
 * @param {Object} options - The chart options
 * @returns {Chart} - The Chart.js instance
 */
function createGaugeChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    
    if (!ctx) return null;
    
    // Destroy existing chart if it exists
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }
    
    // Create new chart
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            indexAxis: 'y',
            ...options
        }
    });
    
    return chartInstances[canvasId];
}
