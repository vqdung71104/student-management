import { useState } from 'react'

export type Language = 'vi' | 'en'

export interface StudentTranslations {
  nav: {
    study: string
    registration: string
    forms: string
    scholarships: string
    support: string
    changePassword: string
    logout: string
    schedule: string
    grades: string
    curriculum: string
    subjectRegistration: string
    classRegistration: string
    userGuide: string
    faq: string
    feedback: string
  }
  common: {
    loading: string
    close: string
    save: string
    cancel: string
    confirm: string
    back: string
    search: string
    upload: string
    daysOfWeekShort: string[]
    daysOfWeekFull: string[]
  }
  pages: {
    userGuide: {
      title: string
      subtitle: string
      sectionOverview: string
      sectionQuickFlow: string
      sectionStudy: string
      sectionPlanner: string
      sectionChatbot: string
      sectionSupport: string
      overviewText: string
      quickFlowSteps: Array<string | { text: string; strong?: string[] }>
      studyBlocks: Array<{ title: string; body: string }>
      plannerBlocks: Array<{ title: string; body: string; bullets?: string[] }>
      chatbotText: string
      chatbotNote: string
      supportBullets: Array<{ title: string; body: string }>
      noteTitle: string
      notes: string[]
    }
  }
}

const texts: Record<Language, StudentTranslations> = {
  vi: {
    nav: {
      study: 'Học tập',
      registration: 'Lập kế hoạch đăng ký',
      forms: 'Biểu mẫu',
      scholarships: 'Học bổng',
      support: 'Hỗ trợ',
      changePassword: 'Đổi mật khẩu',
      logout: 'Đăng xuất',
      schedule: 'Thời khóa biểu',
      grades: 'Xem điểm',
      curriculum: 'Chương trình đào tạo',
      subjectRegistration: 'Chọn học phần (mẫu)',
      classRegistration: 'Chọn lớp (mẫu)',
      userGuide: 'Hướng dẫn sử dụng',
      faq: 'Những câu hỏi thường gặp',
      feedback: 'Phản hồi và góp ý',
    },
    common: {
      loading: 'Đang tải...',
      close: 'Đóng',
      save: 'Lưu',
      cancel: 'Hủy',
      confirm: 'Xác nhận',
      back: 'Quay lại',
      search: 'Tìm kiếm',
      upload: 'Tải lên',
      daysOfWeekShort: ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'],
      daysOfWeekFull: ['Chủ nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7'],
    },
    pages: {
      userGuide: {
        title: 'HƯỚNG DẪN SỬ DỤNG',
        subtitle:
          'Website này dùng để gợi ý và lập kế hoạch đăng ký học phần/lớp. Chỉ mang tính tham khảo và không thay thế việc đăng ký thật.',
        sectionOverview: '1) Tổng quan',
        sectionQuickFlow: '2) Luồng sử dụng nhanh',
        sectionStudy: '3) Học tập',
        sectionPlanner: '4) Lập kế hoạch đăng ký (mẫu)',
        sectionChatbot: '5) Chatbot',
        sectionSupport: '6) Hỗ trợ',
        overviewText:
          'Bạn có thể xem thông tin học tập, upload file điểm để tạo dữ liệu cá nhân, thử chọn học phần/lớp để xem thời khóa biểu mẫu và kiểm tra xung đột lịch.',
        quickFlowSteps: [
          'Đăng nhập tài khoản sinh viên.',
          { text: 'Vào Học tập → Xem điểm để xem điểm và upload file điểm (làm dữ liệu cho gợi ý).', strong: ['Học tập → Xem điểm', 'upload file điểm'] },
          { text: 'Vào Học tập → Chương trình đào tạo để xem CTĐT và các học phần.', strong: ['Học tập → Chương trình đào tạo'] },
          { text: 'Vào Lập kế hoạch đăng ký → Chọn học phần (mẫu) để chọn trước các môn dự định học.', strong: ['Lập kế hoạch đăng ký → Chọn học phần (mẫu)'] },
          { text: 'Vào Lập kế hoạch đăng ký → Chọn lớp (mẫu) để chọn lớp và kiểm tra lịch.', strong: ['Lập kế hoạch đăng ký → Chọn lớp (mẫu)'] },
          { text: 'Vào Học tập → Thời khóa biểu để xem thời khóa biểu mẫu bạn đã chọn.', strong: ['Học tập → Thời khóa biểu'] },
        ],
        studyBlocks: [
          { title: 'Thời khóa biểu', body: 'Hiển thị thời khóa biểu mẫu dựa trên các lớp bạn đã chọn.' },
          {
            title: 'Xem điểm (Upload điểm)',
            body: 'Upload file điểm giúp hệ thống biết bạn đã học những học phần nào và kết quả ra sao để đưa ra gợi ý phù hợp hơn.',
          },
          { title: 'Chương trình đào tạo', body: 'Xem học phần trong CTĐT để lên kế hoạch học kỳ.' },
        ],
        plannerBlocks: [
          {
            title: 'Chọn học phần (mẫu)',
            body: 'Chọn trước các học phần dự định học để so sánh nhiều phương án và đánh giá khối lượng học tập/tiến độ.',
          },
          {
            title: 'Chọn lớp (mẫu)',
            body: 'Bạn có thể thử nhiều lớp để kiểm tra xem lịch có “ổn” không, ví dụ:',
            bullets: ['Trùng giờ giữa các lớp (xung đột lịch).', 'Lịch quá dày trong một ngày/tuần.', 'Khoảng trống quá lớn giữa các ca học.'],
          },
        ],
        chatbotText: 'Chatbot có thể hỗ trợ hướng dẫn sử dụng, giải đáp thắc mắc và gợi ý kế hoạch học tập (tham khảo).',
        chatbotNote: 'Chatbot và website không có quyền đăng ký học phần/lớp thật thay bạn.',
        supportBullets: [
          { title: 'Những câu hỏi thường gặp', body: 'Các câu hỏi phổ biến khi sử dụng hệ thống.' },
          { title: 'Phản hồi và góp ý', body: 'Gửi lỗi, góp ý tính năng, hoặc phản ánh trải nghiệm cho admin.' },
        ],
        noteTitle: 'Lưu ý quan trọng',
        notes: [
          '“Đăng ký” trong website là đăng ký mẫu/lập kế hoạch, không phải đăng ký thật.',
          'Quyết định đăng ký thật vẫn thực hiện trên hệ thống chính thức.',
          'Dữ liệu bạn upload (ví dụ file điểm) được dùng để cá nhân hóa gợi ý.',
        ],
      },
    },
  },
  en: {
    nav: {
      study: 'Study',
      registration: 'Registration Planner',
      forms: 'Forms',
      scholarships: 'Scholarships',
      support: 'Support',
      changePassword: 'Change Password',
      logout: 'Logout',
      schedule: 'Schedule',
      grades: 'Grades',
      curriculum: 'Curriculum',
      subjectRegistration: 'Pick Subjects (Mock)',
      classRegistration: 'Pick Classes (Mock)',
      userGuide: 'User Guide',
      faq: 'FAQ',
      feedback: 'Feedback',
    },
    common: {
      loading: 'Loading...',
      close: 'Close',
      save: 'Save',
      cancel: 'Cancel',
      confirm: 'Confirm',
      back: 'Back',
      search: 'Search',
      upload: 'Upload',
      daysOfWeekShort: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
      daysOfWeekFull: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
    },
    pages: {
      userGuide: {
        title: 'USER GUIDE',
        subtitle:
          'This website helps you plan and get suggestions for subject/class registration. It is for reference only and does not replace official registration.',
        sectionOverview: '1) Overview',
        sectionQuickFlow: '2) Quick flow',
        sectionStudy: '3) Study',
        sectionPlanner: '4) Registration planner (mock)',
        sectionChatbot: '5) Chatbot',
        sectionSupport: '6) Support',
        overviewText:
          'You can view your study info, upload a grades file to build your personal data, and try picking subjects/classes to preview a mock schedule and check conflicts.',
        quickFlowSteps: [
          'Sign in with your student account.',
          { text: 'Go to Study → Grades to view results and upload a grades file (used for suggestions).', strong: ['Study → Grades', 'upload a grades file'] },
          { text: 'Go to Study → Curriculum to review your curriculum and subjects.', strong: ['Study → Curriculum'] },
          { text: 'Go to Registration Planner → Pick Subjects (Mock) to draft planned subjects.', strong: ['Registration Planner → Pick Subjects (Mock)'] },
          { text: 'Go to Registration Planner → Pick Classes (Mock) to pick specific classes and check time.', strong: ['Registration Planner → Pick Classes (Mock)'] },
          { text: 'Go to Study → Schedule to see your planned schedule.', strong: ['Study → Schedule'] },
        ],
        studyBlocks: [
          { title: 'Schedule', body: 'Shows a mock schedule based on the classes you picked.' },
          { title: 'Grades (Upload)', body: 'Uploading your grades helps personalize suggestions and planning.' },
          { title: 'Curriculum', body: 'Review your curriculum subjects to plan upcoming terms.' },
        ],
        plannerBlocks: [
          { title: 'Pick Subjects (Mock)', body: 'Draft subjects you plan to take to compare options and workload.' },
          {
            title: 'Pick Classes (Mock)',
            body: 'Try different class options to see if the timetable looks good, for example:',
            bullets: ['Time conflicts between classes.', 'Overly dense weekly schedule.', 'Large gaps between sessions.'],
          },
        ],
        chatbotText: 'The chatbot can guide usage, answer questions, and suggest study plans (for reference).',
        chatbotNote: 'The chatbot/website cannot perform official registration on your behalf.',
        supportBullets: [
          { title: 'FAQ', body: 'Common questions about using the system.' },
          { title: 'Feedback', body: 'Report bugs, suggest features, or send feedback to admin.' },
        ],
        noteTitle: 'Important notes',
        notes: [
          'Registration in this website is a mock plan, not official registration.',
          'You still register officially on the university system.',
          'Uploaded data (e.g., grades file) is used to personalize suggestions.',
        ],
      },
    },
  },
}

export const useStudentLanguage = () => {
  const [language, setLanguage] = useState<Language>('vi')

  const changeLanguage = (newLanguage: Language) => {
    setLanguage(newLanguage)
  }

  return {
    language,
    changeLanguage,
    t: texts[language],
  }
}
