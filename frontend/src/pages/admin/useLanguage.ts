import { useState } from 'react'

export type Language = 'vi' | 'en'

export interface Translations {
  nav: {
    dashboard: string
    studentManagement: string
    subjectManagement: string
    settings: string
    chatbotSupport: string
    logout: string
    updateSchedule: string
    updateSubjects: string
    languageSettings: string
    changePassword: string
    infoManagement: string
    scholarshipManagement: string
    internshipManagement: string
    projectManagement: string
  }
  common: {
    create: string
    update: string
    delete: string
    get: string
  }
}

const texts: Record<Language, Translations> = {
  vi: {
    nav: {
      dashboard: 'Bảng điều khiển',
      studentManagement: 'Quản lý sinh viên',
      subjectManagement: 'Quản lý học phần',
      settings: 'Cài đặt',
      chatbotSupport: 'Chatbot hỗ trợ',
      logout: 'Đăng xuất',
      updateSchedule: 'Cập nhật thời khóa biểu',
      updateSubjects: 'Cập nhật danh sách học phần',
      languageSettings: 'Cài đặt ngôn ngữ',
      changePassword: 'Đổi mật khẩu',
      infoManagement: 'Quản lý thông tin',
      scholarshipManagement: 'Quản lý học bổng',
      internshipManagement: 'Quản lý thực tập',
      projectManagement: 'Quản lý đồ án',
    },
    common: {
      create: 'Tạo mới',
      update: 'Cập nhật',
      delete: 'Xóa',
      get: 'Danh sách',
    },
  },
  en: {
    nav: {
      dashboard: 'Dashboard',
      studentManagement: 'Student Management',
      subjectManagement: 'Subject Management',
      settings: 'Settings',
      chatbotSupport: 'Chatbot Support',
      logout: 'Logout',
      updateSchedule: 'Update Schedule',
      updateSubjects: 'Update Subject List',
      languageSettings: 'Language Settings',
      changePassword: 'Change Password',
      infoManagement: 'Info Management',
      scholarshipManagement: 'Scholarship Management',
      internshipManagement: 'Internship Management',
      projectManagement: 'Project Management',
    },
    common: {
      create: 'Create',
      update: 'Update',
      delete: 'Delete',
      get: 'List',
    },
  },
}

export const useLanguage = () => {
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

