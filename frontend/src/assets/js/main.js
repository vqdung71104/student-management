// Main JavaScript File
// Global variables and utility functions

// App state
const appState = {
    currentPage: 'home',
    user: {
        name: 'Nguyễn Thành',
        mssv: '20210123',
        major: 'Công nghệ thông tin',
        gpa: 3.65,
        creditsCompleted: 87,
        totalCredits: 145
    },
    selectedCourses: [],
    chatbotOpen: false
};

// Utility functions
function formatNumber(num) {
    return num.toLocaleString('vi-VN');
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('vi-VN');
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = `
        <div class="flex items-center">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-auto text-gray-500 hover:text-gray-700">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentElement) {
            alertDiv.remove();
        }
    }, 5000);
}

function showLoading(element) {
    element.innerHTML = '<div class="spinner"></div>';
}

function hideLoading(element, content) {
    element.innerHTML = content;
}

// API simulation functions
async function fetchData(endpoint) {
    // Simulate API call
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve(mockData[endpoint] || []);
        }, 500);
    });
}

async function postData(endpoint, data) {
    // Simulate API call
    return new Promise((resolve) => {
        setTimeout(() => {
            console.log(`POST ${endpoint}:`, data);
            resolve({ success: true, data });
        }, 1000);
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('Student Management System loaded');
    
    // Initialize the application
    initializeApp();
});

function initializeApp() {
    // Load initial page content
    loadPageContent('home');
    
    // Initialize charts
    initializeCharts();
    
    // Set up event listeners
    setupEventListeners();
}

function setupEventListeners() {
    // Global event listeners
    document.addEventListener('click', function(e) {
        // Handle global clicks
        if (e.target.matches('[data-action]')) {
            const action = e.target.dataset.action;
            handleGlobalAction(action, e.target);
        }
    });
}

function handleGlobalAction(action, element) {
    switch(action) {
        case 'logout':
            logout();
            break;
        case 'refresh':
            refreshPage();
            break;
        case 'help':
            showHelp();
            break;
        default:
            console.log('Unknown action:', action);
    }
}

function logout() {
    if (confirm('Bạn có chắc chắn muốn đăng xuất?')) {
        // Clear session/localStorage
        localStorage.clear();
        // Redirect to login page
        window.location.href = '/login.html';
    }
}

function refreshPage() {
    location.reload();
}

function showHelp() {
    alert('Hướng dẫn sử dụng hệ thống:\n\n1. Sử dụng menu để điều hướng\n2. Chatbot để được hỗ trợ\n3. Click vào các nút để thực hiện thao tác');
}

// Export for use in other modules
window.appState = appState;
window.showAlert = showAlert;
window.formatNumber = formatNumber;
window.formatDate = formatDate; 