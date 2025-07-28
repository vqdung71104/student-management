// Course Management Functions

// Course selection function
function selectCourse(element) {
    element.classList.toggle('selected');
    
    const courseId = element.dataset.courseId;
    if (element.classList.contains('selected')) {
        addToSelectedCourses(courseId);
    } else {
        removeFromSelectedCourses(courseId);
    }
}

// Add course to selected list
function addToSelectedCourses(courseId) {
    const course = mockData.courses.find(c => c.id === courseId);
    if (course && !appState.selectedCourses.find(c => c.id === courseId)) {
        appState.selectedCourses.push(course);
        updateSelectedCoursesTable();
        updateTotalCredits();
    }
}

// Remove course from selected list
function removeFromSelectedCourses(courseId) {
    appState.selectedCourses = appState.selectedCourses.filter(c => c.id !== courseId);
    updateSelectedCoursesTable();
    updateTotalCredits();
}

// Remove selected course from table
function removeSelectedCourse(button) {
    const row = button.closest('tr');
    const courseId = row.dataset.courseId;
    
    // Remove from selected courses
    removeFromSelectedCourses(courseId);
    
    // Remove from UI
    row.remove();
}

// Update selected courses table
function updateSelectedCoursesTable() {
    const tableBody = document.getElementById('selected-courses');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    appState.selectedCourses.forEach(course => {
        const row = document.createElement('tr');
        row.dataset.courseId = course.id;
        row.className = 'table-row';
        
        row.innerHTML = `
            <td class="table-cell font-medium text-gray-900">${course.id}</td>
            <td class="table-cell text-gray-900">${course.name}</td>
            <td class="table-cell text-gray-900">${course.credits}</td>
            <td class="table-cell text-gray-900">${course.id}.1</td>
            <td class="table-cell text-gray-900">${course.instructor}</td>
            <td class="table-cell text-gray-900">${course.schedule}</td>
            <td class="table-cell text-gray-900">
                <button class="text-red-600 hover:text-red-800" onclick="removeSelectedCourse(this)">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Update total credits display
function updateTotalCredits() {
    const totalCredits = appState.selectedCourses.reduce((sum, course) => sum + course.credits, 0);
    const maxCredits = 24;
    
    const totalElement = document.querySelector('[data-total-credits]');
    if (totalElement) {
        totalElement.textContent = totalCredits;
    }
    
    const remainingElement = document.querySelector('[data-remaining-credits]');
    if (remainingElement) {
        remainingElement.textContent = maxCredits - totalCredits;
    }
    
    // Show warning if over limit
    if (totalCredits > maxCredits) {
        showAlert('Bạn đã vượt quá giới hạn tín chỉ cho phép!', 'warning');
    }
}

// Initialize course selection
function initializeCourseSelection() {
    // Add event listeners to course cards
    document.querySelectorAll('.course-card').forEach(card => {
        card.addEventListener('click', function() {
            selectCourse(this);
        });
    });
    
    // Initialize search functionality
    initializeCourseSearch();
    
    // Initialize filters
    initializeCourseFilters();
}

// Course search functionality
function initializeCourseSearch() {
    const searchInput = document.querySelector('input[placeholder*="tìm kiếm"]');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        filterCourses(searchTerm);
    });
}

// Filter courses based on search term
function filterCourses(searchTerm) {
    const courseCards = document.querySelectorAll('.course-card');
    
    courseCards.forEach(card => {
        const courseName = card.querySelector('h4').textContent.toLowerCase();
        const courseId = card.querySelector('h3').textContent.toLowerCase();
        
        if (courseName.includes(searchTerm) || courseId.includes(searchTerm)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Initialize course filters
function initializeCourseFilters() {
    const yearSelect = document.querySelector('select option:contains("2023-2024")');
    const semesterSelect = document.querySelector('select option:contains("Học kỳ 2")');
    const facultySelect = document.querySelector('select option:contains("Tất cả")');
    
    if (yearSelect) {
        yearSelect.addEventListener('change', function() {
            filterCoursesByYear(this.value);
        });
    }
    
    if (semesterSelect) {
        semesterSelect.addEventListener('change', function() {
            filterCoursesBySemester(this.value);
        });
    }
    
    if (facultySelect) {
        facultySelect.addEventListener('change', function() {
            filterCoursesByFaculty(this.value);
        });
    }
}

// Filter courses by year
function filterCoursesByYear(year) {
    console.log('Filtering by year:', year);
    // Implementation would depend on actual data structure
}

// Filter courses by semester
function filterCoursesBySemester(semester) {
    console.log('Filtering by semester:', semester);
    // Implementation would depend on actual data structure
}

// Filter courses by faculty
function filterCoursesByFaculty(faculty) {
    console.log('Filtering by faculty:', faculty);
    // Implementation would depend on actual data structure
}

// Confirm course registration
async function confirmRegistration() {
    if (appState.selectedCourses.length === 0) {
        showAlert('Vui lòng chọn ít nhất một học phần!', 'warning');
        return;
    }
    
    const totalCredits = appState.selectedCourses.reduce((sum, course) => sum + course.credits, 0);
    if (totalCredits > 24) {
        showAlert('Bạn đã vượt quá giới hạn tín chỉ cho phép!', 'error');
        return;
    }
    
    try {
        // Simulate API call
        const response = await postData('/api/registration', {
            courses: appState.selectedCourses,
            totalCredits: totalCredits
        });
        
        if (response.success) {
            showAlert('Đăng ký học phần thành công!', 'success');
            appState.selectedCourses = [];
            updateSelectedCoursesTable();
            updateTotalCredits();
        } else {
            showAlert('Có lỗi xảy ra khi đăng ký học phần!', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showAlert('Có lỗi xảy ra khi đăng ký học phần!', 'error');
    }
}

// Cancel registration
function cancelRegistration() {
    if (confirm('Bạn có chắc chắn muốn hủy đăng ký học phần?')) {
        appState.selectedCourses = [];
        updateSelectedCoursesTable();
        updateTotalCredits();
        
        // Remove selected class from course cards
        document.querySelectorAll('.course-card.selected').forEach(card => {
            card.classList.remove('selected');
        });
        
        showAlert('Đã hủy đăng ký học phần!', 'info');
    }
}

// Generate course card HTML
function generateCourseCard(course) {
    return `
        <div class="course-card border border-gray-200 rounded-lg p-4 hover:shadow-md transition cursor-pointer" 
             data-course-id="${course.id}" onclick="selectCourse(this)">
            <div class="flex justify-between items-start">
                <div>
                    <h3 class="font-medium text-gray-800">${course.id}</h3>
                    <h4 class="text-lg font-semibold text-blue-800">${course.name}</h4>
                </div>
                <span class="badge badge-blue">${course.credits} TC</span>
            </div>
            <div class="mt-3 space-y-1 text-sm">
                <div class="flex items-center text-gray-600">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    <span>GV: ${course.instructor}</span>
                </div>
                <div class="flex items-center text-gray-600">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <span>${course.schedule}</span>
                </div>
                <div class="flex items-center text-gray-600">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span>Phòng: ${course.room}</span>
                </div>
                <div class="flex items-center text-gray-600">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Còn ${course.available}/${course.total} chỗ</span>
                </div>
            </div>
        </div>
    `;
}

// Export functions
window.selectCourse = selectCourse;
window.removeSelectedCourse = removeSelectedCourse;
window.confirmRegistration = confirmRegistration;
window.cancelRegistration = cancelRegistration;
window.initializeCourseSelection = initializeCourseSelection; 