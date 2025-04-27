/**
 * Energy Anomaly Detection System
 * Dashboard specific JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard animations and interactions
    initializeDashboardAnimations();
    
    // Set up event handlers for dashboard elements
    setupDashboardEventHandlers();
});

/**
 * Set up animations and visual effects for the dashboard
 */
function initializeDashboardAnimations() {
    // Animate stat cards on page load
    const statCards = document.querySelectorAll('.dashboard-stat');
    if (statCards.length > 0) {
        statCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 100 * index);
        });
    }
    
    // Set up energy pulse animation on dashboard
    const pulseElements = document.querySelectorAll('.energy-pulse');
    if (pulseElements.length > 0) {
        pulseElements.forEach(element => {
            element.classList.add('pulse-animation');
        });
    }
}

/**
 * Set up event handlers for dashboard interactive elements
 */
function setupDashboardEventHandlers() {
    // Time period selectors for dashboard charts
    const timePeriodSelectors = document.querySelectorAll('.time-period-selector');
    if (timePeriodSelectors.length > 0) {
        timePeriodSelectors.forEach(selector => {
            selector.addEventListener('change', function() {
                const period = this.value;
                const chartId = this.getAttribute('data-chart');
                
                // Show loading state
                const chartContainer = document.getElementById(chartId);
                if (chartContainer) {
                    showLoadingSpinner(chartId, 'Updating chart...');
                    
                    // Simulate data loading (in a real app, this would fetch from the server)
                    setTimeout(() => {
                        // Update chart based on selected time period
                        updateChartTimePeriod(chartId, period);
                    }, 500);
                }
            });
        });
    }
    
    // Refresh dashboard data button
    const refreshBtn = document.getElementById('refresh-dashboard');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            // Show loading overlay
            const dashboardContent = document.getElementById('dashboard-content');
            if (dashboardContent) {
                dashboardContent.classList.add('loading');
                
                // Disable refresh button during refresh
                this.disabled = true;
                this.innerHTML = '<i class="fas fa-sync fa-spin"></i> Refreshing...';
                
                // In a real app, this would fetch fresh data from the server
                setTimeout(() => {
                    // Remove loading state
                    dashboardContent.classList.remove('loading');
                    
                    // Re-enable refresh button
                    this.disabled = false;
                    this.innerHTML = '<i class="fas fa-sync"></i> Refresh Dashboard';
                    
                    // Show toast notification
                    showToast('Dashboard refreshed successfully!', 'success');
                }, 1000);
            }
        });
    }
    
    // Chart view toggles (e.g., between bar/line/pie)
    const chartViewToggles = document.querySelectorAll('.chart-view-toggle');
    if (chartViewToggles.length > 0) {
        chartViewToggles.forEach(toggle => {
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                
                const chartId = this.getAttribute('data-chart');
                const chartType = this.getAttribute('data-type');
                
                // Remove active class from all toggles in this group
                const toggleGroup = document.querySelectorAll(`.chart-view-toggle[data-chart="${chartId}"]`);
                toggleGroup.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked toggle
                this.classList.add('active');
                
                // Change chart type
                changeChartType(chartId, chartType);
            });
        });
    }
}

/**
 * Update chart based on selected time period
 * @param {string} chartId - The ID of the chart element to update
 * @param {string} period - The selected time period (e.g., 'day', 'week', 'month')
 */
function updateChartTimePeriod(chartId, period) {
    // Get the chart instance
    const chartInstance = chartInstances[chartId];
    
    if (!chartInstance) {
        console.error(`Chart with ID ${chartId} not found.`);
        return;
    }
    
    // In a real app, this would fetch new data based on time period
    // For now, we'll just update the chart title to reflect the change
    
    const titleOptions = chartInstance.options.plugins.title;
    const originalTitle = titleOptions.text.split(' - ')[0];
    
    let periodText = '';
    switch(period) {
        case 'day':
            periodText = 'Last 24 Hours';
            break;
        case 'week':
            periodText = 'Last 7 Days';
            break;
        case 'month':
            periodText = 'Last 30 Days';
            break;
        case 'year':
            periodText = 'Last 12 Months';
            break;
        default:
            periodText = 'All Time';
    }
    
    // Update chart title
    titleOptions.text = `${originalTitle} - ${periodText}`;
    
    // Update chart
    chartInstance.update();
    
    // Remove loading spinner
    const chartContainer = document.getElementById(chartId);
    const chartCanvas = chartContainer.querySelector('canvas');
    chartContainer.innerHTML = '';
    chartContainer.appendChild(chartCanvas);
}

/**
 * Change chart type (e.g., from bar to line)
 * @param {string} chartId - The ID of the chart element
 * @param {string} newType - The new chart type
 */
function changeChartType(chartId, newType) {
    // Get the chart instance
    const chartInstance = chartInstances[chartId];
    
    if (!chartInstance) {
        console.error(`Chart with ID ${chartId} not found.`);
        return;
    }
    
    // Store the current data and options
    const data = chartInstance.data;
    const options = chartInstance.options;
    
    // Destroy the current chart
    chartInstance.destroy();
    
    // Create a new chart with the new type
    const ctx = document.getElementById(chartId);
    
    // Create new chart with the same data but different type
    chartInstances[chartId] = new Chart(ctx, {
        type: newType,
        data: data,
        options: options
    });
}

/**
 * Show a toast notification
 * @param {string} message - The notification message
 * @param {string} type - The notification type (success, error, warning, info)
 */
function showToast(message, type = 'info') {
    // Check if toast container exists, create if not
    let toastContainer = document.querySelector('.toast-container');
    
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    // Toast content
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add to container
    toastContainer.appendChild(toastEl);
    
    // Initialize and show the toast
    const toast = new bootstrap.Toast(toastEl, { 
        autohide: true,
        delay: 3000
    });
    toast.show();
    
    // Remove toast after it's hidden
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
}
