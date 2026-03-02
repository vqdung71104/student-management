// Charts and Data Visualization

// Initialize all charts
function initializeCharts() {
    initializeAcademicChart();
    initializeSemesterChart();
    initializeScheduleChart();
}

// Academic Progress Chart
function initializeAcademicChart() {
    const ctx = document.getElementById('academicChart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: mockData.academicProgress.semesters,
            datasets: [{
                label: 'GPA',
                data: mockData.academicProgress.gpa,
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: 2.0,
                    max: 4.0,
                    ticks: {
                        stepSize: 0.5
                    }
                }
            }
        }
    });
}

// Semester Progress Chart
function initializeSemesterChart() {
    const ctx = document.getElementById('semesterChart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: mockData.academicProgress.semesters,
            datasets: [{
                label: 'Tín chỉ đã học',
                data: mockData.academicProgress.credits,
                backgroundColor: 'rgba(59, 130, 246, 0.7)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 25
                }
            }
        }
    });
}

// Schedule Chart
function initializeScheduleChart() {
    const ctx = document.getElementById('scheduleChart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Sáng', 'Chiều', 'Tối'],
            datasets: [{
                data: [10, 14, 0],
                backgroundColor: [
                    'rgba(59, 130, 246, 0.7)',
                    'rgba(16, 185, 129, 0.7)',
                    'rgba(139, 92, 246, 0.7)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Course Distribution Chart
function initializeCourseDistributionChart() {
    const ctx = document.getElementById('courseDistributionChart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Cơ sở', 'Chuyên ngành', 'Tự chọn'],
            datasets: [{
                data: [30, 50, 20],
                backgroundColor: [
                    'rgba(59, 130, 246, 0.7)',
                    'rgba(16, 185, 129, 0.7)',
                    'rgba(139, 92, 246, 0.7)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Grade Distribution Chart
function initializeGradeDistributionChart() {
    const ctx = document.getElementById('gradeDistributionChart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C'],
            datasets: [{
                label: 'Số môn học',
                data: [8, 5, 12, 15, 3, 2, 1],
                backgroundColor: 'rgba(59, 130, 246, 0.7)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Initialize charts for specific pages
function initializeHomeCharts() {
    initializeAcademicChart();
}

function initializeProfileCharts() {
    initializeSemesterChart();
    initializeGradeDistributionChart();
}

function initializeScheduleCharts() {
    initializeScheduleChart();
    initializeCourseDistributionChart();
}

// Update chart data dynamically
function updateChartData(chartId, newData) {
    const chart = Chart.getChart(chartId);
    if (chart) {
        chart.data.datasets[0].data = newData;
        chart.update();
    }
}

// Export functions
window.initializeCharts = initializeCharts;
window.initializeHomeCharts = initializeHomeCharts;
window.initializeProfileCharts = initializeProfileCharts;
window.initializeScheduleCharts = initializeScheduleCharts;
window.updateChartData = updateChartData; 