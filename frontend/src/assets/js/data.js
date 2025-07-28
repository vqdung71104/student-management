// Mock data for the application

const mockData = {
    // Home page data
    home: {
        notifications: [
            {
                id: 1,
                title: 'Đăng ký học phần HK2',
                message: 'Đợt đăng ký học phần học kỳ 2 năm học 2023-2024 sẽ bắt đầu từ ngày 15/12/2023.',
                type: 'info',
                date: '2023-12-15'
            }
        ],
        upcomingEvents: [
            {
                id: 1,
                title: 'Đăng ký học phần HK2',
                date: '15/12',
                time: '8:00 - 22:00',
                type: 'registration'
            },
            {
                id: 2,
                title: 'Kết thúc học kỳ 1',
                date: '20/12',
                time: 'Toàn trường',
                type: 'semester'
            }
        ]
    },

    // Course registration data
    courses: [
        {
            id: 'IT3090',
            name: 'Phát triển ứng dụng web',
            credits: 4,
            instructor: 'TS. Nguyễn Văn A',
            schedule: 'Thứ 2 (7:00 - 10:00)',
            room: 'D3-404',
            available: 15,
            total: 40,
            prerequisites: ['Cơ sở dữ liệu'],
            description: 'Học phần về phát triển ứng dụng web hiện đại'
        },
        {
            id: 'IT4060',
            name: 'Trí tuệ nhân tạo',
            credits: 3,
            instructor: 'PGS.TS. Trần Thị B',
            schedule: 'Thứ 3 (13:00 - 16:00)',
            room: 'D5-301',
            available: 8,
            total: 35,
            prerequisites: ['Cấu trúc dữ liệu và giải thuật', 'Xác suất thống kê'],
            description: 'Học phần về trí tuệ nhân tạo và machine learning'
        },
        {
            id: 'IT4409',
            name: 'Công nghệ phần mềm',
            credits: 3,
            instructor: 'TS. Lê Văn C',
            schedule: 'Thứ 5 (7:00 - 10:00)',
            room: 'D3-305',
            available: 20,
            total: 40,
            prerequisites: ['Lập trình hướng đối tượng'],
            description: 'Học phần về quy trình phát triển phần mềm'
        },
        {
            id: 'IT4785',
            name: 'Phát triển ứng dụng di động',
            credits: 3,
            instructor: 'ThS. Phạm Thị D',
            schedule: 'Thứ 4 (13:00 - 16:00)',
            room: 'D9-404',
            available: 12,
            total: 35,
            prerequisites: ['Lập trình hướng đối tượng'],
            description: 'Học phần về phát triển ứng dụng di động'
        },
        {
            id: 'IT4995',
            name: 'Học máy',
            credits: 3,
            instructor: 'PGS.TS. Hoàng Văn E',
            schedule: 'Thứ 6 (7:00 - 10:00)',
            room: 'D3-505',
            available: 5,
            total: 30,
            prerequisites: ['Xác suất thống kê', 'Trí tuệ nhân tạo'],
            description: 'Học phần nâng cao về machine learning'
        },
        {
            id: 'IT4930',
            name: 'An toàn thông tin',
            credits: 3,
            instructor: 'TS. Vũ Văn F',
            schedule: 'Thứ 5 (13:00 - 16:00)',
            room: 'D5-405',
            available: 18,
            total: 40,
            prerequisites: ['Mạng máy tính'],
            description: 'Học phần về bảo mật và an toàn thông tin'
        }
    ],

    // Profile data
    profile: {
        personal: {
            name: 'Nguyễn Thành',
            mssv: '20210123',
            birthDate: '15/05/2003',
            gender: 'Nam',
            email: 'thanh.n@example.edu.vn',
            phone: '0912345678'
        },
        academic: {
            major: 'Công nghệ thông tin',
            program: 'Kỹ sư',
            year: 'K66',
            class: 'IT-E6',
            gpa: 3.65,
            creditsCompleted: 87,
            totalCredits: 145,
            classification: 'Giỏi'
        },
        recentCourses: [
            {
                id: 'IT3100',
                name: 'Lập trình hướng đối tượng',
                credits: 3,
                grade: 'A',
                semester: '20222'
            },
            {
                id: 'IT3170',
                name: 'Cơ sở dữ liệu',
                credits: 3,
                grade: 'A',
                semester: '20222'
            },
            {
                id: 'IT3150',
                name: 'Cấu trúc dữ liệu và giải thuật',
                credits: 3,
                grade: 'B+',
                semester: '20222'
            },
            {
                id: 'IT3030',
                name: 'Kiến trúc máy tính',
                credits: 3,
                grade: 'B',
                semester: '20222'
            },
            {
                id: 'IT3290',
                name: 'Hệ điều hành',
                credits: 3,
                grade: 'A-',
                semester: '20222'
            }
        ]
    },

    // Schedule data
    schedule: {
        currentWeek: [
            {
                day: 'Thứ 2',
                time: '7:00 - 9:00',
                course: 'Phát triển ứng dụng web',
                room: 'D3-404',
                type: 'lecture'
            },
            {
                day: 'Thứ 3',
                time: '13:00 - 15:00',
                course: 'Trí tuệ nhân tạo',
                room: 'D5-301',
                type: 'lecture'
            },
            {
                day: 'Thứ 4',
                time: '13:00 - 15:00',
                course: 'Phát triển ứng dụng di động',
                room: 'D9-404',
                type: 'lecture'
            },
            {
                day: 'Thứ 5',
                time: '7:00 - 9:00',
                course: 'Công nghệ phần mềm',
                room: 'D3-305',
                type: 'lecture'
            },
            {
                day: 'Thứ 5',
                time: '13:00 - 15:00',
                course: 'An toàn thông tin',
                room: 'D5-405',
                type: 'lecture'
            },
            {
                day: 'Thứ 6',
                time: '7:00 - 9:00',
                course: 'Học máy',
                room: 'D3-505',
                type: 'lecture'
            }
        ],
        statistics: {
            totalCredits: 16,
            daysPerWeek: 5,
            totalHours: 24,
            busiestDay: 'Thứ 5',
            busiestDayHours: 6
        }
    },

    // Academic progress data
    academicProgress: {
        semesters: ['20211', '20212', '20221', '20222', '20231'],
        gpa: [3.2, 3.4, 3.5, 3.8, 3.65],
        credits: [15, 18, 17, 19, 18]
    },

    // Chatbot responses
    chatbotResponses: {
        greetings: [
            'Xin chào! Tôi có thể giúp gì cho bạn?',
            'Chào bạn! Bạn cần hỗ trợ gì không?',
            'Hi! Tôi là trợ lý học tập của bạn.'
        ],
        courseInfo: {
            'IT4060': {
                name: 'Trí tuệ nhân tạo',
                description: 'Học phần về AI và machine learning',
                prerequisites: ['Cấu trúc dữ liệu và giải thuật', 'Xác suất thống kê'],
                classes: [
                    {
                        id: 'IT4060.1',
                        schedule: 'Thứ 3 (13:00 - 16:00)',
                        room: 'D5-301',
                        instructor: 'PGS.TS. Trần Thị B',
                        available: 8,
                        total: 35
                    },
                    {
                        id: 'IT4060.2',
                        schedule: 'Thứ 4 (7:00 - 10:00)',
                        room: 'D3-201',
                        instructor: 'TS. Lê Văn G',
                        available: 12,
                        total: 35
                    }
                ]
            }
        }
    }
};

// Export for use in other modules
window.mockData = mockData; 