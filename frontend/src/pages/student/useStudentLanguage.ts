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
    registration: 'Đăng ký học tập',
    forms: 'Biểu mẫu',
    scholarships: 'Học bổng',
    support: 'Hỗ trợ',
    schedule: 'Thời khóa biểu',
    grades: 'Xem điểm',
    curriculum: 'Chương trình đào tạo',
    subjectRegistration: 'Đăng ký học phần',
    classRegistration: 'Đăng ký lớp',
    userGuide: 'Hướng dẫn sử dụng',
    faq: 'Những câu hỏi thường gặp',
    feedback: 'Phản hồi và góp ý',
    logout: 'Đăng xuất'
  },
  en: {
    study: 'Study',
    registration: 'Course Registration',
    forms: 'Forms',
    scholarships: 'Scholarships',
    support: 'Support',
    schedule: 'Schedule',
    grades: 'Grades',
    curriculum: 'Curriculum',
    subjectRegistration: 'Subject Registration',
    classRegistration: 'Class Registration',
    userGuide: 'User Guide',
    faq: 'Frequently Asked Questions',
    feedback: 'Feedback',
    logout: 'Logout'
  }
}

export const useStudentLanguage = () => {
  const [language, setLanguage] = useState<Language>('vi')

  const changeLanguage = (newLanguage: Language) => {
    setLanguage(newLanguage)
  }

  return {
    language,
    changeLanguage,
    t: texts[language]
  }
}