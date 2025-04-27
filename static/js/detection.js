/**
 * Energy Anomaly Detection System
 * Detection page specific JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize algorithm explanations
    initializeAlgorithmInfos();
    
    // Setup detection form event handlers
    setupDetectionForm();
    
    // Initialize algorithm selection visualization
    initializeAlgorithmVisualization();
});

/**
 * Set up detection form event handlers
 */
function setupDetectionForm() {
    const detectionForm = document.getElementById('detection-form');
    
    if (!detectionForm) return;
    
    // Dataset selection change handler
    const datasetSelect = document.getElementById('dataset');
    if (datasetSelect) {
        datasetSelect.addEventListener('change', function() {
            const datasetId = this.value;
            if (datasetId) {
                // Update dataset preview
                updateDatasetPreview(datasetId);
            }
        });
        
        // Trigger change on page load if a dataset is selected
        if (datasetSelect.value) {
            updateDatasetPreview(datasetSelect.value);
        }
    }
    
    // Algorithm selection change handler
    const algorithmSelect = document.getElementById('algorithm');
    if (algorithmSelect) {
        algorithmSelect.addEventListener('change', function() {
            const algorithm = this.value;
            updateAlgorithmInfo(algorithm);
            updateAlgorithmVisualization(algorithm);
        });
        
        // Trigger change on page load
        if (algorithmSelect.value) {
            updateAlgorithmInfo(algorithmSelect.value);
            updateAlgorithmVisualization(algorithmSelect.value);
        }
    }
    
    // Form submission
    detectionForm.addEventListener('submit', function(e) {
        // Show processing overlay
        const processingOverlay = document.getElementById('processing-overlay');
        if (processingOverlay) {
            processingOverlay.classList.add('show');
        }
        
        // In a real application, the form would submit normally as the backend will handle the processing
        // This just adds a visual confirmation that the form is being processed
    });
}

/**
 * Initialize algorithm info cards
 */
function initializeAlgorithmInfos() {
    // Hide all algorithm info cards initially
    const infoCards = document.querySelectorAll('.algorithm-info');
    infoCards.forEach(card => {
        card.style.display = 'none';
    });
    
    // Show the first one if no algorithm is selected yet
    const algorithmSelect = document.getElementById('algorithm');
    if (algorithmSelect && algorithmSelect.value) {
        const selectedInfo = document.getElementById(`${algorithmSelect.value}-info`);
        if (selectedInfo) {
            selectedInfo.style.display = 'block';
        }
    } else if (infoCards.length > 0) {
        infoCards[0].style.display = 'block';
    }
}

/**
 * Update the algorithm info card when selection changes
 * @param {string} algorithm - The selected algorithm value
 */
function updateAlgorithmInfo(algorithm) {
    // Hide all algorithm info cards
    const infoCards = document.querySelectorAll('.algorithm-info');
    infoCards.forEach(card => {
        card.style.display = 'none';
    });
    
    // Show the selected one
    const selectedInfo = document.getElementById(`${algorithm}-info`);
    if (selectedInfo) {
        selectedInfo.style.display = 'block';
        
        // Add a fade-in effect
        selectedInfo.style.opacity = '0';
        selectedInfo.style.transition = 'opacity 0.5s ease';
        
        setTimeout(() => {
            selectedInfo.style.opacity = '1';
        }, 50);
    }
}

/**
 * Update dataset preview when selection changes
 * @param {string} datasetId - The selected dataset ID
 */
function updateDatasetPreview(datasetId) {
    const previewContainer = document.getElementById('dataset-preview');
    
    if (!previewContainer) return;
    
    // Show loading spinner
    showLoadingSpinner('dataset-preview', 'Loading dataset preview...');
    
    // In a real application, this would fetch the dataset preview from the server
    // For now, we'll just display some info based on the dataset-info data attributes
    
    const datasetOption = document.querySelector(`#dataset option[value="${datasetId}"]`);
    
    if (datasetOption) {
        const fileName = datasetOption.getAttribute('data-filename') || 'Unknown';
        const rowCount = datasetOption.getAttribute('data-rows') || 'Unknown';
        const uploadDate = datasetOption.getAttribute('data-date') || 'Unknown';
        
        setTimeout(() => {
            // Update the preview with dataset info
            const previewHTML = `
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">Dataset Preview</h5>
                        <span class="badge bg-primary">${rowCount} rows</span>
                    </div>
                    <div class="card-body">
                        <p><strong>Filename:</strong> ${fileName}</p>
                        <p><strong>Uploaded:</strong> ${formatDate(uploadDate, true)}</p>
                        <div class="dataset-visualization">
                            <div class="placeholder-chart">
                                <i class="fas fa-chart-line fa-3x mb-3"></i>
                                <p class="text-muted">Dataset visualization will appear after running detection</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove loading spinner and show preview
            previewContainer.innerHTML = previewHTML;
        }, 500);
    } else {
        // No dataset selected or found
        previewContainer.innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                No dataset selected or dataset information not available.
            </div>
        `;
    }
}

/**
 * Initialize algorithm visualization
 */
function initializeAlgorithmVisualization() {
    const visualizationCanvas = document.getElementById('algorithm-visualization');
    
    if (!visualizationCanvas) return;
    
    // Algorithm visualizations will be created dynamically based on selection
    const algorithmSelect = document.getElementById('algorithm');
    
    if (algorithmSelect && algorithmSelect.value) {
        updateAlgorithmVisualization(algorithmSelect.value);
    } else {
        // Create default visualization
        createDefaultAlgorithmVisualization(visualizationCanvas);
    }
}

/**
 * Update the algorithm visualization when selection changes
 * @param {string} algorithm - The selected algorithm value
 */
function updateAlgorithmVisualization(algorithm) {
    const visualizationCanvas = document.getElementById('algorithm-visualization');
    
    if (!visualizationCanvas) return;
    
    // Clear any existing chart
    if (chartInstances['algorithm-visualization']) {
        chartInstances['algorithm-visualization'].destroy();
    }
    
    // Create appropriate visualization based on algorithm
    switch (algorithm) {
        case 'isolation_forest':
            createIsolationForestVisualization(visualizationCanvas);
            break;
        case 'autoencoder':
            createAutoencoderVisualization(visualizationCanvas);
            break;
        case 'kmeans':
            createKMeansVisualization(visualizationCanvas);
            break;
        default:
            createDefaultAlgorithmVisualization(visualizationCanvas);
    }
}

/**
 * Create default algorithm visualization
 * @param {HTMLElement} canvas - The canvas element
 */
function createDefaultAlgorithmVisualization(canvas) {
    // Generate some sample data
    const labels = ['Feature 1', 'Feature 2', 'Feature 3', 'Feature 4', 'Feature 5'];
    const normalData = [65, 59, 80, 81, 56];
    const anomalyData = [28, 48, 40, 19, 96];
    
    // Create the chart
    chartInstances['algorithm-visualization'] = new Chart(canvas, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Normal Data',
                    data: normalData,
                    backgroundColor: 'rgba(46, 204, 113, 0.2)',
                    borderColor: 'rgba(46, 204, 113, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(46, 204, 113, 1)'
                },
                {
                    label: 'Anomalies',
                    data: anomalyData,
                    backgroundColor: 'rgba(231, 76, 60, 0.2)',
                    borderColor: 'rgba(231, 76, 60, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(231, 76, 60, 1)'
                }
            ]
        },
        options: {
            plugins: {
                title: {
                    display: true,
                    text: 'Anomaly Detection Visualization',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            },
            scales: {
                r: {
                    angleLines: {
                        color: 'rgba(255, 255, 255, 0.2)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

/**
 * Create Isolation Forest visualization
 * @param {HTMLElement} canvas - The canvas element
 */
function createIsolationForestVisualization(canvas) {
    // Sample data for visualization
    const data = [];
    const labels = [];
    const anomalyScores = [];
    
    // Generate sample normal data points
    for (let i = 0; i < 50; i++) {
        const value = 50 + Math.random() * 15;
        data.push(value);
        labels.push(`P${i}`);
        anomalyScores.push(Math.random() * 0.3); // Low anomaly scores
    }
    
    // Add some anomalies
    for (let i = 50; i < 60; i++) {
        const anomalyValue = Math.random() > 0.5 ? 
            100 + Math.random() * 30 : // High anomalies
            10 + Math.random() * 20;   // Low anomalies
        data.push(anomalyValue);
        labels.push(`P${i}`);
        anomalyScores.push(0.7 + Math.random() * 0.3); // High anomaly scores
    }
    
    // Create the chart
    chartInstances['algorithm-visualization'] = new Chart(canvas, {
        type: 'scatter',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Data Points',
                    data: data.map((value, index) => ({
                        x: index,
                        y: value,
                        r: anomalyScores[index] * 20 // Scale for visibility
                    })),
                    backgroundColor: data.map((_, index) => {
                        return anomalyScores[index] > 0.5 ? 
                            'rgba(231, 76, 60, 0.7)' : // Anomalies
                            'rgba(46, 204, 113, 0.7)'; // Normal points
                    }),
                    borderColor: data.map((_, index) => {
                        return anomalyScores[index] > 0.5 ? 
                            'rgba(231, 76, 60, 1)' : // Anomalies
                            'rgba(46, 204, 113, 1)'; // Normal points
                    }),
                    borderWidth: 1
                }
            ]
        },
        options: {
            plugins: {
                title: {
                    display: true,
                    text: 'Isolation Forest Visualization',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            return `Value: ${data[index]}, Anomaly Score: ${anomalyScores[index].toFixed(2)}`;
                        }
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
                        text: 'Data Point Index',
                        font: {
                            size: 14
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Value',
                        font: {
                            size: 14
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create Autoencoder visualization
 * @param {HTMLElement} canvas - The canvas element
 */
function createAutoencoderVisualization(canvas) {
    // Sample data for visualization
    const originalValues = [];
    const reconstructedValues = [];
    const anomalyFlags = [];
    
    // Generate data for a smooth curve with some anomalies
    for (let i = 0; i < 50; i++) {
        // Base signal: sine wave
        const baseValue = 50 + 20 * Math.sin(i * 0.2);
        
        // Add random noise to original value
        const originalValue = baseValue + (Math.random() * 5 - 2.5);
        originalValues.push(originalValue);
        
        // For normal points, reconstruction is close to original
        let reconstructedValue, isAnomaly;
        
        // Introduce some anomalies
        if (i % 10 === 0 || i % 13 === 0) {
            // Anomaly: large difference between original and reconstructed
            reconstructedValue = baseValue; // Reconstruction doesn't capture the anomaly
            isAnomaly = 1;
        } else {
            // Normal: small difference
            reconstructedValue = baseValue + (Math.random() * 2 - 1);
            isAnomaly = 0;
        }
        
        reconstructedValues.push(reconstructedValue);
        anomalyFlags.push(isAnomaly);
    }
    
    // Create the chart
    chartInstances['algorithm-visualization'] = new Chart(canvas, {
        type: 'line',
        data: {
            labels: Array.from({ length: originalValues.length }, (_, i) => i),
            datasets: [
                {
                    label: 'Original Values',
                    data: originalValues,
                    borderColor: 'rgba(52, 152, 219, 1)',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    fill: false,
                    borderWidth: 2,
                    pointRadius: 0
                },
                {
                    label: 'Reconstructed Values',
                    data: reconstructedValues,
                    borderColor: 'rgba(46, 204, 113, 1)',
                    backgroundColor: 'rgba(46, 204, 113, 0.1)',
                    borderDash: [5, 5],
                    fill: false,
                    borderWidth: 2,
                    pointRadius: 0
                },
                {
                    label: 'Anomalies',
                    data: originalValues.map((val, i) => anomalyFlags[i] === 1 ? val : null),
                    borderColor: 'rgba(231, 76, 60, 1)',
                    backgroundColor: 'rgba(231, 76, 60, 0.7)',
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    showLine: false
                }
            ]
        },
        options: {
            plugins: {
                title: {
                    display: true,
                    text: 'Autoencoder Reconstruction Visualization',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const datasetIndex = context.datasetIndex;
                            
                            if (datasetIndex === 0) {
                                return `Original: ${originalValues[index].toFixed(2)}`;
                            } else if (datasetIndex === 1) {
                                return `Reconstructed: ${reconstructedValues[index].toFixed(2)}`;
                            } else {
                                const error = Math.abs(originalValues[index] - reconstructedValues[index]);
                                return `Anomaly - Error: ${error.toFixed(2)}`;
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Time Steps',
                        font: {
                            size: 14
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Value',
                        font: {
                            size: 14
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create K-Means visualization
 * @param {HTMLElement} canvas - The canvas element
 */
function createKMeansVisualization(canvas) {
    // Sample data for visualization: x, y coordinates and cluster assignments
    const points = [];
    const clusters = [];
    const isAnomaly = [];
    
    // Generate cluster centers
    const clusterCenters = [
        { x: 20, y: 20 },
        { x: 70, y: 20 },
        { x: 20, y: 70 },
        { x: 70, y: 70 }
    ];
    
    // Generate points around cluster centers
    for (let i = 0; i < 4; i++) {
        const center = clusterCenters[i];
        
        // 20 points per cluster
        for (let j = 0; j < 20; j++) {
            // Normal cluster points
            const x = center.x + (Math.random() * 10 - 5);
            const y = center.y + (Math.random() * 10 - 5);
            
            points.push({ x, y });
            clusters.push(i);
            isAnomaly.push(0); // Normal point
        }
    }
    
    // Add anomalies (outliers)
    for (let i = 0; i < 8; i++) {
        // Anomalies are far from cluster centers
        const x = Math.random() * 100;
        const y = Math.random() * 100;
        
        points.push({ x, y });
        clusters.push(4); // Separate cluster for anomalies
        isAnomaly.push(1); // Anomaly flag
    }
    
    // Cluster colors
    const clusterColors = [
        'rgba(46, 204, 113, 0.7)',  // green
        'rgba(52, 152, 219, 0.7)',  // blue
        'rgba(155, 89, 182, 0.7)',  // purple
        'rgba(241, 196, 15, 0.7)',  // yellow
        'rgba(231, 76, 60, 0.7)'    // red (anomalies)
    ];
    
    // Create the chart
    chartInstances['algorithm-visualization'] = new Chart(canvas, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'K-Means Clusters',
                data: points,
                backgroundColor: points.map((_, i) => clusterColors[clusters[i]]),
                borderColor: points.map((_, i) => {
                    return isAnomaly[i] === 1 ? 
                        'rgba(231, 76, 60, 1)' : // Anomalies
                        clusterColors[clusters[i]].replace('0.7', '1');
                }),
                borderWidth: points.map((_, i) => isAnomaly[i] === 1 ? 2 : 1),
                pointRadius: points.map((_, i) => isAnomaly[i] === 1 ? 8 : 6),
                pointHoverRadius: points.map((_, i) => isAnomaly[i] === 1 ? 10 : 8)
            }]
        },
        options: {
            plugins: {
                title: {
                    display: true,
                    text: 'K-Means Clustering Visualization',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const clusterLabel = isAnomaly[index] === 1 ? 
                                'Anomaly (Outlier)' : 
                                `Cluster ${clusters[index] + 1}`;
                            return `${clusterLabel} - (${points[index].x.toFixed(1)}, ${points[index].y.toFixed(1)})`;
                        }
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
                        text: 'Feature 1',
                        font: {
                            size: 14
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Feature 2',
                        font: {
                            size: 14
                        }
                    }
                }
            }
        }
    });
}
