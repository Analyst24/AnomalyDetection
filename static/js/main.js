/**
 * Energy Anomaly Detection System
 * Main JavaScript file for general UI functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize sidebar functionality
    initializeSidebar();
    
    // Setup flash message auto-dismissal
    setupFlashMessages();
    
    // Initialize any charts if they exist
    if(typeof initializeCharts === 'function') {
        initializeCharts();
    }
    
    // Add event listeners for any toggleable elements
    setupToggleElements();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize sidebar toggle functionality
 */
function initializeSidebar() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const contentWrapper = document.querySelector('.content-wrapper');
    
    if(sidebarToggle && sidebar && contentWrapper) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            contentWrapper.classList.toggle('expanded');
            
            // Store sidebar state in localStorage
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebar-collapsed', isCollapsed);
        });
        
        // Check for saved sidebar state
        const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
        if(isCollapsed) {
            sidebar.classList.add('collapsed');
            contentWrapper.classList.add('expanded');
        }
        
        // For mobile: handle showing/hiding sidebar
        const mobileToggle = document.getElementById('mobile-sidebar-toggle');
        if(mobileToggle) {
            mobileToggle.addEventListener('click', function() {
                sidebar.classList.toggle('show');
            });
            
            // Close sidebar when clicking outside
            document.addEventListener('click', function(event) {
                const isClickInside = sidebar.contains(event.target) || 
                                     mobileToggle.contains(event.target);
                
                if(!isClickInside && sidebar.classList.contains('show')) {
                    sidebar.classList.remove('show');
                }
            });
        }
    }
}

/**
 * Set up automatic dismissal of flash messages after a delay
 */
function setupFlashMessages() {
    const flashMessages = document.querySelectorAll('.alert-dismissible');
    
    flashMessages.forEach(function(message) {
        // Auto dismiss after 5 seconds
        setTimeout(function() {
            // Create and get the Bootstrap alert instance
            const alert = new bootstrap.Alert(message);
            alert.close();
        }, 5000);
    });
}

/**
 * Set up toggle elements like collapsible cards
 */
function setupToggleElements() {
    const toggleButtons = document.querySelectorAll('[data-toggle="collapse"]');
    
    toggleButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const targetElement = document.querySelector(targetId);
            
            if(targetElement) {
                const isCollapsed = targetElement.classList.contains('show');
                
                if(isCollapsed) {
                    targetElement.classList.remove('show');
                    this.classList.remove('collapsed');
                } else {
                    targetElement.classList.add('show');
                    this.classList.add('collapsed');
                }
            }
        });
    });
}

/**
 * Format a date for display
 * @param {string} dateString - The date string to format
 * @param {boolean} includeTime - Whether to include time
 * @returns {string} - Formatted date string
 */
function formatDate(dateString, includeTime = false) {
    const date = new Date(dateString);
    
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };
    
    if(includeTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
    }
    
    return date.toLocaleDateString('en-US', options);
}

/**
 * Show a loading spinner in the target element
 * @param {string} targetId - The ID of the element to show spinner in
 * @param {string} message - Optional loading message
 */
function showLoadingSpinner(targetId, message = 'Loading...') {
    const targetElement = document.getElementById(targetId);
    if(targetElement) {
        targetElement.innerHTML = `
            <div class="spinner-container">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3 text-center">${message}</p>
            </div>
        `;
    }
}

/**
 * Hide the loading spinner and replace with content
 * @param {string} targetId - The ID of the element containing spinner
 * @param {string} content - The HTML content to replace spinner with
 */
function hideLoadingSpinner(targetId, content) {
    const targetElement = document.getElementById(targetId);
    if(targetElement) {
        targetElement.innerHTML = content;
    }
}

/**
 * Format a number for display with commas and decimals
 * @param {number} number - The number to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} - Formatted number
 */
function formatNumber(number, decimals = 0) {
    return number.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Create a random color with specified opacity
 * @param {number} opacity - The opacity value (0-1)
 * @returns {string} - RGBA color string
 */
function getRandomColor(opacity = 1) {
    const r = Math.floor(Math.random() * 256);
    const g = Math.floor(Math.random() * 256);
    const b = Math.floor(Math.random() * 256);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

/**
 * Create a themed color set for charts
 * @param {number} count - Number of colors needed
 * @param {number} opacity - The opacity value (0-1)
 * @returns {Array} - Array of color strings
 */
function getChartColors(count, opacity = 0.7) {
    // Base colors in the theme
    const baseColors = [
        [26, 188, 156],   // teal
        [231, 76, 60],    // red
        [52, 152, 219],   // blue
        [241, 196, 15],   // yellow
        [155, 89, 182],   // purple
        [46, 204, 113],   // green
        [230, 126, 34],   // orange
        [149, 165, 166],  // gray
    ];
    
    const colors = [];
    
    for(let i = 0; i < count; i++) {
        const color = baseColors[i % baseColors.length];
        colors.push(`rgba(${color[0]}, ${color[1]}, ${color[2]}, ${opacity})`);
    }
    
    return colors;
}
