// Navigation and Page Loading

// Page navigation function
function showPage(pageId) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.add('hidden');
    });
    
    // Show selected page
    const selectedPage = document.getElementById(pageId);
    if (selectedPage) {
        selectedPage.classList.remove('hidden');
        appState.currentPage = pageId;
        
        // Load page content
        loadPageContent(pageId);
        
        // Update active navigation
        updateActiveNavigation(pageId);
    }
}

function updateActiveNavigation(pageId) {
    // Remove active class from all nav items
    document.querySelectorAll('nav a, header a').forEach(link => {
        link.classList.remove('active');
    });
    
    // Add active class to current page link
    const activeLink = document.querySelector(`[onclick="showPage('${pageId}')"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
}

function loadPageContent(pageId) {
    const contentContainer = document.getElementById(`${pageId}-content`);
    if (!contentContainer) return;
    
    // Show loading
    showLoading(contentContainer);
    
    // Load content based on page
    switch(pageId) {
        case 'home':
            loadHomeContent(contentContainer);
            break;
        case 'registration':
            loadRegistrationContent(contentContainer);
            break;
        case 'profile':
            loadProfileContent(contentContainer);
            break;
        case 'schedule':
            loadScheduleContent(contentContainer);
            break;
        default:
            contentContainer.innerHTML = '<p>Trang không tồn tại</p>';
    }
}

async function loadHomeContent(container) {
    try {
        const data = await fetchData('home');
        const html = generateHomeHTML(data);
        hideLoading(container, html);
        
        // Initialize home page charts
        initializeHomeCharts();
    } catch (error) {
        console.error('Error loading home content:', error);
        container.innerHTML = '<p class="text-red-600">Lỗi tải dữ liệu</p>';
    }
}

async function loadRegistrationContent(container) {
    try {
        const data = await fetchData('courses');
        const html = generateRegistrationHTML(data);
        hideLoading(container, html);
        
        // Initialize course selection
        initializeCourseSelection();
    } catch (error) {
        console.error('Error loading registration content:', error);
        container.innerHTML = '<p class="text-red-600">Lỗi tải dữ liệu</p>';
    }
}

async function loadProfileContent(container) {
    try {
        const data = await fetchData('profile');
        const html = generateProfileHTML(data);
        hideLoading(container, html);
        
        // Initialize profile charts
        initializeProfileCharts();
    } catch (error) {
        console.error('Error loading profile content:', error);
        container.innerHTML = '<p class="text-red-600">Lỗi tải dữ liệu</p>';
    }
}

async function loadScheduleContent(container) {
    try {
        const data = await fetchData('schedule');
        const html = generateScheduleHTML(data);
        hideLoading(container, html);
        
        // Initialize schedule charts
        initializeScheduleCharts();
    } catch (error) {
        console.error('Error loading schedule content:', error);
        container.innerHTML = '<p class="text-red-600">Lỗi tải dữ liệu</p>';
    }
}

// HTML Generation Functions
function generateHomeHTML(data) {
    return `
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Welcome Card -->
            <div class="md:col-span-2 bg-white rounded-xl shadow-md p-6">
                <div class="flex items-center space-x-4 mb-4">
                    <div class="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                    </div>
                    <div>
                        <h2 class="text-2xl font-bold text-gray-800">Xin chào, ${appState.user.name}!</h2>
                        <p class="text-gray-600">MSSV: ${appState.user.mssv} | Ngành: ${appState.user.major}</p>
                    </div>
                </div>
                <div class="bg-blue-50 rounded-lg p-4 mb-6">
                    <div class="flex items-center space-x-2 text-blue-800">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span class="font-medium">Thông báo quan trọng</span>
                    </div>
                    <p class="mt-2 text-sm">Đợt đăng ký học phần học kỳ 2 năm học 2023-2024 sẽ bắt đầu từ ngày 15/12/2023. Vui lòng chuẩn bị kế hoạch học tập của bạn.</p>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="stat-card blue">
                        <div class="flex justify-between items-center">
                            <h3 class="font-semibold">GPA Hiện tại</h3>
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                            </svg>
                        </div>
                        <p class="text-3xl font-bold mt-2">${appState.user.gpa}</p>
                        <p class="text-sm text-blue-100">Xếp loại: Giỏi</p>
                    </div>
                    <div class="stat-card green">
                        <div class="flex justify-between items-center">
                            <h3 class="font-semibold">Tín chỉ đã hoàn thành</h3>
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <p class="text-3xl font-bold mt-2">${appState.user.creditsCompleted}/${appState.user.totalCredits}</p>
                        <p class="text-sm text-green-100">Còn lại: ${appState.user.totalCredits - appState.user.creditsCompleted} tín chỉ</p>
                    </div>
                    <div class="stat-card purple">
                        <div class="flex justify-between items-center">
                            <h3 class="font-semibold">Học kỳ hiện tại</h3>
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                        </div>
                        <p class="text-3xl font-bold mt-2">HK1</p>
                        <p class="text-sm text-purple-100">2023-2024</p>
                    </div>
                </div>
            </div>

            <!-- Quick Actions -->
            <div class="bg-white rounded-xl shadow-md p-6">
                <h2 class="text-lg font-semibold text-gray-800 mb-4">Truy cập nhanh</h2>
                <div class="space-y-3">
                    <button onclick="showPage('registration')" class="w-full flex items-center space-x-3 bg-blue-50 hover:bg-blue-100 text-blue-800 py-3 px-4 rounded-lg transition">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                        </svg>
                        <span>Đăng ký học phần</span>
                    </button>
                    <button onclick="showPage('schedule')" class="w-full flex items-center space-x-3 bg-green-50 hover:bg-green-100 text-green-800 py-3 px-4 rounded-lg transition">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <span>Thời khóa biểu</span>
                    </button>
                    <button onclick="showPage('profile')" class="w-full flex items-center space-x-3 bg-purple-50 hover:bg-purple-100 text-purple-800 py-3 px-4 rounded-lg transition">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        <span>Thông tin cá nhân</span>
                    </button>
                    <button onclick="toggleChatbot()" class="w-full flex items-center space-x-3 bg-yellow-50 hover:bg-yellow-100 text-yellow-800 py-3 px-4 rounded-lg transition pulse-animation">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                        </svg>
                        <span>Tư vấn học tập</span>
                    </button>
                </div>
            </div>

            <!-- Academic Progress -->
            <div class="md:col-span-2 bg-white rounded-xl shadow-md p-6">
                <h2 class="text-lg font-semibold text-gray-800 mb-4">Tiến độ học tập</h2>
                <div class="h-64">
                    <canvas id="academicChart"></canvas>
                </div>
            </div>

            <!-- Recommended Courses -->
            <div class="bg-white rounded-xl shadow-md p-6">
                <h2 class="text-lg font-semibold text-gray-800 mb-4">Môn học gợi ý</h2>
                <div class="space-y-3">
                    <div class="p-3 border border-blue-200 rounded-lg hover:bg-blue-50 transition cursor-pointer">
                        <div class="flex justify-between">
                            <h3 class="font-medium text-blue-800">Trí tuệ nhân tạo</h3>
                            <span class="badge badge-blue">3 TC</span>
                        </div>
                        <p class="text-xs text-gray-500 mt-1">Tiên quyết: Cấu trúc dữ liệu và giải thuật</p>
                    </div>
                    <div class="p-3 border border-blue-200 rounded-lg hover:bg-blue-50 transition cursor-pointer">
                        <div class="flex justify-between">
                            <h3 class="font-medium text-blue-800">Phát triển ứng dụng web</h3>
                            <span class="badge badge-blue">4 TC</span>
                        </div>
                        <p class="text-xs text-gray-500 mt-1">Tiên quyết: Cơ sở dữ liệu</p>
                    </div>
                    <div class="p-3 border border-blue-200 rounded-lg hover:bg-blue-50 transition cursor-pointer">
                        <div class="flex justify-between">
                            <h3 class="font-medium text-blue-800">Học máy</h3>
                            <span class="badge badge-blue">3 TC</span>
                        </div>
                        <p class="text-xs text-gray-500 mt-1">Tiên quyết: Xác suất thống kê</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Export functions
window.showPage = showPage;
window.loadPageContent = loadPageContent; 