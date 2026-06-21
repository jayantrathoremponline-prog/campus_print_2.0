// admin.js - Shared utilities for admin pages

const BACKEND_URL = 'https://campus-print-2-0.onrender.com';

// Check if user is authenticated and admin
function checkAdminAccess() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '../index.html';
        return false;
    }
    return true;
}

// Logout function
function adminLogout() {
    localStorage.clear();
    window.location.href = '../index.html';
}