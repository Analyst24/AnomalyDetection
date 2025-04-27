/**
 * Energy Anomaly Detection System
 * Authentication specific JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
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