import { useState } from 'react'

export type Language = 'vi' | 'en'

export interface StudentTranslations {
  study: string
  registration: string
  forms: string
  scholarships: string
  support: string
  schedule: string
  grades: string
  curriculum: string
  subjectRegistration: string
  classRegistration: string
  userGuide: string
  faq: string
  feedback: string
  logout: string
}

const texts: Record<Language, StudentTranslations> = {
  vi: {
    study: 'Học tập',
    registration: 'Lập kế hoạch đăng ký',
    forms: 'Biểu mẫu',
    scholarships: 'Học bổng',
    support: 'Hỗ trợ',
    schedule: 'Thời khóa biểu',
    grades: 'Xem điểm',
    curriculum: 'Chương trình đào tạo',
    subjectRegistration: 'Chọn học phần (mẫu)',
    classRegistration: 'Chọn lớp (mẫu)',
    userGuide: 'Hướng dẫn sử dụng',
    faq: 'Những câu hỏi thường gặp',
    feedback: 'Phản hồi và góp ý',
    logout: 'Đăng xuất',
  },
  en: {
    study: 'Study',
    registration: 'Registration Planner',
    forms: 'Forms',
    scholarships: 'Scholarships',
    support: 'Support',
    schedule: 'Schedule',
    grades: 'Grades',
    curriculum: 'Curriculum',
    subjectRegistration: 'Pick Subjects (Mock)',
    classRegistration: 'Pick Classes (Mock)',
    userGuide: 'User Guide',
    faq: 'Frequently Asked Questions',
    feedback: 'Feedback',
    logout: 'Logout',
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

