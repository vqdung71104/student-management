import { useState } from 'react'

export type Language = 'vi' | 'en'

export interface Translations {
  dashboard: string
  studentManagement: string
  subjectManagement: string
  settings: string
  chatbotSupport: string
  create: string
  update: string
  delete: string
  get: string
  updateSchedule: string
  updateSubjects: string
  languageSettings: string
  changePassword: string
  logout: string
}

const texts: Record<Language, Translations> = {
  vi: {
    dashboard: 'Bảng điều khiển',
    studentManagement: 'Quản lý sinh viên',
    subjectManagement: 'Quản lý học phần',
    settings: 'Cài đặt',
    chatbotSupport: 'Chatbot hỗ trợ',
    create: 'Tạo mới',
    update: 'Cập nhật',
    delete: 'Xóa',
    get: 'Danh sách',
    updateSchedule: 'Cập nhật thời khóa biểu',
    updateSubjects: 'Cập nhật danh sách học phần',
    languageSettings: 'Cài đặt ngôn ngữ',
    changePassword: 'Đổi mật khẩu',
    logout: 'Đăng xuất'
  },
  en: {
    dashboard: 'Dashboard',
    studentManagement: 'Student Management',
    subjectManagement: 'Subject Management',
    settings: 'Settings',
    chatbotSupport: 'Chatbot Support',
    create: 'Create',
    update: 'Update',
    delete: 'Delete',
    get: 'List',
    updateSchedule: 'Update Schedule',
    updateSubjects: 'Update Subject List',
    languageSettings: 'Language Settings',
    changePassword: 'Change Password',
    logout: 'Logout'
  }
}

export const useLanguage = () => {
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