/**
 * Energy Anomaly Detection System
 * Authentication specific JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Create animated energy lines and nodes for the login page
    const gridBackground = document.querySelector('.energy-grid-background');
    if (gridBackground) {
        // Create energy connection lines
        createEnergyNodes(gridBackground);
        
        // Make the animation respond to mouse movement
        document.addEventListener('mousemove', function(e) {
            const xPos = (e.clientX / window.innerWidth) - 0.5;
            const yPos = (e.clientY / window.innerHeight) - 0.5;
            
            gridBackground.style.transform = `perspective(1000px) rotateX(${yPos * 5}deg) rotateY(${xPos * 5}deg)`;
        });
    }
    
    // Function to create dynamic energy nodes
    function createEnergyNodes(container) {
        const numNodes = 15;
        const nodesContainer = document.createElement('div');
        nodesContainer.className = 'dynamic-nodes';
        nodesContainer.style.position = 'absolute';
        nodesContainer.style.width = '100%';
        nodesContainer.style.height = '100%';
        nodesContainer.style.zIndex = '4';
        
        for (let i = 0; i < numNodes; i++) {
            const node = document.createElement('div');
            node.className = 'energy-node';
            
            // Random position
            const x = Math.random() * 100;
            const y = Math.random() * 100;
            
            // Random size
            const size = 3 + Math.random() * 5;
            
            // Random animation duration
            const duration = 2 + Math.random() * 4;
            
            // Random delay
            const delay = Math.random() * 2;
            
            // Set styles
            node.style.position = 'absolute';
            node.style.left = `${x}%`;
            node.style.top = `${y}%`;
            node.style.width = `${size}px`;
            node.style.height = `${size}px`;
            node.style.backgroundColor = 'rgba(26, 188, 156, 0.8)';
            node.style.borderRadius = '50%';
            node.style.boxShadow = '0 0 10px rgba(26, 188, 156, 0.6), 0 0 20px rgba(26, 188, 156, 0.3)';
            node.style.animation = `pulseNode ${duration}s infinite ease-in-out ${delay}s`;
            
            nodesContainer.appendChild(node);
        }
        
        // Add keyframes for node animation if not already present
        if (!document.getElementById('node-animation-style')) {
            const style = document.createElement('style');
            style.id = 'node-animation-style';
            style.textContent = `
                @keyframes pulseNode {
                    0%, 100% { transform: scale(1); opacity: 0.6; }
                    50% { transform: scale(1.5); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }
        
        container.appendChild(nodesContainer);
    }
    
    // Get started page
    const loginLink = document.querySelector('a[href="/login"]');
    const registerLink = document.querySelector('a[href="/register"]');
    
    if (loginLink) {
        loginLink.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = '/login';
        });
    }
    
    if (registerLink) {
        registerLink.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = '/register';
        });
    }
    
    // Login form submission
    const loginForm = document.querySelector('form[action="/login"]');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            // Form will be submitted normally, but we can add validation here if needed
            console.log('Login form submitted');
        });
    }
    
    // Registration form submission
    const registerForm = document.querySelector('form[action="/register"]');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            // Form will be submitted normally, but we can add validation here if needed
            console.log('Registration form submitted');
        });
    }
});